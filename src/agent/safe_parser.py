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
        # Khung mẫu cơ bản:
        final_match = re.search(r"Final Answer:\s*(.*)", llm_output, re.DOTALL | re.IGNORECASE)
        if final_match and "Action:" not in llm_output[final_match.start():]:
            return None, None, final_match.group(1).strip()

        action_match = re.search(r"Action:\s*([a-zA-Z0-9_\-]+)", llm_output)
        if not action_match:
            return None, None, llm_output.strip()

        action_name = action_match.group(1).strip()
        # TODO: Bổ sung logic parse an toàn Action Input
        return action_name, {}, None
