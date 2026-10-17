"""
- Đọc testset từ tests/testset.jsonl (14 câu gồm: grounding, reasoning, action_and_verify, no_answer)
- Đo lường Grounding (Trích dẫn đúng mã tài liệu DOCxxxx)
- Đo lường Calibration (Tỉ lệ từ chối đúng khi câu hỏi ngoài phạm vi - no_answer)
- Đo lường Side Effect & Verification (Tỉ lệ thực thi đủ quy trình Ghi + Xác minh)
- Log USAGE từng câu (calls, prompt_tokens, completion_tokens, max_prompt, latency)
- Xuất log chạy ra thư mục logs/run_<timestamp>.jsonl và logs/eval_summary.csv
"""
import sys
import os
import json
import time
from datetime import datetime
import pandas as pd
from tabulate import tabulate

# Đảm bảo import được các module từ thư mục gốc
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from src.rag.chunker import DocumentChunker
from src.rag.hybrid_search import HybridSearchEngine
from src.agent.mcp_client import DynamicMCPClient
from src.core.llm_client import LLMClient
from src.agent.loop import ScholarshipAgent

def check_refusal(answer: str) -> bool:
    """Kiểm tra xem câu trả lời có chứa các cụm từ từ chối chuẩn khi không có dữ liệu hay không."""
    refusal_keywords = [
        "không tìm thấy", "không có thông tin", "ngoài phạm vi", "chưa đủ dữ liệu",
        "không nằm trong", "không được quy định", "không thể kết luận", "không thể trả lời"
    ]
    ans_lower = answer.lower()
    return any(kw in ans_lower for kw in refusal_keywords)

def check_grounding(answer: str, expected_docs_str: str) -> bool:
    """Kiểm tra câu trả lời có trích dẫn đúng mã văn bản kỳ vọng (ví dụ: DOC0001, DOC0002) hay không."""
    if not expected_docs_str:
        return True
    expected_docs = [d.strip() for d in expected_docs_str.split(",")]
    # Đạt yêu cầu nếu trích dẫn được ít nhất 1 mã tài liệu trong danh sách yêu cầu
    return any(doc in answer for doc in expected_docs)

def check_action_verified(steps: list) -> bool:
    """Kiểm tra quy trình Action có gọi submit_scholarship_nomination và verify_scholarship_nomination không."""
    has_submit = False
    has_verify = False
    for step in steps:
        action = step.get("action")
        if action == "submit_scholarship_nomination":
            has_submit = True
        elif action == "verify_scholarship_nomination":
            has_verify = True
    return has_submit and has_verify

