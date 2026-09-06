"""Build CineMate's deterministic 999-row seed from the canonical TMDB CSV."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_INPUT = HERE / "TMDB_movie_dataset_v11.csv"
DEFAULT_OUTPUT = HERE / "first_hundred.csv"
REQUIRED_COLUMNS = {"id", "title", "overview", "release_date", "genres"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write the first N valid, unique TMDB records deterministically."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--rows", type=int, default=999)
    args = parser.parse_args()
    if args.rows <= 0:
        parser.error("--rows must be positive")
    return args


def valid_row(row: dict[str, str | None]) -> bool:
    return all((row.get(column) or "").strip() for column in REQUIRED_COLUMNS)


def build_seed(source: Path, destination: Path, row_count: int) -> None:
    with source.open("r", encoding="utf-8", newline="") as source_handle:
        reader = csv.DictReader(source_handle)
        fieldnames = reader.fieldnames or []
        missing = REQUIRED_COLUMNS.difference(fieldnames)
        if missing:
            raise ValueError(f"Source CSV is missing columns: {sorted(missing)}")

        selected: list[dict[str, str | None]] = []
        seen_ids: set[str] = set()
        for row in reader:
            movie_id = (row.get("id") or "").strip()
            if not valid_row(row) or movie_id in seen_ids:
                continue
            seen_ids.add(movie_id)
            selected.append(row)
            if len(selected) == row_count:
                break

    if len(selected) != row_count:
        raise ValueError(
            f"Source supplied {len(selected)} valid unique rows; {row_count} required."
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as output_handle:
        writer = csv.DictWriter(
            output_handle,
            fieldnames=fieldnames,
            lineterminator="\n",
            quoting=csv.QUOTE_ALL,
        )
        writer.writeheader()
        writer.writerows(selected)
    print(f"Wrote {len(selected)} deterministic rows to {destination}.")


if __name__ == "__main__":
    arguments = parse_args()
    build_seed(arguments.input, arguments.output, arguments.rows)
