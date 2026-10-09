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
        """
        TODO (Thành viên phụ trách W2):
        Khởi tạo client Gemini API (hoặc OpenAI/tương đương).
        Gợi ý:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        """
        pass

    def call(self, prompt: str, temperature: float = 0.2) -> Tuple[str, int, int, float]:
        """
        Gọi LLM API với cơ chế retry và tính thời gian.
        Trả về: (response_text, prompt_tokens, completion_tokens, latency_seconds)

        TODO (Thành viên phụ trách W2):
        1. Tạo vòng lặp retry từ 1 đến self.max_retries.
        2. Gọi self._client.models.generate_content(...).
        3. Bắt lỗi HTTP/Exception: time.sleep((2 ** attempt) * 0.5) và ghi logger.error.
        4. Trích xuất prompt_token_count và candidates_token_count từ usage_metadata.
        5. Tính độ trễ: latency = time.time() - start_time.
        """
        start_time = time.time()

        # TODO: Thay thế đoạn code giữ chỗ này bằng logic gọi API thật của nhóm:
        response_text = "TODO: Triển khai gọi LLM API tại đây."
        latency = time.time() - start_time
        prompt_tokens = max(1, len(prompt) // 4)
        completion_tokens = max(1, len(response_text) // 4)

        return response_text, prompt_tokens, completion_tokens, latency
