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
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
        self.timeout = timeout
        self.max_retries = max_retries

        # CẤU HÌNH LOCAL LLM (OLLAMA / GPU):
        # Mặc định dùng 'gemini'. Khi muốn chuyển sang chạy mô hình nội bộ,
        # đổi trong .env: LLM_PROVIDER=local
        self.provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        self.local_url = os.getenv("LOCAL_LLM_URL", "http://localhost:11434/v1/chat/completions")
        self.local_model = os.getenv("LOCAL_MODEL_NAME", "qwen2.5:7b")

        self._init_client()

    def _init_client(self):
        self._client = None
        if self.provider == "gemini" and self.api_key and self.api_key != "your_gemini_api_key_here":
            try:
                from google import genai
                self._client = genai.Client(api_key = self.api_key)
                logger.info("Đã khởi tạo Gemini Client thành công.")
            except Exception as e:
                logger.warning(f"Lỗi khi nạp google.genai: {e}. Sẽ dùng fallback offline.")

    def call(self, prompt: str, temperature: float = 0.2) -> Tuple[str, int, int, float]:
        start_time = time.time()

        # =====================================================================
        # NHÁNH GỌI LOCAL LLM (OLLAMA)
        # =====================================================================
        if self.provider == "local":
            import httpx
            payload = {
                "model": self.local_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "stream": False
            }
            try:
                with httpx.Client(timeout=self.timeout) as http_client:
                    res = http_client.post(self.local_url, json=payload)
                    res.raise_for_status()
                    data = res.json()
                    text = data["choices"][0]["message"]["content"]
                    usage = data.get("usage", {})
                    p_tok = usage.get("prompt_tokens", len(prompt) // 4)
                    c_tok = usage.get("completion_tokens", len(text) // 4)
                    latency = time.time() - start_time
                    return text, p_tok, c_tok, latency
            except Exception as e:
                logger.error(f"[Local LLM Error] Không thể kết nối tới Ollama ({self.local_url}): {e}")
                latency = time.time() - start_time
                return f"Error: Local LLM failed ({e})", len(prompt) // 4, 10, latency

        # =====================================================================
        # NHÁNH FALLBACK OFFLINE THÔNG MINH (KHI CHƯA CÓ KEY)
        # =====================================================================
        if not self._client:
            from .mock_agent_reasoner import generate_smart_mock_response
            latency = time.time() - start_time
            mock_text = generate_smart_mock_response(prompt)
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
                err_str = str(e)
                wait_time = (2 ** attempt) * 1.0
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    import re
                    # Bắt số giây Google yêu cầu đợi (ví dụ: 'retryDelay': '28s' hoặc 'Please retry in 28.5s')
                    match = re.search(r"retry in (\d+(?:\.\d+)?)s", err_str) or re.search(r"'retryDelay':\s*'(\d+)s'", err_str)
                    if match:
                        wait_time = float(match.group(1)) + 1.0  # Đợi đúng số giây Google yêu cầu + 1s an toàn
                    else:
                        wait_time = 15.0

                logger.error(f"[HTTP/API Error] Lần thử {attempt}/{self.max_retries} thất bại: {e}. Đang đợi {wait_time:.1f}s...")
                time.sleep(wait_time)
        # Nếu thử hết số lần mà vẫn lỗi -> raise hoặc trả về fallback kèm log critical
        logger.critical(f"Tất cả {self.max_retries} lần gọi LLM đều thất bại! Lỗi cuối: {last_error}")
        latency = time.time() - start_time
        return f"Error: Không thể kết nối LLM ({last_error})", len(prompt) // 4, 10, latency