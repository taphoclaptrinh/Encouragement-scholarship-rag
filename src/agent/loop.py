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
        Thực thi vòng lặp ReAct giải quyết yêu cầu của người dùng.
        Trả về kết quả gồm: query, final_answer, steps trace và usage metrics.
        """
        usage = UsageMetric()
        trace_steps: List[Dict[str, Any]] = []

        mcp_tools = self.mcp_client.discover_tools()
        tools_description = self._build_tools_description(mcp_tools)

        conversation_history = (
            f"{self.system_prompt}\n\n"
            f"DANH SÁCH TOOLS KHẢ DỤNG:\n{tools_description}\n\n"
            f"YÊU CẦU CỦA NGƯỜI DÙNG: {user_query}\n"
        )

        step = 0
        final_answer = None

        while step < self.max_steps:
            step += 1
            logger.info(f"--- ReAct Step {step}/{self.max_steps} ---")

            prompt_for_step = (
                f"{conversation_history}\n"
                f"Bước {step}: Hãy suy nghĩ (Thought) và chọn Action hoặc đưa ra Final Answer nếu đã có kết quả."
            )

            response_text, p_tok, c_tok, latency = self.llm_client.call(prompt_for_step)
            usage.add(p_tok, c_tok, latency)

            action_name, action_args, direct_final = SafeActionParser.parse(response_text)

            step_record = {
                "step": step,
                "thought_and_raw": response_text,
                "action": action_name,
                "action_args": action_args,
                "observation": None
            }

            # 1. Final Answer
            if direct_final:
                final_answer = direct_final
                trace_steps.append(step_record)
                break

            # 2. Không gọi Action
            if not action_name:
                final_answer = response_text
                trace_steps.append(step_record)
                break

            # 3. Gọi Tool
            observation = self._execute_tool(action_name, action_args)
            step_record["observation"] = observation
            trace_steps.append(step_record)

            conversation_history += (
                f"\nAction: {action_name}\n"
                f"Action Input: {json.dumps(action_args, ensure_ascii=False)}\n"
                f"Observation: {observation}\n"
            )

            # 4. Auto-verify sau khi gọi write tool
            if action_name == "submit_scholarship_nomination" and "nomination_id" in observation:
                try:
                    obs_json = json.loads(observation)
                    nom_id = obs_json.get("nomination_id") or (
                        obs_json.get("data", {}).get("nomination_id")
                        if isinstance(obs_json.get("data"), dict) else None
                    )
                    if nom_id:
                        # Gọi tool verify
                        verify_obs = self.mcp_client.call_tool(
                            "verify_scholarship_nomination",
                            {"nomination_id": nom_id}
                        )

                        conversation_history += (
                            f"\n[AUTO-VERIFY STEP]\n"
                            f"Action: verify_scholarship_nomination\n"
                            f"Action Input: {{\"nomination_id\": \"{nom_id}\"}}\n"
                            f"Observation: {verify_obs}\n"
                        )

                        trace_steps.append({
                            "step": step,
                            "substep": "auto_verify",
                            "action": "verify_scholarship_nomination",
                            "action_args": {"nomination_id": nom_id},
                            "observation": verify_obs
                        })
                except Exception as e:
                    logger.warning(f"Lỗi khi auto-verify: {e}")

        # Nếu đạt giới hạn MAX_STEPS mà chưa có final_answer thì ép LLM tóm tắt
        if not final_answer:
            final_prompt = (
                f"{conversation_history}\n"
                f"Đã đạt giới hạn số bước. Hãy tóm tắt lại toàn bộ kết quả đã tìm được và trả lời người dùng."
            )
            final_text, p_tok, c_tok, lat = self.llm_client.call(final_prompt)
            usage.add(p_tok, c_tok, lat)
            final_answer = final_text

        return {
            "query": user_query,
            "final_answer": final_answer,
            "steps": trace_steps,
            "total_steps": step,
            "usage": {
                "calls": usage.calls,
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
                "max_prompt_tokens": usage.max_prompt_tokens,
                "latency_seconds": usage.latency_seconds
            }
        }

    def _build_tools_description(self, mcp_tools: List[Dict[str, Any]]) -> str:
        """Tạo chuỗi mô tả các tool khả dụng (RAG + MCP tools) cho LLM"""
        rag_desc = "- rag_search(query: str, filter_doc_id: Optional[str] = None): Tra cứu quy chế đào tạo, học bổng, khung điểm GPA/ĐRL và phân bổ ngân sách.\n"
        mcp_desc = self.mcp_client.get_tools_description_text()
        return rag_desc + mcp_desc

    def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Điều phối thực thi tool nội bộ (RAG) hoặc MCP Server Tools"""
        if tool_name == "rag_search":
            query = args.get("query") or args.get("value") or ""
            doc_id = args.get("filter_doc_id")
            faculty = args.get("filter_faculty")
            results = self.hybrid_engine.search(
                query=query,
                top_k=3,
                filter_doc_id=doc_id,
                filter_faculty=faculty
            )
            if not results:
                return "Không tìm thấy đoạn trích nào phù hợp trong quy chế."
            formatted = []
            for r in results:
                formatted.append(f"[{r.chunk.chunk_id}] (Score: {r.score:.3f})\n{r.chunk.text}")
            return "\n\n---\n\n".join(formatted)

        # Mọi tool còn lại gọi qua MCP Client
        return self.mcp_client.call_tool(tool_name, args)