from transformers import AutoTokenizer, AutoModel
import torch

tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2").to("cuda")

inputs = tokenizer(["test"], return_tensors="pt", padding=True, truncation=True).to("cuda")

with torch.no_grad():
    outputs = model(**inputs)
    print("Tensör hangi cihazda?", outputs.last_hidden_state.device)
