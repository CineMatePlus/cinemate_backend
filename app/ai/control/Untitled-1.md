mpnet_v2:
PS C:\Users\Berk\CineMate\cinemate_backend> & c:/Users/Berk/CineMate/cinemate_backend/.venv/Scripts/python.exe c:/Users/Berk/CineMate/cinemate_backend/app/ai/control/migration.py
#################################################################
PERFORMANS OPTİMİZE EDİLMİŞ VERSİYON
Gerekli kütüphaneler: pip install pandas pymongo sentence-transformers tqdm
#################################################################

Performans ayarları:
- Chunk size: 2000
- Embedding batch size: 64
- Max workers: 4
- CPU cores: 16
Embedding modeli yükleniyor...
Model başarıyla yüklendi. Kullanılan cihaz: cuda
MongoDB'ye başarıyla bağlanıldı.
Mevcut 'movie_embeddings' koleksiyonu temizlendi.
'app/ai/control/first_hundred.csv' dosyasından veri okuma ve taşıma işlemi başlıyor...
Toplam işlenecek satır sayısı: 99999
İşlenen satırlar: 100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 99999/99999 [03:36<00:00, 461.43it/s, RPS=450, Chunk_time=4.4s]

Indexler oluşturuluyor...
Indexler başarıyla oluşturuldu.

Veri taşıma işlemi başarıyla tamamlandı!
Toplam işlenen satır: 99999
Toplam süre: 220.03 saniye
Ortalama hız: 454 satır/saniye
Veritabanındaki toplam belge sayısı: 99999
MongoDB bağlantısı kapatıldı.
PS C:\Users\Berk\CineMate\cinemate_backend> 

all-MiniLM-L6-v2:

PS C:\Users\Berk\CineMate\cinemate_backend> & c:/Users/Berk/CineMate/cinemate_backend/.venv/Scripts/python.exe c:/Users/Berk/CineMate/cinemate_backend/app/ai/control/migration.py
#################################################################
PERFORMANS OPTİMİZE EDİLMİŞ VERSİYON
Gerekli kütüphaneler: pip install pandas pymongo sentence-transformers tqdm
#################################################################

Performans ayarları:
- Chunk size: 2000
- Embedding batch size: 64
- Max workers: 4
- CPU cores: 16
Embedding modeli yükleniyor...
Model başarıyla yüklendi. Kullanılan cihaz: cuda
MongoDB'ye başarıyla bağlanıldı.
Mevcut 'movie_embeddings_MiniLM-L6-v2' koleksiyonu temizlendi.
'app/ai/control/first_hundred.csv' dosyasından veri okuma ve taşıma işlemi başlıyor...
Toplam işlenecek satır sayısı: 99999
İşlenen satırlar: 100%|█████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 99999/99999 [01:01<00:00, 1619.15it/s, RPS=1816, Chunk_time=1.1s]

Indexler oluşturuluyor...
Indexler başarıyla oluşturuldu.

Veri taşıma işlemi başarıyla tamamlandı!
Toplam işlenen satır: 99999
Toplam süre: 63.03 saniye
Ortalama hız: 1587 satır/saniye
Veritabanındaki toplam belge sayısı: 99999
MongoDB bağlantısı kapatıldı.