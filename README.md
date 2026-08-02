# CineMate Backend

CineMate'in kimlik doğrulama, içerik, koleksiyon, yorum, kullanıcı etkileşimi ve yapay zeka destekli öneri işlevlerini sunan FastAPI servisidir.

## Gereksinimler

- Python 3.10 veya üzeri
- Poetry 2.x
- MongoDB
- BGE-M3 modelini ilk kullanımda indirebilmek için internet bağlantısı

Temel CRUD işlevleri yerel MongoDB ile çalışır. Metinle arama, benzer film, koleksiyon önerisi ve benzer kullanıcı özellikleri için MongoDB Atlas Vector Search gerekir.

## 1. Bağımlılıkları kurma

CPU kurulumu varsayılandır ve NVIDIA ekran kartı gerektirmez:

```powershell
poetry install
```

NVIDIA GPU ve CUDA 12.8 uyumlu sürücü bulunan bir sistemde, CPU paketlerini aynı sürümlerin CUDA wheel'leriyle değiştirin:

```powershell
poetry install
poetry run pip install --force-reinstall torch==2.7.1+cu128 torchvision==0.22.1+cu128 numpy==1.26.4 --index-url https://download.pytorch.org/whl/cu128
```

Poetry kilit dosyası taşınabilirlik için CPU profilini sabitler; CUDA değişimi aynı PyTorch/Torchvision sürümlerini kullanır. Daha sonra tekrar `poetry install` çalıştırmak ortamı kilitli CPU profiline döndürür. Kurulumu doğrulamak için:

```powershell
poetry run python -c "import torch; print(torch.__version__); print('CUDA:', torch.cuda.is_available())"
```

## 2. Ortam ayarları

```powershell
Copy-Item .env.example .env
```

`.env` içinde en azından MongoDB bağlantısını ve JWT anahtarını düzenleyin:

```dotenv
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=cinemate
JWT_SECRET_KEY=replace-with-a-random-secret
```

Güvenli bir JWT anahtarı üretmek için:

```powershell
poetry run python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Tam yapay zeka özellikleri kullanılacaksa `MONGODB_URL` bir MongoDB Atlas deployment'ına işaret etmelidir.

## 3. Örnek film verisini yükleme

Repo, üçüncü taraf veri lisansına bağlı olmayan sekiz sentetik film içeren `data/sample_movies.csv` dosyasını içerir. Dosyayı ve komutu veritabanına bağlanmadan doğrulayabilirsiniz:

```powershell
poetry run python scripts/seed_movies.py --dry-run
```

Temel ekranları yerel MongoDB ile denemek ve BGE-M3 indirmemek için:

```powershell
poetry run python scripts/seed_movies.py --skip-embeddings
```

Vektör arama ve önerilerde kullanılacak 1024 boyutlu embedding'leri de üretmek için:

```powershell
poetry run python scripts/seed_movies.py
```

İlk embedding işlemi `BAAI/bge-m3` modelini Hugging Face üzerinden indirir ve yerel model önbelleğine kaydeder. Sonraki çalıştırmalar önbelleği kullanır. CUDA profili kuruluysa `--device cuda`, CPU'yu zorlamak için `--device cpu` kullanılabilir.

Seed komutu `seed_id` üzerinden upsert yaptığı için güvenle tekrar çalıştırılabilir. `--reset` yalnızca bu örnek seed tarafından oluşturulmuş kayıtları siler. Ayrıntılar ve kendi lisanslı CSV dosyanızı kullanma biçimi için [`docs/data-seeding.md`](docs/data-seeding.md) dosyasına bakın.

## 4. Atlas Vector Search indeksleri

Atlas bağlantısı `.env` içinde ayarlandıktan sonra gerekli iki indeksi oluşturun:

```powershell
poetry run python scripts/create_vector_indexes.py
```

Script aşağıdaki 1024 boyutlu cosine indekslerini oluşturur:

| Koleksiyon | İndeks | Alan |
| --- | --- | --- |
| `movies` | `vector_index` | `embedding` |
| `users` | `user_vector_index` | `embedding` |

Oluşturma isteği tamamlandıktan sonra Atlas arayüzünde her iki indeksin durumu `READY` olana kadar vektör sorgularını çalıştırmayın. Atlas kurulumu ve hata giderme adımları için [`docs/atlas-vector-search.md`](docs/atlas-vector-search.md) dosyasını kullanın.

## 5. API'yi çalıştırma

```powershell
poetry run uvicorn app.main:app --reload
```

Uygulama başladıktan sonra:

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`

BGE-M3, API başlangıcında değil ilk embedding isteğinde belleğe yüklenir. CPU'da ilk vektör isteğinin tamamlanması GPU'ya göre daha uzun sürebilir.

## Testler

Davranış testleri çalışan bir MongoDB örneği kullanır:

```powershell
poetry run behave tests/features
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
| `scripts/` | Veri seed ve Atlas indeks araçları |
| `tests/` | Davranış ve servis testleri |
| `docs/` | Backend teknik dokümantasyonu |

Backend belgelerinin tamamı ve kaynak önceliği için [`docs/README.md`](docs/README.md) dosyasını kullanın. API sözleşmesinde çalışan OpenAPI şeması, statik endpoint açıklamalarından daha yetkilidir.

## İlgili depolar

- [Mobil uygulama](https://github.com/CineMatePlus/cinemate_mobile)
- [Sistem diyagramları](https://github.com/CineMatePlus/docs)
- [Akademik raporlar](https://github.com/CineMatePlus/rapor)

## Lisans

Bu proje, telif hakkı Muhammet Berk'e ait olmak üzere [MIT License](LICENSE) ile lisanslanmıştır.
