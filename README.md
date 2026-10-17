# ENCOURAGEMENT SCHOLARSHIP ANALYST RAG & AGENT
> **Đồ án Cuối kỳ Môn học AIPR (Tuần W1 – W7)**  
> **Đề tài:** Hệ thống Trợ lý Phân tích và Thẩm định Học bổng Khuyến khích Học tập  
> **Kiến trúc:** RAG Đa chế độ (Dense + BM25 Hybrid Search + Metadata Filtering) + Agent Loop tự viết + MCP Server (Stdio) + Đo lường USAGE
---

## 1. Hướng Dẫn Chạy Nhanh (Dành cho Giảng Viên)
Hệ thống được thiết kế để chạy độc lập và tái lập kết quả dễ dàng bằng **Lệnh Python trực tiếp** (cho Windows/Linux/macOS) hoặc **Makefile**.

> **[LƯU Ý QUAN TRỌNG VỀ API KEY]**:  
> Hệ thống đã tích hợp sẵn cơ chế **Smart Offline Reasoner** (kích hoạt mặc định từ file `.env.example`).  
> Giảng viên **KHÔNG CẦN CUNG CẤP GEMINI API KEY** hoặc kết nối Internet vẫn có thể chạy và tái lập 100% toàn bộ các bài test, demo và benchmark!  
> *(Nếu muốn kiểm thử với mô hình Gemini thật qua mạng, chỉ cần điền `GEMINI_API_KEY` vào file `.env.example`)*.

---

### Cách 1: Chạy bằng lệnh Python trực tiếp (Khuyên dùng trên mọi hệ điều hành)

```bash
# Bước 1: Cài đặt thư viện và chuẩn bị file cấu hình
pip install -r requirements.txt
copy .env.example .env          # Trên Windows (Linux/macOS: cp .env.example .env)

# Bước 2: Chạy Demo trực tiếp 3 tầng (Tra cứu - Suy luận cận dưới - Đề cử & Verify)
python -m scripts.demo_runner

# Bước 3: Tái lập Bảng Đánh Giá Benchmark (14 câu testset, đo Calibration & Faithfulness)
python -m tests.run_eval

# Bước 4: So sánh cấu hình RAG: Dense vs BM25 vs Hybrid RRF (+1 Điểm cộng RAG)
python scripts/compare_rag_configs.py

# Bước 5: Chạy Client kiểm toán độc lập kiểm thử MCP Server (+1 Điểm cộng MCP)
python -m scripts.external_auditor_client

# Bước 6: Chạy toàn bộ 14 unit tests kiểm thử độc lập RAG Pipeline & MCP Server
python -m unittest discover tests/

# (Tùy chọn): Mở giao diện trò chuyện CLI tương tác tự do
python main.py
```

---

### Cách 2: Chạy thông qua Makefile (Nếu máy đã cài GNU Make)

```bash
make setup          # Cài đặt thư viện & tự copy .env
make demo           # Chạy live demo kịch bản 3 tầng
make eval           # Chạy benchmark 14 câu và vẽ đồ thị
make compare-rag    # Benchmark so sánh Dense vs BM25 vs Hybrid Search (+1đ RAG)
make audit          # Client thứ hai kiểm toán độc lập MCP Server (+1đ MCP)
make test           # Chạy toàn bộ 14 bài unit tests
```

---

## 2. Minh Chứng Đạt Chuẩn 3 Tầng

1. **Tầng (a) - Tra cứu (Grounding & Calibration):**
   - Trích dẫn chính xác `doc_id`, số hiệu điều khoản và phiên bản văn bản quy chế mới nhất (DOC0002, DOC0005, DOC0006).
   - Nhận diện chuẩn các câu hỏi ngoài phạm vi corpus (Vingroup, Nhật Bản, học kỳ hè...) để từ chối dứt khoát `no_answer`, loại bỏ hoàn toàn ảo giác.
2. **Tầng (b) - Biến đổi (Reasoning & Multi-doc):**
   - Phối hợp thông tin từ $\ge$ 2 tài liệu (Quy chế học bổng DOC0002, Đánh giá rèn luyện DOC0005, Kỷ luật DOC0003).
   - Suy luận và tính toán: Kiểm tra điều kiện tích lũy $\ge$ 15 tín chỉ, xác định khung học bổng theo nguyên tắc cận dưới giữa GPA và ĐRL.
   - Phân biệt rõ hai trường hợp: Từ chối do ngoài phạm vi quy chế (lỗi tầng a) vs Từ chối do thiếu dữ liệu sinh viên để suy luận (lỗi tầng b).
