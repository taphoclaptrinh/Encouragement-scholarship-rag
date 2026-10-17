"""
SO SÁNH CẤU HÌNH TRUY XUẤT RAG (DENSE VÀ HYBRID)
- Đo độ trễ truy vấn của DenseRetriever và HybridSearchEngine.
- Kiểm tra tài liệu mong đợi có xuất hiện trong top 5 kết quả hay không.
- Lưu kết quả so sánh vào file CSV trong thư mục logs/.
"""
import csv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag.chunker import DocumentChunker
from src.rag.hybrid_search import HybridSearchEngine
from src.rag.retriever_dense import DenseRetriever

QUERIES = [
    {
        "id": "Q1",
        "query": "điều kiện điểm rèn luyện của sinh viên",
        "expected_doc": "DOC0005"
    },
    {
        "id": "Q2",
        "query": "điểm rèn luyện được đánh giá và phân loại như thế nào",
        "expected_doc": "DOC0005"
    },
    {
        "id": "Q3",
        "query": "quy định về học bổng khuyến khích học tập",
        "expected_doc": "DOC0001"
    },
    {
        "id": "Q4",
        "query": "điều kiện số tín chỉ tích lũy để xét học bổng",
        "expected_doc": "DOC0006"
    }
]


def compare_rag_configs():
    """Chạy bộ truy vấn và lưu kết quả so sánh Dense với Hybrid."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    corpus_dir = os.path.join(base_dir, "data", "corpus")
    chunks = DocumentChunker(corpus_dir).load_and_chunk_all()

    if not chunks:
        print(f"[ERROR] Không tìm thấy chunk nào trong {corpus_dir}")
        return

    os.environ.setdefault("GEMINI_API_KEY", "")
    dense_retriever = DenseRetriever(chunks)
    hybrid_retriever = HybridSearchEngine(chunks)
    results_log = []

    print("=" * 72)
    print("SO SÁNH TRUY XUẤT RAG: DENSE VÀ HYBRID")
    print(f"Số lượng chunks: {len(chunks)}")
    print("=" * 72)

    for case in QUERIES:
        for mode, retriever in (("dense", dense_retriever), ("hybrid", hybrid_retriever)):
            start_time = time.perf_counter()
            results = retriever.search(case["query"], top_k=5)
            latency_ms = (time.perf_counter() - start_time) * 1000
            doc_ids = [result.chunk.metadata.doc_id for result in results]
            hit = case["expected_doc"] in doc_ids

            results_log.append({
                "query_id": case["id"],
                "query": case["query"],
                "mode": mode,
                "expected_doc": case["expected_doc"],
                "top_doc_ids": ";".join(doc_ids),
                "expected_doc_in_top5": hit,
                "result_count": len(results),
                "latency_ms": round(latency_ms, 3)
            })
            print(f"{case['id']} | {mode.upper():6} | hit@5={str(hit):5} | {latency_ms:8.2f} ms | {', '.join(doc_ids)}")

    output_dir = os.path.join(base_dir, "logs")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "compare_rag_configs.csv")

    with open(output_file, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(results_log[0].keys()))
        writer.writeheader()
        writer.writerows(results_log)

    print("-" * 72)
    for mode in ("dense", "hybrid"):
        mode_results = [row for row in results_log if row["mode"] == mode]
        hits = sum(row["expected_doc_in_top5"] for row in mode_results)
        average_latency = sum(row["latency_ms"] for row in mode_results) / len(mode_results)
        print(f"{mode.upper()}: hit@5={hits}/{len(mode_results)}, độ trễ trung bình={average_latency:.2f} ms")
    print(f"CSV đã lưu tại: {output_file}")


if __name__ == "__main__":
    compare_rag_configs()
