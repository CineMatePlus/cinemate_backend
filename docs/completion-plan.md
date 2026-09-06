# CineMate — CV ve demo için tamamlanma planı

Tarih: 6 Eylül 2026

Kapsam: `cinemate_backend` ve kardeş `cinemate_mobile` deposu; geliştirme, test, demo dağıtımı ve portföy sunumu. Bu belge bir uygulama planıdır; işaretlenmemiş işler henüz tamamlanmış değildir.

Kaynaklar: 26 Ağustos incelemesi ve devamındaki backend uygulamasını içeren “Cinemate production hazırlığını ince” görevi (`01a03f65-466e-7870-b638-b0463f0d0e9d`), 6 Eylül yerel kod incelemesi ve çalıştırılan kontroller.

## 1. Hedef ve kapsam sınırı

Hedef, bir değerlendiricinin projeyi anlayabildiği, belgelenmiş adımlarla çalıştırabildiği ve temel kullanıcı akışlarını hatasız deneyebildiği bir portföy sürümü çıkarmaktır.

- Ana kabul platformu Android: bir emülatör ve en az bir fiziksel cihaz. Android önceliği bu planın varsayımıdır.
- Backend: mevcut FastAPI, async PyMongo, Vector Search ve Ollama mimarisi korunur.
- iOS, web ve masaüstü klasörlerinin bulunması destek iddiası sayılmaz. Bu platformlar ayrıca doğrulanmadıkça README'de deneysel/doğrulanmamış olarak belirtilir.
- Kayıt, giriş, oturum devamlılığı, film keşfi, semantik arama, film detayı, etkileşimler, koleksiyonlar, yorumlar, profil istatistikleri, öneriler ve benzer kullanıcılar mevcut ürün kapsamıdır.
- Profil düzenleme, e-posta ile şifre sıfırlama, biyometri, bildirim, ödeme, tam çevrimdışı senkronizasyon ve yeni sosyal özellikler sürümün zorunlu kapsamına alınmaz. Çalışmayan menüler kaldırılır veya açıkça kapsam dışında bırakılır.
- Kubernetes, mikroservislere bölme, çok bölgeli dağıtım, yüksek erişilebilirlik ve mağaza yayını bu hedef için gerekli değildir.
- Yerel geliştirmede `JWT_SECRET_KEY=your-secret-key` önceki kullanıcı kararı gereği şimdilik korunur. İnternete açık demoda güçlü ve benzersiz secret ayrı bir yayın koşuludur.

## 2. Başlangıç durumu ve kanıt ayrımı

| Alan | Durum | Plandaki karşılığı |
| --- | --- | --- |
| Tek Compose, indeks bootstrap, 999 film seed'i, non-root image | Kodda mevcut; önceki görev gerçek Docker kabulünün geçtiğini raporladı | Yeniden yazma; son sürümde regresyon kabulü yap |
| Async PyMongo, lifespan, PyJWT, parola politikası, refresh rotasyonu ve logout endpointleri | Uygulanmış | Mobil sözleşmeyi uyumla |
| Backend CI ve Dependabot | Takip edilen dosyalar mevcut | Uzak CI ve required check durumunu doğrula |
| Backend DATA_NOTICE, SECURITY, CONTRIBUTING, README | Mevcut | Yalnız değişen sözleşmeleri ve demo adımlarını güncelle |
| Backend test/seed | 6 Eylül: 28 birim testi, seed SHA/satır kontrolü ve Black geçti | Koru, eksik iş akışı testlerini ekle |
| Docker/embedding, Behave, pip-audit, Gitleaks | Önceki görevde başarılı raporlandı; bu incelemede tekrar çalıştırılmadı | Son kabulde güncel commit üzerinde yeniden çalıştır |
| Mobil kayıt ve refresh | Güncel backend ile uyumsuz | Faz 2, demo engeli |
| Mobil araç zinciri | Önceki görev normal build hatası raporladı; eski Gradle/AGP ayarları hâlâ mevcut | Faz 1'de normal build'i yeniden üret ve düzelt |
| Mobil test/CI | Test klasörü ve CI yok; flutter test başarısız | Faz 2–5 |
| Mobil analiz | 26 bilgi seviyesinde lint/deprecation bulgusu | Faz 3'te temizle, Faz 5'te CI kapısı yap |
| Görseller | transparent.png dosyasının ASCII metin olduğu yeniden doğrulandı | Faz 3 |
| Git durumu | İnceleme öncesi iki repo temiz; backend değişiklikleri 0cbf395 commit'inde mevcut | Önceki görevin “commit edilmedi” sonucu artık güncel değil |
| Repo görünürlüğü, metadata, branch protection, son uzak CI sonucu | Bu turda uzaktan doğrulanmadı | Faz 5 ve 7'de denetle |

