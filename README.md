# ENCOURAGEMENT SCHOLARSHIP ANALYST RAG & AGENT
> **Đồ án Cuối kỳ Môn học AIPR (Tuần W1 – W7)**  
> **Đề tài:** Hệ thống Trợ lý Phân tích và Thẩm định Học bổng Khuyến khích Học tập  
> **Kiến trúc:** RAG Đa chế độ (Dense + BM25) + Agent Loop tự viết + MCP Server (Stdio) + Đo lường USAGE  

---

## 1. Hướng Dẫn Chạy Nhanh (Dành cho Giảng Viên)
Hệ thống được thiết kế để chạy độc lập và tái lập kết quả dễ dàng bằng lệnh Makefile duy nhất trên môi trường Python 3.11+.
### Bước 1: Cài đặt môi trường
```bash
make setup
```

### Bước 2: Chạy Demo trực tiếp
```bash
make demo
```

### Bước 3: Tái lập Bảng Đánh Giá & Benchmark
```bash
make eval
```

---

## 2. Minh Chứng Đạt Chuẩn 3 Tầng

1. **Tầng (a) - Tra cứu (Grounding & Calibration):**
   - Trích dẫn chính xác `doc_id`, số hiệu điều khoản và phiên bản văn bản quy chế mới nhất.
   - Nhận diện chuẩn các câu hỏi ngoài phạm vi corpus để từ chối `no_answer`, tuyệt đối không bịa đặt.
2. **Tầng (b) - Biến đổi (Reasoning & Multi-doc):**
   - Phối hợp thông tin từ ≥2 tài liệu (Quy chế học bổng, Quy chế đào tạo tín chỉ, Quy định phân bổ ngân sách khoa).
   - Suy luận và tính toán: Kiểm tra điều kiện tích lũy ≥15 tín chỉ, xác định khung học bổng (Khá/Giỏi/Xuất sắc) theo nguyên tắc cận dưới giữa GPA và ĐRL.
   - Phân biệt rõ hai trường hợp từ chối: Từ chối do thiếu văn bản (lỗi tầng a) vs Từ chối do thiếu dữ liệu để suy luận (lỗi tầng b).
3. **Tầng (c) - Hành động (Side-effect + Verify bắt buộc):**
   - Tool ghi `submit_scholarship_nomination`: Ghi nhận đề xuất xét duyệt vào CSDL SQLite/File, thay đổi trạng thái hồ sơ sang PENDING.
   - Tool đọc verify `verify_scholarship_nomination`: Gọi lại ngay sau tool ghi để xác nhận dữ liệu đã được ghi nhận thật và cập nhật sang trạng thái VERIFIED.

---

## 3. Cấu Trúc Dự Án 

├── data/                  # Tài liệu quy chế có metadata (doc_id, version, owner)
├── prompts/               # Prompt templates tách biệt khỏi code (.txt)
├── logs/                  # Logs các lần chạy thật (.jsonl) kèm USAGE tokens
├── scripts/               # Scripts tiện ích & so sánh cấu hình
├── src/
│   ├── core/              # LLM client (retry, timeout, logging)
│   ├── rag/               # Chunker, Hybrid search (BM25 + Dense), Filter
│   ├── agent/             # Agent loop (ReAct, Safe Action Parser, Max steps)
│   └── mcp_server/        # MCP server (Stdio, Dataclass tools, Side-effect)
├── tests/
│   └── testset.jsonl      # Testset chuẩn (≥12 câu hỏi, ≥4 câu no_answer)
├── ai-usage.md            # Báo cáo minh bạch sử dụng AI theo quy định
├── Makefile               # Điều khiển setup, demo, eval
└── requirements.txt       # Danh sách thư viện phụ thuộc

## 4. Phân Công Thành Viên & Ma Trận Trách Nhiệm

1. **Thành viên 1:** Chuyên trách RAG Pipeline & Tri thức Quy chế.
   - Trách nhiệm code: src/rag/chunker.py, src/rag/hybrid_search.py, tiền xử lý dữ liệu trong data/.
   - Hạng mục kỹ thuật: Chiến lược chunking theo điều khoản, kết hợp BM25 + Dense Retrieval (alpha weighting), Metadata filtering theo phiên bản văn bản.
   - Báo cáo & Đánh giá: Phụ trách Mục 3 (Thiết kế RAG) trong báo cáo; Viết benchmark so sánh cấu hình (Dense vs Hybrid).
2. **Thành viên 2:** Chuyên trách Giao thức MCP & CSDL Tác vụ.
   - Trách nhiệm code: src/mcp_server/server.py, định nghĩa dataclass schemas cho tools, lưu trữ trạng thái hồ sơ.
   - Hạng mục kỹ thuật: Triển khai MCP Server chuẩn giao thức Stdio (stdout sạch), xây dựng cặp tool Side-effect + Verify bắt buộc.
   - Báo cáo & Đánh giá: Phụ trách Mục 5 (Thiết kế MCP Server) trong báo cáo; Xây dựng client phụ kiểm thử tính interop.
3. **Thành viên 3:** Chuyên trách Agent Loop, Core Client & Đánh giá Hệ thống.
   - Trách nhiệm code: src/core/llm_client.py, src/agent/loop.py.
   - Hạng mục kỹ thuật: Xây dựng vòng lặp ReAct độc lập (không dùng framework đen), cơ chế MAX_STEPS, Parser chống crash cú pháp, Dynamic Tool Discovery từ MCP.
   - Báo cáo & Đánh giá: Xây dựng tests/testset.jsonl, viết pipeline make eval ghi nhận USAGE tokens; Phụ trách Mục 2, 4, 6 trong báo cáo.
