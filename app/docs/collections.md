# Koleksiyon API Dokümantasyonu

Bu dokümantasyon, Cinemate API'nin koleksiyon işlemleri için kullanılan endpoint'lerini açıklamaktadır.

## Endpoint'ler

### Koleksiyon Oluşturma

```http
POST /api/collections/
```

Yeni bir koleksiyon oluşturur.

#### İstek Gövdesi

```json
{
  "title": "Favori Filmlerim",
  "description": "En sevdiğim filmlerin listesi",
  "is_public": true
}
```

#### Başarılı Yanıt

```json
{
  "id": "507f1f77bcf86cd799439011",
  "user_id": "507f1f77bcf86cd799439012",
  "title": "Favori Filmlerim",
  "description": "En sevdiğim filmlerin listesi",
  "is_public": true,
  "content_ids": [],
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

### Koleksiyonları Listeleme

```http
GET /api/collections/
```

Kullanıcının koleksiyonlarını listeler.

#### Başarılı Yanıt

```json
[
  {
    "id": "507f1f77bcf86cd799439011",
    "user_id": "507f1f77bcf86cd799439012",
    "title": "Favori Filmlerim",
    "description": "En sevdiğim filmlerin listesi",
    "is_public": true,
    "content_ids": [],
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
]
```

### Koleksiyon Detayı Getirme

```http
GET /api/collections/{collection_id}
```

Belirli bir koleksiyonun detaylarını getirir.

#### Başarılı Yanıt

```json
{
  "id": "507f1f77bcf86cd799439011",
  "user_id": "507f1f77bcf86cd799439012",
  "title": "Favori Filmlerim",
  "description": "En sevdiğim filmlerin listesi",
  "is_public": true,
  "content_ids": [],
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

### Koleksiyon Güncelleme

```http
PUT /api/collections/{collection_id}
```

Koleksiyon bilgilerini günceller.

#### İstek Gövdesi

```json
{
  "title": "Güncellenmiş Başlık",
  "description": "Güncellenmiş Açıklama",
  "is_public": false
}
```

#### Başarılı Yanıt

```json
{
  "id": "507f1f77bcf86cd799439011",
  "user_id": "507f1f77bcf86cd799439012",
  "title": "Güncellenmiş Başlık",
  "description": "Güncellenmiş Açıklama",
  "is_public": false,
  "content_ids": [],
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

### Koleksiyon Silme

```http
DELETE /api/collections/{collection_id}
```

Koleksiyonu siler.

#### Başarılı Yanıt

```json
{
  "message": "Collection deleted successfully"
}
```

### Koleksiyona İçerik Ekleme

```http
POST /api/collections/{collection_id}/contents/{content_id}
```

Koleksiyona yeni bir içerik ekler.

#### Başarılı Yanıt

```json
{
  "message": "Content added to collection successfully"
}
```

### Koleksiyondan İçerik Çıkarma

```http
DELETE /api/collections/{collection_id}/contents/{content_id}
```

Koleksiyondan bir içeriği çıkarır.

#### Başarılı Yanıt

```json
{
  "message": "Content removed from collection successfully"
}
```

### Kullanıcının Public Koleksiyonlarını Getirme

```http
GET /api/collections/user/{user_id}
```

Kullanıcının public koleksiyonlarını getirir.

#### Başarılı Yanıt

```json
[
  {
    "id": "507f1f77bcf86cd799439011",
    "user_id": "507f1f77bcf86cd799439012",
    "title": "Favori Filmlerim",
    "description": "En sevdiğim filmlerin listesi",
    "is_public": true,
    "content_ids": [],
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
]
```

## Hata Yanıtları

### 401 Unauthorized

```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden

```json
{
  "detail": "Not authorized to modify this collection"
}
```

### 404 Not Found

```json
{
  "detail": "Collection not found"
}
```

### 409 Conflict

```json
{
  "detail": "Collection with this title already exists"
}
```

## Güvenlik

Tüm endpoint'ler (public koleksiyonları getirme hariç) için kimlik doğrulama gereklidir. İsteklerin `Authorization` header'ında geçerli bir JWT token'ı bulunmalıdır:

```http
Authorization: Bearer <token>
``` 