import asyncio
import os
import sys
from dotenv import load_dotenv

# Proje kök dizinini Python yoluna ekleyerek 'app' modülünün içe aktarılmasını sağlıyoruz.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.mongodb import get_database


async def list_unique_genres():
    """
    MongoDB veritabanındaki 'movies' koleksiyonuna bağlanır,
    tüm benzersiz 'genres' alanlarını çeker ve bunları yazdırır.
    """
    print("Veritabanına bağlanılıyor...")
    load_dotenv()
    db = get_database()

    print("Benzersiz film türleri çekiliyor...")
    try:
        # 'distinct' metodu, bir alan için tüm benzersiz değerleri verimli bir şekilde getirir.
        genres = await db.movies.distinct("genres")

        if genres:
            # Daha okunaklı bir çıktı için türleri alfabetik olarak sıralayalım.
            genres.sort()
            
            print("\n--- Sistemde Bulunan Film Türleri ---")
            for genre in genres:
                print(f"- {genre}")
            print("-------------------------------------\n")
        else:
            print("Veritabanında hiç film türü bulunamadı.")
            
    except Exception as e:
        print(f"Bir hata oluştu: {e}")

if __name__ == "__main__":
    # Asenkron fonksiyonu çalıştırmak için asyncio.run() kullanıyoruz.
    asyncio.run(list_unique_genres()) 