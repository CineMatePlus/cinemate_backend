"""Stream a CineMate movie CSV into MongoDB with resumable embeddings."""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Iterator, Sequence

from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
DEFAULT_CSV = PROJECT_ROOT / "app" / "ai" / "control" / "first_hundred.csv"
DEFAULT_CHUNK_SIZE = 2000
EMBEDDING_METADATA_FIELDS = (
    "embedding",
    "embedding_model",
    "embedding_dimensions",
    "embedding_text_hash",
    "embedding_updated_at",
)
LIST_FIELDS = {
    "genres",
    "keywords",
    "production_companies",
    "production_countries",
    "spoken_languages",
}


@dataclass
class ImportStats:
    processed: int = 0
    embedded: int = 0
    skipped: int = 0
    failed: int = 0
    inserted: int = 0
    updated: int = 0
    embed_seconds: float = 0.0
    mongo_seconds: float = 0.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stream and upsert a CineMate movie CSV into MongoDB."
    )
    parser.add_argument("--mongo-url", default=None)
    parser.add_argument("--database", default=None)
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--embedding-batch-size", type=int, default=None)
    parser.add_argument("--embedding-timeout", type=float, default=None)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--force-reembed", action="store_true")
    parser.add_argument(
        "--resume",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Reuse matching embeddings (default); use --no-resume to regenerate.",
    )
    parser.add_argument("--continue-on-error", action="store_true")
    parser.add_argument(
        "--rebuild-user-embeddings",
        action="store_true",
        help="Recalculate every user taste vector after the movie import.",
    )
    parser.add_argument("--skip-embeddings", action="store_true")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.chunk_size <= 0:
        parser.error("--chunk-size must be positive")
    if args.embedding_batch_size is not None and args.embedding_batch_size <= 0:
        parser.error("--embedding-batch-size must be positive")
    if args.embedding_timeout is not None and args.embedding_timeout <= 0:
        parser.error("--embedding-timeout must be positive")
    if args.max_retries < 0:
        parser.error("--max-retries cannot be negative")
    if args.skip_embeddings and args.rebuild_user_embeddings:
        parser.error("--rebuild-user-embeddings cannot be used with --skip-embeddings")
    return args


def optional_text(value: str | None) -> str | None:
    cleaned = (value or "").strip()
    return cleaned or None


def parse_bool(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes"}


def parse_list(value: str | None) -> list[str]:
    raw = value or ""
    separator = "|" if "|" in raw else ","
    return [item.strip() for item in raw.split(separator) if item.strip()]


def parse_optional_int(value: str | None) -> int | None:
    cleaned = (value or "").strip()
    return int(cleaned) if cleaned else None


def parse_optional_float(value: str | None) -> float | None:
    cleaned = (value or "").strip()
    return float(cleaned) if cleaned else None


def _parse_movie(
    row: dict[str, str | None], line_number: int, identity_field: str
) -> dict[str, Any]:
    source_id = (row.get(identity_field) or "").strip()
    title = (row.get("title") or "").strip()
    overview = (row.get("overview") or "").strip()
    if not source_id or not title or not overview:
        raise ValueError(
            f"Line {line_number}: {identity_field}, title and overview are required."
        )
    try:
        release_date = datetime.strptime(
            (row.get("release_date") or "").strip(), "%Y-%m-%d"
        )
    except ValueError as exc:
        raise ValueError(f"Line {line_number}: invalid release_date.") from exc
    movie: dict[str, Any] = {
        "title": title,
        "original_title": optional_text(row.get("original_title")) or title,
        "overview": overview,
        "release_date": release_date,
        "vote_average": parse_optional_float(row.get("vote_average")),
        "vote_count": parse_optional_int(row.get("vote_count")),
        "status": optional_text(row.get("status")) or "Released",
        "revenue": parse_optional_int(row.get("revenue")),
        "runtime": parse_optional_int(row.get("runtime")),
        "adult": parse_bool(row.get("adult")),
        "budget": parse_optional_int(row.get("budget")),
        "homepage": optional_text(row.get("homepage")),
        "imdb_id": optional_text(row.get("imdb_id")),
        "original_language": optional_text(row.get("original_language")),
        "tagline": optional_text(row.get("tagline")),
        "poster_path": optional_text(row.get("poster_path")),
        "backdrop_path": optional_text(row.get("backdrop_path")),
        "popularity": parse_optional_float(row.get("popularity")),
        "num_likes": 0,
        "num_watches": 0,
    }
    try:
        movie["id"] = int(source_id)
    except ValueError as exc:
        raise ValueError(f"Line {line_number}: id must be an integer.") from exc
    for field in LIST_FIELDS:
        movie[field] = parse_list(row.get(field))
    return movie


def iter_movie_chunks(
    csv_path: Path, chunk_size: int
) -> Iterator[tuple[str, list[dict[str, Any]]]]:
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    seen_ids: set[str] = set()
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or [])
        identity_field = "id"
        required = {identity_field, "title", "overview", "release_date", "genres"}
        missing = required.difference(fieldnames)
        if missing:
            raise ValueError(f"CSV is missing required columns: {sorted(missing)}")
        chunk: list[dict[str, Any]] = []
        for line_number, row in enumerate(reader, start=2):
            source_id = (row.get(identity_field) or "").strip()
            if source_id in seen_ids:
                raise ValueError(
                    f"Line {line_number}: duplicate {identity_field} {source_id!r}."
                )
            seen_ids.add(source_id)
            chunk.append(_parse_movie(row, line_number, identity_field))
            if len(chunk) >= chunk_size:
                yield identity_field, chunk
                chunk = []
        if chunk:
            yield identity_field, chunk
        elif not seen_ids:
            raise ValueError("CSV does not contain any movie rows.")


