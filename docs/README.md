# Backend Dokümantasyonu

Bu klasör yalnızca backend'e ait teknik belgeleri içerir.

| Belge | Amaç | Yetki düzeyi |
| --- | --- | --- |
| [`architecture.md`](architecture.md) | Katmanlar, veri yönetimi, güvenlik ve teknik tasarım | Mimari başvuru |
| [`product-overview.md`](product-overview.md) | Ürün özellikleri ve teknoloji özeti | Ürün bağlamı |
| [`use-cases.md`](use-cases.md) | Aktörler ve kullanım senaryoları | Analiz başvurusu |
| [`object-model.md`](object-model.md) | Temel nesneler ve ilişkileri | Model başvurusu |
| [`api/collections.md`](api/collections.md) | Koleksiyon işlemlerine ait ayrıntılar | İkincil başvuru |
| [`api/cinemate.postman_collection.json`](api/cinemate.postman_collection.json) | İçe aktarılabilir Postman koleksiyonu | API istemci örnekleri |
| [`data-seeding.md`](data-seeding.md) | Örnek film verisi ve özel CSV yükleme akışı | Kurulum başvurusu |
| [`atlas-vector-search.md`](atlas-vector-search.md) | Atlas indeksleri ve AI altyapısı | Kurulum başvurusu |
| [`development/seed-data.md`](development/seed-data.md) | Yerel geliştirme için örnek kullanıcılar | Geliştirme verisi |

## Kaynak önceliği

Çelişki olduğunda aşağıdaki sıra kullanılır:

1. Çalışan API'nin `/api/v1/docs` adresindeki OpenAPI sözleşmesi
2. `app/` altındaki uygulama kodu ve modeller
3. Bu klasördeki açıklayıcı belgeler

Yeni bir backend belgesi eklemeden önce bu dizine bağlantı ekleyin. Aynı içeriği proje köküne veya `project/` gibi ikinci bir klasöre kopyalamayın.
