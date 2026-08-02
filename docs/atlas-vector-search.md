# MongoDB Atlas Vector Search Kurulumu

CineMate iki Atlas Vector Search indeksini sabit adlarla kullanır. Normal MongoDB `createIndex` çağrısı embedding alanı için yeterli değildir; Atlas Search türünde bir `vectorSearch` indeksi gerekir.

## Gereksinimler

- Vector Search destekleyen bir MongoDB Atlas deployment'ı
- `.env` içinde Atlas bağlantı URI'si
- `movies` kayıtlarında 1024 boyutlu `embedding` dizileri

`BAAI/bge-m3` modelinin dense embedding boyutu 1024'tür. Bu nedenle hem film hem kullanıcı indeksleri aynı boyutu kullanır.

## Ortam ayarı

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

Script aşağıdaki tanımı `movies.vector_index` ve `users.user_vector_index` için uygular:

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

Script tekrar çalıştırıldığında aynı isimdeki mevcut indeksleri atlar. Atlas indeks oluşturmayı arka planda tamamlar; Atlas arayüzündeki Search Indexes ekranında durum `READY` olmadan ilgili API çağrılarını test etmeyin.

## Hangi özellik hangi indeksi kullanır?

| İndeks | Kullanan özellikler |
| --- | --- |
| `movies.vector_index` | Metinle film arama, benzer filmler, koleksiyon ve kullanıcı listesi önerileri |
| `users.user_vector_index` | Benzer zevke sahip kullanıcılar |

## Hata giderme

- `CommandNotSupported` veya benzeri bir hata, bağlantının Vector Search desteklemeyen yerel/Atlas dışı MongoDB'ye gittiğini gösterebilir.
- `index not found`, indeks adının kodla aynı olmadığını veya oluşturma işleminin henüz tamamlanmadığını gösterir.
- Boyut uyuşmazlığı hatasında film ve kullanıcı embedding'lerinin 1024 değer içerdiğini doğrulayın.
- Boş sonuçlarda önce filmlerin `embedding` alanıyla seed edildiğini kontrol edin.

Başvuru kaynakları: [MongoDB `createSearchIndex` belgeleri](https://www.mongodb.com/docs/v8.0/reference/method/db.collection.createsearchindex/), [MongoDB Vector Search indeks alanları](https://www.mongodb.com/docs/atlas/atlas-search/field-types/vector-type/) ve [BGE-M3 model kartı](https://huggingface.co/BAAI/bge-m3).
