# Contributing

## Development setup

1. Create `.env` from `.env.example` and do not commit secrets.
2. Install Python 3.12 and Poetry 2.2.
3. Run `poetry install --with dev,test`.
4. Start Atlas Local with `docker compose up -d mongodb`.

## Before opening a pull request

```bash
poetry check --lock
poetry run black --check app scripts tests
poetry run isort --check-only app scripts tests
poetry run python -m compileall -q app scripts tests
poetry run python scripts/verify_seed.py
poetry run python -m unittest discover -s tests/unit -v
```

For database/auth changes, also run Behave against Atlas Local and verify the relevant Docker flow from the README. Keep production dependencies in `main`; test, development, and performance tools belong in their corresponding Poetry groups.

Commit only the approved 999-row seed. The full TMDB source dataset, local `.env`, reports, virtual environments, caches, and credentials must remain untracked.
