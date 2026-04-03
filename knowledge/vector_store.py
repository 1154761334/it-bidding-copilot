"""
向量知识库封装
基于 FAISS 的文档存储与相似性检索
"""
import os
import json
from pathlib import Path
from typing import Optional

try:
    from langchain_community.vectorstores import FAISS
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.schema import Document
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False

from config import VECTOR_STORE_DIR
from knowledge.embeddings import get_embeddings


class KnowledgeBase:
    """企业知识库 — 基于 FAISS 向量检索"""

    def __init__(self, enterprise_id: str, embeddings=None):
        self.enterprise_id = enterprise_id
        self.store_path = VECTOR_STORE_DIR / enterprise_id
        self.embeddings = embeddings or get_embeddings()
        self.vectorstore = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            separators=["\n\n", "\n", "。", "；", " "],
        ) if HAS_LANGCHAIN else None

        # 尝试加载已有索引
        self._load()

    def add_documents(self, texts: list[str], metadatas: list[dict] = None):
        """将文本加入知识库"""
        if not HAS_LANGCHAIN or self.embeddings is None:
            self._mock_add(texts)
            return

        docs = self.text_splitter.create_documents(
            texts,
            metadatas=metadatas or [{}] * len(texts),
        )

        if self.vectorstore is None:
            # 兼容旧版本初始化方式，如果目录不存在则创建新索引
            self.vectorstore = FAISS.from_documents(docs, self.embeddings)
        else:
            self.vectorstore.add_documents(docs)

        self._save()

    def search(self, query: str, k: int = 5) -> list[dict]:
        """相似性检索"""
        if not HAS_LANGCHAIN or self.vectorstore is None:
            return self._mock_search(query, k)

        results = self.vectorstore.similarity_search_with_score(query, k=k)
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score),
            }
            for doc, score in results
        ]

    def _save(self):
        """持久化索引"""
        if self.vectorstore:
            self.store_path.mkdir(parents=True, exist_ok=True)
            self.vectorstore.save_local(str(self.store_path))

    def _load(self):
        """加载已有索引"""
        if not HAS_LANGCHAIN or self.embeddings is None:
            return
        index_file = self.store_path / "index.faiss"
        if index_file.exists():
            try:
                self.vectorstore = FAISS.load_local(
                    str(self.store_path),
                    self.embeddings,
                    allow_dangerous_deserialization=True,
                )
            except Exception:
                self.vectorstore = None

    # ── Mock 方法（Phase 2 兼容） ──

    def _mock_add(self, texts: list[str]):
        """Mock 文档添加"""
        meta_path = self.store_path / "mock_docs.json"
        self.store_path.mkdir(parents=True, exist_ok=True)

        existing = []
        if meta_path.exists():
            try:
                existing = json.loads(meta_path.read_text(encoding="utf-8"))
            except:
                existing = []

        for t in texts:
            existing.append({"content": t[:200], "length": len(t)})

        meta_path.write_text(
            json.dumps(existing, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _mock_search(self, query: str, k: int) -> list[dict]:
        """Mock 搜索"""
        return [
            {
                "content": f"（Mock 检索结果）与查询 '{query[:30]}...' 相关的知识片段",
                "metadata": {"source": "mock"},
                "score": 0.85,
            }
        ]
