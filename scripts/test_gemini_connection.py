"""
Script kiểm tra kết nối và tính sẵn sàng của Gemini API Key và các Models đã cấu hình.
Chạy lệnh: python scripts/test_gemini_connection.py
"""
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY", "")
text_model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
embed_model = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")

print("=" * 60)
print("   KIỂM TRA KẾT NỐI GOOGLE GEMINI API")
print("=" * 60)

if not api_key or api_key == "your_gemini_api_key_here":
    print("[ERROR] Chưa cấu hình GEMINI_API_KEY trong file .env!")
    exit(1)

print(f"API Key: {api_key[:6]}...{api_key[-4:] if len(api_key) > 10 else ''}")
print(f"Text Model: {text_model}")
print(f"Embedding Model: {embed_model}\n")

client = genai.Client(api_key=api_key)

# 1. Test Text Generation
try:
    print(f"[1/2] Đang kiểm tra Text Model '{text_model}'...")
    res = client.models.generate_content(
        model=text_model,
        contents="Xin chào, đây là bài kiểm tra kết nối API hệ thống RAG xét học bổng."
    )
    print(f"  -> [SUCCESS] Phản hồi: {res.text.strip()[:60]}...")
except Exception as e:
    print(f"  -> [FAILED] Lỗi gọi model '{text_model}': {e}")

# 2. Test Embedding
try:
    print(f"\n[2/2] Đang kiểm tra Embedding Model '{embed_model}'...")
    emb_res = client.models.embed_content(
        model=embed_model,
        contents="Quy chế học bổng khuyến khích học tập năm 2024"
    )
    values = emb_res.embeddings[0].values
    print(f"  -> [SUCCESS] Tạo vector thành công! Chiều vector: {len(values)}")
except Exception as e:
    print(f"  -> [FAILED] Lỗi tạo vector với '{embed_model}': {e}")

print("=" * 60)
print("KIỂM TRA HOÀN TẤT!")
print("=" * 60)
