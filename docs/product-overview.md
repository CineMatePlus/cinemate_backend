# CineMate Ürün Özeti

Cinemate projeniz, kullanıcıların geçmiş izleme geçmişine dayalı olarak film önerileri sunan ve benzer zevklere sahip kullanıcıları bir araya getiren bir uygulama. Proje, kullanıcıların film ve dizi veritabanını yönetmelerini ve içerikleri derecelendirmelerini sağlayacak bir platform oluşturmayı amaçlıyor. Ayrıca, AI destekli öneri ve eşleştirme sistemleriyle, kullanıcıların daha iyi içerikler keşfetmesini sağlayacak.

## Proje Özeti
Cinemate, kullanıcıların izledikleri filmleri takip etmelerini, beğenilerini ve izleme listelerini oluşturup düzenlemelerini sağlayan bir film izleme ve keşif platformudur. Yapay zeka destekli öneri ve eşleştirme sistemi, kullanıcıların izleme alışkanlıklarına dayalı kişiselleştirilmiş içerikler sunar ve benzer film zevklerine sahip kullanıcıları birbirleriyle eşleştirir.

## Ana Özellikler

### Film ve Dizi Veritabanı
- Uygulama, bir film ve dizi veritabanına erişim sağlar ve bu veritabanında içeriklerin detayları (isim, kategori, açıklama, oyuncular, vb.) yer alır.

### Kullanıcı Profili ve Yönetimi
- Kullanıcılar, sistemdeki içerikleri izledikçe kişisel profillerini günceller. Her kullanıcı kendi izleme geçmişine, izleme listesini ve beğendikleri içeriklere sahip olur.

### İzleme Geçmişi Takibi
- Kullanıcılar, izledikleri içerikleri takip edebilir, izleme geçmişlerini güncelleyebilir ve izledikleri içeriklere puan verebilir.

### Öneri Sistemi (AI Destekli)
- Kullanıcıların geçmiş izleme davranışlarına dayalı olarak, yapay zeka algoritmaları içerik önerileri sunar.
- Ayrıca, kullanıcıların benzer film zevklerine sahip kişilerle eşleşmesini sağlayacak bir eşleştirme sistemi de bulunur.

### Watchlist (İzleme Listesi)
- Kullanıcılar, izlemek istedikleri içerikleri bir liste halinde tutabilirler. Bu listeye içerikler eklenip çıkarılabilir.

### Derecelendirme Sistemi
- Kullanıcılar, izledikleri filmleri 10 puanlık bir sistemle derecelendirebilir. Bu derecelendirmeler, öneri algoritmasını besler.

### Yorumlar
- Kullanıcılar izledikleri içerikler hakkında yorum yazabilir ve diğer kullanıcılarla fikir alışverişinde bulunabilirler.

### Kullanıcı Eşleştirme
- Benzer izleme geçmişine sahip kullanıcılar, birbirleriyle eşleştirilir ve önerilerde bulunabilirler.

## Teknolojik Yapı

### Backend
- **FastAPI python**: Backend API için Go kullanılacak. Go, yüksek performanslı ve hızlı bir dil olduğu için bu projede veritabanı ve AI algoritmalarının hızlı bir şekilde çalışmasını sağlar.

### Veritabanı
- **MongoDB**: Kullanıcılar ve içerikler hakkında veriler MongoDB veritabanında tutulacak. MongoDB, verilerin esnek ve ölçeklenebilir şekilde depolanmasını sağlar.

### Yapay Zeka (AI) Algoritması
- **Python**: Öneri ve eşleştirme algoritmalarını geliştirmek için Python kullanılacak. Python, AI ve makine öğrenmesi kütüphaneleriyle güçlüdür.

### Mobil Uygulama
- **Flutter**: Mobil uygulama geliştirmek için Flutter kullanılacak. Bu, uygulamanın hem Android hem de iOS cihazlarda çalışmasını sağlar.

### Kullanıcı Kimlik Doğrulama
- **JWT**: Kullanıcı doğrulama işlemleri için JWT (JSON Web Token) kullanılacak.

## Veritabanı Tasarımı

### Kullanıcılar (Users)
- **user_id**: Benzersiz kullanıcı kimliği
- **email**: Kullanıcı e-posta adresi
- **password**: Şifre (şifrelenmiş)

### İçerikler (Contents)
- **content_id**: Benzersiz içerik kimliği
- **title**: İçerik adı
- **description**: İçerik açıklaması
- **category**: İçerik kategorisi
- **cast**: İçerik oyuncu listesi

### Kullanıcı İçerik Etkileşimleri (User_Content)
- **user_id**: Kullanıcı kimliği
- **content_id**: İçerik kimliği
- **watched**: İçeriğin izlenip izlenmediği
- **liked**: İçeriğin beğenilip beğenilmediği
- **watchlist**: İçeriğin izleme listesinde olup olmadığı

### Öneri ve Eşleştirme
- Kullanıcıların geçmiş izleme verilerine göre içerik önerileri ve benzer zevklere sahip kullanıcıların eşleştirilmesi.

Bu proje, kullanıcıların eğlenceli bir şekilde film keşfetmesini ve daha kişiselleştirilmiş içerikler almasını sağlayacak bir platform sunmayı amaçlıyor.