Eski rapordaki “seed yok”, “refresh sistemi yok”, “backend CI yok” maddeleri kapanmıştır. Eski bağımlılık zafiyet sayıları güncel durum olarak kullanılmaz. Önceki başarılı testler yeni release'in doğrulaması yerine geçmez.

## 3. Uygulama sırası

Her faz küçük, gözden geçirilebilir commit/PR'larla teslim edilir. İki depoyu değiştiren işler karşılıklı bağlantı içerir; final kabulde test edilen backend ve mobil commit SHA'ları birlikte kaydedilir. Temel davranış testleri ilgili değişiklikle aynı fazda eklenir.

### Faz 1 — Tekrarlanabilir mobil kurulum ve ortam seçimi

- [ ] Flutter/Dart, JDK, Gradle, AGP, Kotlin, compileSdk ve NDK için uyumlu sürüm kombinasyonunu doğrula ve yerel/CI ortamında sabitle. Bağımlılık doğrulamasını atlayan bayrakları normal kurulumdan çıkar.
- [ ] `flutter pub get`, kod üretimi ve standart debug APK build'ini temiz checkout'ta çalıştır.
- [ ] API adresini `--dart-define=API_BASE_URL=...` üzerinden seçilebilir yap; yerel emülatör, fiziksel cihaz ve HTTPS demo örneklerini belgele. Release için yanlış/eksik URL'yi erken yakala.
- [ ] Mobil `.gitignore` içine gerçek env dosyaları, key.properties, keystore/JKS ve credential dosyalarını ekle; örnek dosyalar takip edilsin. Mevcut takip edilen dosyaları da kontrol et.
- [ ] Android uygulama adı ve paket kimliğini son hâline getir; release imzasını debug anahtarından ayır. Özel anahtar repo dışında kalmalı.

Kabul: Temiz checkout'tan belgelenmiş komutlarla debug APK üretilir; adres değiştirmek için kaynak kod düzenlemek gerekmez; gerçek cihaz seçilen backend'e ulaşır. Release imzalama adımları hazırlanır, final artifact Faz 6'da üretilir.

### Faz 2 — Mobil auth ve HTTP sözleşmesi

- [ ] Kayıtta backend'in `201` cevabını başarı kabul et; `200/201/204` sözleşmelerini diğer servislerde de denetle.
- [ ] Access ve refresh token çiftini secure storage'da sakla; rotasyonda ikisini birlikte güncelle. Eski yalnız access-token kaydını kontrollü yeniden girişe taşı.
- [ ] Açılışta geçerli oturumu geri yükle; refresh isteğinde doğru gövdeyi gönder.
- [ ] Eşzamanlı 401'lerde tek ortak refresh işlemi kullan. Bekleyen istekler aynı yenilemeyi beklesin; aynı refresh token tekrar gönderilip backend'de aile iptaline yol açmasın.
- [ ] Yenilemeden sonra isteği en fazla bir kez tekrarla; login/refresh isteklerini yenileme döngüsüne sokma. Sonucu belirsiz yazma işlemlerini otomatik tekrar etme.
- [ ] Çıkışta backend logout çağrısını ve yerel temizliği uygula; başka kullanıcıya geçildiğinde kullanıcıya ait provider/cache verilerini temizle.
- [ ] Geçici bağlantı hatasını geçersiz oturumdan ayır; ağ yokken refresh token'ı silme. Geçersiz/iptal token'da login'e dön.
- [ ] Parola/token içeren istek ve yanıt loglarını kaldır. HTTP hata modelini, bağlantı/gönderme/yanıt zaman aşımını ve kullanıcı mesajlarını düzenle.
- [ ] Auth state içindeki nullable user/error alanlarının gerçekten temizlenmesini sağla; positional register parametrelerindeki karışıklığı gider.
- [ ] Kayıt, açılış, token süresi dolması, eşzamanlı 401, refresh reddi, bağlantı kesintisi, logout ve hesap değişimi testlerini ekle.

Kabul: Kullanıcı kayıt olur, yeniden açılışta oturumu korunur, token süresi dolduğunda işlem devam eder, çıkış ve hesap değişiminde önceki kullanıcı verileri görünmez. Hassas içerik loglarda bulunmaz.

