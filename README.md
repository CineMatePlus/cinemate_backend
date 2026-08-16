# CineMate Backend

CineMate'in kimlik doğrulama, içerik, koleksiyon, yorum, kullanıcı etkileşimi ve yapay zeka destekli öneri işlevlerini sunan FastAPI servisidir.

## Gereksinimler

- Python 3.10 veya üzeri
- Poetry 2.x
- Docker Desktop (MongoDB Atlas Local ve Vector Search için)
- [Ollama](https://ollama.com/) ve `qwen3-embedding:0.6b` modeli

MongoDB Atlas Local sayesinde CRUD ve Vector Search özelliklerinin tamamı yerelde çalışır.

## 1. Bağımlılıkları kurma

Backend yalnızca platform bağımsız HTTP istemcisini kurar; PyTorch, CUDA veya
Sentence Transformers içermez:

```powershell
poetry install
```

Embedding runtime'ını ve modeli hazırlayın:

```powershell
ollama pull qwen3-embedding:0.6b
```

Ollama Windows ve Linux'ta desteklenen NVIDIA/AMD GPU'yu, Apple Silicon'da
Metal'i otomatik kullanır; uygun hızlandırıcı yoksa CPU'ya düşer.

## 2. Ortam ayarları

```powershell
Copy-Item .env.example .env
```

`.env` içinde en azından MongoDB bağlantısını ve JWT anahtarını düzenleyin:

```dotenv
MONGODB_URL=mongodb://localhost:27018/?directConnection=true
MONGODB_DB=cinemate
JWT_SECRET_KEY=replace-with-a-random-secret
EMBEDDING_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=qwen3-embedding:0.6b
```

Güvenli bir JWT anahtarı üretmek için:

```powershell
poetry run python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Atlas Local'i başlatın:

```powershell
docker compose up -d
```

`27018` portu, bilgisayarda çalışan mevcut MongoDB servisiyle çakışmaması için kullanılır.

## 3. Örnek film verisini yükleme

Eski migration kaynağındaki 999 filmi doğrulamak için:

```powershell
poetry run python scripts/seed_movies.py --csv app/ai/control/first_hundred.csv --dry-run
```

Filmleri Qwen3 embedding'leriyle veritabanına yazmak için:

```powershell
poetry run python scripts/seed_movies.py --csv app/ai/control/first_hundred.csv
```

Importer `id` tabanlı eski CSV şemasını otomatik algılar; sayısal alanları, tarihi
ve virgülle ayrılmış liste sütunlarını eski migration ile aynı veri tiplerine
dönüştürür. Metinler Ollama'ya batch halinde gönderilir ve 1024 boyutlu
embedding her film kaydına eklenir.

Yalnızca sekiz sentetik örnek filmi kullanmak isterseniz:

```powershell
poetry run python scripts/seed_movies.py --csv data/sample_movies.csv
```

Embedding olmadan yalnızca içerikleri yüklemek için herhangi bir CSV komutuna
`--skip-embeddings` ekleyebilirsiniz.

Import komutu eski CSV'de `id`, örnek CSV'de `seed_id` üzerinden upsert yaptığı
için güvenle tekrar çalıştırılabilir. Ayrıntılar için
[`docs/data-seeding.md`](docs/data-seeding.md) dosyasına bakın.

## 4. Vector Search indeksleri

Atlas Local sağlıklı duruma geldikten sonra gerekli iki indeksi oluşturun:

```powershell
poetry run python scripts/create_vector_indexes.py
```

Script aşağıdaki 1024 boyutlu cosine indekslerini oluşturur:

| Koleksiyon | İndeks | Alan |
| --- | --- | --- |
| `movies` | `movie_vector_index` | `embedding` |
| `users` | `user_vector_index` | `embedding` |

İndekslerin durumu `READY` olana kadar vektör sorgularını çalıştırmayın. Yerel ve Atlas kurulum adımları için [`docs/atlas-vector-search.md`](docs/atlas-vector-search.md) dosyasını kullanın.

## 5. API'yi çalıştırma

```powershell
poetry run uvicorn app.main:app --reload
```

Uygulama başladıktan sonra:

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`

Embedding sağlık kontrolü `http://localhost:8000/health/embedding` adresindedir.
`EMBEDDING_WARMUP=true` ayarlanırsa API başlangıçta bir deneme embedding'i üretir
ve Ollama/model hazır değilse başlangıcı durdurur. Varsayılan `false` olduğundan
embedding servisi kapalıyken CRUD endpoint'leri çalışmaya devam eder.

Backend Docker içinde, Ollama host işletim sisteminde çalışıyorsa
`EMBEDDING_BASE_URL=http://host.docker.internal:11434` kullanın. Apple Silicon'da
Metal hızlandırmasını korumak için Ollama'nın host üzerinde native çalışması önerilir.

## Testler

Davranış testleri çalışan bir MongoDB örneği kullanır:

```powershell
poetry run behave tests/features
```

Embedding birim testleri Ollama veya MongoDB gerektirmez:

```powershell
poetry run python -m unittest discover -s tests/unit -v
```

`run.bat`, Behave sonuçlarını Allure raporuna dönüştürmek için kullanılır ve sistemde Allure CLI bulunmasını bekler.

## Kaynak yapısı

| Yol | Sorumluluk |
| --- | --- |
| `app/routes/` | HTTP endpoint'leri |
| `app/services/` | İş kuralları ve AI servisleri |
| `app/models/` | İstek, yanıt ve alan modelleri |
| `app/db/` | MongoDB bağlantısı ve temel indeksler |
| `data/` | Yeniden dağıtılabilir örnek veriler |
| `scripts/` | Veri seed ve Vector Search indeks araçları |
| `tests/` | Davranış ve servis testleri |
| `docs/` | Backend teknik dokümantasyonu |

Backend belgelerinin tamamı ve kaynak önceliği için [`docs/README.md`](docs/README.md) dosyasını kullanın. API sözleşmesinde çalışan OpenAPI şeması, statik endpoint açıklamalarından daha yetkilidir.

## İlgili depolar

- [Mobil uygulama](https://github.com/CineMatePlus/cinemate_mobile)
- [Sistem diyagramları](https://github.com/CineMatePlus/docs)
- [Akademik raporlar](https://github.com/CineMatePlus/rapor)

## Lisans

Bu proje, telif hakkı Muhammet Berk'e ait olmak üzere [MIT License](LICENSE) ile lisanslanmıştır.
