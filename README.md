# CineMate Backend

CineMate; FastAPI, MongoDB Atlas Vector Search ve Ollama ile film keşfi, koleksiyon yönetimi ve kişiselleştirilmiş öneriler sunan bir backend servisidir.

## Hızlı başlangıç

Gereksinimler: Docker Desktop, Docker Compose ve varsayılan geliştirme yolu için host işletim sisteminde [Ollama](https://ollama.com/). Python ile yerel geliştirme yapmak için Python 3.12 ve Poetry 2.2 gerekir.

```bash
cp .env.example .env
```

`JWT_SECRET_KEY=your-secret-key` yalnız geliştirme uyumluluğu için desteklenir. İnternete açık veya gerçek kullanıcı verisi tutan hiçbir ortamda kullanılmamalıdır; güçlü ve benzersiz bir anahtar üretin:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### Host Ollama — macOS/Metal için önerilen

```bash
ollama pull qwen3-embedding:0.6b
docker compose up -d --build --wait
docker compose --profile seed run --rm seed
```

Bu akış MongoDB'yi başlatır, Vector Search indekslerini idempotent biçimde oluşturup `READY` durumunu bekler, API'yi kaldırır ve 999 filmi `id` üzerinden upsert eder. İlk embedding üretimi donanıma göre birkaç dakika sürebilir; aynı seed komutu tekrar çalıştırıldığında güncel embedding'ler atlanır ve duplicate oluşmaz.

### Tam container Ollama

```bash
docker compose --env-file .env.ollama.example --profile ollama up -d ollama
docker compose --env-file .env.ollama.example --profile ollama run --rm ollama-model
docker compose --env-file .env.ollama.example up -d --build --wait
docker compose --env-file .env.ollama.example --profile seed run --rm seed
```

Model yaklaşık 639 MB indirilir. Apple Silicon'da host Ollama, Metal hızlandırmasını doğrudan kullandığı için genellikle daha hızlıdır.

Servisleri durdurmak için `docker compose down`; verileri de silmek için bilinçli olarak `docker compose down -v` kullanın.

## Doğrulama ve sağlık sözleşmesi

```bash
python scripts/verify_seed.py
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
curl http://localhost:8000/health/embedding
```

- `/health/live`: API process'i ayakta mı?
- `/health/ready`: MongoDB ve zorunlu Vector Search indeksleri hazır mı? Docker healthcheck bunu kullanır.
- `/health/embedding`: Ollama ve seçili embedding modeli hazır mı?
- `/health/vector-search`: indeks durumlarının ayrıntılı görünümü.

API: `http://localhost:8000`

Swagger UI: `http://localhost:8000/api/v1/docs`

MongoDB host üzerinde `localhost:27018`, Compose ağı içinde `mongodb:27017` adresindedir.

## Kimlik doğrulama

Parolalar config üzerinden 8–32 karakter, whitespace-only yasağı ve bcrypt'in 72 UTF-8 byte sınırıyla doğrulanır. Access token 60 dakika, refresh token 7 gün geçerlidir. Her refresh token tek kullanımlıktır; tekrar kullanım tespit edilirse aynı cihaz/oturum ailesinin tamamı iptal edilir. Ham refresh token MongoDB'ye yazılmaz, yalnız SHA-256 özeti saklanır.

Register, login ve refresh yanıtı:

```json
{
  "user": { "_id": "...", "email": "user@example.com", "name": "User" },
  "token_type": "bearer",
  "access_token": "...",
  "refresh_token": "...",
  "access_expires_in": 3600,
  "refresh_expires_in": 604800
}
```

Refresh ve logout örnekleri:

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H 'Content-Type: application/json' \
  -d '{"refresh_token":"REFRESH_TOKEN"}'

curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H 'Content-Type: application/json' \
  -d '{"refresh_token":"REFRESH_TOKEN"}'

curl -X POST http://localhost:8000/api/v1/auth/logout-all \
  -H 'Authorization: Bearer ACCESS_TOKEN'
```

`logout`, `logout-all` ve parola değişimi refresh oturumlarını kapatır. Mevcut access token'lar blacklist edilmez ve kalan ömürleri boyunca, en fazla 60 dakika, geçerli olabilir.

## Yerel geliştirme ve test

```bash
poetry install --with dev,test
poetry run black --check app scripts tests
poetry run isort --check-only app scripts tests
poetry run python -m unittest discover -s tests/unit -v
TEST_MONGODB_URL='mongodb://localhost:27018/?directConnection=true' poetry run behave tests/features
poetry run pip-audit
```

Locust yalnız gerektiğinde kurulur: `poetry install --with performance`.

CI; `quality`, `unit`, `integration` ve `container-security` job'larını PR ve `main` push'larında çalıştırır. Coverage XML artifact olarak üretilir; mevcut kod için global eşik uygulanmaz.

## Seed verisi ve lisans

Repo yalnız doğrulanmış 999 satırlık `app/ai/control/first_hundred.csv` seed'ini içerir. 533 MB canonical kaynak Git'e ve Docker build context'ine alınmaz. Kaynak, lisans, TMDB attribution ve sabit SHA-256 bilgileri [DATA_NOTICE.md](DATA_NOTICE.md) içindedir. Seed'i canonical dosyadan tekrar üretmek için:

```bash
python app/ai/control/first_hundred.py --input /path/to/TMDB_movie_dataset_v11.csv
python scripts/verify_seed.py
```

## Proje yapısı

| Yol | Sorumluluk |
| --- | --- |
| `app/routes/` | HTTP endpoint'leri |
| `app/services/` | İş kuralları, auth ve embedding servisleri |
| `app/models/` | Pydantic istek/yanıt modelleri |
| `app/db/` | Async PyMongo lifecycle ve indeksler |
| `scripts/` | Seed ve Vector Search bootstrap araçları |
| `tests/` | Birim ve Behave entegrasyon testleri |

Güvenlik bildirimi için [SECURITY.md](SECURITY.md), katkı akışı için [CONTRIBUTING.md](CONTRIBUTING.md) dosyasına bakın.

## Lisans

Uygulama kodu [MIT License](LICENSE) altındadır. Veri dosyası için ayrı koşullar [DATA_NOTICE.md](DATA_NOTICE.md) içinde belirtilmiştir.
