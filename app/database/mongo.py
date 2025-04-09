from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
db = client["cinemate"]

user_collection = db["users"]
collection_collection = db["collections"]
content_collection = db["contents"]


""" from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client["cinemate"]
user_collection = db["users"]
 """