### Faz 3 — Ürün akışları ve mobil görünüm

- [ ] Her ekranı mevcut OpenAPI sözleşmesiyle eşleştir: alanlar, status kodları, URL/query kodlama, nullable posterler ve sayfalama.
- [ ] Önerilerdeki sahte sayfalamayı kaldır: bu sürümde backend'in sınırlı öneri listesini göster; desteklenmeyen `skip` ile aynı sonuçları tekrar isteme. Katalog/koleksiyon listelerinde gerçek sayfalama korunur.
- [ ] Aramada eski isteğin geç gelen cevabının yeni aramayı ezmesini engelle; boş sorgu ve sayfadan çıkış davranışını doğrula.
- [ ] Etkileşim ve koleksiyon değişikliklerinin detay, liste ve profil sayaçlarına yansımasını sağla. Hatalı istekte iyimser güncelleme geri alınsın; çift dokunma kontrol edilsin.
- [ ] Her ana akışa loading, empty, error ve retry durumları ekle. Kayıt hatası yalnız debug çıktısında kalmasın.
- [ ] İlk kullanıcının öneri/benzer kullanıcı boş durumuna açık yönlendirme ekle; demo seed'i dışında da anlaşılır deneyim sun.
- [ ] Bozuk transparent.png, varsayılan avatar ve eksik poster fallback'lerini düzelt.
- [ ] Çalışmayan profil düzenleme/yorum menülerini tamamlanmış gibi göstermeyi bırak; kapsam içindeki yorum işlemlerini çalışır hâle getir.
- [ ] Lint bulgularını, async sonrası mounted kontrolünü, küçük ekran/klavye taşmalarını, geri gezinmeyi, metin tutarlılığını ve temel erişilebilirliği düzelt.
- [ ] Kritik form, hata/boş durum ve liste davranışları için widget/state testleri ekle.

Kabul: Yeni kullanıcı ve hazırlanmış demo kullanıcısıyla tüm ana ekranlar denenir; ölü buton, tekrarlayan sayfa, eksik görsel veya görünmeyen hata kalmaz. `flutter analyze` temiz geçer.

### Faz 4 — Backend'de kalan doğruluk ve veri güvenliği

- [ ] Koleksiyonlar başta olmak üzere dışarıdan gelen ID'leri ortak doğrulama ile ele al; bozuk ID `400/422`, bulunmayan kayıt `404` dönsün.
- [ ] İki kullanıcıyla özel/açık koleksiyon erişimi, sahiplik, yorum düzenleme/silme ve kullanıcıya özel liste izolasyonunu entegrasyon testiyle doğrula.
- [ ] Herkese/başka kullanıcılara dönen kullanıcı modelini özel `/me` modelinden ayır; yorumlar ve benzer kullanıcılar üzerinden e-posta gibi gereksiz kişisel alanlar dönmesin. Mobil modelleri birlikte güncelle.
- [ ] Eşzamanlı etkileşim ve koleksiyon işlemlerini test et; unique-index hataları, çift artırılan/azaltılan sayaçlar ve embedding güncelleme tutarsızlıklarını gider. Toggle işlemlerine kör otomatik retry uygulama.
- [ ] Yorum, koleksiyon ve arama girdilerine makul uzunluk/limit sınırları koy; boş metinleri reddet.
- [ ] Ollama erişilemez veya indeks hazır değilken kontrollü hata ve mobil retry akışını doğrula; normal katalog akışının davranışını belgele.
- [ ] Gerçek embedding ile birkaç sabit sorguda sonuçların anlamlılığını elle değerlendir; veri/model/indeks ölçülerini eşleştir. Ölçülmeyen öneri doğruluğu iddiası ekleme.

Kabul: Geçersiz girdiler beklenmeyen 500 üretmez; iki kullanıcının özel verileri ayrılır; eşzamanlı temel yazma testleri geçer; embedding kesintisi kullanıcıya anlaşılır biçimde gösterilir.

### Faz 5 — CI ve regresyon kapıları

