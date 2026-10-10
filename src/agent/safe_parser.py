"""
PARSER ACTION AN TOÀN (YÊU CẦU TUẦN W6)
Yêu cầu:
- Parse Action và Action Input từ output văn bản của LLM
- Xử lý ngoại lệ an toàn: Khi thiếu dấu ngoặc nhọn, dấu nháy kép, không làm crash toàn bộ run
"""
import re
import json
from typing import Tuple, Optional, Dict, Any

class SafeActionParser:
    @staticmethod
    def parse(llm_output: str) -> Tuple[Optional[str], Optional[Dict[str, Any]], Optional[str]]:
        """
        Phân tích kết quả từ LLM.
        Trả về: (action_name, action_input_dict, final_answer)

        TODO (Thành viên phụ trách Agent Loop):
        1. Kiểm tra xem LLM có trả về "Final Answer:" hay không -> Trả về (None, None, final_answer).
        2. Dùng regex tìm 'Action: <tool_name>'.
        3. Dùng regex tìm 'Action Input: <json_args>'.
        4. Bọc json.loads trong try...except để không bị crash khi LLM sinh cú pháp JSON lỗi.
        """
        if not llm_output or not llm_output.strip():
            return None, None, "Error: LLM trả về phản hồi rỗng."

        text = llm_output.strip()

        #--- Kiem tra Final Answer ---
        final_match = re.search(r"Final Answer:\s*(.*)", text, re.DOTALL | re.IGNORECASE)

        if final_match and "Action:" not in text[final_match.start():]:
            final_content = final_match.group(1).strip()
            return None, None, final_content

        #--- Tim Action ---
        action_match = re.search(r"Action:\s*([a-zA-Z0-9_\-]+)", text)
        if not action_match:
            return None, None, text 

        action_name = action_match.group(1).strip()

        #--- Boc tach Action Input ---
        input_match = re.search(r"Action Input:\s*(.*)", text, re.DOTALL | re.IGNORECASE)
        if not input_match:
            return action_name, {}, None

        raw_input = input_match.group(1).strip()

        next_break = re.search(r"\n(?:Observation|Action|Final Answer|Thought):", raw_input, re.IGNORECASE)
        if next_break:
            raw_input = raw_input[:next_break.start()].strip()

        #--- Lam sach va PARSE JSON ---
        clean_input = re.sub(r"^```(?:json)?\s*", "", raw_input, flags=re.IGNORECASE)
        clean_input = re.sub(r"\s*```$", "", clean_input).strip()

        parsed_args: Dict[str, Any] = {}
        try:
            parsed_args = json.loads(clean_input)
            # Đảm bảo kết quả parse phải là một Dictionary
            if not isinstance(parsed_args, dict):
                parsed_args = {"value": parsed_args}
        except json.JSONDecodeError:
            # XỬ LÝ LỖI AN TOÀN (FALLBACK) KHI JSON BỊ LỖI CÚ PHÁP:
            # Cách 1: Thử vá lỗi phổ biến nhất của LLM là thiếu dấu đóng ngoặc nhọn '}'
            try:
                fixed_input = clean_input + "}"
                parsed_args = json.loads(fixed_input)
                if not isinstance(parsed_args, dict):
                    parsed_args = {"value": parsed_args}
            except Exception:
                # Cách 2: Nếu vẫn không parse được -> bọc chuỗi gốc vào key 'raw_input'
                # Tuyệt đối không để crash run!
                parsed_args = {"raw_input": clean_input}
        return action_name, parsed_args, None