def load_movies(csv_path: Path) -> list[dict[str, Any]]:
    """Compatibility helper; the actual importer uses streaming chunks."""
    return [
        m for _, chunk in iter_movie_chunks(csv_path, DEFAULT_CHUNK_SIZE) for m in chunk
    ]


def embedding_text(movie: dict[str, Any]) -> str:
    parts: list[str] = []
    field_order = (
        ("title", False),
        ("original_title", True),
        ("overview", False),
        ("genres", True),
        ("keywords", True),
        ("tagline", False),
        ("production_companies", True),
        ("production_countries", True),
        ("spoken_languages", True),
    )
    for field, include_label in field_order:
        value = movie.get(field)
        if isinstance(value, list):
            value = ", ".join(value)
        if value:
            parts.append(
                f"{field.replace('_', ' ').title()}: {value}"
                if include_label
                else str(value)
            )
    if movie.get("release_date"):
        parts.append(f"Released in {movie['release_date'].year}")
    if movie.get("adult"):
        parts.append("Adult Content")
    return ". ".join(parts)


def embedding_text_hash(text: str) -> str:
    normalized = "\n".join(line.rstrip() for line in text.strip().splitlines())
    return f"sha256:{hashlib.sha256(normalized.encode('utf-8')).hexdigest()}"


def embedding_is_current(
    existing: dict[str, Any] | None, *, model: str, dimensions: int, text_hash: str
) -> bool:
    if not existing:
        return False
    vector = existing.get("embedding")
    return (
        isinstance(vector, list)
        and len(vector) == dimensions
        and existing.get("embedding_model") == model
        and existing.get("embedding_dimensions") == dimensions
        and existing.get("embedding_text_hash") == text_hash
    )


async def _embed_with_retry(
    service: Any,
    texts: Sequence[str],
    *,
    max_retries: int,
    continue_on_error: bool,
) -> list[list[float] | None]:
    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return list(await service.embed_documents(texts))
        except Exception as exc:
            last_error = exc
            if attempt < max_retries:
                await asyncio.sleep(2**attempt)
    if len(texts) > 1:
        middle = len(texts) // 2
        left = await _embed_with_retry(
            service,
            texts[:middle],
            max_retries=max_retries,
            continue_on_error=continue_on_error,
        )
        right = await _embed_with_retry(
            service,
            texts[middle:],
            max_retries=max_retries,
            continue_on_error=continue_on_error,
        )
        return left + right
    if continue_on_error:
        print(f"WARNING: skipping one embedding after retries: {last_error}")
        return [None]
    assert last_error is not None
    raise last_error


async def embed_movies(
    service: Any,
    movies: list[dict[str, Any]],
    *,
    max_retries: int,
    continue_on_error: bool,
) -> int:
    failed = 0
    now = datetime.now(timezone.utc)
    for start in range(0, len(movies), service.batch_size):
        batch = movies[start : start + service.batch_size]
        texts = [embedding_text(movie) for movie in batch]
        vectors = await _embed_with_retry(
            service,
            texts,
            max_retries=max_retries,
            continue_on_error=continue_on_error,
        )
        for movie, text, vector in zip(batch, texts, vectors, strict=True):
            if vector is None:
                failed += 1
                movie["_embedding_failed"] = True
                continue
            movie["embedding"] = vector
            movie["embedding_model"] = service.model
            movie["embedding_dimensions"] = service.dimensions
            movie["embedding_text_hash"] = embedding_text_hash(text)
            movie["embedding_updated_at"] = now
    return failed


