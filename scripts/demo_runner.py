"""
Hệ thống demo trực quan 3 kịch bản đại diện:
- Kịch bản 1 (Tầng tra cứu - Multi-doc): So sánh quy định tín chỉ giữa Quy chế 2023 (DOC0001) và 2024 (DOC0002).
- Kịch bản 2 (Tầng suy luận - Reasoning Floor): Thẩm định sinh viên có GPA Xuất sắc nhưng ĐRL loại Giỏi.
- Kịch bản 3 (Tầng hành động - Action & Auto Verify): Thẩm định hồ sơ sinh viên -> Nộp đơn đề cử -> Tự động xác minh.
"""
import sys
import os
import time

# Đảm bảo import được các module từ thư mục gốc
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from src.rag.chunker import DocumentChunker
from src.rag.hybrid_search import HybridSearchEngine
from src.agent.mcp_client import DynamicMCPClient
from src.core.llm_client import LLMClient
from src.agent.loop import ScholarshipAgent

DEMO_SCENARIOS = [
    {
        "title": "KỊCH BẢN 1: TRA CỨU & SO SÁNH QUY CHẾ ĐA PHIÊN BẢN (MULTI-DOC REASONING)",
        "description": "Yêu cầu Agent đối chiếu quy định giữa Quy chế cũ 2023 (DOC0001) và Quy chế sửa đổi 2024 (DOC0002).",
        "query": "So sánh quy định về số tín chỉ đăng ký tối thiểu trong học kỳ chính để được xét học bổng giữa quy chế năm 2023 và quy chế sửa đổi năm 2024?"
    },
    {
        "title": "KỊCH BẢN 2: SUY LUẬN THEO NGUYÊN TẮC CẬN DƯỚI (REASONING FLOOR)",
        "description": "Sinh viên có GPA đạt mức Xuất sắc (3.75) nhưng Điểm rèn luyện chỉ đạt mức Giỏi (82).",
        "query": "Sinh viên có điểm trung bình GPA 3.75 và Điểm rèn luyện 82 điểm trong học kỳ thì được xếp loại học bổng nào theo quy chế 2024? Hãy giải thích rõ nguyên tắc xếp loại."
    },
    {
        "title": "KỊCH BẢN 3: THỰC THI HÀNH ĐỘNG GHI & TỰ ĐỘNG XÁC MINH (SIDE EFFECT & AUTO-VERIFY)",
        "description": "Agent tra cứu thông tin sinh viên, kiểm tra điều kiện, tự động gọi MCP Tool ghi đơn đề cử và xác minh mã đơn.",
        "query": "Hãy kiểm tra hồ sơ học tập của sinh viên Nguyễn Văn An (mã số SV2024001). Nếu đủ điều kiện loại Xuất sắc, hãy thực hiện nộp đơn đề cử học bổng và xác minh mã đơn trên hệ thống."
    }
]

def run_live_demo():
    print("=" * 80)
    print("    LIVE DEMO: HỆ THỐNG TRỢ LÝ XÉT HỌC BỔNG KHUYẾN KHÍCH HỌC TẬP")
    print("    ĐỒ ÁN TỐT NGHIỆP / BẢO VỆ FINAL PROJECT (AIPR W1-W7)")
    print("=" * 80)

    corpus_dir = os.path.join(base_dir, "data", "corpus")
    server_path = os.path.join(base_dir, "src", "mcp_server", "server.py")

    print("\n[+] Đang khởi tạo hệ thống RAG & MCP Agent...")
    chunker = DocumentChunker(corpus_dir)
    chunks = chunker.load_and_chunk_all()
    hybrid_engine = HybridSearchEngine(chunks)
    mcp_client = DynamicMCPClient(server_path)
    llm_client = LLMClient()
    agent = ScholarshipAgent(
        hybrid_engine=hybrid_engine,
        mcp_client=mcp_client,
        llm_client=llm_client,
        max_steps=6
    )
    print("[+] Hệ thống đã sẵn sàng cho buổi trình diễn!\n")

    for idx, sc in enumerate(DEMO_SCENARIOS, 1):
        print("\n" + "#" * 80)
        print(f"[{idx}/3] {sc['title']}")
        print(f"Mô tả: {sc['description']}")
        print(f"Câu hỏi: \"{sc['query']}\"")
        print("#" * 80)

        start_time = time.time()
        result = agent.run(sc["query"])
        elapsed = time.time() - start_time

        print("\n--- [VẾT THỰC THI CỦA AGENT (REASONING & TOOL TRACE)] ---")
        for step in result.get("steps", []):
            s_num = step.get("step")
            action = step.get("action")
            action_args = step.get("action_args")
            obs = step.get("observation", "")
            obs_preview = obs[:120] + "..." if len(obs) > 120 else obs

            if action:
                print(f"  * Bước {s_num} -> Gọi Tool: [{action}] với args: {action_args}")
                print(f"               Kết quả: {obs_preview}")
            else:
                print(f"  * Bước {s_num} -> Suy nghĩ / Kết luận")

        print("\n--- [CÂU TRẢ LỜI CUỐI CÙNG (FINAL ANSWER)] ---")
        print(result.get("final_answer", "").strip())

        usage = result.get("usage", {})
        print("\n--- [THỐNG KÊ CHI PHÍ & THỜI GIAN] ---")
        print(f"  * Số bước ReAct:   {result.get('total_steps')} bước")
        print(f"  * Tổng số Token:   {usage.get('total_tokens', 0):,} tokens")
        print(f"  * Thời gian xử lý: {elapsed:.2f} giây")
        print("-" * 80)

        if idx < len(DEMO_SCENARIOS):
            input("\n>> Nhấn [ENTER] để chuyển sang kịch bản demo tiếp theo...")

    print("\n" + "=" * 80)
    print("   BUỔI DEMO HOÀN TẤT THÀNH CÔNG RỰC RỠ!")
    print("=" * 80)

if __name__ == "__main__":
    run_live_demo()
