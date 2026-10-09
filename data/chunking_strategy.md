# Chiến Lược Chunking (Chunking Strategy)

### 1. Kích thước và Độ chồng lấn (Chunk Size & Overlap)
- **Kích thước chunk (Chunk Size):** 350 - 450 tokens (tương đương khoảng 150 - 250 từ tiếng Việt).
- **Độ chồng lấn (Chunk Overlap):** 50 tokens nhằm bảo tồn ngữ cảnh liền mạch giữa các điều khoản liền kề.

### 2. Lý do lựa chọn (Rationales - 4 dòng)
1. **Bảo toàn tính toàn vẹn của điều khoản pháp lý:** Mỗi chunk được tách theo ranh giới đoạn/Điều (Điều 1, Điều 2...) để một điều kiện tiên quyết (ví dụ số tín chỉ tối thiểu) không bị cắt đôi sang hai chunk khác nhau.
2. **Gắn chặt Metadata vào từng Chunk:** Mỗi chunk đều được tiền tố hóa với metadata (`doc_id`, `title`, `version`, `status`) giúp mô hình embedding và BM25 phân biệt chính xác phiên bản có hiệu lực (2024 vs 2023).
3. **Phù hợp kích thước ngữ cảnh suy luận (Context Budget):** Kích thước 400 tokens đủ ngắn để tăng độ chính xác tìm kiếm (Retrieval Precision), đồng thời đủ dài để chứa toàn bộ một bảng khung phân loại (GPA + ĐRL).
4. **Hỗ trợ đa tài liệu (Multi-document fusion):** Khi retrieve Top-K (K=3), tổng context đưa vào LLM chỉ khoảng 1200 tokens, đảm bảo tốc độ phản hồi nhanh, tiết kiệm chi phí token và tránh hiện tượng "lost in the middle".
