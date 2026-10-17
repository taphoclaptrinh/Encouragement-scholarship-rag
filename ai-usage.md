# BẢNG KHAI BÁO SỬ DỤNG CÔNG CỤ TRÍ TUỆ NHÂN TẠO (AI-USAGE DECLARATION)
*Môn học: Trí tuệ nhân tạo và Ứng dụng (AIPR) - Final Project*  
*Đề tài: Hệ thống Trợ lý Phân tích và Thẩm định Học bổng Khuyến khích Học tập*  
*Nhóm thực hiện: Nhóm 3 sinh viên - Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCMUTE)*

---

## 1. NGUYÊN TẮC LIÊM CHÍNH HỌC THUẬT VÀ PHẠM VI ỨNG DỤNG AI
Nhóm cam kết tuân thủ nghiêm ngặt quy định tại Mục 6 và Mục 7 của Đề cương đồ án:
- Toàn bộ sinh viên trong nhóm nắm vững, giải thích được từng dòng lệnh trong mã nguồn thuộc phần mình phụ trách và sẵn sàng thao tác sửa đổi trực tiếp khi giảng viên yêu cầu tại buổi vấn đáp bảo vệ.
- Các mô hình AI chỉ đóng vai trò trợ lý hỗ trợ (Copilot): rà soát cú pháp thư viện mới (MCP SDK 2.x), định dạng cấu trúc báo cáo Word và sinh dữ liệu giả lập (synthetic data) phục vụ kiểm thử. Toàn bộ logic nghiệp vụ, quy tắc suy luận pháp lý, thiết kế kiến trúc phân tầng do các thành viên tự chủ thực hiện.

---

## 2. BẢNG KHAI BÁO CHI TIẾT THEO TỪNG CẤU PHẦN

| STT | Cấu phần / Hạng mục | Công cụ AI sử dụng | Nhiệm vụ & Prompt chính | Mức độ AI sinh vs Sinh viên tự viết | Sinh viên phụ trách |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **1** | **Khởi tạo Tool Contracts & Dataclass Schema (W1)** | Antigravity AI / Claude 3.5 Sonnet | *"Tạo cấu trúc dataclass Python chuẩn có type hints cho kết quả tra cứu sinh viên, ngân sách khoa, hồ sơ đề cử học bổng và kết quả trả về của tool."* | - **AI sinh**: Khung dataclass cú pháp chuẩn.<br>- **SV tự viết**: Quy tắc định danh ID, ràng buộc trạng thái `SUBMITTED`/`VERIFIED`/`CANCELLED`, kiểm tra schema. | Thành viên 2 (Võ Mạnh Đức Tín - `@Bevil0301`) |
| **2** | **LLM Client & Retry Mechanism (W2)** | Antigravity AI / Google GenAI SDK | *"Sinh code mẫu kết nối Google GenAI SDK (gemini-3.5-flash-lite) và khung hàm Retry Exponential Backoff."* | - **AI sinh**: Cú pháp khởi tạo `genai.Client`, hàm `models.generate_content`, bóc tách `usage_metadata` và khung vòng lặp retry.<br>- **SV đọc hiểu & kiểm thử**: Rà soát mã nguồn, kiểm thử bắt mã lỗi 429 RESOURCE_EXHAUSTED thực tế, căn chỉnh thời gian `wait_time = 2^attempt * 0.5`, đo lường độ trễ và tích hợp vào hệ thống chung. | Thành viên 3 (Nguyễn Minh Thành - `@taphoclaptrinh`) |
| **3** | **Chunking & Hybrid Search RRF + So sánh cấu hình (W3-W4)** | ChatGPT / Gemini 1.5 Pro | *"Cách kết hợp BM25Okapi và Dense Vector theo công thức Reciprocal Rank Fusion (RRF) k=60 và viết script so sánh cấu hình."* | - **AI sinh**: Công thức toán học RRF mẫu.<br>- **SV tự viết**: Chunker tách theo regex điều khoản (`Điều \d+`), trích xuất metadata header, bộ lọc metadata filter, tích hợp quy định thật HTRL.md và DOC0006, script so sánh cấu hình `compare_rag_configs.py`. | Thành viên 1 (Nguyễn Huy Thái - `@Sthboring`) |
| **4** | **Agent Loop & Safe Parser (W6)** | Antigravity AI | *"Viết parser regex để bóc tách Action và Action Input an toàn khi LLM sinh thiếu dấu ngoặc JSON."* | - **AI sinh**: Biểu thức regex fallback.<br>- **SV tự viết**: Vòng lặp ReAct tự viết tay, chặn đệ quy `MAX_STEPS = 6`, cơ chế bắt lỗi trả về chuỗi `"Error: ..."` không crash run. | Thành viên 3 (Nguyễn Minh Thành - `@taphoclaptrinh`) |
| **5** | **MCP Server (Stdio) & External Auditor Client (W7)** | Antigravity AI | *"Viết script Client Python độc lập kết nối stdio đến MCP server cung cấp 5 tools để gọi danh sách tools và test tính tương thích."* | - **AI sinh**: Boilerplate asyncio subprocess giao tiếp qua stdin/stdout.<br>- **SV tự viết**: Cơ chế cô lập `stdout` (chuyển toàn bộ log sang `stderr`), 5 tools nghiệp vụ (2 đọc, 2 ghi, 1 verify), backward compatibility MCP 1.x & 2.x. | Thành viên 2 (Võ Mạnh Đức Tín - `@Bevil0301`) |
| **6** | **Cơ sở dữ liệu giả lập (Synthetic Data)** | Antigravity AI | *"Sinh 10 bản ghi hồ sơ sinh viên JSON bao gồm các ca kiểm thử biên: cận dưới, thiếu ĐRL, nợ tín chỉ, kỷ luật."* | - **AI sinh**: Dữ liệu họ tên mẫu.<br>- **SV tự viết**: Ma trận điểm số, MSSV chuẩn HCMUTE, logic giá trị null để kiểm thử từ chối do thiếu dữ liệu. | Thành viên 2 (Võ Mạnh Đức Tín - `@Bevil0301`) |
| **7** | **Benchmark Script & Đồ thị thực nghiệm (W6-W7)** | Antigravity AI | *"Tạo script chạy 14 câu testset, đo latency, log token USAGE ra file CSV và vẽ biểu đồ phân phối tokens."* | - **AI sinh**: Cú pháp matplotlib vẽ bar chart.<br>- **SV tự viết**: 14 câu hỏi testset, tiêu chuẩn đo lường Calibration Rate, Faithfulness, cơ chế log `.jsonl`. | Thành viên 3 (Nguyễn Minh Thành - `@taphoclaptrinh`) |

