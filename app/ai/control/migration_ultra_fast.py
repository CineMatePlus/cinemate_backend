import pandas as pd
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
import torch
import numpy as np
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing as mp
from typing import List, Dict, Any, Tuple
import time
from tqdm import tqdm
import gc
import queue
import threading
from dataclasses import dataclass
import os
import math


@dataclass
class ProcessedBatch:
    """İşlenmiş batch'i temsil eden data class"""
    records: List[Dict[str, Any]]
    texts: List[str]
    batch_id: int
    chunk_start: int
    chunk_end: int


def get_csv_chunk_ranges(csv_file_path: str, num_processes: int) -> List[Tuple[int, int]]:
    """CSV dosyasını process sayısına göre chunk'lara böler"""
    total_rows = sum(1 for _ in open(csv_file_path, encoding='utf-8')) - 1  # -1 for header
    
    # Daha küçük chunk'lar için ideal chunk size hesapla
    ideal_chunk_size = min(5000, max(1000, total_rows // (num_processes * 2)))
    num_chunks = math.ceil(total_rows / ideal_chunk_size)
    
    # Minimum process sayısını kullan
    actual_processes = min(num_processes, num_chunks)
    chunk_size = math.ceil(total_rows / actual_processes)
    
    ranges = []
    for i in range(actual_processes):
        start_row = i * chunk_size + 1  # +1 for header
        end_row = min((i + 1) * chunk_size, total_rows)
        if start_row <= total_rows:
            ranges.append((start_row, end_row))
    
    return ranges


def process_csv_chunk(args: Tuple[str, int, int, int]) -> ProcessedBatch:
    """
    CSV'nin belirli bir chunk'ını işleyen worker function
    """
    csv_file_path, start_row, end_row, batch_id = args
    
    try:
        # İlgili chunk'ı oku
        chunk = pd.read_csv(
            csv_file_path, 
            skiprows=range(1, start_row),  # Skip rows before our chunk
            nrows=end_row - start_row + 1,
            encoding='utf-8'
        )
        
        # Veri tiplerini optimize et
        chunk = optimize_dataframe_dtypes(chunk)
        chunk = chunk.where(pd.notnull(chunk), None)
        
        # Metin işleme
        chunk = process_text_columns_vectorized(chunk)
        
        # Paralel olarak metinleri ve record'ları hazırla
        with ThreadPoolExecutor(max_workers=min(4, mp.cpu_count())) as executor:
            future_texts = executor.submit(prepare_embedding_texts_parallel, chunk)
            future_records = executor.submit(prepare_records_parallel, chunk)
            
            texts = future_texts.result()
            records = future_records.result()
        
        return ProcessedBatch(
            records=records,
            texts=texts,
            batch_id=batch_id,
            chunk_start=start_row,
            chunk_end=end_row
        )
        
    except Exception as e:
        print(f"❌ Chunk {batch_id} işleme hatası: {e}")
        return ProcessedBatch(
            records=[],
            texts=[],
            batch_id=batch_id,
            chunk_start=start_row,
            chunk_end=end_row
        )


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


def prepare_embedding_texts_parallel(df_chunk: pd.DataFrame) -> List[str]:
    """Embedding için metinleri paralel olarak hazırlar"""
    def process_row(row_data):
        _, row = row_data
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
        return embedding_text if embedding_text.strip() else ""
    
    # Paralel işleme
    with ThreadPoolExecutor(max_workers=min(8, mp.cpu_count())) as executor:
        texts = list(executor.map(process_row, df_chunk.iterrows()))
    
    return texts


def prepare_records_parallel(df_chunk: pd.DataFrame) -> List[Dict[str, Any]]:
    """Record'ları paralel olarak hazırlar"""
    def process_row(row_data):
        _, row = row_data
        record = row.to_dict()
        
        # Handle NaN values
        for key, value in record.items():
            if not isinstance(value, list) and pd.isna(value):
                record[key] = None
        
        return record
    
    # Paralel işleme
    with ThreadPoolExecutor(max_workers=min(8, mp.cpu_count())) as executor:
        records = list(executor.map(process_row, df_chunk.iterrows()))
    
    return records


def multi_process_data_producer(csv_file_path: str, data_queue: queue.Queue, num_processes: int = 4):
    """
    Multi-process ile CSV'yi okuyup CPU tarafında hazırlayan producer
    """
    try:
        print(f"🚀 {num_processes} process ile paralel CSV okuma başlıyor...")
        
        # CSV'yi chunk'lara böl
        chunk_ranges = get_csv_chunk_ranges(csv_file_path, num_processes)
        print(f"📊 CSV {len(chunk_ranges)} chunk'a bölündü")
        
        # Process arguments hazırla
        process_args = [
            (csv_file_path, start_row, end_row, i) 
            for i, (start_row, end_row) in enumerate(chunk_ranges)
        ]
        
        # Multi-process execution
        with ProcessPoolExecutor(max_workers=num_processes) as executor:
            # Submit all jobs
            future_to_batch_id = {
                executor.submit(process_csv_chunk, args): args[3] 
                for args in process_args
            }
            
            # Collect results as they complete
            completed_batches = {}
            for future in as_completed(future_to_batch_id):
                batch_id = future_to_batch_id[future]
                try:
                    processed_batch = future.result()
                    completed_batches[batch_id] = processed_batch
                    print(f"✅ Chunk {batch_id} tamamlandı ({len(processed_batch.records)} kayıt)")
                except Exception as e:
                    print(f"❌ Chunk {batch_id} işlenemedi: {e}")
            
            # Sıralı şekilde queue'ya ekle (batch_id sırasına göre)
            for batch_id in sorted(completed_batches.keys()):
                processed_batch = completed_batches[batch_id]
                if processed_batch.records:  # Boş değilse ekle
                    data_queue.put(processed_batch, block=True)
                    print(f"📤 Batch {batch_id} GPU queue'ya eklendi")
        
        # İşlem bittiğini belirtmek için None gönder
        data_queue.put(None)
        print("🏁 Tüm chunk'lar işlendi, producer tamamlandı")
        
    except Exception as e:
        print(f"❌ Multi-process producer hatası: {e}")
        import traceback
        traceback.print_exc()
        data_queue.put(None)


def generate_embeddings_optimized(model: SentenceTransformer, texts: List[str], device: str, batch_size: int = 512) -> List[List[float]]:
    """
    GPU'yu maksimum kullanımla ve adaptive batch sizing ile embedding'leri oluşturur
    """
    embeddings = []
    
    # Boş text handling
    non_empty_indices = [i for i, text in enumerate(texts) if text.strip()]
    non_empty_texts = [texts[i] for i in non_empty_indices]
    
    if not non_empty_texts:
        return [None] * len(texts)
    
    # Adaptive batch sizing - CUDA OOM durumunda batch size'ı otomatik küçültür
    current_batch_size = batch_size
    
    for i in range(0, len(non_empty_texts), current_batch_size):
        batch_texts = non_empty_texts[i:i + current_batch_size]
        
        try:
            # GPU'da batch processing
            with torch.no_grad():  # Memory optimization
                batch_embeddings = model.encode(
                    batch_texts,
                    convert_to_tensor=True,
                    device=device,
                    show_progress_bar=False,
                    batch_size=current_batch_size,
                    normalize_embeddings=True
                ).cpu().numpy().tolist()
            
            embeddings.extend(batch_embeddings)
            
            # Başarılı batch sonrası memory temizliği
            if device == "cuda":
                torch.cuda.empty_cache()
        
        except RuntimeError as e:
            if "out of memory" in str(e):
                # CUDA OOM durumunda batch size'ı yarıya düşür
                current_batch_size = max(current_batch_size // 2, 32)
                print(f"⚠️  CUDA OOM! Batch size düşürülüyor: {current_batch_size}")
                
                # GPU memory'yi temizle
                if device == "cuda":
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()
                
                # Bu batch'i daha küçük parçalarda tekrar işle
                for j in range(i, min(i + len(batch_texts), len(non_empty_texts)), current_batch_size):
                    small_batch = non_empty_texts[j:j + current_batch_size]
                    try:
                        with torch.no_grad():
                            small_embeddings = model.encode(
                                small_batch,
                                convert_to_tensor=True,
                                device=device,
                                show_progress_bar=False,
                                batch_size=current_batch_size,
                                normalize_embeddings=True
                            ).cpu().numpy().tolist()
                        
                        embeddings.extend(small_embeddings)
                        
                        if device == "cuda":
                            torch.cuda.empty_cache()
                    
                    except RuntimeError as e2:
                        if "out of memory" in str(e2):
                            # Son çare: tek tek işle
                            current_batch_size = 1
                            print(f"🚨 Kritik memory durumu! Tek tek işleme geçiliyor...")
                            
                            for single_text in small_batch:
                                try:
                                    with torch.no_grad():
                                        single_embedding = model.encode(
                                            [single_text],
                                            convert_to_tensor=True,
                                            device=device,
                                            show_progress_bar=False,
                                            normalize_embeddings=True
                                        ).cpu().numpy().tolist()
                                    
                                    embeddings.extend(single_embedding)
                                    
                                    if device == "cuda":
                                        torch.cuda.empty_cache()
                                
                                except Exception as e3:
                                    print(f"❌ Tek text işlenemedi: {e3}")
                                    embeddings.append(None)
                        else:
                            raise e2
            else:
                raise e
    
    # Orijinal sıraya göre map et
    result_embeddings = [None] * len(texts)
    for i, embedding in enumerate(embeddings):
        result_embeddings[non_empty_indices[i]] = embedding
    
    return result_embeddings


def migrate_csv_to_mongodb_optimized():
    """
    Multi-process CPU + GPU pipeline optimize edilmiş CSV to MongoDB migration fonksiyonu
    """
    # --- Configuration ---
    csv_file_path = "app/ai/control/first_hundred.csv"
    mongo_uri = "mongodb://localhost:27017/"
    db_name = "CineMateDB"
    collection_name = "movie_embeddings"
    
    # Multi-process parametreleri
    num_cpu_processes = min(mp.cpu_count(), 12)  # Maximum 12 process'e çıkarıldı
    max_queue_size = 16  # Daha büyük queue
    
    # GPU memory'ye göre batch size'ı belirle
    if torch.cuda.is_available():
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3  # GB
        if gpu_memory >= 8:
            embedding_batch_size = 768  # 8GB+ için çok büyük batch (512'den artırıldı)
        elif gpu_memory >= 4:
            embedding_batch_size = 384  # 4-8GB için büyük batch (256'dan artırıldı)
        else:
            embedding_batch_size = 192  # 4GB altı için orta batch (128'den artırıldı)
    else:
        embedding_batch_size = 128

    print(f"🏗️  Multi-Process Pipeline Ayarları:")
    print(f"- CPU Processes: {num_cpu_processes}")
    print(f"- GPU Batch Size: {embedding_batch_size}")
    print(f"- Queue Size: {max_queue_size}")
    print(f"- CPU Cores: {mp.cpu_count()}")
    if torch.cuda.is_available():
        print(f"- GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

    # --- Load Embedding Model ---
    print("\n🤖 Embedding modeli yükleniyor...")
    model = SentenceTransformer("all-mpnet-base-v2")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    
    # Model optimization
    if device == "cuda":
        model.half()  # FP16 for faster inference
        torch.backends.cudnn.benchmark = True
        torch.backends.cudnn.deterministic = False
        
        # GPU memory optimization
        torch.cuda.empty_cache()
        torch.cuda.set_per_process_memory_fraction(0.98)  # %98'e çıkarıldı maksimum performans için
        
        # Memory fragmentation'ı azaltmak için
        os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'
    
    print(f"✅ Model başarıyla yüklendi. Kullanılan cihaz: {device}")

    # --- MongoDB Connection ---
    try:
        client = MongoClient(
            mongo_uri,
            maxPoolSize=50,
            maxIdleTimeMS=30000,
            waitQueueTimeoutMS=5000
        )
        db = client[db_name]
        collection = db[collection_name]
        print("✅ MongoDB'ye başarıyla bağlanıldı.")
        
        # Drop and recreate collection
        collection.drop()
        print(f"🗑️  Mevcut '{collection_name}' koleksiyonu temizlendi.")
        
    except Exception as e:
        print(f"❌ MongoDB bağlantı hatası: {e}")
        return

    # --- Multi-Process Pipeline Processing ---
    try:
        print(f"\n🚀 Multi-process pipeline migration başlıyor...")
        
        # Total row count
        total_rows = sum(1 for _ in open(csv_file_path, encoding='utf-8')) - 1
        print(f"📊 Toplam işlenecek satır sayısı: {total_rows}")
        
        # Multi-process producer-consumer queue
        data_queue = queue.Queue(maxsize=max_queue_size)
        
        # Multi-process producer thread'i başlat
        producer_thread = threading.Thread(
            target=multi_process_data_producer,
            args=(csv_file_path, data_queue, num_cpu_processes),
            daemon=True
        )
        producer_thread.start()
        
        total_rows_processed = 0
        start_time = time.time()
        successful_batches = 0
        failed_batches = 0
        
        # Progress tracking
        with tqdm(total=total_rows, desc="🔥 Multi-Process GPU Pipeline") as pbar:
            
            while True:
                # Queue'dan batch al
                try:
                    batch = data_queue.get(timeout=60)  # 60 saniye timeout (multi-process için daha uzun)
                    
                    if batch is None:  # Producer bitmiş
                        break
                    
                    batch_start_time = time.time()
                    
                    # GPU'da embedding generation
                    embeddings = generate_embeddings_optimized(
                        model, batch.texts, device, embedding_batch_size
                    )
                    
                    # Embedding'leri record'lara ekle
                    valid_records = []
                    for i, record in enumerate(batch.records):
                        if embeddings[i] is not None:
                            record["embedding"] = embeddings[i]
                            valid_records.append(record)
                    
                    # MongoDB'ye bulk insert
                    if valid_records:
                        collection.insert_many(valid_records, ordered=False)
                        total_rows_processed += len(valid_records)
                        successful_batches += 1
                        
                        # Performance metrics
                        batch_time = time.time() - batch_start_time
                        rows_per_second = len(valid_records) / batch_time
                        
                        pbar.update(len(valid_records))
                        pbar.set_postfix({
                            'RPS': f"{rows_per_second:.0f}",
                            'Batch_time': f"{batch_time:.1f}s",
                            'Success': successful_batches,
                            'Failed': failed_batches,
                            'Queue': data_queue.qsize()
                        })
                    else:
                        failed_batches += 1
                    
                    # Memory cleanup
                    del batch, embeddings, valid_records
                    data_queue.task_done()
                    
                    if device == "cuda":
                        torch.cuda.empty_cache()
                    
                    # Periodic garbage collection
                    if total_rows_processed % 10000 == 0:
                        gc.collect()
                    
                except queue.Empty:
                    print("⏰ Queue timeout - multi-process producer hala çalışıyor olabilir")
                    continue
                except Exception as e:
                    failed_batches += 1
                    print(f"❌ Batch işleme hatası: {e}")
                    continue

        # Producer thread'in bitmesini bekle
        producer_thread.join(timeout=30)

        # Create indexes
        print("\n📇 Indexler oluşturuluyor...")
        collection.create_index("title")
        collection.create_index("id", unique=True)
        print("✅ Indexler başarıyla oluşturuldu.")

        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n🎉 Multi-Process Pipeline Migration Başarıyla Tamamlandı!")
        print(f"📊 Toplam işlenen satır: {total_rows_processed:,}")
        print(f"✅ Başarılı batch'ler: {successful_batches}")
        print(f"❌ Başarısız batch'ler: {failed_batches}")
        print(f"⏱️  Toplam süre: {total_time:.2f} saniye ({total_time/60:.1f} dakika)")
        print(f"🚀 Ortalama hız: {total_rows_processed / total_time:.0f} satır/saniye")
        print(f"💾 Veritabanındaki toplam belge sayısı: {collection.count_documents({}):,}")

    except FileNotFoundError:
        print(f"❌ Hata: '{csv_file_path}' dosyası bulunamadı.")
    except Exception as e:
        print(f"❌ Multi-process pipeline işleme sırasında bir hata oluştu: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()
        print("🔒 MongoDB bağlantısı kapatıldı.")


def migrate_csv_to_mongodb():
    """
    Geriye dönük uyumluluk için eski fonksiyon adını korur
    """
    migrate_csv_to_mongodb_optimized()


if __name__ == "__main__":
    print("#################################################################")
    print("🔥 MULTI-PROCESS CPU + GPU PIPELINE OPTİMİZE EDİLMİŞ VERSİYON")
    print("Birden fazla CPU process ile paralel CSV okuma + GPU pipeline")
    print("Gerekli kütüphaneler: pip install pandas pymongo sentence-transformers tqdm")
    print("#################################################################\n")
    migrate_csv_to_mongodb_optimized()
