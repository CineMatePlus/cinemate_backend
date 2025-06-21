import pandas as pd
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
import torch
import numpy as np
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
from typing import List, Dict, Any
import time
from tqdm import tqdm
import gc


def optimize_dataframe_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """DataFrame'in memory kullanımını optimize eder"""
    # Numeric optimization
    for col in ["vote_average", "popularity"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype('float32')
    
    # Integer optimization with size checking
    integer_columns = {
        "id": "Int64",  # Can be very large
        "vote_count": "Int32", 
        "revenue": "Int64",  # Can be very large  
        "runtime": "Int32",
        "budget": "Int64"  # Can be very large
    }
    
    for col, dtype in integer_columns.items():
        if col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col], errors="coerce").astype(dtype)
            except (ValueError, TypeError):
                # If casting fails, use Int64 as fallback
                df[col] = pd.to_numeric(df[col], errors="coerce").astype('Int64')
    
    return df


def process_text_columns_vectorized(df: pd.DataFrame) -> pd.DataFrame:
    """Metin sütunlarını vektörize edilmiş şekilde işler"""
    # Adult column - boolean conversion
    if 'adult' in df.columns:
        df['adult'] = df['adult'].astype(str).str.lower() == 'true'
    
    # Date conversion
    if 'release_date' in df.columns:
        df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
    
    # List columns - vectorized processing
    list_columns = ["genres", "production_companies", "production_countries", "spoken_languages", "keywords"]
    for col in list_columns:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str).apply(
                lambda x: [item.strip() for item in x.split(",") if item.strip()] if x else []
            )
    
    return df


def prepare_embedding_texts_batch(df: pd.DataFrame) -> List[str]:
    """Embedding için tüm metinleri batch olarak hazırlar"""
    texts = []
    
    for _, row in df.iterrows():
        text_parts = []
        
        if pd.notna(row.get("title")):
            text_parts.append(str(row["title"]))
        if pd.notna(row.get("overview")):
            text_parts.append(str(row["overview"]))
        if row.get("genres"):
            text_parts.append("Genres: " + ", ".join(row["genres"]))
        if row.get("keywords"):
            text_parts.append("Keywords: " + ", ".join(row["keywords"]))
        if pd.notna(row.get("tagline")):
            text_parts.append("Tagline: " + str(row["tagline"]))
        
        embedding_text = ". ".join(text_parts)
        texts.append(embedding_text if embedding_text.strip() else "")
    
    return texts


def generate_embeddings_batch(model: SentenceTransformer, texts: List[str], device: str, batch_size: int = 32) -> List[List[float]]:
    """Batch halinde embedding'leri oluşturur"""
    embeddings = []
    
    # Empty text handling
    non_empty_indices = [i for i, text in enumerate(texts) if text.strip()]
    non_empty_texts = [texts[i] for i in non_empty_indices]
    
    if not non_empty_texts:
        return [None] * len(texts)
    
    # Batch processing
    for i in range(0, len(non_empty_texts), batch_size):
        batch_texts = non_empty_texts[i:i + batch_size]
        batch_embeddings = model.encode(
            batch_texts,
            convert_to_tensor=True,
            device=device,
            show_progress_bar=False,
            batch_size=min(batch_size, len(batch_texts))
        ).cpu().numpy().tolist()
        embeddings.extend(batch_embeddings)
    
    # Map back to original order
    result_embeddings = [None] * len(texts)
    for i, embedding in enumerate(embeddings):
        result_embeddings[non_empty_indices[i]] = embedding
    
    return result_embeddings


def process_chunk_optimized(chunk: pd.DataFrame, model: SentenceTransformer, device: str) -> List[Dict[str, Any]]:
    """Chunk'ı optimize edilmiş şekilde işler"""
    # Dtype optimization
    chunk = optimize_dataframe_dtypes(chunk)
    
    # Text processing
    chunk = process_text_columns_vectorized(chunk)
    
    # Batch embedding generation
    texts = prepare_embedding_texts_batch(chunk)
    embeddings = generate_embeddings_batch(model, texts, device, batch_size=64)
    
    # Record preparation
    records = []
    for i, (_, row) in enumerate(chunk.iterrows()):
        record = row.to_dict()
        
        # Handle NaN values
        for key, value in record.items():
            if not isinstance(value, list) and pd.isna(value):
                record[key] = None
        
        record["embedding"] = embeddings[i]
        records.append(record)
    
    return records


