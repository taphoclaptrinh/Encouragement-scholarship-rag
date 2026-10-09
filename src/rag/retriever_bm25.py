"""
MODULE BM25 LEXICAL RETRIEVER (YÊU CẦU TUẦN W4)
Yêu cầu:
- Tái sử dụng thư viện rank_bm25 (BM25Okapi)
- Tách từ (tokenize) cho văn bản tiếng Việt / tiếng Anh
- Trả về danh sách SearchResult kèm điểm số score
"""
import re
from typing import List
from rank_bm25 import BM25Okapi
from ..schemas.rag_types import Chunk, SearchResult

class BM25Retriever:
    def __init__(self, chunks: List[Chunk]):
        self.chunks = chunks
        self._build_index()

    def _build_index(self):
        """
        TODO (Thành viên phụ trách RAG):
        Tách từ các chunks và khởi tạo mô hình BM25Okapi:
        self.corpus_tokens = [self._tokenize(c.text) for c in self.chunks]
        self.bm25 = BM25Okapi(self.corpus_tokens)
        """
        pass

    def _tokenize(self, text: str) -> List[str]:
        # Tách từ cơ bản
        text_clean = re.sub(r'[^\w\s]', ' ', text.lower())
        return [w for w in text_clean.split() if w]

    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """
        TODO (Thành viên phụ trách RAG):
        1. Tokenize query.
        2. Tính scores = self.bm25.get_scores(query_tokens).
        3. Lấy top_k kết quả có điểm cao nhất và tạo danh sách SearchResult.
        """
        return []
