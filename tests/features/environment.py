import asyncio
import os
import subprocess
import sys
import time
import uuid

import requests
from behave import fixture, use_fixture
from pymongo import AsyncMongoClient


@fixture
def fastapi_server(context):
    port = os.getenv("TEST_API_PORT", "8011")
    mongodb_url = os.getenv("TEST_MONGODB_URL", "mongodb://localhost:27017")
    process_env = os.environ.copy()
    process_env.update(
        {
            "MONGODB_URL": mongodb_url,
            "MONGODB_DB": context.test_db,
            "EMBEDDING_WARMUP": "false",
            "VECTOR_SEARCH_STARTUP_CHECK": "false",
        }
    )
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            port,
        ],
        env=process_env,
    )
    base_url = f"http://127.0.0.1:{port}"
    for _ in range(50):
        if process.poll() is not None:
            raise RuntimeError("The FastAPI test server exited before becoming ready.")
        try:
            if requests.get(base_url, timeout=0.2).status_code == 200:
                break
        except requests.RequestException:
            time.sleep(0.1)
    else:
        process.terminate()
        raise RuntimeError("The FastAPI test server did not become ready.")
    yield process
    process.terminate()
    process.wait(timeout=10)


@fixture
def mongodb_connection(context):
    # MongoDB bağlantısını test veritabanına yap
    mongodb_url = os.getenv("TEST_MONGODB_URL", "mongodb://localhost:27017")

    async def reset_database():
        client = AsyncMongoClient(mongodb_url)
        try:
            await client.drop_database(context.test_db)
        finally:
            await client.close()

    asyncio.run(reset_database())
    yield None
    asyncio.run(reset_database())


def before_all(context):
    context.test_db = "cinemate_test_" + uuid.uuid4().hex
    use_fixture(mongodb_connection, context)
    use_fixture(fastapi_server, context)