def migrate_csv_to_mongodb_optimized():
    """
    Optimize edilmiş CSV to MongoDB migration fonksiyonu
    """
    # --- Configuration ---
    csv_file_path = "app/ai/control/first_hundred.csv"
    mongo_uri = "mongodb://localhost:27017/"
    db_name = "tests"
    collection_name = "movie_embeddings"
    chunk_size = 2000  # Arttırıldı
    embedding_batch_size = 64  # GPU memory'ye göre ayarlanabilir
    max_workers = min(4, mp.cpu_count())  # CPU core sayısına göre

    print(f"Performans ayarları:")
    print(f"- Chunk size: {chunk_size}")
    print(f"- Embedding batch size: {embedding_batch_size}")
    print(f"- Max workers: {max_workers}")
    print(f"- CPU cores: {mp.cpu_count()}")

    # --- Load Embedding Model ---
    print("Embedding modeli yükleniyor...")
    model = SentenceTransformer("all-mpnet-base-v2")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    
    # Model optimization for inference
    if device == "cuda":
        model.half()  # FP16 for faster inference
        torch.backends.cudnn.benchmark = True
    
    print(f"Model başarıyla yüklendi. Kullanılan cihaz: {device}")

    # --- MongoDB Connection with optimization ---
    try:
        client = MongoClient(
            mongo_uri,
            maxPoolSize=50,  # Connection pool optimization
            maxIdleTimeMS=30000,
            waitQueueTimeoutMS=5000
        )
        db = client[db_name]
        collection = db[collection_name]
        print("MongoDB'ye başarıyla bağlanıldı.")
        
        # Drop and recreate collection
        collection.drop()
        print(f"Mevcut '{collection_name}' koleksiyonu temizlendi.")
        
    except Exception as e:
        print(f"MongoDB bağlantı hatası: {e}")
        return

    # --- Data Processing and Migration ---
    try:
        print(f"'{csv_file_path}' dosyasından veri okuma ve taşıma işlemi başlıyor...")
        
        # Get total row count for progress bar
        total_rows = sum(1 for _ in open(csv_file_path, encoding='utf-8')) - 1  # -1 for header
        print(f"Toplam işlenecek satır sayısı: {total_rows}")
        
        total_rows_processed = 0
        start_time = time.time()
        
        # Progress bar setup
        with tqdm(total=total_rows, desc="İşlenen satırlar") as pbar:
            
            for chunk in pd.read_csv(csv_file_path, chunksize=chunk_size, encoding='utf-8'):
                chunk_start_time = time.time()
                
                # Fill NaN values
                chunk = chunk.where(pd.notnull(chunk), None)
                
                # Process chunk
                records = process_chunk_optimized(chunk, model, device)
                
                # Bulk insert with ordered=False for better performance
                if records:
                    collection.insert_many(records, ordered=False)
                    total_rows_processed += len(records)
                    
                    chunk_time = time.time() - chunk_start_time
                    rows_per_second = len(records) / chunk_time
                    
                    pbar.update(len(records))
                    pbar.set_postfix({
                        'RPS': f"{rows_per_second:.0f}",
                        'Chunk_time': f"{chunk_time:.1f}s"
                    })
                
                # Memory cleanup
                del records, chunk
                gc.collect()
                if device == "cuda":
                    torch.cuda.empty_cache()

        # Create indexes after insertion for better performance
        print("\nIndexler oluşturuluyor...")
        collection.create_index("title")
        collection.create_index("id", unique=True)
        collection.create_index([("embedding", "2dsphere")])  # For vector similarity if needed
        print("Indexler başarıyla oluşturuldu.")

        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\nVeri taşıma işlemi başarıyla tamamlandı!")
        print(f"Toplam işlenen satır: {total_rows_processed}")
        print(f"Toplam süre: {total_time:.2f} saniye")
        print(f"Ortalama hız: {total_rows_processed / total_time:.0f} satır/saniye")
        print(f"Veritabanındaki toplam belge sayısı: {collection.count_documents({})}")

    except FileNotFoundError:
        print(f"Hata: '{csv_file_path}' dosyası bulunamadı.")
    except Exception as e:
        print(f"Veri işleme sırasında bir hata oluştu: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()
        print("MongoDB bağlantısı kapatıldı.")


def migrate_csv_to_mongodb():
    """
    Geriye dönük uyumluluk için eski fonksiyon adını korur
    """
    migrate_csv_to_mongodb_optimized()


if __name__ == "__main__":
    print("#################################################################")
    print("PERFORMANS OPTİMİZE EDİLMİŞ VERSİYON")
    print("Gerekli kütüphaneler: pip install pandas pymongo sentence-transformers tqdm")
    print("#################################################################\n")
    migrate_csv_to_mongodb_optimized()
