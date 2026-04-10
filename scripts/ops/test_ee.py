import os
import sys
sys.path.append(os.getcwd())
from utils.embedding_engine import EmbeddingEngine

def test():
    print("Initializing EmbeddingEngine...", flush=True)
    ee = EmbeddingEngine()
    print("EmbeddingEngine initialized.", flush=True)
    
    q = "test query"
    print(f"Embedding query: '{q}'...", flush=True)
    emb = ee.embed_query(q)
    print(f"Embedding length: {len(emb)}", flush=True)
    print(f"First 5 values: {emb[:5]}", flush=True)

if __name__ == "__main__":
    test()
