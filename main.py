"""
GIAO DIỆN TƯƠNG TÁC TRÒ CHUYỆN VỚI TRỢ LÝ HỌC BỔNG (INTERACTIVE AGENT CLI)
Cho phép người dùng nhập câu hỏi tự do từ bàn phím, Agent sẽ tự động:
1. Nhận câu hỏi
2. Suy luận (Thought)
3. Tra cứu quy chế (rag_search) hoặc gọi MCP Tools (get_student, submit, verify)
4. Trả lời chi tiết và hiển thị vết thực thi (Trace)
"""
import sys
import os
import time

# Đảm bảo import được các module từ thư mục gốc
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from src.rag.chunker import DocumentChunker
from src.rag.hybrid_search import HybridSearchEngine
from src.agent.mcp_client import DynamicMCPClient
from src.core.llm_client import LLMClient
from src.agent.loop import ScholarshipAgent

def interactive_chat():
    print("=" * 75)
    print("   TRỢ LÝ PHÂN TÍCH VÀ THẨM ĐỊNH HỌC BỔNG KHUYẾN KHÍCH HỌC TẬP (CLI)")
    print("=" * 75)
    print("Đang khởi tạo hệ thống (Vui lòng đợi vài giây)...")

    corpus_dir = os.path.join(base_dir, "data", "corpus")
    server_path = os.path.join(base_dir, "src", "mcp_server", "server.py")

    try:
        chunker = DocumentChunker(corpus_dir)
        chunks = chunker.load_and_chunk_all()
        hybrid_engine = HybridSearchEngine(chunks)
        mcp_client = DynamicMCPClient(server_path)
        llm_client = LLMClient()
        agent = ScholarshipAgent(
            hybrid_engine=hybrid_engine,
            mcp_client=mcp_client,
            llm_client=llm_client,
            max_steps=8
        )
    except Exception as e:
        print(f"\n[LỖI KHỞI TẠO]: {e}")
        return

    DEMO_QUERIES = {
        "1": "So sánh quy định về số tín chỉ đăng ký tối thiểu trong học kỳ chính để được xét học bổng giữa quy chế năm 2023 và quy chế sửa đổi năm 2024?",
        "2": "Sinh viên có điểm trung bình GPA 3.75 và Điểm rèn luyện 82 điểm trong học kỳ thì được xếp loại học bổng nào theo quy chế 2024? Hãy giải thích rõ nguyên tắc xếp loại.",
        "3": "Hãy kiểm tra hồ sơ học tập của sinh viên Nguyễn Văn An (mã số 23110101). Nếu đủ điều kiện loại Xuất sắc, hãy thực hiện nộp đơn đề cử học bổng và xác minh mã đơn trên hệ thống."
    }

    streaming_enabled = True

    print("\n[OK] Hệ thống đã sẵn sàng!")
    print("Bạn có thể gõ câu hỏi tự do, HOẶC dùng các lệnh điều khiển tiện ích:")
    print("  👉 Gõ [1] hoặc [demo1]: Tra cứu & So sánh quy chế đa phiên bản (2023 vs 2024)")
    print("  👉 Gõ [2] hoặc [demo2]: Suy luận nguyên tắc cận dưới (GPA 3.75 & ĐRL 82)")
    print("  👉 Gõ [3] hoặc [demo3]: Thẩm định hồ sơ + Nộp đơn đề cử + Tự động xác minh")
    print("  👉 Gõ [stream on] hoặc [stream off]: Bật / Tắt hiệu ứng hiển thị chữ Streaming")
    print("  👉 Gõ 'exit', 'quit' hoặc 'q' để kết thúc trò chuyện.\n")
    print("-" * 75)

    while True:
        try:
            stream_status = "BẬT" if streaming_enabled else "TẮT"
            user_input = input(f"\n👤 BẠN [Stream: {stream_status}]: ").strip()
            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "q"]:
                print("\nCảm ơn bạn đã sử dụng Trợ lý Học bổng. Tạm biệt!\n")
                break

            # Lệnh Bật / Tắt chế độ Streaming
            if user_input.lower() in ["stream on", "streaming on", "stream:on"]:
                streaming_enabled = True
                print("⚡ [HỆ THỐNG]: Đã BẬT chế độ Streaming (Hiển thị từng từ trực quan)!")
                continue
            elif user_input.lower() in ["stream off", "streaming off", "stream:off"]:
                streaming_enabled = False
                print("⚡ [HỆ THỐNG]: Đã TẮT chế độ Streaming (In một lần toàn bộ văn bản)!")
                continue

            # Kiểm tra nếu người dùng dùng phím tắt chạy 3 trường hợp dựng sẵn
            clean_input = user_input.lower().replace("demo", "").strip()
            if clean_input in DEMO_QUERIES:
                user_input = DEMO_QUERIES[clean_input]
                print(f"👉 [ĐÃ CHỌN TRƯỜNG HỢP MẪU {clean_input}]: \"{user_input}\"")

            print("\n🤖 TRỢ LÝ ĐANG SUY NGHĨ VÀ XỬ LÝ...")
            start_t = time.time()
            result = agent.run(user_input)
            elapsed = time.time() - start_t

            # 1. Hiển thị vết hành động của Agent nếu có gọi tool
            steps = result.get("steps", [])
            has_action = any(s.get("action") for s in steps)
            if has_action:
                print("\n[VẾT THỰC THI / ACTIONS]:")
                for s in steps:
                    act = s.get("action")
                    if act:
                        args = s.get("action_args")
                        obs = s.get("observation", "")
                        obs_short = (obs[:100] + "...") if len(obs) > 100 else obs
                        print(f"  ⚡ Gọi Tool [{act}] | Tham số: {args}")
                        print(f"     -> Phản hồi: {obs_short}")

            # 2. Hiển thị câu trả lời cuối cùng (Hỗ trợ Streaming hoặc In thẳng)
            print("\n" + "=" * 35 + " PHẢN HỒI " + "=" * 35)
            final_text = result.get("final_answer", "").strip()
            if streaming_enabled:
                for char in final_text:
                    sys.stdout.write(char)
                    sys.stdout.flush()
                    time.sleep(0.005)
                print()
            else:
                print(final_text)
            print("=" * 80)

            # 3. Thống kê nhanh
            usage = result.get("usage", {})
            print(f"(Thời gian: {elapsed:.2f}s | Số bước: {result.get('total_steps')} | Tokens: {usage.get('total_tokens', 0):,})")

        except KeyboardInterrupt:
            print("\nĐã hủy lệnh. Tạm biệt!")
            break
        except Exception as e:
            print(f"\n[LỖI XỬ LÝ]: {e}")

if __name__ == "__main__":
    interactive_chat()