- [ ] Backend'de mevcut quality/unit/integration/container-security job'larının güncel uzak commit'te çalıştığını doğrula ve varsa hataları gider. Dependabot'u koru.
- [ ] Mobil CI: sabit Flutter/JDK, pub get, kod üretimi tutarlılığı, format/analyze, unit/widget testleri ve normal debug APK build'i. Release imzası PR testleri için gerekli olmasın.
- [ ] Mobil auth sözleşme testlerinin gerçek backend şemasından sapmasını yakala; en az bir uçtan uca akışı Android emülatör + test backend üzerinde çalıştır.
- [ ] Test DB'si ve Compose proje adını geliştirme verisinden ayır; teardown yalnız kendisine ait kaynakları temizlesin.
- [ ] Backend bağımlılık audit'i ve iki repo için secret taramasını tekrar çalıştır; mobil bağımlılık güvenlik kontrolünü ekle. Güvenlik taraması tarihini kaydet.
- [ ] Destekleniyorsa main branch protection/ruleset'e gerçekten çalışan job adlarını required check olarak ekle; repo hesabı/planı nedeniyle uygulanamıyorsa bunu açıkça belgele.

Kabul: Test edilen iki commit için uzak CI yeşil; hata olan PR kontrolü başarısız olur. Backend coverage raporu korunur; keyfi global yüzde hedefi yerine kritik auth ve sahiplik karar dalları kapsanır.

### Faz 6 — Demo verisi, dağıtım ve işletim

Zorunlu portföy teslimi yerel çalıştırılabilir sürüm + Android release APK + demo videosudur. Sürekli açık sunucu ek maliyet ve bakım yaratacağından canlı URL ayrı, isteğe bağlı bir yayın aşamasıdır.

- [ ] Mevcut 999 film seed'ini koru; birkaç sentetik demo kullanıcısı, beğeni, yorum ve koleksiyon için tekrar çalıştırılabilir demo seed/reset aracı hazırla.
- [ ] Demo reset yalnız açıkça seçilen demo veritabanında çalışsın. Gerçek e-posta, kişisel veri veya repoda gizli credential bulunmasın.
- [ ] Yeni kullanıcı ve dolu demo kullanıcısı senaryolarını ayrı doğrula; benzer kullanıcı ve öneri ekranları demo verisiyle dolsun.
- [ ] Temiz checkout'ta belgelenmiş Docker/Ollama adımlarıyla sistemi kur; ilk seed süresi ve kaynak gereksinimini ölç.
- [ ] Sabit sürüm numarasıyla imzalı Android release APK üret; checksum, backend/mobil commit SHA'ları ve kurulum bilgilerini kaydet.
- [ ] Fiziksel cihazda release build ile kabul senaryosunu çalıştır; debug başarısını release kanıtı sayma.

Canlı demo yayımlanacaksa, yayın öncesi ek kapı:

- [ ] Önceki Atlas Local = geliştirme/CI kararını koru; canlı ortam için Vector Search destekleyen veritabanı ve embedding barındırma seçeneklerini kaynak gereksinimiyle doğrula.
- [ ] HTTPS reverse proxy, güçlü benzersiz JWT secret, ortam doğrulaması ve dar CORS ayarlarını uygula. Geliştirme varsayılanı canlı ortamda kabul edilmesin.
- [ ] MongoDB ve Ollama portlarını internete açma; veritabanı erişimini kimlik doğrulama ve ağ sınırıyla koru.
- [ ] Login/register/refresh, yazma işlemleri ve pahalı aramalara sunucu tarafı rate limit koy; proxy arkasındaki istemci IP güvenini doğru yapılandır. Limitler yük denemesiyle seçilsin.
- [ ] Liveness/readiness/embedding health, log rotasyonu, secret içermeyen hata kayıtları ve istek kimliği ekle; basit erişilebilirlik kontrolü kur.
- [ ] Yedekleme/geri yükleme ve önceki uygulama sürümüne dönme adımlarını yaz, bir kez dene. Demo verisinin sıfırlanabildiğini kullanıcıya belirt.
- [ ] Hafif yük denemesinde ortam, eşzamanlı kullanıcı, süre, hata oranı ve p50/p95 gecikmeyi kaydet; sonuçları yüksek ölçek kanıtı olarak sunma.

Kabul: APK fiziksel cihazda çalışır; demoyu hazırlamak kişisel makinedeki gizli dosyalara bağlı değildir. Canlı URL seçildiyse ek yayın kapısındaki maddelerin tümü geçer. Canlı URL yoksa APK'nın backend gereksinimi açıkça yazılır.

### Faz 7 — Dokümantasyon ve CV vitrini

