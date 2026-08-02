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

CSV yapısını MongoDB veya model indirmesi olmadan doğrulayın:

```powershell
poetry run python scripts/seed_movies.py --dry-run
```

Yalnızca listeleme ve detay ekranları için embedding olmadan yükleyin:

```powershell
poetry run python scripts/seed_movies.py --skip-embeddings
```

BGE-M3 embedding'leriyle yükleyin:

```powershell
poetry run python scripts/seed_movies.py --device auto
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

- Kayıtlar `seed_id` üzerinden upsert edilir; komut tekrar çalıştırılabilir.
- Embedding üretimi `BAAI/bge-m3` kullanır ve her film için 1024 değer oluşturur.
- `--device auto`, erişilebiliyorsa CUDA'yı; aksi durumda CPU'yu seçer.
- `--skip-embeddings`, daha önce aynı seed ile yazılmış embedding alanlarını da kaldırır.
- MongoDB adresi ve veritabanı adı varsayılan olarak `.env` içindeki `MONGODB_URL` ve `MONGODB_DB` değerlerinden okunur.
