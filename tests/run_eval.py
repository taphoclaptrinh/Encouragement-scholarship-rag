"""
HỆ THỐNG ĐÁNH GIÁ CHẤT LƯỢNG RAG & AGENT (YÊU CẦU TUẦN W5)
Yêu cầu:
- Đọc testset từ tests/testset.jsonl (>= 12 câu, >= 4 câu no_answer)
- Đo lường Faithfulness và Tỉ lệ từ chối đúng (Calibration Rate)
- Log USAGE từng câu (calls, prompt_tokens, completion_tokens, max_prompt)
- Xuất log chạy ra thư mục logs/run_*.jsonl
"""
import os
import json
import time
import pandas as pd
from tabulate import tabulate

def run_evaluation():
    print("=" * 65)
    print("   HỆ THỐNG ĐÁNH GIÁ CHẤT LƯỢNG RAG & AGENT (AIPR FINAL EVAL)")
    print("=" * 65)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    testset_path = os.path.join(base_dir, "tests", "testset.jsonl")

    # TODO (Thành viên phụ trách Đánh giá W5):
    # 1. Khởi tạo DocumentChunker, HybridSearchEngine, MCP Client, LLMClient và ScholarshipAgent.
    # 2. Đọc danh sách câu hỏi trong testset.jsonl.
    # 3. Lặp qua từng câu hỏi, gọi agent.run(question).
    # 4. Kiểm tra xem câu no_answer có được từ chối đúng hay không.
    # 5. Lưu vết chạy vào logs/run_<timestamp>.jsonl và xuất eval_results.csv.
    # 6. In bảng tổng kết token và độ chính xác ra màn hình.
    print("TODO: Triển khai kịch bản đánh giá benchmark tại đây.")

if __name__ == "__main__":
    run_evaluation()