---

## 3. CÁC PROMPT CHÍNH ĐÃ SỬ DỤNG
1. **Prompt thiết kế MCP Server Stdio (W7)**:
   > *"Tôi cần xây dựng một MCP Server bằng Python chạy qua Stdio tuân thủ giao thức Model Context Protocol. Server cung cấp 5 tools: tra cứu học bạ, tra cứu ngân sách học bổng khoa, tạo đề cử học bổng, hủy đề cử và xác minh đề cử. Yêu cầu tuyệt đối không in log ra stdout để tránh làm lỗi khung JSON-RPC. Hãy hướng dẫn cách cấu hình logging an toàn qua stderr."*
2. **Prompt tối ưu Safe Action Parser (W6)**:
   > *"Viết hàm parse bằng Python nhận vào phản hồi dạng văn bản thô của mô hình ngôn ngữ (theo khuôn mẫu ReAct: Thought, Action, Action Input). Cần đảm bảo nếu LLM trả về JSON khuyết thiếu dấu đóng mở ngoặc hoặc lẫn text thừa thì parser vẫn bóc tách được đúng tên tool và dictionary tham số mà không raise JSONDecodeError."*
3. **Prompt thiết kế RRF Search & So sánh cấu hình (W3-W4)**:
   > *"Cung cấp đoạn mã kết hợp kết quả xếp hạng từ thuật toán từ khóa BM25Okapi và vector similarity theo thuật toán Reciprocal Rank Fusion với hệ số rank constant k = 60 và trọng số alpha = 0.5, kèm theo script benchmark so sánh Hit Rate giữa Dense-only, BM25-only và Hybrid Search."*
4. **Prompt tối ưu Closed-Domain Guardrails & Few-Shot Calibration (W5)**:
   > *"Hướng dẫn thiết lập Guardrail phạm vi đóng và các ví dụ mẫu Few-Shot trong system prompt để Agent nhận biết các câu hỏi ngoài phạm vi corpus (như học bổng Vingroup, du học Tokyo, dự kiến năm tương lai) và xuất Final Answer từ chối theo quy định, loại bỏ hoàn toàn hiện tượng ảo giác (hallucination)."*
5. **Prompt xây dựng LLM Client & Cơ chế Exponential Backoff (W2)**:
   > *"Xây dựng LLM Client bằng Python sử dụng Google GenAI SDK (google-genai). Yêu cầu tích hợp cơ chế Exponential Backoff với công thức wait_time = 2^attempt * 0.5 để bắt lỗi HTTP 429 RESOURCE_EXHAUSTED và trích xuất token usage từ response.usage_metadata."*

---

## 4. CAM KẾT CỦA CÁC THÀNH VIÊN
- Thành viên 1: **Nguyễn Huy Thái** (MSSV: 24110133 - GitHub: `@Sthboring` - Khoa FIE) - Cam kết nắm vững toàn bộ pipeline RAG, Chunker ngữ nghĩa, Hybrid Search RRF và Benchmark so sánh cấu hình.
- Thành viên 2: **Võ Mạnh Đức Tín** (MSSV: 24110137 - GitHub: `@Bevil0301` - Khoa FIE) - Cam kết nắm vững kiến trúc MCP Server Stdio (5 tools), Dataclass Contracts, CSDL SQLite/JSON và Client kiểm toán độc lập.
- Thành viên 3: **Nguyễn Minh Thành** (MSSV: 24110132 - GitHub: `@taphoclaptrinh` - Khoa FIE) - Cam kết nắm vững LLM Client (Retry/Backoff), Agent Loop ReAct, Safe Action Parser, Evaluation Metrics và Benchmark testset 14 câu.
