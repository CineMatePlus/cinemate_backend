from sentence_transformers import SentenceTransformer
import torch

print("GPU kullanılabilir mi?", torch.cuda.is_available())

model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model device:", model.device)
print("Model hangi cihazda çalışıyor:", next(model.parameters()).device)

texts = [
    "Inception is a movie about dreams within dreams.",
    "The Matrix explores simulated reality and human consciousness.",
    "Titanic is a tragic love story set on a sinking ship."
]

embeddings = model.encode(texts)

for i, vec in enumerate(embeddings):
    print(f"\n🎬 {texts[i]}")
    print(f"📐 Vector: {vec[:5]}... ({len(vec)} dimension)")