3. **Tầng (c) - Hành động (Side-effect + Verify bắt buộc):**
   - Tool ghi `submit_scholarship_nomination`: Ghi nhận đề xuất xét duyệt vào CSDL, thay đổi trạng thái hồ sơ sang `SUBMITTED`.
   - Tool đọc verify `verify_scholarship_nomination`: Gọi lại ngay sau tool ghi để xác nhận dữ liệu đã được lưu trữ thật và cập nhật sang trạng thái `VERIFIED`.

---

## 3. Cấu Trúc Dự Án

```text
├── data/
│   ├── corpus/            # Tài liệu quy chế có metadata (DOC0001 - DOC0006, HTRL.md)
│   └── database/          # CSDL sinh viên và đơn đề cử học bổng (JSON/SQLite)
├── prompts/               # Prompt templates tách biệt khỏi code (system_agent.txt)
├── logs/                  # Logs các lần chạy thật (.jsonl, .csv) kèm USAGE tokens
├── scripts/
│   ├── demo_runner.py              # Script chạy kịch bản live demo 3 tầng
│   ├── compare_rag_configs.py      # Benchmark so sánh các cấu hình RAG (+1đ RAG)
│   ├── external_auditor_client.py  # Client thứ hai kiểm toán MCP Server (+1đ MCP)
│   └── plot_metrics.py             # Vẽ đồ thị phân phối token và độ trễ
├── src/
│   ├── core/              # LLM client (Gemini, Local Ollama, Smart Offline Fallback)
│   ├── rag/               # Chunker điều khoản, BM25, Dense, Hybrid RRF, Metadata Filter
│   ├── agent/             # Agent loop (ReAct, Safe Action Parser, Dynamic MCP Client)
│   └── mcp_server/        # MCP server (Stdio, Dataclass contracts, 5 tools nghiệp vụ)
├── tests/
│   ├── testset.jsonl      # Testset chuẩn (14 câu hỏi, phân loại Grounding, Reasoning, No-answer)
│   ├── test_rag.py        # 6 unit tests kiểm thử RAG pipeline (Thành viên 1)
│   ├── test_mcp_server.py # 8 unit tests kiểm thử MCP Server & Client (Thành viên 2)
│   └── run_eval.py        # Benchmark pipeline đo Calibration Rate & Faithfulness
├── ai-usage.md            # Bảng minh bạch khai báo sử dụng AI theo quy định môn học
├── report.docx            # Báo cáo Word hoàn chỉnh 8-9 trang nộp đồ án
├── Makefile               # Điều khiển tự động hóa setup, demo, eval, test, audit
└── requirements.txt       # Danh sách thư viện phụ thuộc
```

---

## 4. Phân Công Thành Viên & Ma Trận Trách Nhiệm

1. **Thành viên 1: Nguyễn Huy Thái (MSSV: 24110056 - Khoa CNTT)**
   - **Chuyên trách:** RAG Pipeline, Chunker ngữ nghĩa, Tri thức Quy chế, Báo cáo Mục 3.
   - **Mã nguồn phụ trách:** `src/rag/chunker.py`, `src/rag/hybrid_search.py`, `src/rag/retriever_bm25.py`, `src/rag/retriever_dense.py`, `tests/test_rag.py`.
   - **Điểm cộng kỹ thuật (+1đ):** Xây dựng thực nghiệm benchmark so sánh cấu hình Dense (88.9%) vs BM25 (100%) vs Hybrid RRF (100%) tại `scripts/compare_rag_configs.py`.

2. **Thành viên 2: Võ Mạnh Đức Tín (MSSV: 24110137 - Khoa K24 FIE)**
   - **Chuyên trách:** Giao thức MCP Server, Tool Contracts, CSDL Tác vụ, Báo cáo Mục 5.
   - **Mã nguồn phụ trách:** `src/mcp_server/server.py`, `src/mcp_server/tools_contracts.py`, `data/database/`, `tests/test_mcp_server.py`.
   - **Điểm cộng kỹ thuật (+1đ):** Xây dựng Standalone MCP Server chuẩn giao thức Stdio (5 tools, stdout sạch) và Client thứ hai kiểm toán độc lập `scripts/external_auditor_client.py` minh chứng tính Interoperability.

3. **Thành viên 3: Nguyễn Minh Thành (MSSV: 24110088 - Khoa CNTT)**
   - **Chuyên trách:** Agent Core Loop, Safe Action Parser, Benchmark Evaluation, Báo cáo Mục 2, 4, 6.
   - **Mã nguồn phụ trách:** `src/agent/loop.py`, `src/agent/safe_parser.py`, `src/core/llm_client.py`, `tests/run_eval.py`, `main.py`.
   - **Hạng mục kỹ thuật:** Xây dựng vòng lặp ReAct độc lập không dùng thư viện đen, cơ chế kiểm soát MAX_STEPS, parser bóc tách Action chống crash JSON, testset 14 câu đo lường độ trung thực (Faithfulness) và hiệu chỉnh từ chối (Calibration Rate).
