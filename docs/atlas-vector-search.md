# MongoDB Vector Search Kurulumu

CineMate iki Vector Search indeksini sabit adlarla kullanır. Normal MongoDB `createIndex` çağrısı embedding alanı için yeterli değildir; `mongot` içeren Atlas Local veya Atlas üzerinde `vectorSearch` indeksi gerekir.

## Gereksinimler

- Docker Desktop ve Docker Compose (lokal kullanım için)
- `.env` içinde Atlas Local veya Atlas bağlantı URI'si
- `movies` kayıtlarında 1024 boyutlu `embedding` dizileri

Varsayılan `qwen3-embedding:0.6b` modelinin embedding boyutu 1024'tür. Film ve
kullanıcı koleksiyonlarındaki vektör indeksleri bu boyutu kullanır.

## Lokal ortam ayarı

Projede bulunan Atlas Local servisini başlatın:

```powershell
docker compose up -d
docker compose ps
```

Mevcut Windows MongoDB servisi `27017` portunda kalabilir. Atlas Local host üzerinde `27018` portunu kullanır:

```dotenv
MONGODB_URL=mongodb://localhost:27018/?directConnection=true
MONGODB_DB=cinemate
```

## Atlas ortam ayarı

Atlas bağlantısını `.env` içine yazın ve gerçek kullanıcı adı/parola içeren dosyayı Git'e eklemeyin:

```dotenv
MONGODB_URL=mongodb+srv://USER:PASSWORD@CLUSTER_HOST/?retryWrites=true&w=majority
MONGODB_DB=cinemate
```

Atlas Network Access bölümünde geliştirme makinenizin IP adresine, Database Access bölümünde ise uygulama kullanıcısına gerekli veritabanı yetkilerine izin verin.

## İndeksleri oluşturma

Oluşturulacak tanımları bağlantı kurmadan görüntüleyin:

```powershell
poetry run python scripts/create_vector_indexes.py --dry-run
```

Ardından indeksleri oluşturun:

```powershell
poetry run python scripts/create_vector_indexes.py
```

Script varsayılan olarak `movies.movie_vector_index` ve
`users.user_vector_index` indekslerine aşağıdaki alanı uygular:

```json
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 1024,
      "similarity": "cosine"
    }
  ]
}
```

Script tekrar çalıştırıldığında aynı isimdeki mevcut indeksleri atlar. MongoDB indeks oluşturmayı arka planda tamamlar; durum `READY` olmadan ilgili API çağrılarını test etmeyin.

## Hangi özellik hangi indeksi kullanır?

| İndeks | Kullanan özellikler |
| --- | --- |
| `movies.movie_vector_index` | Metinle film arama, benzer filmler, koleksiyon ve kullanıcı listesi önerileri |
| `users.user_vector_index` | Benzer zevke sahip kullanıcılar |

## Hata giderme

- `CommandNotSupported` veya benzeri bir hata, bağlantının Atlas Local yerine standart MongoDB servisine (`27017`) gittiğini gösterebilir.
- `index not found`, indeks adının kodla aynı olmadığını veya oluşturma işleminin henüz tamamlanmadığını gösterir.
- Boyut uyuşmazlığı hatasında film ve kullanıcı embedding'lerinin 1024 değer içerdiğini doğrulayın.
- Boş sonuçlarda önce filmlerde 1024 boyutlu `embedding` alanı bulunduğunu kontrol edin.

Başvuru kaynakları: [MongoDB `createSearchIndex` belgeleri](https://www.mongodb.com/docs/v8.0/reference/method/db.collection.createsearchindex/), [MongoDB Vector Search indeks alanları](https://www.mongodb.com/docs/atlas/atlas-search/field-types/vector-type/) ve [Qwen3 Embedding](https://github.com/QwenLM/Qwen3-Embedding).