def _existing_embeddings(
    collection: Any, identity_field: str, movies: list[dict[str, Any]]
) -> dict[Any, dict[str, Any]]:
    ids = [movie[identity_field] for movie in movies]
    projection = {identity_field: 1, **{f: 1 for f in EMBEDDING_METADATA_FIELDS}}
    return {
        item[identity_field]: item
        for item in collection.find({identity_field: {"$in": ids}}, projection)
    }


def _format_progress(
    stats: ImportStats, started_at: float, *, total: int, batch_size: int
) -> str:
    elapsed = max(perf_counter() - started_at, 0.001)
    rate = stats.processed / elapsed
    remaining = max(total - stats.processed, 0)
    eta_seconds = remaining / rate if rate else 0
    return (
        f"processed={stats.processed}/{total} embedded={stats.embedded} "
        f"skipped={stats.skipped} failed={stats.failed} "
        f"batch={batch_size} speed={rate:.1f} movies/s eta={eta_seconds:.0f}s "
        f"embed_time={stats.embed_seconds:.1f}s mongo_time={stats.mongo_seconds:.1f}s"
    )


def validate_csv(csv_path: Path, chunk_size: int) -> tuple[int, str]:
    count = 0
    identity_field = ""
    for identity_field, chunk in iter_movie_chunks(csv_path, chunk_size):
        count += len(chunk)
    return count, identity_field


def rebuild_user_embeddings(
    database: Any, *, model: str, dimensions: int, bulk_size: int = 500
) -> tuple[int, int]:
    """Rebuild user taste vectors from liked movies in the current model space."""
    from app.services.vector_math import average_vectors

    rebuilt = 0
    cleared = 0
    operations = []
    for user in database.users.find({}, {"_id": 1}):
        movie_ids = [
            item["movie_id"]
            for item in database.interactions.find(
                {"user_id": user["_id"], "interaction_type": "like"},
                {"movie_id": 1},
            )
            if "movie_id" in item
        ]
        vectors = [
            movie["embedding"]
            for movie in database.movies.find(
                {
                    "_id": {"$in": movie_ids},
                    "embedding_model": model,
                    "embedding_dimensions": dimensions,
                },
                {"embedding": 1},
            )
            if isinstance(movie.get("embedding"), list)
            and len(movie["embedding"]) == dimensions
        ]
        if vectors:
            operations.append(
                UpdateOne(
                    {"_id": user["_id"]},
                    {
                        "$set": {
                            "embedding": average_vectors(vectors),
                            "embedding_model": model,
                            "embedding_dimensions": dimensions,
                            "embedding_updated_at": datetime.now(timezone.utc),
                        }
                    },
                )
            )
            rebuilt += 1
        else:
            operations.append(
                UpdateOne(
                    {"_id": user["_id"]},
                    {
                        "$unset": {
                            "embedding": "",
                            "embedding_model": "",
                            "embedding_dimensions": "",
                            "embedding_updated_at": "",
                        }
                    },
                )
            )
            cleared += 1
        if len(operations) >= bulk_size:
            database.users.bulk_write(operations, ordered=False)
            operations = []
    if operations:
        database.users.bulk_write(operations, ordered=False)
    return rebuilt, cleared


