"""
BỘ KIỂM THỬ TỰ ĐỘNG CHO RAG PIPELINE
1. Kiểm tra tách tài liệu theo Điều khoản và đọc metadata.
2. Kiểm tra truy xuất BM25 và Dense.
3. Kiểm tra Hybrid Search và Metadata Filter.
4. Kiểm tra đầu vào rỗng.
"""
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag.chunker import DocumentChunker
from src.rag.hybrid_search import HybridSearchEngine
from src.rag.retriever_bm25 import BM25Retriever
from src.rag.retriever_dense import DenseRetriever
from src.schemas.rag_types import Chunk, DocMetadata


class TestRAGPipeline(unittest.TestCase):
    def setUp(self):
        self.metadata_drl = DocMetadata(
            doc_id="DOC0005",
            title="Quy định điểm rèn luyện",
            date="2023-10-01",
            version="1.2",
            owner="P.CTSV",
            status="ACTIVE_CURRENT",
            faculty="ALL"
        )
        self.metadata_scholarship = DocMetadata(
            doc_id="DOC0006",
            title="Thông báo xét học bổng",
            date="2026-03-16",
            version="3.0",
            owner="P.CTSV",
            status="ACTIVE_CURRENT",
            faculty="ALL"
        )
        self.chunks = [
            Chunk(
                "DOC0005_c01",
                "Điều 1. Điểm rèn luyện sinh viên được đánh giá theo kết quả học tập và hoạt động.",
                self.metadata_drl
            ),
            Chunk(
                "DOC0005_c02",
                "Điều 2. Kết quả rèn luyện được phân loại theo khung điểm quy định.",
                self.metadata_drl
            ),
            Chunk(
                "DOC0006_c01",
                "Điều 3. Điều kiện xét học bổng gồm điểm trung bình và số tín chỉ tích lũy.",
                self.metadata_scholarship
            )
        ]

    def test_01_chunker_reads_frontmatter_and_splits_articles(self):
        """Kiểm tra chunker đọc metadata và tách văn bản theo Điều."""
        document = (
            "---\ndoc_id: DOC0005\ntitle: Quy định điểm rèn luyện\n"
            "date: 2023-10-01\nversion: 1.2\nowner: P.CTSV\n"
            "status: ACTIVE_CURRENT\n---\n"
            "Điều 1. Phạm vi áp dụng.\nNội dung thứ nhất.\n\n"
            "Điều 2. Cách đánh giá.\nNội dung thứ hai."
        )

        with patch("builtins.open", unittest.mock.mock_open(read_data=document)):
            chunks = DocumentChunker("data/corpus").chunk_document("DOC0005_test.txt")

        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0].metadata.doc_id, "DOC0005")
        self.assertIn("Điều 1", chunks[0].text)
        self.assertIn("Điều 2", chunks[1].text)

    def test_02_bm25_returns_relevant_chunk(self):
        """Kiểm tra BM25 trả về chunk liên quan đến truy vấn."""
        results = BM25Retriever(self.chunks).search("điểm rèn luyện sinh viên", top_k=3)
        self.assertTrue(results)
        self.assertEqual(results[0].chunk.metadata.doc_id, "DOC0005")
        self.assertTrue(all(result.retrieval_mode == "bm25" for result in results))

    def test_03_dense_retriever_runs_offline(self):
        """Kiểm tra Dense Retriever hoạt động khi không có API key."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            results = DenseRetriever(self.chunks).search("điểm rèn luyện sinh viên", top_k=3)

        self.assertTrue(results)
        self.assertTrue(all(result.retrieval_mode == "dense" for result in results))

    def test_04_hybrid_search_returns_results(self):
        """Kiểm tra Hybrid Search kết hợp kết quả truy xuất."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            results = HybridSearchEngine(self.chunks).search("điểm rèn luyện sinh viên", top_k=3)

        self.assertTrue(results)
        self.assertTrue(all(result.retrieval_mode == "hybrid_rrf" for result in results))

    def test_05_hybrid_metadata_filter(self):
        """Kiểm tra lọc kết quả theo mã tài liệu và trạng thái."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            engine = HybridSearchEngine(self.chunks)
            results = engine.search(
                "điểm rèn luyện sinh viên",
                top_k=5,
                filter_doc_id="DOC0005",
                filter_status="ACTIVE_CURRENT"
            )

        self.assertTrue(results)
        self.assertTrue(all(result.chunk.metadata.doc_id == "DOC0005" for result in results))
        self.assertTrue(all(result.chunk.metadata.status == "ACTIVE_CURRENT" for result in results))

    def test_06_empty_retrievers_return_no_results(self):
        """Kiểm tra các retriever trả về danh sách rỗng khi không có chunk."""
        self.assertEqual(BM25Retriever([]).search("anything"), [])
        self.assertEqual(DenseRetriever([]).search("anything"), [])
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            self.assertEqual(HybridSearchEngine([]).search("anything"), [])


if __name__ == "__main__":
    unittest.main()