def run_evaluation():
    print("=" * 75)
    print("   HỆ THỐNG ĐÁNH GIÁ CHẤT LƯỢNG RAG & AGENT (AIPR FINAL EVAL W5)")
    print("=" * 75)

    corpus_dir = os.path.join(base_dir, "data", "corpus")
    server_path = os.path.join(base_dir, "src", "mcp_server", "server.py")
    testset_path = os.path.join(base_dir, "tests", "testset.jsonl")
    logs_dir = os.path.join(base_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    # 1. Khởi tạo Pipeline
    print("\n[1/4] Đang khởi tạo Document Chunker & Hybrid Search Engine...")
    chunker = DocumentChunker(corpus_dir)
    chunks = chunker.load_and_chunk_all()
    hybrid_engine = HybridSearchEngine(chunks)

    print("[2/4] Đang khởi tạo MCP Client và Gemini LLM Client...")
    mcp_client = DynamicMCPClient(server_path)
    llm_client = LLMClient()
    agent = ScholarshipAgent(
        hybrid_engine=hybrid_engine,
        mcp_client=mcp_client,
        llm_client=llm_client,
        max_steps=6
    )

    # 2. Đọc bộ testset
    print(f"[3/4] Đang tải bộ câu hỏi kiểm thử từ: {testset_path}")
    test_cases = []
    with open(testset_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                test_cases.append(json.loads(line))
    print(f"      -> Tổng số ca kiểm thử: {len(test_cases)}")

    # 3. Chạy từng câu và chấm điểm
    print("\n[4/4] BẮT ĐẦU CHẠY ĐÁNH GIÁ (BENCHMARK EVALUATION)...")
    eval_results = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_log_file = os.path.join(logs_dir, f"run_{timestamp}.jsonl")

    with open(run_log_file, "w", encoding="utf-8") as log_f:
        for idx, tc in enumerate(test_cases, 1):
            q_id = tc.get("id")
            q_type = tc.get("type")
            question = tc.get("question")
            is_no_ans = tc.get("is_no_answer", False)
            expected_doc = tc.get("expected_doc")

            print(f"\n--- [{idx}/{len(test_cases)}] Đang chạy câu {q_id} ({q_type}) ---")
            print(f"Câu hỏi: {question}")

            start_t = time.time()
            try:
                res = agent.run(question)
            except Exception as e:
                print(f"[ERROR] Lỗi khi chạy câu {q_id}: {e}")
                res = {
                    "query": question,
                    "final_answer": f"Lỗi hệ thống: {e}",
                    "steps": [],
                    "total_steps": 0,
                    "usage": {"calls": 0, "total_tokens": 0, "prompt_tokens": 0, "completion_tokens": 0, "latency_seconds": 0}
                }
            elapsed = time.time() - start_t

            final_answer = res.get("final_answer", "")
            steps = res.get("steps", [])
            usage = res.get("usage", {})

            # Đánh giá tiêu chí
            is_correct_refusal = None
            is_grounded = None
            is_action_ok = None

            should_refuse = is_no_ans or (q_type == "missing_data_refusal")

            if should_refuse:
                # Câu hỏi ngoài phạm vi hoặc thiếu dữ liệu: Phải từ chối đúng (Calibration)
                is_correct_refusal = check_refusal(final_answer)
                status_str = "PASS (Từ chối đúng)" if is_correct_refusal else "FAIL (Bị ảo giác)"
            elif q_type == "action_and_verify":
                # Câu hỏi thực hiện hành động: Phải gọi đủ submit + verify
                is_action_ok = check_action_verified(steps)
                status_str = "PASS (Submit + Verify)" if is_action_ok else "FAIL (Thiếu bước verify)"
            else:
                # Câu hỏi thông thường: Đo Grounding (trích dẫn đúng mã tài liệu)
                is_grounded = check_grounding(final_answer, expected_doc)
                status_str = "PASS (Đã trích dẫn)" if is_grounded else "WARN (Chưa trích dẫn rõ mã)"

            print(f">> Kết quả đánh giá: {status_str} | Số bước: {res.get('total_steps')} | Thời gian: {elapsed:.2f}s")
            time.sleep(4)

            record = {
                "id": q_id,
                "type": q_type,
                "question": question,
                "is_no_answer": is_no_ans,
                "expected_doc": expected_doc,
                "final_answer": final_answer,
                "total_steps": res.get("total_steps", 0),
                "is_correct_refusal": is_correct_refusal,
                "is_grounded": is_grounded,
                "is_action_ok": is_action_ok,
                "calls": usage.get("calls", 0),
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "latency_seconds": round(usage.get("latency_seconds", elapsed), 2)
            }
            eval_results.append(record)

            # Ghi vết chi tiết vào run_*.jsonl
            full_log_item = {
                "test_id": q_id,
                "metadata": tc,
                "result": res,
                "evaluation": {
                    "is_correct_refusal": is_correct_refusal,
                    "is_grounded": is_grounded,
                    "is_action_ok": is_action_ok
                }
            }
            log_f.write(json.dumps(full_log_item, ensure_ascii=False) + "\n")

    # 4. Xuất báo cáo CSV & Bảng tổng kết
    df = pd.DataFrame(eval_results)
    csv_path = os.path.join(logs_dir, "eval_summary.csv")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    print("\n" + "=" * 75)
    print("                     BẢNG TỔNG KẾT KẾT QUẢ ĐÁNH GIÁ (EVALUATION)")
    print("=" * 75)
    summary_cols = ["id", "type", "is_no_answer", "total_steps", "total_tokens", "latency_seconds"]
    print(tabulate(df[summary_cols], headers="keys", tablefmt="pretty", showindex=False))

    # Tính toán các chỉ số cốt lõi
    refusal_df = df[(df["is_no_answer"] == True) | (df["type"] == "missing_data_refusal")]
    calib_rate = (refusal_df["is_correct_refusal"].sum() / len(refusal_df)) * 100 if len(refusal_df) > 0 else 0

    grounding_df = df[(df["is_no_answer"] == False) & (df["type"] != "action_and_verify") & (df["type"] != "missing_data_refusal")]
    grounding_rate = (grounding_df["is_grounded"].sum() / len(grounding_df)) * 100 if len(grounding_df) > 0 else 0

    action_df = df[df["type"] == "action_and_verify"]
    action_rate = (action_df["is_action_ok"].sum() / len(action_df)) * 100 if len(action_df) > 0 else 0

    print("\n" + "*" * 75)
    print(f"1. Tỉ lệ Từ chối đúng (Calibration Rate trên câu No-Answer & Thiếu dữ liệu): {calib_rate:.1f}% ({refusal_df['is_correct_refusal'].sum()}/{len(refusal_df)})")
    print(f"2. Tỉ lệ Trích dẫn có căn cứ (Grounding Rate):                 {grounding_rate:.1f}% ({grounding_df['is_grounded'].sum()}/{len(grounding_df)})")
    print(f"3. Tỉ lệ Thực thi Đúng & Xác minh (Action & Verify Rate):       {action_rate:.1f}% ({action_df['is_action_ok'].sum()}/{len(action_df)})")
    print(f"4. Tổng lượng Token tiêu thụ:                                   {df['total_tokens'].sum():,} tokens")
    print(f"5. Thời gian chạy trung bình mỗi câu:                           {df['latency_seconds'].mean():.2f} giây")
    print("*" * 75)
    print(f"\n[OK] Đã lưu chi tiết toàn bộ vết chạy tại: {run_log_file}")
    print(f"[OK] Đã xuất file số liệu báo cáo tại:       {csv_path}\n")

if __name__ == "__main__":
    run_evaluation()
