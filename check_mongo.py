from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import asyncio
from app.core.config import settings


async def check_data():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client.cinetest

    # user_contents koleksiyonundan bir kayıt al
    user_content = await db.user_contents.find_one()
    print("User Content:", user_content)

    if user_content:
        # İlgili content'i bul
        content_id = user_content.get("content_id")
        print("Content ID:", content_id)
        print("Content ID type:", type(content_id))

        # İçeriği farklı şekillerde arayalım
        content = await db.contents.find_one({"_id": ObjectId(content_id)})
        print("Content with ObjectId:", content)

        # contents koleksiyonundaki tüm kayıtları kontrol edelim
        all_contents = await db.contents.find().to_list(length=10)
        print("\nFirst 10 contents:")
        for c in all_contents:
            print(f"ID: {c['_id']}, Type: {type(c['_id'])}")

    client.close()


asyncio.run(check_data())
