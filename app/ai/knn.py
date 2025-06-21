import numpy as np
from pymongo import MongoClient
from sklearn.metrics.pairwise import cosine_similarity
from bson import ObjectId

client = MongoClient("mongodb://localhost:27017")
db = client["tests"]
collection = db["movie_embeddings"]  # veya hangi koleksiyon ismini verdiysen

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
    # Bu kısım, dosya doğrudan çalıştırıldığında (import edildiğinde değil) çalışır.
    # Mevcut 46-49. satırları buraya taşıyarak veya kopyalayarak kullanabilirsiniz.
    # Orijinal 46-49. satırları bu bloğun dışından silmeyi unutmayın.
    result = get_similar_movies(ObjectId("6857369c0119eb4aa22f5339"))
    for r in result:
        print(f"{r['title']}: {r['similarity']:.4f}")


