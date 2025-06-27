# CineMate: Yapay Zeka Motoru ve Öneri Sistemleri

CineMate projesinin benzer uygulamalardan en ayırt edici özelliği, yapay zeka tabanlı içerik önerileri ve kullanıcı eşleştirme sistemidir. Uygulamamız, kullanıcıların izleme alışkanlıklarını analiz ederek kişiselleştirilmiş içerik önerileri sunar ve benzer film zevklerine sahip kullanıcıları bir araya getirerek sosyal bir etkileşim platformu oluşturur.

Bu doküman, projenin yapay zeka altyapısının nasıl tasarlandığını, hangi tekniklerin kullanıldığını ve bu altyapının API aracılığıyla hangi özellikleri sunduğunu detaylandırmaktadır.

## 1. Yapay Zeka Mimarisi ve Teknikleri

CineMate'in yapay zeka motoru, kullanıcılar için derinlemesine kişiselleştirme sağlayan sofistike bir sistemdir. Bu sistem, veri hazırlama, gelişmiş modelleme ve yüksek performanslı bir veritabanına entegrasyonu içeren çok aşamalı bir süreçle oluşturulmuştur.

### 1.1. Veri Hazırlama ve Vektörleştirme

Yapay zeka motorunun temeli, ham film verilerinin anlamlı sayısal temsillere (vektör gömme veya embeddings) dönüştürülmesi sürecidir. Bu, `app/ai/control/migration.py` dosyasında detaylandırılan özel bir veri boru hattı kullanılarak gerçekleştirilir.

*   **Akıllı Metin Birleştirme:** Sistem, her film için sadece tek bir metin parçasına güvenmek yerine, `title`, `overview`, `tagline` ve `production_companies` gibi birden çok alanı akıllıca birleştirir.
*   **Anlamsal Ağırlıklandırma:** Gömme işlemlerinin kalitesini artırmak için, `genres` (türler) ve `keywords` (anahtar kelimeler) gibi kritik alanlara daha fazla önem verilir. Bu alanlar, gömme işleminden önce metin bloğu içinde tekrarlanır. Bu "anlamsal ağırlıklandırma" tekniği, modelin bir filmin en belirleyici özelliklerine daha fazla dikkat etmesini sağlar.
*   **Yüksek Performanslı Gömme Modeli:** Her film için hazırlanan metin, daha sonra `sentence-transformers` kütüphanesinden güçlü **`all-mpnet-base-v2`** modeli kullanılarak 768 boyutlu bir vektöre dönüştürülür. Bu model, metnin nüanslarını ve anlamsal bağlamını anlama yeteneğiyle ünlüdür.
*   **Optimize Edilmiş Migrasyon:** Tüm veri taşıma süreci yüksek düzeyde optimize edilmiştir. Veriler büyük yığınlar halinde işlenir ve gömme işlemleri toplu olarak oluşturulur. Mevcutsa, önemli bir performans artışı için CUDA özellikli bir GPU'dan yararlanılır.

### 1.2. Vektör Veritabanı ve Anlamsal Arama

Oluşturulan vektör gömme işlemleri **MongoDB Atlas**'ta saklanır. Tüm yapay zeka özelliklerini mümkün kılan anahtar teknoloji, **MongoDB Atlas Vector Search** yeteneğidir.

*   **Özelleştirilmiş İndeksleme:** `movies` ve `users` koleksiyonlarındaki `embedding` alanları üzerinde özel bir Vektör Arama indeksi oluşturulur.
*   **Benzerlik Metriği:** Bu indeks, yüksek boyutlu vektörlerin açısal yakınlığını karşılaştırmak için ideal olan **Kosinüs Benzerliği (Cosine Similarity)** metriğini kullanarak son derece verimli benzerlik aramalarına olanak tanır. Bu altyapı, MongoDB'yi etkili bir şekilde güçlü, entegre bir vektör veritabanına dönüştürür ve harici hizmetlere olan ihtiyacı ortadan kaldırır.

## 2. API Üzerinden Sunulan Yapay Zeka Destekli Özellikler

Bu güçlü altyapı, API aracılığıyla sunulan bir dizi akıllı özelliği mümkün kılar:

