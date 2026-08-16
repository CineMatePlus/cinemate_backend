import asyncio
import os
import subprocess
import time

import requests
from behave import fixture, use_fixture
from motor.motor_asyncio import AsyncIOMotorClient


@fixture
def fastapi_server(context):
    port = os.getenv("TEST_API_PORT", "8011")
    mongodb_url = os.getenv("TEST_MONGODB_URL", "mongodb://localhost:27017")
    process_env = os.environ.copy()
    process_env.update(
        {
            "MONGODB_URL": mongodb_url,
            "MONGODB_DB": "cinetest",
            "EMBEDDING_WARMUP": "false",
        }
    )
    process = subprocess.Popen(
        ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", port],
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
    context.mongo_client = AsyncIOMotorClient(mongodb_url)
    context.db = context.mongo_client.cinetest
    yield context.db
    # Testler bittiğinde veritabanını temizle
    loop = asyncio.get_event_loop()
    loop.run_until_complete(context.mongo_client.drop_database("cinetest"))


def before_all(context):
    use_fixture(fastapi_server, context)
    use_fixture(mongodb_connection, context)
