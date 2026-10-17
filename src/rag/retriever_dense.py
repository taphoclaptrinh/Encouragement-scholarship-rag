"""
MODULE DENSE VECTOR RETRIEVER 
Tạo embedding vector và tính toán độ tương đồng Cosine Similarity.
Hỗ trợ cả Gemini Embedding và Local TF-IDF Fallback nếu chưa cấu hình API key.
"""
import os
import re
import numpy as np
from typing import List
from ..schemas.rag_types import Chunk, SearchResult

class DenseRetriever:
    def __init__(self, chunks: List[Chunk]):
        self.chunks = chunks
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model_name = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
        self.embeddings = None
        self._build_index()

    def _build_index(self):
        """Tạo ma trận embedding cho toàn bộ chunks."""
        if not self.chunks:
            return

        # Thử dùng Gemini Embedding nếu có API Key hợp lệ
        if self.api_key and self.api_key != "your_gemini_api_key_here":
            try:
                from google import genai
                client = genai.Client(api_key=self.api_key)
                vecs = []
                for c in self.chunks:
                    res = client.models.embed_content(
                        model=self.model_name,
                        contents=c.text
                    )
                    vecs.append(res.embedding.values)
                self.embeddings = np.array(vecs, dtype=np.float32)
                return
            except Exception:
                pass

        # Fallback offline TF-IDF dense vectorization
        self._build_fallback_dense_index()

    def _build_fallback_dense_index(self):
        """Vector hóa Dense cục bộ không phụ thuộc internet."""
        vocab = {}
        for c in self.chunks:
            for w in re.findall(r'\w+', c.text.lower()):
                if w not in vocab:
                    vocab[w] = len(vocab)
        self.vocab = vocab

        vecs = []
        for c in self.chunks:
            v = np.zeros(len(vocab), dtype=np.float32)
            for w in re.findall(r'\w+', c.text.lower()):
                if w in vocab:
                    v[vocab[w]] += 1.0
            norm = np.linalg.norm(v)
            if norm > 0:
                v = v / norm
            vecs.append(v)
        self.embeddings = np.array(vecs, dtype=np.float32)

    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        if self.embeddings is None or len(self.chunks) == 0:
            return []

        # Vector hóa query
        q_vec = np.zeros(self.embeddings.shape[1], dtype=np.float32)
        for w in re.findall(r'\w+', query.lower()):
            if hasattr(self, 'vocab') and w in self.vocab:
                q_vec[self.vocab[w]] += 1.0
        norm = np.linalg.norm(q_vec)
        if norm > 0:
            q_vec = q_vec / norm

        # Tính Cosine Similarity
        scores = np.dot(self.embeddings, q_vec)
        ranked_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for rank, idx in enumerate(ranked_indices, start=1):
            if scores[idx] > 0.05:
                results.append(SearchResult(
                    chunk=self.chunks[idx],
                    score=float(scores[idx]),
                    retrieval_mode="dense"
                ))
        return results
