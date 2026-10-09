"""
MODULE HYBRID SEARCH ENGINE (YÊU CẦU TUẦN W4 & ĐIỂM CỘNG METADATA FILTER)
Yêu cầu:
- Tái sử dụng logic w4/ex2_1_hybrid_search.py
- Kết hợp kết quả từ DenseRetriever và BM25Retriever bằng phương pháp RRF (Reciprocal Rank Fusion)
- [+1 Điểm cộng]: Metadata filter dùng thật trong pipeline (lọc theo filter_doc_id, filter_faculty, filter_status)
"""
from typing import List, Optional
from ..schemas.rag_types import Chunk, SearchResult
from .retriever_bm25 import BM25Retriever
from .retriever_dense import DenseRetriever

class HybridSearchEngine:
    def __init__(self, chunks: List[Chunk], rrf_k: int = 60, dense_weight: float = 0.5):
        self.chunks = chunks
        self.rrf_k = rrf_k
        self.dense_weight = dense_weight
        self.bm25_retriever = BM25Retriever(chunks)
        self.dense_retriever = DenseRetriever(chunks)

    def search(
        self,
        query: str,
        top_k: int = 4,
        filter_doc_id: Optional[str] = None,
        filter_faculty: Optional[str] = None,
        filter_status: Optional[str] = None
    ) -> List[SearchResult]:
        """
        TODO (Thành viên phụ trách RAG):
        1. Gọi BM25 search và Dense search với top_k*2.
        2. Lọc kết quả theo metadata (doc_id, faculty, status) nếu tham số được cung cấp.
        3. Tính điểm RRF kết hợp:
           score = (1 - dense_weight) * (1 / (rrf_k + rank_bm25)) + dense_weight * (1 / (rrf_k + rank_dense))
        4. Sắp xếp và trả về Top-K kết quả SearchResult(retrieval_mode="hybrid_rrf").
        """
        return []
