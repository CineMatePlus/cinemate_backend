from behave import fixture, use_fixture
import subprocess
import time
import os
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio


@fixture
def fastapi_server(context):
    # FastAPI sunucusunu başlat
    process = subprocess.Popen(["uvicorn", "app.main:app", "--reload"])
    time.sleep(5)  # Sunucunun başlaması için bekle
    yield process
    # Testler bittiğinde sunucuyu kapat
    process.terminate()


@fixture
def mongodb_connection(context):
    # MongoDB bağlantısını test veritabanına yap
    context.mongo_client = AsyncIOMotorClient(
        "mongodb://localhost:27017"
    )
    context.db = context.mongo_client.cinetest
    yield context.db
    # Testler bittiğinde veritabanını temizle
    loop = asyncio.get_event_loop()
    loop.run_until_complete(context.mongo_client.drop_database("cinetest"))


def before_all(context):
    use_fixture(fastapi_server, context)
    use_fixture(mongodb_connection, context)
