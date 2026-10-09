# ENCOURAGEMENT SCHOLARSHIP ANALYST RAG & AGENT
> **Đồ án Cuối kỳ Môn học AIPR (Tuần W1 – W7)**  
> **Đề tài:** Hệ thống Trợ lý Phân tích và Thẩm định Học bổng Khuyến khích Học tập  
> **Kiến trúc:** RAG Đa chế độ (Dense + BM25) + Agent Loop tự viết + MCP Server (Stdio) + Đo lường USAGE  

---

## 1. Hướng Dẫn Chạy Nhanh (Dành cho Giảng Viên)

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
   - Trích dẫn rõ `doc_id`, phiên bản văn bản quy chế.
   - Biết từ chối khi câu hỏi ngoài corpus (`no_answer`), không bịa đặt.
2. **Tầng (b) - Biến đổi (Reasoning & Multi-doc):**
   - Tổng hợp $\ge 2$ tài liệu (Quy chế học bổng, Đào tạo tín chỉ, Phân bổ ngân sách khoa).
   - Suy luận tính toán: Kiểm tra điều kiện $\ge 15$ tín chỉ, áp dụng **Nguyên tắc cận dưới** khi GPA và ĐRL khác khung, từ chối khi thiếu dữ liệu.
3. **Tầng (c) - Hành động (Side-effect + Verify bắt buộc):**
   - Tool ghi `submit_scholarship_nomination` tạo thay đổi trạng thái thật vào CSDL.
   - Tool đọc `verify_scholarship_nomination` được gọi ngay sau đó để chứng minh trạng thái đã đổi thành `VERIFIED`.

---

## 3. Phân Công Thành Viên Trong Nhóm

- **Thành viên 1:** Phụ trách RAG (Chunking, BM25, Dense, Hybrid search, Metadata filter).
- **Thành viên 2:** Phụ trách MCP Server (Stdio, Tool khai báo, Side effect + Verify).
- **Thành viên 3:** Phụ trách Agent Loop (ReAct loop, Safe action parser, LLM Client, Evaluation).
