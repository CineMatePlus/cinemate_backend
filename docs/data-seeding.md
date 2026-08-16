# Film Verisi Seed Rehberi

## Seed verisi

Seed işleminin tek varsayılan kaynağı `app/ai/control/first_hundred.csv` dosyasıdır.

CSV sütunlarındaki çoklu değerler `|` karakteriyle ayrılır. Zorunlu alanlar:

- `id`
- `title`
- `overview`
- `release_date` (`YYYY-MM-DD`)
- `genres`

Mobil istemcinin beklediği `vote_average`, `vote_count`, `runtime` ve dil alanlarının da kendi veri dosyanızda bulunması önerilir.

## Komutlar

Eski migration tarafından kullanılan 999 satırlık kataloğu doğrulayın:

```powershell
poetry run python scripts/seed_movies.py --dry-run
```

Ollama üzerinden embedding üretip MongoDB'ye aktarın:

```powershell
poetry run python scripts/seed_movies.py
```

Importer CSV'yi varsayılan olarak 2000 satırlık chunk'lar halinde okur,
embedding isteklerini 64'lük batch'ler halinde Ollama'ya gönderir ve her chunk
tamamlandığında MongoDB'ye yazar. Her kayıtta model, boyut ve embedding metninin
hash'i saklanır. Aynı komut yeniden çalıştırıldığında geçerli embedding'ler
atlanır; kesilen bir aktarım böylece kaldığı yerden devam eder.

Büyük kataloglar için ayarlar komut satırından değiştirilebilir:

```powershell
poetry run python scripts/seed_movies.py `
  --chunk-size 2000 `
  --embedding-batch-size 64 `
  --embedding-timeout 120 `
  --max-retries 3
```

- `--force-reembed`, geçerli olanlar dahil bütün film embedding'lerini yeniler.
- `--resume` varsayılan davranıştır; `--no-resume` metadata eşleşse bile yeniden
  embedding üretir.
- `--rebuild-user-embeddings`, film aktarımından sonra kullanıcı zevk vektörlerini
  güncel modeldeki beğenilmiş filmlerden yeniden hesaplar.
- `--continue-on-error`, retry ve batch bölme sonrasında hatalı kalan tekil
  filmleri embeddingsiz kaydederek aktarımı sürdürür.
- `--dry-run`, MongoDB ve Ollama'ya bağlanmadan CSV ile chunk/model/batch
  ayarlarını doğrular.

CSV yapısını MongoDB veya model indirmesi olmadan doğrulayın:

```powershell
poetry run python scripts/seed_movies.py --dry-run
```

Yalnızca listeleme ve detay ekranları için embedding olmadan yükleyin:

```powershell
poetry run python scripts/seed_movies.py --skip-embeddings
```

Yapılandırılmış Ollama modeliyle embedding üreterek yükleyin:

```powershell
ollama pull qwen3-embedding:0.6b
poetry run python scripts/seed_movies.py
```

Önceki örnek kayıtları temizleyip yeniden yükleyin:

```powershell
poetry run python scripts/seed_movies.py --reset
```

Komut yalnızca seçilen CSV'deki `id` değerlerini temizler;
kullanıcı tarafından eklenmiş diğer film kayıtlarını silmez.

## Çalışma biçimi

- Importer `first_hundred.csv` içindeki `id` alanı üzerinden upsert yapar.
- `first_hundred.csv` içindeki virgülle ayrılmış liste alanları eski migration ile aynı şekilde Python listelerine dönüştürülür.
- Bütçe, gelir, popülerlik, IMDb kimliği ve diğer katalog alanları korunur.
- Embedding üretimi `.env` içindeki Ollama URL'sini ve modelini kullanır.
- Varsayılan `qwen3-embedding:0.6b` her film için 1024 değer oluşturur.
- Model varsayılan olarak `EMBEDDING_KEEP_ALIVE=30m` süresince Ollama belleğinde tutulur.
- Donanımı (Metal, CUDA/ROCm veya CPU) backend değil Ollama seçer.
- `--skip-embeddings`, seed kayıtlarındaki embedding ve embedding metadata alanlarını kaldırır.
- `BAAI/bge-m3` ve Qwen3 aynı boyutta vektör üretse bile vektör uzayları
  uyumlu değildir. Model değişiminde `--force-reembed --rebuild-user-embeddings`
  birlikte kullanılarak film ve kullanıcı vektörleri aynı modelle üretilmelidir.
- MongoDB adresi ve veritabanı adı varsayılan olarak `.env` içindeki `MONGODB_URL` ve `MONGODB_DB` değerlerinden okunur.
