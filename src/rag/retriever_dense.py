"""
MODULE DENSE VECTOR RETRIEVER (YÊU CẦU TUẦN W3-W4)
Yêu cầu:
- Tạo embedding vector cho các chunks
- Tính toán độ tương đồng Cosine Similarity giữa câu hỏi và chunks
- Hỗ trợ text-embedding-004 qua Gemini SDK (hoặc thư viện embedding cục bộ)
"""
import os
import numpy as np
from typing import List
from ..schemas.rag_types import Chunk, SearchResult

class DenseRetriever:
    def __init__(self, chunks: List[Chunk]):
        self.chunks = chunks
        self.model_name = os.getenv("EMBEDDING_MODEL", "text-embedding-004")
        self._build_index()

    def _build_index(self):
        """
        TODO (Thành viên phụ trách RAG):
        Tạo ma trận embedding cho toàn bộ self.chunks và lưu trữ dưới dạng np.ndarray.
        """
        pass

    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """
        TODO (Thành viên phụ trách RAG):
        1. Tạo vector embedding cho query.
        2. Tính Cosine Similarity với ma trận chunk embeddings.
        3. Lấy top_k kết quả có độ tương đồng cao nhất và trả về SearchResult(retrieval_mode="dense").
        """
        return []
