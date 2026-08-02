"""Seed CineMate with a small, redistributable sample movie catalog."""

from __future__ import annotations

import argparse
import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = PROJECT_ROOT / "data" / "sample_movies.csv"
MODEL_NAME = "BAAI/bge-m3"
EMBEDDING_DIMENSIONS = 1024
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
        description="Upsert sample movies into the CineMate movies collection."
    )
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--mongo-url", default=None)
    parser.add_argument("--database", default=None)
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda"),
        default="auto",
        help="Device used while generating BGE-M3 embeddings.",
    )
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Seed browseable data without downloading BGE-M3.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete only records created by this sample seed before upserting.",
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
    return [item.strip() for item in (value or "").split("|") if item.strip()]


def load_movies(csv_path: Path) -> list[dict[str, Any]]:
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    movies: list[dict[str, Any]] = []
    seen_seed_ids: set[str] = set()

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"seed_id", "title", "overview", "release_date", "genres"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV is missing required columns: {sorted(missing)}")

        for line_number, row in enumerate(reader, start=2):
            seed_id = (row.get("seed_id") or "").strip()
            title = (row.get("title") or "").strip()
            overview = (row.get("overview") or "").strip()
            if not seed_id or not title or not overview:
                raise ValueError(
                    f"Line {line_number}: seed_id, title and overview are required."
                )
            if seed_id in seen_seed_ids:
                raise ValueError(f"Line {line_number}: duplicate seed_id {seed_id!r}.")
            seen_seed_ids.add(seed_id)

            release_date = datetime.strptime(
                (row.get("release_date") or "").strip(), "%Y-%m-%d"
            )
            movie: dict[str, Any] = {
                "seed_id": seed_id,
                "seed_source": SEED_SOURCE,
                "title": title,
                "original_title": optional_text(row.get("original_title")) or title,
                "overview": overview,
                "release_date": release_date,
                "vote_average": float(row.get("vote_average") or 0),
                "vote_count": int(row.get("vote_count") or 0),
                "status": optional_text(row.get("status")) or "Released",
                "runtime": int(row.get("runtime") or 0),
                "adult": parse_bool(row.get("adult")),
                "original_language": optional_text(row.get("original_language")),
                "tagline": optional_text(row.get("tagline")),
                "poster_path": optional_text(row.get("poster_path")),
                "backdrop_path": optional_text(row.get("backdrop_path")),
                "popularity": 0.0,
                "num_likes": 0,
                "num_watches": 0,
            }
            for field in LIST_FIELDS:
                movie[field] = parse_list(row.get(field))
            movies.append(movie)

    if not movies:
        raise ValueError("CSV does not contain any movie rows.")
    return movies


def embedding_text(movie: dict[str, Any]) -> str:
    parts = [
        movie["title"],
        movie["original_title"],
        movie["overview"],
        movie.get("tagline"),
        ", ".join(movie["genres"]),
        ", ".join(movie["keywords"]),
        ", ".join(movie["production_companies"]),
        ", ".join(movie["production_countries"]),
        ", ".join(movie["spoken_languages"]),
        str(movie["release_date"].year),
    ]
    return ". ".join(str(part) for part in parts if part)


def add_embeddings(movies: list[dict[str, Any]], requested_device: str) -> str:
    import torch
    from sentence_transformers import SentenceTransformer

    if requested_device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA was requested but PyTorch cannot access a CUDA device."
        )
    device = (
        "cuda"
        if requested_device == "auto" and torch.cuda.is_available()
        else requested_device
    )
    if device == "auto":
        device = "cpu"

    print(f"Loading {MODEL_NAME} on {device}; the first run downloads the model...")
    model = SentenceTransformer(MODEL_NAME, device=device)
    vectors = model.encode(
        [embedding_text(movie) for movie in movies],
        batch_size=16,
        show_progress_bar=True,
    )
    for movie, vector in zip(movies, vectors, strict=True):
        embedding = vector.tolist()
        if len(embedding) != EMBEDDING_DIMENSIONS:
            raise RuntimeError(
                f"Unexpected embedding size {len(embedding)}; expected {EMBEDDING_DIMENSIONS}."
            )
        movie["embedding"] = embedding
    return device


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
        device = "disabled"
    else:
        device = add_embeddings(movies, args.device)

    mongo_url = args.mongo_url or os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    database_name = args.database or os.getenv("MONGODB_DB", "cinemate")
    client = MongoClient(mongo_url, serverSelectionTimeoutMS=10_000)
    try:
        client.admin.command("ping")
        collection = client[database_name]["movies"]
        collection.create_index("seed_id", unique=True, sparse=True)
        if args.reset:
            deleted = collection.delete_many({"seed_source": SEED_SOURCE}).deleted_count
            print(f"Removed {deleted} previous sample records.")

        operations = []
        for movie in movies:
            update: dict[str, Any] = {"$set": movie}
            if args.skip_embeddings:
                update["$unset"] = {"embedding": ""}
            operations.append(
                UpdateOne({"seed_id": movie["seed_id"]}, update, upsert=True)
            )
        result = collection.bulk_write(operations, ordered=False)
        print(
            f"Seeded {len(movies)} movies into {database_name}.movies "
            f"(inserted={result.upserted_count}, updated={result.modified_count}, "
            f"embedding_device={device})."
        )
    finally:
        client.close()


if __name__ == "__main__":
    main()
