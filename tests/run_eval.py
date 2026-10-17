"""
HỆ THỐNG ĐÁNH GIÁ CHẤT LƯỢNG RAG & AGENT (YÊU CẦU TUẦN W5)
Độc lập, không phụ thuộc thư viện ngoài nặng:
- Tự động đọc tests/testset.jsonl (14 câu hỏi)
- Đánh giá Faithfulness & Calibration Rate (tỉ lệ từ chối đúng)
- Ghi log USAGE chi tiết từng câu theo định dạng JSONL (calls, tokens, latency)
- Xuất tệp logs/run_<timestamp>.jsonl và logs/eval_results.csv
"""
import os
import sys
import json
import time
from datetime import datetime

# Cấu hình UTF-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Thêm root vào sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    return any(kw in answer.lower() for kw in refusal_keywords)

def run_evaluation():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    testset_path = os.path.join(base_dir, "tests", "testset.jsonl")
    logs_dir = os.path.join(base_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    print("=" * 75)
    print("   CHƯƠNG TRÌNH ĐÁNH GIÁ CHẤT LƯỢNG HỆ THỐNG (BENCHMARK EVALUATION)")
    print("=" * 75)

    print("\n[1/4] Đang khởi tạo DocumentChunker và HybridSearchEngine...")
    chunker = DocumentChunker(os.path.join(base_dir, "data", "corpus"))
    chunks = chunker.load_and_chunk_all()
    hybrid_engine = HybridSearchEngine(chunks)
    print(f" -> Đã nạp thành công {len(chunks)} chunks quy chế vào chỉ mục.")

    print("\n[2/4] Đang kết nối MCP Server và LLM Client...")
    mcp_client = DynamicMCPClient(os.path.join(base_dir, "src", "mcp_server", "server.py"))
    llm_client = LLMClient()
    agent = ScholarshipAgent(
        hybrid_engine=hybrid_engine,
        mcp_client=mcp_client,
        llm_client=llm_client,
        max_steps=6
    )

    # 2. Đọc Testset
    print(f"\n[3/4] Đang nạp bộ testset từ: {testset_path}")
    test_cases = []
    with open(testset_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                test_cases.append(json.loads(line.strip()))
    print(f" -> Tổng số test cases: {len(test_cases)} câu hỏi.")

    # 3. Chạy từng test case
    print("\n[4/4] Bắt đầu thực thi vòng lặp đánh giá từng câu...")
    results = []
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_jsonl_path = os.path.join(logs_dir, f"run_{timestamp_str}.jsonl")

    total_no_answer = 0
    total_correct_refusal = 0
    total_grounding_cases = 0
    total_grounded = 0

    with open(log_jsonl_path, "w", encoding="utf-8") as log_file:
        for idx, tc in enumerate(test_cases, start=1):
            qid = tc.get("id")
            q_type = tc.get("type")
            question = tc.get("question")
            is_no_ans = tc.get("is_no_answer", False)
            expected_doc = tc.get("expected_doc")

            print(f"  [{idx:02d}/{len(test_cases):02d}] Đang xử lý {qid} ({q_type})...", end=" ", flush=True)

            start_t = time.time()
            agent_res = agent.run(question)
            duration = time.time() - start_t

            final_ans = agent_res.get("final_answer", "")
            usage = agent_res.get("usage", {})
            steps = agent_res.get("steps", [])

            # Đánh giá Calibration (Từ chối đúng / Thiếu dữ liệu)
            refusal_keywords = [
                "không tìm thấy", "không có thông tin", "ngoài phạm vi", "chưa đủ dữ liệu",
                "không nằm trong", "không được quy định", "không thể kết luận", "không thể trả lời",
                "từ chối", "no_answer", "thiếu dữ liệu", "chưa có quy định"
            ]
            is_refused = any(kw in final_ans.lower() for kw in refusal_keywords)
            should_refuse = is_no_ans or (q_type == "missing_data_refusal")
            correct_calibration = (should_refuse and is_refused) or (not should_refuse and not is_refused)

            if should_refuse:
                total_no_answer += 1
                if is_refused:
                    total_correct_refusal += 1

            # Đánh giá Grounding Doc ID
            grounded = False
            if expected_doc:
                total_grounding_cases += 1
                for doc in expected_doc.split(","):
                    if doc.strip() in final_ans or any(doc.strip() in str(s) for s in steps):
                        grounded = True
                        break
                if grounded:
                    total_grounded += 1

            print(f"XONG ({duration:.2f}s | {usage.get('total_tokens', 0)} tokens)")

            # Bản ghi log chuẩn theo yêu cầu giảng viên
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "test_id": qid,
                "type": q_type,
                "question": question,
                "is_no_answer": is_no_ans,
                "expected_doc": expected_doc,
                "final_answer": final_ans,
                "steps_trace": steps,
                "evaluation": {
                    "is_refused": is_refused,
                    "correct_calibration": correct_calibration,
                    "grounded_doc": grounded
                },
                "usage": {
                    "calls": usage.get("calls", 0),
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                    "max_prompt_tokens": usage.get("max_prompt_tokens", 0),
                    "latency_seconds": usage.get("latency_seconds", duration)
                }
            }
            log_file.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

            results.append({
                "id": qid,
                "type": q_type,
                "tokens": usage.get("total_tokens", 0),
                "steps": len(steps),
                "latency": round(duration, 2),
                "calibration": "PASS" if correct_calibration else "FAIL",
                "grounding": "PASS" if (grounded or not expected_doc) else "FAIL"
            })

    # Xuất file CSV thuần túy
    csv_path = os.path.join(logs_dir, "eval_results.csv")
    with open(csv_path, "w", encoding="utf-8-sig") as csv_f:
        csv_f.write("id,type,tokens,steps,latency,calibration,grounding\n")
        for r in results:
            csv_f.write(f"{r['id']},{r['type']},{r['tokens']},{r['steps']},{r['latency']},{r['calibration']},{r['grounding']}\n")

    # In bảng ra console thuần túy
    print("\n" + "=" * 75)
    print(f"{'ID':<6} | {'LOẠI CÂU HỎI':<22} | {'TOKENS':<8} | {'BƯỚC':<6} | {'THỜI GIAN':<10} | {'TỪ CHỐI ĐÚNG':<12}")
    print("-" * 75)
    for r in results:
        print(f"{r['id']:<6} | {r['type']:<22} | {r['tokens']:<8} | {r['steps']:<6} | {r['latency']:<10} | {r['calibration']:<12}")

    calib_rate = (total_correct_refusal / total_no_answer * 100) if total_no_answer > 0 else 100.0
    faith_rate = (total_grounded / total_grounding_cases * 100) if total_grounding_cases > 0 else 100.0

    print("\n" + "=" * 75)
    print(f" >> TỈ LỆ TỪ CHỐI ĐÚNG (Calibration Rate): {calib_rate:.1f}% ({total_correct_refusal}/{total_no_answer})")
    print(f" >> ĐỘ TRUNG THỰC TRÍCH DẪN (Faithfulness): {faith_rate:.1f}% ({total_grounded}/{total_grounding_cases})")
    print(f" >> Tệp log JSONL: {log_jsonl_path}")
    print(f" >> Tệp CSV tổng hợp: {csv_path}")
    print("=" * 75)

if __name__ == "__main__":
    run_evaluation()
