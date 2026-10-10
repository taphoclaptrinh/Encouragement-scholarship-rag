"""
MODULE GỌI API LLM (YÊU CẦU TUẦN W2)
Yêu cầu:
- Tách prompt khỏi code (đọc template từ thư mục prompts/)
- Triển khai hàm call_llm có cơ chế Retry (với Exponential Backoff) khi gặp lỗi mạng
- Có Timeout và ghi nhận Log lỗi HTTP / API
- Đo lường và trả về số token (prompt_tokens, completion_tokens) và độ trễ (latency_seconds)
"""
import os
import time
import logging
from typing import Tuple, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("LLMClient")

class LLMClient:
    def __init__(self, model_name: Optional[str] = None, timeout: float = 30.0, max_retries: int = 3):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.timeout = timeout
        self.max_retries = max_retries
        self._init_client()

    def _init_client(self):
        self._client = None
        if self.api_key and self.api_key != "your_gemini_api_key_here":
            try:
                from google import genai
                self._client = genai.Client(api_key = self.api_key)
                logger.info("Đã khởi tạo Gemini Client thành công.")
            except Exception as e:
                logger.warning(f"Lỗi khi nạp google.genai: {e}. Sẽ dùng fallback offline.")

    def call(self, prompt: str, temperature: float = 0.2) -> Tuple[str, int, int, float]:
        start_time = None

        if not self._client:
            latency = time.time() - start_time
            mock_text = "[OFFLINE] Phản hồi thử nghiệm từ hệ thống."
            return mock_text, len(prompt) // 4, len(mock_text) // 4, latency
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                # Gọi API thông qua models.generate_content
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config={
                        "temperature": temperature,
                    }
                )
                latency = time.time() - start_time
                # Thu thập token usage từ response.usage_metadata
                prompt_tokens = 0
                completion_tokens = 0
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
                    completion_tokens = getattr(response.usage_metadata, "candidates_token_count", 0) or 0

                if prompt_tokens == 0:
                    prompt_tokens = max(1, len(prompt) // 4)
                if completion_tokens == 0:
                    completion_tokens = max(1, len(response.text or "") // 4)
                return response.text or "", prompt_tokens, completion_tokens, latency
            except Exception as e:
                last_error = e
                #Cong thuc : wait_time = 2^attempt * 0.5
                wait_time = (2 ** attempt) * 0.5
                logger.error(f"[HTTP/API Error] Lần thử {attempt}/{self.max_retries} thất bại: {e}. Đang đợi {wait_time}s...")
                time.sleep(wait_time)
        # Nếu thử hết số lần mà vẫn lỗi -> raise hoặc trả về fallback kèm log critical
        logger.critical(f"Tất cả {self.max_retries} lần gọi LLM đều thất bại! Lỗi cuối: {last_error}")
        latency = time.time() - start_time
        return f"Error: Không thể kết nối LLM ({last_error})", len(prompt) // 4, 10, latency