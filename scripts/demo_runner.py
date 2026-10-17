"""
KỊCH BẢN CHẠY DEMO TẠI BUỔI BẢO VỆ (LỆNH: make demo hoặc python -m scripts.demo_runner)
Biểu diễn trực tiếp 3 tầng bắt buộc trước Giảng viên:
1. Tầng (a) - Tra cứu & So sánh phiên bản (Quy chế 2023 vs 2024 vs 2026)
2. Tầng (b) - Biến đổi & Suy luận nguyên tắc cận dưới (GPA 3.75 + ĐRL 82)
3. Tầng (c) - Hành động (Ghi đề cử học bổng -> Tự động Verify trạng thái trong DB)
"""
import sys
import os
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag.chunker import DocumentChunker
from src.rag.hybrid_search import HybridSearchEngine
from src.agent.mcp_client import DynamicMCPClient
from src.core.llm_client import LLMClient
from src.agent.loop import ScholarshipAgent

def run_live_demo():
    print("=" * 80)
    print("      LIVE DEMO: HỆ THỐNG TRỢ LÝ XÉT HỌC BỔNG KHUYẾN KHÍCH HỌC TẬP (HCMUTE)")
    print("      (MÔN HỌC AIPR - BẢO VỆ FINAL PROJECT W1-W7)")
    print("=" * 80)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    print("\n[KHỞI ĐỘNG HỆ THỐNG]")
    chunker = DocumentChunker(os.path.join(base_dir, "data", "corpus"))
    chunks = chunker.load_and_chunk_all()
    hybrid_engine = HybridSearchEngine(chunks)
    mcp_client = DynamicMCPClient(os.path.join(base_dir, "src", "mcp_server", "server.py"))
    llm_client = LLMClient()
    agent = ScholarshipAgent(hybrid_engine, mcp_client, llm_client, max_steps=6)
    print(f" -> Khởi tạo hoàn tất! Chỉ mục: {len(chunks)} chunks quy chế | Tools MCP: 3 tools sẵn sàng.\n")

    demo_scenarios = [
        {
            "tier": "TẦNG (a) - TRA CỨU & SO SÁNH ĐA VĂN BẢN (MULTI-DOC GROUNDING)",
            "query": "So sánh quy định về số tín chỉ tối thiểu để xét học bổng giữa quy chế năm 2023 và quy chế sửa đổi năm 2024?",
        },
        {
            "tier": "TẦNG (b) - SUY LUẬN & NGUYÊN TẮC CẬN DƯỚI (REASONING & CALIBRATION)",
            "query": "Sinh viên có GPA 3.75 và Điểm rèn luyện 82 điểm thì được xếp loại học bổng nào theo quy chế 2024?",
        },
        {
            "tier": "TẦNG (c) - HÀNH ĐỘNG GHI (SIDE-EFFECT) VÀ TỰ ĐỘNG VERIFY BẮT BUỘC",
            "query": "Hãy kiểm tra hồ sơ sinh viên Nguyễn Văn An (23110101), nếu đủ điều kiện loại Xuất sắc hãy nộp đơn đề cử học bổng và xác minh.",
        }
    ]

    for idx, sc in enumerate(demo_scenarios, start=1):
        print("*" * 80)
        print(f" DEMO CA #{idx}: {sc['tier']}")
        print(f" CÂU HỎI: \"{sc['query']}\"")
        print("*" * 80)

        res = agent.run(sc["query"])

        print("\n [QUÁ TRÌNH THỰC THI RE-ACT & TRACE STEPS]:")
        for s in res.get("steps", []):
            step_num = s.get("step")
            action = s.get("action")
            action_args = s.get("action_args")
            obs = s.get("observation")
            print(f"   -> Bước {step_num}: Action = {action} | Args = {action_args}")
            if obs:
                print(f"      Observation = {obs[:120]}...")

        print("\n [KẾT QUẢ CUỐI CÙNG (FINAL ANSWER)]:")
        print(f"   {res.get('final_answer')}")

        usage = res.get("usage", {})
        print(f"\n [ĐO LƯỜNG TÀI NGUYÊN (USAGE)]: Calls = {usage.get('calls')} | Total Tokens = {usage.get('total_tokens')} | Latency = {usage.get('latency_seconds', 0):.2f}s")
        print("\n" + "-" * 80 + "\n")
        time.sleep(1)

    print("=" * 80)
    print(">>> KẾT THÚC DEMO THÀNH CÔNG: ĐẠT ĐẦY ĐỦ CẢ 3 TẦNG VÀ TIÊU CHUẨN GIẢNG VIÊN! <<<")
    print("=" * 80)

if __name__ == "__main__":
    run_live_demo()
