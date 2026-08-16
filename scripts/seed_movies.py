"""Import CineMate movie CSV files and optionally generate embeddings."""

from __future__ import annotations

import argparse
import asyncio
import csv
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
DEFAULT_CSV = PROJECT_ROOT / "data" / "sample_movies.csv"
SEED_SOURCE = "cinemate-sample-v1"
LIST_FIELDS = {
    "genres",
    "keywords",
    "production_companies",
    "production_countries",
    "spoken_languages",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Upsert a CineMate movie CSV into the movies collection."
    )
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--mongo-url", default=None)
    parser.add_argument("--database", default=None)
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Seed browseable data without calling the embedding service.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete records identified by the selected CSV before upserting them.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and summarize the CSV without connecting to MongoDB.",
    )
    return parser.parse_args()


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


def load_movies(csv_path: Path) -> list[dict[str, Any]]:
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    movies: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or [])
        identity_field = "seed_id" if "seed_id" in fieldnames else "id"
        required = {identity_field, "title", "overview", "release_date", "genres"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV is missing required columns: {sorted(missing)}")

        for line_number, row in enumerate(reader, start=2):
            source_id = (row.get(identity_field) or "").strip()
            title = (row.get("title") or "").strip()
            overview = (row.get("overview") or "").strip()
            if not source_id or not title or not overview:
                raise ValueError(
                    f"Line {line_number}: {identity_field}, title and overview are required."
                )
            if source_id in seen_ids:
                raise ValueError(
                    f"Line {line_number}: duplicate {identity_field} {source_id!r}."
                )
            seen_ids.add(source_id)

            release_date = datetime.strptime(
                (row.get("release_date") or "").strip(), "%Y-%m-%d"
            )
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
            if identity_field == "seed_id":
                movie["seed_id"] = source_id
                movie["seed_source"] = SEED_SOURCE
            else:
                movie["id"] = int(source_id)
            for field in LIST_FIELDS:
                movie[field] = parse_list(row.get(field))
            movies.append(movie)

    if not movies:
        raise ValueError("CSV does not contain any movie rows.")
    return movies


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
            if include_label:
                label = field.replace("_", " ").title()
                parts.append(f"{label}: {value}")
            else:
                parts.append(str(value))
    if movie.get("release_date"):
        parts.append(f"Released in {movie['release_date'].year}")
    if movie.get("adult"):
        parts.append("Adult Content")
    return ". ".join(str(part) for part in parts if part)


async def add_embeddings(movies: list[dict[str, Any]]) -> str:
    from app.services.embedding import (
        EmbeddingProviderError,
        close_embedding_service,
        get_embedding_service,
    )

    service = get_embedding_service()
    print(
        f"Requesting {service.model} embeddings from the configured "
        "embedding service..."
    )
    try:
        try:
            health = await service.health()
        except EmbeddingProviderError as exc:
            raise RuntimeError(
                "Ollama is not reachable. Start Ollama and run "
                f"'ollama pull {service.model}' before importing."
            ) from exc
        if not health.get("model_installed"):
            raise RuntimeError(
                f"Ollama model {service.model!r} is not installed. "
                f"Run: ollama pull {service.model}"
            )

        texts = [embedding_text(movie) for movie in movies]
        vectors: list[list[float]] = []
        for start in range(0, len(texts), service.batch_size):
            batch = texts[start : start + service.batch_size]
            vectors.extend(await service.embed_documents(batch))
            print(f"Embedded {min(start + len(batch), len(texts))}/{len(texts)} movies")
    finally:
        await close_embedding_service()

    for movie, vector in zip(movies, vectors, strict=True):
        movie["embedding"] = vector
    return service.model


def main() -> None:
    args = parse_args()
    load_dotenv(PROJECT_ROOT / ".env")
    csv_path = args.csv if args.csv.is_absolute() else PROJECT_ROOT / args.csv
    movies = load_movies(csv_path.resolve())

    if args.dry_run:
        print(f"Validated {len(movies)} movies from {csv_path}.")
        print("No MongoDB connection or model download was performed.")
        return

    if args.skip_embeddings:
        embedding_backend = "disabled"
    else:
        embedding_backend = asyncio.run(add_embeddings(movies))

    mongo_url = args.mongo_url or os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    database_name = args.database or os.getenv("MONGODB_DB", "cinemate")
    client = MongoClient(mongo_url, serverSelectionTimeoutMS=10_000)
    try:
        client.admin.command("ping")
        collection = client[database_name]["movies"]
        identity_field = "seed_id" if "seed_id" in movies[0] else "id"
        collection.create_index(identity_field, unique=True, sparse=True)
        collection.create_index("title")
        if args.reset:
            source_ids = [movie[identity_field] for movie in movies]
            deleted = collection.delete_many(
                {identity_field: {"$in": source_ids}}
            ).deleted_count
            print(f"Removed {deleted} records identified by the selected CSV.")

        operations = []
        for movie in movies:
            update: dict[str, Any] = {"$set": movie}
            if args.skip_embeddings:
                update["$unset"] = {"embedding": ""}
            operations.append(
                UpdateOne({identity_field: movie[identity_field]}, update, upsert=True)
            )
        result = collection.bulk_write(operations, ordered=False)
        print(
            f"Seeded {len(movies)} movies into {database_name}.movies "
            f"(inserted={result.upserted_count}, updated={result.modified_count}, "
            f"embedding_backend={embedding_backend})."
        )
    finally:
        client.close()


if __name__ == "__main__":
    main()
