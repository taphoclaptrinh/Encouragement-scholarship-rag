"""
MODULE HYBRID SEARCH ENGINE (YÊU CẦU TUẦN W4 & ĐIỂM CỘNG METADATA FILTER)
Tái sử dụng logic w4/ex2_1_hybrid_search.py:
- Kết hợp kết quả từ DenseRetriever và BM25Retriever bằng phương pháp RRF (Reciprocal Rank Fusion).
- [+1 Điểm cộng]: Metadata filter dùng thật trong pipeline (lọc theo filter_doc_id, filter_faculty, filter_status).
"""
from typing import List, Optional, Dict
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
        Tìm kiếm lai (Hybrid Search) kết hợp BM25 và Dense qua RRF, hỗ trợ Metadata Filter (+1 điểm cộng).
        """
        # 1. Thu thập kết quả từ 2 nhánh retriever
        bm25_res = self.bm25_retriever.search(query, top_k=top_k * 3)
        dense_res = self.dense_retriever.search(query, top_k=top_k * 3)

        # 2. Áp dụng Metadata Filtering (+1 Điểm cộng tuần W4/W6)
        def _matches_filter(chunk: Chunk) -> bool:
            meta = chunk.metadata
            if filter_doc_id and meta.doc_id != filter_doc_id:
                return False
            if filter_status and meta.status != filter_status:
                return False
            if filter_faculty and meta.faculty_scope and meta.faculty_scope != "ALL" and filter_faculty not in meta.faculty_scope:
                return False
            return True

        bm25_filtered = [r for r in bm25_res if _matches_filter(r.chunk)]
        dense_filtered = [r for r in dense_res if _matches_filter(r.chunk)]

        # 3. Thuật toán Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, Chunk] = {}

        # Điểm từ BM25 rank
        for rank, item in enumerate(bm25_filtered, start=1):
            cid = item.chunk.chunk_id
            chunk_map[cid] = item.chunk
            bm25_contrib = (1.0 - self.dense_weight) * (1.0 / (self.rrf_k + rank))
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + bm25_contrib

        # Điểm từ Dense rank
        for rank, item in enumerate(dense_filtered, start=1):
            cid = item.chunk.chunk_id
            chunk_map[cid] = item.chunk
            dense_contrib = self.dense_weight * (1.0 / (self.rrf_k + rank))
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + dense_contrib

        # 4. Sắp xếp điểm RRF từ cao xuống thấp
        sorted_chunks = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        results: List[SearchResult] = []
        for rank, (cid, score) in enumerate(sorted_chunks, start=1):
            results.append(SearchResult(
                chunk=chunk_map[cid],
                score=float(score),
                retrieval_mode="hybrid_rrf"
            ))

        return results
