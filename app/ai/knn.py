import numpy as np
from pymongo import MongoClient
from sklearn.metrics.pairwise import cosine_similarity
from bson import ObjectId
from sentence_transformers import SentenceTransformer

client = MongoClient("mongodb://localhost:27017")
db = client["tests"]
collection = db["movie_embeddings_bge_m3"]  # NOT: Kullandığınız embedding modeline göre doğru koleksiyonu seçtiğinizden emin olun.

# AI Modelini Yükle
print("Embedding modeli yükleniyor...")
# Film embedding'lerini oluşturmak için kullanılan model ile aynı olmalı.
# app/services/ai.py dosyasında 'all-MiniLM-L6-v2' kullanılıyor.
model = SentenceTransformer('BAAI/bge-m3')
print("Model başarıyla yüklendi.")


def get_similar_movies_by_prompt(prompt: str, top_k: int = 10):
    """
    Verilen bir metin istemine dayalı olarak benzer filmleri bulur.
    """
    # 1. Kullanıcının girdiği metin için anlamsal bir vektör oluştur
    prompt_embedding = model.encode(prompt, normalize_embeddings=True)
    prompt_vector = np.array(prompt_embedding).reshape(1, -1)

    # 2. Veritabanındaki tüm filmleri ve vektörlerini al
    all_docs = list(collection.find({}, {"_id": 1, "title": 1, "embedding": 1}))

    if not all_docs:
        print("Veritabanında hiç film bulunamadı.")
        return []

    ids = [str(doc["_id"]) for doc in all_docs]
    titles = [doc.get("title", "Başlıksız") for doc in all_docs]
    embeddings = np.array([doc["embedding"] for doc in all_docs])

    # 3. Kosinüs benzerliğini hesapla
    similarities = cosine_similarity(prompt_vector, embeddings)[0]

    # 4. En benzer K sonucu sırala
    similar_indices = similarities.argsort()[::-1][:top_k]

    # 5. Sonuçları hazırla
    results = []
    for i in similar_indices:
        results.append({
            "id": ids[i],
            "title": titles[i],
            "similarity": float(similarities[i])
        })

    return results


def get_similar_movies(target_id, top_k=10):
    # 1. Tüm içerikleri ve embedding'lerini al
    all_docs = list(collection.find({}, {"_id": 1, "title": 1, "embedding": 1}))

    # 2. Embedding listesi ve id eşlemesi oluştur
    ids = [str(doc["_id"]) for doc in all_docs]
    titles = [doc["title"] for doc in all_docs]
    embeddings = np.array([doc["embedding"] for doc in all_docs])

    # 3. Hedef içeriği bul
    try:
        target_index = ids.index(str(target_id))
    except ValueError:
        raise Exception("Verilen içerik ID'si bulunamadı.")

    target_vector = embeddings[target_index].reshape(1, -1)

    # 4. Cosine similarity hesapla
    similarities = cosine_similarity(target_vector, embeddings)[0]

    # 5. En benzer k içeriği sırala (kendisi hariç)
    similar_indices = similarities.argsort()[::-1]
    similar_indices = [i for i in similar_indices if i != target_index][:top_k]

    # 6. Sonuçları hazırla
    results = []
    for i in similar_indices:
        results.append({
            "id": ids[i],
            "title": titles[i],
            "similarity": float(similarities[i])
        })

    return results


# result = get_similar_movies(ObjectId("6657c1e9e14b17e264d0fa73"))
# for r in result:
#     print(f"{r['title']}: {r['similarity']:.4f}")


if __name__ == "__main__":
    while True:
        # Kullanıcıdan bir metin al (çıkış seçeneği ile birlikte)
        user_prompt = input("\n🎬 Benzer filmleri bulmak için bir konu girin (çıkmak için 'q', 'quit' veya 'exit' yazın): ")

        # Çıkış komutlarını kontrol et
        if user_prompt.lower() in ['q', 'quit', 'exit']:
            print("👋 Görüşmek üzere!")
            break

        if user_prompt and user_prompt.strip():
            # Tavsiyeleri al ve yazdır
            recommendations = get_similar_movies_by_prompt(user_prompt, top_k=10)
            
            if recommendations:
                print(f"\n✨ '{user_prompt}' için en iyi {len(recommendations)} öneri:")
                for r in recommendations:
                    print(f"  - {r['title']} (Benzerlik: {r['similarity']:.4f})")
            else:
                print("Bu konuyla eşleşen bir film bulunamadı.")
        else:
            print("❌ Geçerli bir metin girilmedi. Lütfen tekrar deneyin.")


