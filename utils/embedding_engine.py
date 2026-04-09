import os
from typing import List
from fastembed import TextEmbedding
from fastembed.rerank.cross_encoder.text_cross_encoder import TextCrossEncoder

class EmbeddingEngine:
    """
    Local Embedding and Reranking Engine using FastEmbed.
    Optimized for CPU inference.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(EmbeddingEngine, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_name: str = "intfloat/multilingual-e5-large", rerank_model: str = "BAAI/bge-reranker-base"):
        if self._initialized:
            return
        
        # Cache directory for models
        cache_dir = os.path.join(os.getcwd(), "models", "fastembed")
        os.makedirs(cache_dir, exist_ok=True)
        
        print(f"[EmbeddingEngine] Loading text embedding model: {model_name}...")
        self.model = TextEmbedding(model_name=model_name, cache_dir=cache_dir)
        
        print(f"[EmbeddingEngine] Loading reranker model: {rerank_model}...")
        try:
            self.reranker = TextCrossEncoder(model_name=rerank_model, cache_dir=cache_dir)
            print(f"[EmbeddingEngine] Reranker model {rerank_model} loaded successfully.")
        except Exception as e:
            print(f"⚠️ [EmbeddingEngine] Failed to load reranker {rerank_model}: {e}. Reranking will be skipped.")
            self.reranker = None
            
        self._initialized = True

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query string.
        """
        if not text:
            return [0.0] * 1024
        # list() is needed because embed() returns a generator
        embeddings = list(self.model.embed([text]))
        return embeddings[0].tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of document strings.
        """
        if not texts:
            return []
        embeddings = list(self.model.embed(texts))
        return [e.tolist() for e in embeddings]

    def rerank(self, query: str, documents: List[str]) -> List[float]:
        """
        Rerank a list of documents based on a query.
        Returns a list of scores.
        """
        if not documents:
            return []
            
        if not self.reranker:
            # Fallback: if reranker is not available, return uniform scores
            # This preserves the original order from the vector search
            return [1.0] * len(documents)
            
        try:
            scores = list(self.reranker.rerank(query, documents))
            return scores
        except Exception as e:
            print(f"⚠️ [EmbeddingEngine] Rerank execution failed: {e}")
            return [1.0] * len(documents)
