# Portföy sürümü kabul kaydı

6 Eylül 2026. Kapsam Android + yerel backend; sürekli açık internet servisi ve mağaza yayını kapsam dışıdır.

## Tamamlanan uygulama

- Sabit Android araç zinciri, ortama göre API adresi ve özel release imzalama.
- Mobil kayıt sözleşmesi, atomik token çifti, tek ortak refresh, güvenli logout ve oturum geri yükleme.
- Arama yarış koşulları, öneri sayfalaması, koleksiyon görünürlüğü, yorum menüleri ve görsel fallback düzeltmeleri.
- Backend girdi doğrulaması, herkese açık kullanıcı verisinden e-posta çıkarılması, transaction ile etkileşim/yorum sayaçları ve sahiplik testleri.
- İdempotent sentetik demo seed, mobil CI ve bağımlılık taraması; mimari ve varlık kaynak belgeleri.

## Yerel kanıt

| Kontrol | Sonuç |
| --- | --- |
| Backend birim testleri | 36 geçti; önceki 33 testlik ölçümde satır coverage %61 |
| Behave | 5 senaryo, 20 adım geçti; her çalıştırmaya özel DB |
| Gerçek API auth kabulü | Rotation, reuse, logout, iki cihaz ve concurrency geçti |
| Ürün kabulü | İki kullanıcı sahiplik/izolasyon, yorum CRUD ve 8 eşzamanlı toggle geçti |
| Mobil testler | 12 unit/widget/state testi geçti |
| Android gerçek API testi | Kayıt, restore ve logout geçti |
| Android demo testi | Keşif, detay, semantik arama, benzer kullanıcı, koleksiyon ve profil geçti |
| Kalite | Black, isort, Dart format ve fatal-info analyze temiz |
| Güvenlik | pip-audit ve 119 mobil paketin OSV taraması temiz; Gitleaks geçmiş taraması temiz |
| Seed | 999 gerçek embedding; tekrarında 999 atlandı, duplicate yok; Mongo restart sonrası 999 korundu |
| Build | Normal debug ve özel anahtarla imzalı release APK üretildi |

Gitleaks iki tarihsel dokümantasyon örneği için yalnız tam fingerprint istisnası kullanır: literal ACCESS_TOKEN ve üç noktayla kesilmiş JWT başlığı. Gerçek credential istisnası yoktur.

## Açık kabul kapıları

- Backend uzak CI: `933a046` commit’inde quality, unit, integration ve container-security job’larının tamamı geçti: https://github.com/CineMatePlus/cinemate_backend/actions/runs/34052413361
- Mobil dal SSH ile gönderildi; GitHub bağlantısı mobil repo için 404, PR yazımı için 403 dönüyor. Mobil uzak CI ve main required-check ayarları doğrulanamadı.
- Fiziksel Android cihaz bağlı değildir; emülatör testi fiziksel cihaz kabulünün yerine geçmez.
- Backend anonim erişime açık; mobil depo anonim API erişiminde 404 dönüyor. Görünürlük değiştirilmedi; metadata/PR işlemleri GitHub oturumu veya bağlantı yetkisi bekliyor.
- Release artifact SHA/kurulum ve video teslim bilgileri mobil `docs/release.md` dosyasında tutulur.

Tüm planı bitmiş veya internet ölçeğinde production-ready olarak sunmayın. Çalışan Android/ML destekli portföy projesi olarak sunulabilir; açık kabul kapıları bu sürümün sınırlarıdır.

## CV metni

Flutter/Riverpod ve FastAPI ile film keşfi, semantik arama ve kişisel koleksiyon uygulaması geliştirdim. MongoDB Vector Search ve 1024 boyutlu Ollama embedding’lerini 999 filmlik veri kümesiyle birleştirdim; refresh-token rotasyonu, eşzamanlı istek yönetimi ve sahiplik kontrollerini otomatik testlerle doğruladım. Android build, CI ve tekrar üretilebilir demo verisi hazırladım.

## Main entegrasyonu — 6 Eylül 2026

Backend uygulama değişikliklerinin tamamı `a224a7f` üzerinde uzak CI’dan geçti: https://github.com/CineMatePlus/cinemate_backend/actions/runs/34053568353. Main’e fast-forward ile alındı; geçmiş commitler korundu. Fiziksel cihaz kabulü ve mobil uzak CI erişimi ayrı doğrulama sınırları olarak devam eder.
