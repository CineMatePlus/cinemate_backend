# Film Verisi Seed Rehberi

## Dahil edilen veri

`data/sample_movies.csv`, CineMate veri modelini göstermek amacıyla hazırlanmış sekiz sentetik film kaydı içerir. Veriler üçüncü taraf film kataloğundan kopyalanmamıştır ve uygulamanın geliştirme ortamını boş veritabanıyla başlatmamak için kullanılır.

CSV sütunlarındaki çoklu değerler `|` karakteriyle ayrılır. Zorunlu alanlar:

- `seed_id`
- `title`
- `overview`
- `release_date` (`YYYY-MM-DD`)
- `genres`

Mobil istemcinin beklediği `vote_average`, `vote_count`, `runtime` ve dil alanlarının da kendi veri dosyanızda bulunması önerilir.

## Komutlar

Eski migration tarafından kullanılan 999 satırlık kataloğu doğrulayın:

```powershell
poetry run python scripts/seed_movies.py --csv app/ai/control/first_hundred.csv --dry-run
```

Ollama üzerinden embedding üretip MongoDB'ye aktarın:

```powershell
poetry run python scripts/seed_movies.py --csv app/ai/control/first_hundred.csv
```

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

Komut yalnızca `seed_source=cinemate-sample-v1` kayıtlarını temizler; kullanıcı tarafından eklenmiş diğer film kayıtlarını silmez.

## Kendi CSV dosyanızı kullanma

Yalnızca kullanım ve yeniden dağıtım hakkına sahip olduğunuz bir veri kaynağı kullanın. Dosyanızı repo dışında tutabilir ve mutlak ya da proje köküne göre bağıl yol verebilirsiniz:

```powershell
poetry run python scripts/seed_movies.py --csv C:\data\authorized_movies.csv
```

`*.csv` genel olarak `.gitignore` kapsamındadır. Yalnızca yeniden dağıtımı güvenli olan `data/sample_movies.csv` Git'e özellikle dahil edilmiştir.

## Çalışma biçimi

- Importer `first_hundred.csv` için `id`, örnek CSV için `seed_id` alanını otomatik seçer ve bu alan üzerinden upsert yapar.
- `first_hundred.csv` içindeki virgülle ayrılmış liste alanları eski migration ile aynı şekilde Python listelerine dönüştürülür.
- Bütçe, gelir, popülerlik, IMDb kimliği ve diğer katalog alanları korunur.
- Embedding üretimi `.env` içindeki Ollama URL'sini ve modelini kullanır.
- Varsayılan `qwen3-embedding:0.6b` her film için 1024 değer oluşturur.
- Donanımı (Metal, CUDA/ROCm veya CPU) backend değil Ollama seçer.
- `--skip-embeddings`, seed kayıtlarındaki embedding alanını kaldırır.
- MongoDB adresi ve veritabanı adı varsayılan olarak `.env` içindeki `MONGODB_URL` ve `MONGODB_DB` değerlerinden okunur.
