"""
VÒNG LẶP AGENT TỰ VIẾT (YÊU CẦU TUẦN W6)
Yêu cầu bắt buộc:
1. Vòng lặp ReAct do sinh viên tự viết tay (không dùng LangChain Agent hay CrewAI).
2. Dynamic tool discovery từ MCP Client.
3. Có MAX_STEPS chặn lặp vô tận.
4. Tool lỗi trả chuỗi "Error: ..." (không làm chết run).
5. BẮT BUỘC có cặp: write_tool() -> gọi lại verify_tool() ngay sau đó.
6. Ghi nhận và trả về USAGE tokens chi tiết (calls, prompt_tokens, completion_tokens).
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional
from ..schemas.rag_types import UsageMetric
from ..core.llm_client import LLMClient
from ..rag.hybrid_search import HybridSearchEngine
from .safe_parser import SafeActionParser
from .mcp_client import DynamicMCPClient

logger = logging.getLogger("AgentLoop")

class ScholarshipAgent:
    def __init__(
        self,
        hybrid_engine: HybridSearchEngine,
        mcp_client: DynamicMCPClient,
        llm_client: LLMClient,
        max_steps: int = 8,
        prompts_dir: Optional[str] = None
    ):
        self.hybrid_engine = hybrid_engine
        self.mcp_client = mcp_client
        self.llm_client = llm_client
        self.max_steps = max_steps

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.prompts_dir = prompts_dir or os.path.join(base_dir, "prompts")
        self.system_prompt = self._load_prompt("system_agent.txt")

    def _load_prompt(self, filename: str) -> str:
        filepath = os.path.join(self.prompts_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        return "Bạn là trợ lý xét học bổng thông minh."

    def run(self, user_query: str) -> Dict[str, Any]:
        """
        TODO (Thành viên phụ trách Agent Loop):
        1. Khám phá động tools từ MCP client (self.mcp_client.discover_tools()).
        2. Ghép system_prompt + tools_description + user_query vào prompt.
        3. Khởi tạo vòng lặp step = 1 đến self.max_steps:
           - Gọi self.llm_client.call(...) và ghi nhận token usage.
           - Parse Action và Action Input an toàn qua SafeActionParser.
           - Nếu có Final Answer -> ngắt vòng lặp.
           - Nếu gọi tool -> thực thi tool (rag_search hoặc mcp_client.call_tool).
           - BẮT BUỘC AUTO-VERIFY: Nếu vừa gọi submit_scholarship_nomination,
             ngay lập tức gọi tiếp verify_scholarship_nomination để kiểm chứng thay đổi.
           - Đưa Observation vào ngữ cảnh hội thoại.
        4. Trả về dict: {"query": ..., "final_answer": ..., "steps": ..., "usage": ...}
        """
        usage = UsageMetric()
        trace_steps: List[Dict[str, Any]] = []

        # TODO: Viết logic vòng lặp Agent ReAct tại đây

        return {
            "query": user_query,
            "final_answer": "TODO: Kết quả phản hồi của Agent",
            "steps": trace_steps,
            "total_steps": 1,
            "usage": {
                "calls": usage.calls,
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
                "max_prompt_tokens": usage.max_prompt_tokens,
                "latency_seconds": usage.latency_seconds
            }
        }
