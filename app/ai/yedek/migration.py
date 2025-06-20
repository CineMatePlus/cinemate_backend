import pandas as pd
from pymongo import MongoClient
import json

def migrate_csv_to_mongodb():
    """
    Reads movie data from a large CSV file in chunks, processes it,
    and inserts it into a MongoDB collection.
    """
    # --- Configuration ---
    csv_file_path = 'app/ai/control/TMDB_movie_dataset_v11.csv'
    mongo_uri = "mongodb://localhost:27017/"
    db_name = "CineMateDB"
    collection_name = "movie_top_100_deneme"
    chunk_size = 1000  # Process 1000 rows at a time

    # --- MongoDB Connection ---
    try:
        client = MongoClient(mongo_uri)
        db = client[db_name]
        collection = db[collection_name]
        print("MongoDB'ye başarıyla bağlanıldı.")
        # Optional: Create an index on movie titles for faster lookups
        collection.create_index("title")
        print(f"'{collection_name}' koleksiyonunda 'title' için dizin oluşturuldu veya zaten var.")
    except Exception as e:
        print(f"MongoDB bağlantı hatası: {e}")
        return

    # --- Data Processing and Migration ---
    try:
        print(f"'{csv_file_path}' dosyasından veri okuma ve taşıma işlemi başlıyor...")
        total_rows_processed = 0
        
        # Drop the collection if it exists to avoid duplicates on re-run
        collection.drop()
        print(f"Mevcut '{collection_name}' koleksiyonu temizlendi.")

        for chunk in pd.read_csv(csv_file_path, chunksize=chunk_size):
            # Clean and transform data
            chunk = chunk.where(pd.notnull(chunk), None) # Replace NaN with None for MongoDB compatibility

            # Convert types
            for col in ['vote_average', 'popularity']:
                chunk[col] = pd.to_numeric(chunk[col], errors='coerce')
            
            for col in ['id', 'vote_count', 'revenue', 'runtime', 'budget']:
                 chunk[col] = pd.to_numeric(chunk[col], errors='coerce').astype('Int64')

            chunk['adult'] = chunk['adult'].apply(lambda x: x if isinstance(x, bool) else str(x).lower() == 'true')
            chunk['release_date'] = pd.to_datetime(chunk['release_date'], errors='coerce')
            # Convert NaT to None before inserting to MongoDB
            chunk['release_date'] = chunk['release_date'].apply(lambda x: x if pd.notnull(x) else None)

            # Split string fields into arrays. Handle potential errors if data is not a string.
            for col in ['genres', 'production_companies', 'production_countries', 'spoken_languages', 'keywords']:
                 chunk[col] = chunk[col].apply(lambda x: [item.strip() for item in x.split(',')] if isinstance(x, str) else [])

            # Convert DataFrame to a list of dictionaries
            records = chunk.to_dict('records')

            # Final cleaning of NaT values from records before inserting
            for record in records:
                for key, value in record.items():
                    # Check if value is a scalar (not a list/array) before calling pd.isna
                    if not isinstance(value, list) and pd.isna(value):
                        record[key] = None
            
            # Insert records into MongoDB
            if records:
                collection.insert_many(records)
                total_rows_processed += len(records)
                print(f"{total_rows_processed} satır işlendi ve MongoDB'ye eklendi.")

        print("\nVeri taşıma işlemi başarıyla tamamlandı!")
        print(f"Toplam {collection.count_documents({})} belge '{collection_name}' koleksiyonuna eklendi.")

    except FileNotFoundError:
        print(f"Hata: '{csv_file_path}' dosyası bulunamadı.")
    except Exception as e:
        print(f"Veri işleme sırasında bir hata oluştu: {e}")
    finally:
        # --- Close Connection ---
        client.close()
        print("MongoDB bağlantısı kapatıldı.")


if __name__ == '__main__':
    print("#################################################################")
    print("Bu betiği çalıştırmadan önce 'pandas' ve 'pymongo' kütüphanelerinin")
    print("kurulu olduğundan emin olun.")
    print("Kurulum için: pip install pandas pymongo")
    print("#################################################################\n")
    migrate_csv_to_mongodb()