async def run_import(args: argparse.Namespace, csv_path: Path) -> ImportStats:
    service = None
    if not args.skip_embeddings:
        from app.services.embedding import EmbeddingProviderError, get_embedding_service

        service = get_embedding_service()
        try:
            health = await service.health()
        except EmbeddingProviderError as exc:
            raise RuntimeError(
                f"Ollama is not reachable. Start it and pull {service.model!r}."
            ) from exc
        if not health.get("model_installed"):
            raise RuntimeError(f"Ollama model {service.model!r} is not installed.")

    mongo_url = args.mongo_url or os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    database_name = args.database or os.getenv("MONGODB_DB", "cinemate")
    client = MongoClient(mongo_url, serverSelectionTimeoutMS=10_000)
    stats = ImportStats()
    started_at = perf_counter()
    indexed_fields: set[str] = set()
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        total_movies = sum(1 for _ in csv.DictReader(handle))
    try:
        client.admin.command("ping")
        collection = client[database_name]["movies"]
        for identity_field, movies in iter_movie_chunks(csv_path, args.chunk_size):
            if identity_field not in indexed_fields:
                collection.create_index(identity_field, unique=True, sparse=True)
                collection.create_index("title")
                indexed_fields.add(identity_field)
            existing = _existing_embeddings(collection, identity_field, movies)
            if args.reset:
                ids = [movie[identity_field] for movie in movies]
                collection.delete_many({identity_field: {"$in": ids}})
                existing = {}

            to_embed: list[dict[str, Any]] = []
            if service is not None:
                for movie in movies:
                    text_hash = embedding_text_hash(embedding_text(movie))
                    current = embedding_is_current(
                        existing.get(movie[identity_field]),
                        model=service.model,
                        dimensions=service.dimensions,
                        text_hash=text_hash,
                    )
                    if current and args.resume and not args.force_reembed:
                        stats.skipped += 1
                    else:
                        to_embed.append(movie)
                embed_started = perf_counter()
                failed = await embed_movies(
                    service,
                    to_embed,
                    max_retries=args.max_retries,
                    continue_on_error=args.continue_on_error,
                )
                stats.embed_seconds += perf_counter() - embed_started
                stats.failed += failed
                stats.embedded += len(to_embed) - failed

            operations = []
            for movie in movies:
                embedding_failed = movie.pop("_embedding_failed", False)
                counters = {
                    field: movie.pop(field)
                    for field in ("num_likes", "num_watches")
                    if field in movie
                }
                update: dict[str, Any] = {
                    "$set": movie,
                    "$setOnInsert": counters,
                }
                if args.skip_embeddings or embedding_failed:
                    update["$unset"] = {f: "" for f in EMBEDDING_METADATA_FIELDS}
                operations.append(
                    UpdateOne(
                        {identity_field: movie[identity_field]}, update, upsert=True
                    )
                )
            mongo_started = perf_counter()
            result = collection.bulk_write(operations, ordered=False)
            stats.mongo_seconds += perf_counter() - mongo_started
            stats.inserted += result.upserted_count
            stats.updated += result.modified_count
            stats.processed += len(movies)
            print(
                _format_progress(
                    stats,
                    started_at,
                    total=total_movies,
                    batch_size=service.batch_size if service is not None else 0,
                )
            )
        if args.rebuild_user_embeddings and service is not None:
            rebuilt, cleared = rebuild_user_embeddings(
                client[database_name],
                model=service.model,
                dimensions=service.dimensions,
            )
            print(f"User embeddings rebuilt={rebuilt} cleared={cleared}.")
    finally:
        client.close()
        if service is not None:
            from app.services.embedding import close_embedding_service

            await close_embedding_service()
    return stats


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    args = parse_args()
    if args.embedding_batch_size is not None:
        os.environ["EMBEDDING_BATCH_SIZE"] = str(args.embedding_batch_size)
    if args.embedding_timeout is not None:
        os.environ["EMBEDDING_TIMEOUT_SECONDS"] = str(args.embedding_timeout)
    csv_path = DEFAULT_CSV.resolve()
    if args.dry_run:
        count, identity_field = validate_csv(csv_path, args.chunk_size)
        batch = args.embedding_batch_size or os.getenv("EMBEDDING_BATCH_SIZE", "64")
        model = os.getenv("EMBEDDING_MODEL", "qwen3-embedding:0.6b")
        print(
            f"Validated {count} movies from {csv_path} "
            f"(identity={identity_field}, chunks={(count + args.chunk_size - 1) // args.chunk_size}, "
            f"chunk_size={args.chunk_size}, batch_size={batch}, model={model})."
        )
        print("No MongoDB connection or embedding request was performed.")
        return
    stats = asyncio.run(run_import(args, csv_path))
    backend = (
        "disabled"
        if args.skip_embeddings
        else os.getenv("EMBEDDING_MODEL", "qwen3-embedding:0.6b")
    )
    print(
        f"Seed complete: processed={stats.processed}, inserted={stats.inserted}, "
        f"updated={stats.updated}, embedded={stats.embedded}, skipped={stats.skipped}, "
        f"failed={stats.failed}, embedding_backend={backend}."
    )


if __name__ == "__main__":
    started_at = perf_counter()
    try:
        main()
    finally:
        print(f"Seed operation completed in {perf_counter() - started_at:.2f} seconds.")