- [ ] Mobil mimari belgesini mevcut kodla eşleştir; biyometri, certificate pinning, repository katmanı, şifre sıfırlama gibi uygulanmamış iddiaları kaldır. Eski `/contents` sözleşmesini temizle.
- [ ] İki README'ye ürün amacı, mevcut özellikler, desteklenen platformlar, mimari, kurulum, test komutları ve bilinen sınırları ekle. Backend'in mevcut ayrıntılı belgelerini tekrar yazma.
- [ ] Aynı demo hesabı ve cihazla 6–8 gerçek ekran görüntüsü al: keşif, arama, detay, koleksiyon, profil/öneriler ve auth. Token/kişisel veri görünmesin.
- [ ] 60–90 saniyelik demo videosu hazırla; yeni kullanıcı akışı ve öneri özelliğini göster. Video bağlantısını ilk ekran/README üst kısmından erişilebilir yap.
- [ ] Görsel varlıkların kaynak/lisans tablosunu hazırla; backend DATA_NOTICE ile uyumlu attribution ekle. Kaynağı belirsiz varlıkları değiştir.
- [ ] GitHub repo görünürlüğünü anonim erişimle doğrula; açıklama, topics, karşılıklı bağlantılar ve demo bağlantısını düzenle. Private repo varsa görünürlük değişikliğini ayrı yayın kararı olarak ele al.
- [ ] Birbiriyle uyumlu release tag'leri, kısa changelog, APK ve kurulum notlarını yayıma hazırla.
- [ ] CV için 2–3 cümle yaz: kendi katkın, teknik problem, çözüm ve doğrulanmış sonuç. Desteklenmeyen ölçek/production iddiaları kullanma.

Kabul: Projeyi ilk kez gören biri README'nin ilk bölümünden ne yaptığını anlar, videosunu izler ve belgelenmiş yoldan çalıştırabilir. Tüm görünür özellik iddialarının çalışan karşılığı vardır.

## 4. Son kabul senaryosu

Her madde için tarih, ortam, backend/mobil commit SHA'ları ve geçti/kaldı sonucu kaydedilir.

1. Temiz checkout ve yeni, izole test volume'u ile backend kurulur; indeksler READY, 999 film ve embedding'ler doğrulanır.
2. Seed tekrar çalışır; duplicate oluşmaz. Mongo/backend restart sonrası veri korunur.
3. Normal araç zinciriyle Android debug ve imzalı release build alınır; CI yeşildir.
4. Yeni kullanıcı kayıt olur; hatalı/duplicate kayıt anlaşılır hata gösterir.
5. Giriş, uygulamayı kapatıp açma, kontrollü token expiry, eşzamanlı yenileme ve çıkış denenir.
6. Katalog, semantik arama, boş sonuç, film detayı ve benzer filmler denenir.
7. Beğeni/watchlist/watched işlemleri ve geri alma sonrasında liste/sayaç tutarlılığı kontrol edilir.
8. Koleksiyon oluşturma, film ekleme/çıkarma, görünürlük ve silme denenir; ikinci kullanıcıyla sahiplik sınırı kontrol edilir.
9. Yorum işlemleri, profil istatistikleri, kişisel öneriler ve benzer kullanıcılar doğrulanır.
10. Ağ kesintisi, API hatası, Ollama kesintisi, bozuk poster ve retry denenir; uygulama kilitlenmez.
11. Güvenlik/bağımlılık taramaları ve hassas log kontrolü geçer; canlı yayın varsa ek yayın kapısı geçer.
12. README, ekran görüntüleri, video, release artifact'i ve CV metni aynı sürümü anlatır.

## 5. Efor ve bitirme kararı

Tek geliştirici için ilk planlama tahmini; garanti değildir, araç zinciri ve cihaz testinden sonra güncellenir:

| Faz | Tahmini odaklı iş günü |
| --- | --- |
| 1 — Build ve ortam | 1–2 |
| 2 — Auth/HTTP | 2–3 |
| 3 — Ürün akışları | 2–4 |
| 4 — Backend kalan işler | 1–3 |
| 5 — CI/test entegrasyonu | 1–2 |
| 6 — Yerel demo/release kabulü | 1–2 |
| 7 — Belgeler ve vitrin | 1–2 |

Toplam yaklaşık 9–18 odaklı iş günü; canlı barındırma seçilirse buna altyapı ve kaynak belirsizliğine bağlı ek süre eklenir. Her fazın testleri kendi tahminine dahildir.

CV/demo sürümü, zorunlu fazlar ve son kabul senaryosu geçtiğinde tamamlanır. Sürekli açık demo ayrıca seçilmediyse CV sürümünü engellemez. Bilinen düşük etkili sınırlamalar release notunda yazabilir; kırık auth, veri erişim ihlali, başarısız normal build ve çalışmayan ana akışlar açıkken sürüm tamamlandı sayılmaz.
