"""
MODULE BM25 LEXICAL RETRIEVER 
Tái sử dụng rank_bm25 (BM25Okapi)
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
        self.corpus_tokens = [self._tokenize(c.text) for c in self.chunks]
        if self.corpus_tokens:
            self.bm25 = BM25Okapi(self.corpus_tokens)
        else:
            self.bm25 = None

    def _tokenize(self, text: str) -> List[str]:
        text_clean = re.sub(r'[^\w\s]', ' ', text.lower())
        return [w for w in text_clean.split() if w]

    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        if not self.bm25 or not self.chunks:
            return []

        q_tokens = self._tokenize(query)
        if not q_tokens:
            return []

        scores = self.bm25.get_scores(q_tokens)
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for rank, idx in enumerate(ranked_indices, start=1):
            if scores[idx] > 0:
                results.append(SearchResult(
                    chunk=self.chunks[idx],
                    score=float(scores[idx]),
                    retrieval_mode="bm25"
                ))
        return results