*   **Anlamsal Arama (Semantic Search):** Bir kullanıcı bir sorgu yazdığında (örneğin, "rüyalar hakkında akıl almaz bir film"), API bu metni gerçek zamanlı olarak bir sorgu vektörüne dönüştürmek için `all-mpnet-base-v2` modelini kullanır. Ardından, gömme vektörleri bu sorgu vektörüne en çok benzeyen filmleri bulmak için Atlas Vector Search'ü kullanarak basit anahtar kelime eşleşmesinin çok ötesinde, son derece alakalı sonuçlar sunar.
*   **Benzer Film Önerileri:** Herhangi bir film için sistem, hedef filmin gömme vektörünü alıp en yakın vektörlere sahip diğer filmleri bulmak için bir vektör araması yaparak anında benzer filmler önerebilir.
*   **Dinamik, Liste Tabanlı Öneriler:** Öneri motoru inanılmaz derecede esnektir. Herhangi bir film listesine dayalı olarak kişiselleştirilmiş öneriler üretebilir. Örneğin, bir kullanıcının "beğendiği filmleri", "izleme listesini" ve hatta özel olarak oluşturulmuş bir koleksiyonu (örneğin, "80'ler Bilim Kurgu Klasikleri") analiz edebilir. Bunu, listedeki tüm filmlerin *ortalama gömme vektörünü* hesaplayarak ve ardından bu ortalama "zevk vektörüne" en çok benzeyen yeni filmleri bularak yapar.
*   **"Zevk Profilleri" ile Kullanıcı Eşleştirme:** CineMate, her kullanıcı için benzersiz bir "zevk profili" oluşturur. Bu, bir kullanıcının beğendiği tüm filmlerin ortalama gömme vektörünün hesaplanmasıyla elde edilir. Kullanıcının profilinde saklanan bu tek vektör, genel sinema tercihini temsil eder. Sistem daha sonra, en benzer zevk profillerine sahip diğer kullanıcıları bulmak için `users` koleksiyonunda Vektör Araması kullanarak bir topluluk ve sosyal keşif duygusunu teşvik eder. Zevk profillerinin ne kadar yakın olduğunu göstermek için her eşleşmeyle birlikte bir "benzerlik puanı" döndürülür.

## 3. Sistem Tasarımına Entegrasyon

Yapay zeka yetenekleri, sistem mimarisinin ve veri modelinin merkezinde yer alır.

### 3.1. Kalıcı Veri Yönetimi (Persistent Data Management)

Sistemin kalıcı verileri, **MongoDB** NoSQL veritabanı tarafından yönetilir. Yapay zeka için kritik olan koleksiyonlar ve alanlar şunlardır:

-   **`movies` koleksiyonu:**
    -   **`embedding` (vektör):** Filmin metinsel bilgilerinin (başlık, özet, türler) vektör temsilini saklayan önemli bir alan. Bu vektör, `sentence-transformers` modeli tarafından oluşturulur ve benzerlik hesaplamaları için kullanılır. Bu alan, bir MongoDB Atlas Vektör Arama indeksi (örneğin, `vector_index`) kullanılarak **indekslenmelidir**.
-   **`users` koleksiyonu:**
    -   **`embedding` (vektör):** Kullanıcının "zevk vektörünü" saklar. Bu vektör, kullanıcının "beğendiği" tüm filmlerin gömme vektörlerinin ortalaması olarak hesaplanır. Kullanıcının film tercihlerinin matematiksel bir temsili olarak hizmet eder ve benzer zevklere sahip diğer kullanıcıları bulmak için kullanılır. Bu alanın da bir Vektör Arama indeksi (örneğin, `user_vector_index`) kullanılarak **indekslenmesi gerekir**.
-   **`interactions` koleksiyonu:** Kullanıcıların filmlerle olan tüm etkileşimlerini (beğenme, izleme, izleme listesine ekleme) izler. Bu koleksiyondaki veriler, kullanıcının zevk vektörünü hesaplamak ve kişiselleştirilmiş öneriler sunmak için kullanılır.

### 3.2. Yazılım Mimarisi

- **`services/` Katmanı:** Yapay zeka destekli özelliklerin arkasındaki tüm karmaşık iş mantığını içerir. Örneğin, `MovieService` bir film listesi için ortalama gömme vektörünü hesaplama mantığını içerirken, `UserService` bir kullanıcının zevk profilini (gömme vektörünü) güncelleme ve benzer kullanıcıları bulma mantığını yönetir.
- **`ai/` Katmanı:** `sentence-transformers` modelini soyutlayan `AIService`'i içerir. Birincil rolü, bir metin dizesini alıp onu bir vektör gömme işlemine dönüştürmektir.

## 4. Geleceğe Yönelik Gelişim Noktaları

CineMate projesi, gelecekte aşağıdaki ileri teknikleri ve geliştirmeleri entegre ederek yapay zeka yeteneklerini daha da ileriye taşımayı hedeflemektedir:

- **Derin Öğrenme Tabanlı, Çok Kriterli ve Hibrit Öneri Algoritmaları:** Daha karmaşık ve isabetli öneriler için mevcut sistemin geliştirilmesi.
- **Daha Sofistike Benzerlik Metrikleri ve Sosyal Etkileşim Algoritmaları:** Kullanıcı eşleştirme sisteminin zenginleştirilmesi. 