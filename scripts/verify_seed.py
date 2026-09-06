"""Verify the public seed artifact's immutable CI contract."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = PROJECT_ROOT / "app" / "ai" / "control" / "first_hundred.csv"
EXPECTED_ROWS = 999
EXPECTED_SHA256 = "85bb1130b8cc2b59621c1c94e5efad285103e8ad09f42634a7a6fd40769bc9aa"
REQUIRED_COLUMNS = {"id", "title", "overview", "release_date", "genres"}


def verify_seed(path: Path = SEED_PATH) -> None:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(
            f"Seed SHA-256 mismatch: expected {EXPECTED_SHA256}, got {digest}"
        )

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_COLUMNS.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Seed is missing required columns: {sorted(missing)}")
        rows = list(reader)

    if len(rows) != EXPECTED_ROWS:
        raise ValueError(f"Seed must contain {EXPECTED_ROWS} rows, found {len(rows)}")
    ids = [row["id"].strip() for row in rows]
    if any(not movie_id for movie_id in ids) or len(ids) != len(set(ids)):
        raise ValueError("Seed movie IDs must be non-empty and unique")
    for number, row in enumerate(rows, start=2):
        if any(not row[column].strip() for column in REQUIRED_COLUMNS):
            raise ValueError(f"Seed row {number} has an empty required value")
    print(
        f"Seed verified: rows={EXPECTED_ROWS} sha256={EXPECTED_SHA256} "
        f"columns={len(reader.fieldnames or [])}."
    )


if __name__ == "__main__":
    verify_seed()
