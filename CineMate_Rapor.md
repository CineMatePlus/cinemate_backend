# CineMate Projesi - Teknik Rapor

## İçindekiler
1. [Proje Genel Bakış](#proje-genel-bakış)
2. [Sistem Mimarisi](#sistem-mimarisi)
3. [Veritabanı Yapısı](#veritabanı-yapısı)
4. [Güvenlik Özellikleri](#güvenlik-özellikleri)
5. [API Katmanı](#api-katmanı)
6. [Servis Katmanı](#servis-katmanı)
7. [Model Yapısı](#model-yapısı)
8. [Özel Özellikler ve Optimizasyonlar](#özel-özellikler-ve-optimizasyonlar)
9. [Potansiyel Gelişim Noktaları](#potansiyel-gelişim-noktaları)

## Proje Genel Bakış

CineMate, film ve dizi takibi, koleksiyon oluşturma ve sosyal etkileşim sağlayan kapsamlı bir platform sunmaktadır. Projenin backend kısmı FastAPI ile geliştirilmiş olup, MongoDB veritabanı üzerine kurulmuştur. Platform, kullanıcıların film ve diziler hakkında bilgi edinmelerini, beğendiklerini koleksiyonlara eklemelerini, yorum yapmalarını ve izleme durumlarını takip etmelerini sağlamaktadır.

### Temel Özellikleri

- Kullanıcı kaydı ve JWT tabanlı kimlik doğrulama
- Film ve dizi içeriklerinin listelenme, arama ve filtreleme özellikleri
- Kullanıcı koleksiyonları oluşturma ve yönetme
- İçeriklere yorum yapma ve puanlama
- İçerikleri beğenme, izleme listesine alma ve izlendi olarak işaretleme
- Text-search ile içerik arama

## Sistem Mimarisi

CineMate backend sistemi, katmanlı bir mimari kullanarak modülerlik ve bakım kolaylığı sağlamaktadır:

```
app/
├── core/          # Çekirdek yapılandırma ve sabitler
├── db/            # Veritabanı bağlantısı ve işlemleri
├── models/        # Veri modelleri (Pydantic)
├── routes/        # API endpoint'leri
├── services/      # İş mantığı ve servis katmanı
└── main.py        # Uygulama giriş noktası
```

Sistem FastAPI çerçevesi üzerine kurulmuş olup, asenkron programlama paradigması ile yüksek performans ve ölçeklenebilirlik sağlamaktadır.

## Veritabanı Yapısı

MongoDB, projenin ihtiyaç duyduğu esnek şema ve hızlı sorgu yetenekleri nedeniyle tercih edilmiştir. Veritabanı şeması şu koleksiyonlardan oluşmaktadır:

- **users**: Kullanıcı bilgileri ve kimlik doğrulama verileri
- **contents**: Film ve dizi bilgileri
- **collections**: Kullanıcı koleksiyonları
- **comments**: İçerikler hakkında kullanıcı yorumları
- **user_contents**: Kullanıcı-içerik ilişkisi (beğenme, izleme, puanlama)

### İndeksleme ve Performans Optimizasyonu

Sistem, veritabanına uygun indeksler oluşturarak sorgu performansını optimize etmektedir:

- Tekil indeksler (unique): `users.email`, `collections.user_id+title`, `user_contents.user_id+content_id`
- Metin arama indeksi: `contents.title` ve `contents.description` alanları üzerinde
- Sıralı erişim için indeksler: `created_at`, `user_id`, `content_id` gibi sık kullanılan sorgularda

## Güvenlik Özellikleri

### Şifre Güvenliği

- **BCrypt Şifreleme**: Kullanıcı şifreleri veritabanında bcrypt algoritması ile güvenli bir şekilde hash'lenerek saklanmaktadır.
- **Şifre Doğrulama Sistemi**: Kullanıcı girişinde şifre doğrulaması güvenli bir şekilde gerçekleştirilir.
- **Şifre Politikası**: Minimum ve maksimum şifre uzunluğu ayarları yapılandırılabilir.

### JWT Tabanlı Kimlik Doğrulama

- **Güvenli Token Oluşturma**: JWT (JSON Web Token) standardı kullanılarak güvenli erişim token'ları oluşturulmaktadır.
- **Token Süresi Yönetimi**: Token'lar belirli bir süre sonra geçerliliğini yitirir.
- **Token Yenileme Mekanizması**: Mevcut token'ın yenilenmesi için endpoint bulunmaktadır.

### API Güvenliği

- **CORS Koruması**: Cross-Origin Resource Sharing (CORS) ayarları ile istemci erişimleri kontrol edilmektedir.
- **Korumalı Endpoint'ler**: Kimlik doğrulama gerektiren endpoint'ler yetkilendirme kontrolü ile korunmaktadır.

## API Katmanı

### Endpoint'ler

CineMate API, aşağıdaki ana endpoint gruplarını içermektedir:

- **Auth API (`/api/v1/auth`)**: Kimlik doğrulama, kayıt ve kullanıcı işlemleri
- **Collections API (`/api/v1/collections`)**: Kullanıcı koleksiyonları yönetimi
- **Contents API (`/api/v1/contents`)**: İçerik arama, listeleme ve yönetimi
- **Comments API (`/api/v1/comments`)**: Yorum yönetimi
- **User-Content API (`/api/v1/user-contents`)**: Kullanıcı-içerik ilişkisi yönetimi

### API Dokümantasyonu

- Swagger UI: `/api/v1/docs`
- ReDoc: `/api/v1/redoc`

## Servis Katmanı

### AuthService

- Kullanıcı kaydı ve kimlik doğrulama
- JWT token oluşturma ve yönetimi
- Şifre hashing ve doğrulama

### ContentService

- İçerik arama ve listeleme
- İçerik filtreleme (tür, yıl, tür)
- Metin tabanlı arama (title ve description)

### CollectionService

- Kullanıcı koleksiyonlarının oluşturulması ve yönetimi
- Koleksiyonlara içerik ekleme/çıkarma
- Koleksiyon listeleme ve arama

### CommentService

- İçeriklere yorum ekleme ve yönetimi
- Yorum listeleme ve filtreleme

### UserContentService

- Kullanıcı içerik etkileşimleri (beğeni, izleme, puanlama)
- Kullanıcı izleme listesi yönetimi
- Kullanıcı bazlı içerik önerileri

## Model Yapısı

Veri modelleri Pydantic kullanılarak tanımlanmış, hem API istek/yanıt modelleri hem de veritabanı eşleşmeleri için kullanılmaktadır:

### Kullanıcı Modelleri

- `UserBase`: Temel kullanıcı bilgileri
- `UserInDB`: Veritabanındaki kullanıcı modeli (şifre hash'i içerir)
- `UserResponse`: API yanıtları için kullanıcı modeli

### İçerik Modelleri

- `ContentBase`: Film/dizi temel bilgileri
- `ContentInDB`: Veritabanındaki içerik modeli
- `ContentResponse`: API yanıtları için içerik modeli

### Koleksiyon Modelleri

- `CollectionBase`: Temel koleksiyon bilgileri
- `CollectionInDB`: Veritabanındaki koleksiyon modeli
- `CollectionResponse`: API yanıtları için koleksiyon modeli

## Özel Özellikler ve Optimizasyonlar

### İçerik Arama Optimizasyonu

MongoDB'nin text search özelliği kullanılarak içerik aramaları optimize edilmiştir:
- Title ve description alanlarında metin araması
- Arama sonuçlarının relevance'a göre sıralanması
- Metin arama indeksi ile hızlı sonuçlar

### İçerik Etkileşim İstatistikleri

İçerik modelleri, kullanıcı etkileşimlerini özetleyen istatistikleri içerir:
- Ortalama puan
- Beğeni sayısı
- İzlenme sayısı
- Yorum sayısı
- Puanlama sayısı

### Asenkron İşlemler

Tüm veritabanı işlemleri asenkron olarak gerçekleştirilmekte, bu da yüksek eşzamanlı kullanıcı sayısını desteklemektedir:
- Motor (MongoDB asenkron sürücüsü) kullanımı
- FastAPI'nin asenkron yeteneklerinden tam faydalanma
- Veritabanı işlemlerinin non-blocking yapısı

### Hata Yönetimi

Tüm servislerde kapsamlı hata yakalama ve işleme mekanizmaları:
- Exception handling pattern ile tutarlı hata yanıtları
- İstemciye anlamlı hata mesajları
- HTTP durum kodları ile uyumlu hata yanıtları

## Potansiyel Gelişim Noktaları

### Teknik İyileştirmeler

1. **Önbellek Sistemi**: Redis veya benzer bir önbellek sisteminin entegrasyonu ile sık kullanılan verilerin önbelleğe alınması performansı artırabilir.
2. **Asenkron İş Kuyruğu**: Arka plan işleri için Celery gibi bir iş kuyruğu sistemi eklenebilir.
3. **Dağıtık Kimlik Doğrulama**: OAuth2 ve üçüncü taraf kimlik doğrulama sağlayıcıları entegrasyonu.
4. **Dosya Yükleme Servisi**: Kullanıcı profil resimleri ve içerik görselleri için özel bir dosya yükleme servisi.
5. **GraphQL Desteği**: REST API'ye ek olarak GraphQL desteği eklenebilir.

### İş Özellikleri

1. **Sosyal Ağ Özellikleri**: Kullanıcıların birbirini takip etmesi, arkadaş olması.
2. **İçerik Önerileri**: Gelişmiş öneri algoritmaları ile kişiselleştirilmiş içerik önerileri.
3. **Bildirim Sistemi**: Kullanıcılara önemli etkileşimler için bildirim gönderme.
4. **İçerik Puanlama Algoritması**: Daha kapsamlı puanlama sistemi ve analizi.
5. **İstatistik Sayfaları**: Kullanıcı davranışlarına dair detaylı istatistikler ve grafikler.

---

Bu rapor, CineMate projesinin teknik yapısını ve özelliklerini detaylı bir şekilde anlatmaktadır. Proje, modern web geliştirme yöntemlerini kullanarak ölçeklenebilir, güvenli ve performanslı bir film/dizi platformu sunmaktadır. 