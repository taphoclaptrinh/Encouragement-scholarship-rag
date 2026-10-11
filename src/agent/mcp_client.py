"""
DYNAMIC MCP CLIENT (YÊU CẦU TUẦN W7)
Yêu cầu:
- Kết nối tới MCP Server
- Tự động khám phá động (Dynamic Discovery) danh sách tools (không hard-code)
- Thực thi gọi tool và bắt lỗi: Lỗi trả về chuỗi "Error: ..." thay vì raise crash run (W6)
"""
import logging
from typing import List, Dict, Any, Optional
logger = logging.getLogger("MCPClient")
class DynamicMCPClient:
    def __init__(self, server_script_path: str):
        self.server_script_path = server_script_path
        self._tools_cache: Optional[List[Dict[str, Any]]] = None
        self._server_instance = None
        self._init_server_connection()
    def _init_server_connection(self):
        try:
            from ..mcp_server.server import mcp
            self._server_instance = mcp
            logger.info("Đã kết nối thành công tới MCP Server instance.")
        except Exception as e:
            logger.error(f"Lỗi khi kết nối tới MCP Server: {e}")
            self._server_instance = None
    def discover_tools(self) -> List[Dict[str, Any]]:
        # Nếu đã discover trước đó thì dùng lại từ cache
        if self._tools_cache is not None:
            return self._tools_cache
        tools = []
        if self._server_instance:
            # Lấy registry tools từ FastMCP / MCPServer tương thích mọi phiên bản SDK
            tool_dict = {}
            if hasattr(self._server_instance, "_tool_manager") and hasattr(self._server_instance._tool_manager, "_tools"):
                tool_dict = self._server_instance._tool_manager._tools
            elif hasattr(self._server_instance, "_tools"):
                tool_dict = self._server_instance._tools
            for tool_name, tool_obj in tool_dict.items():
                # Lấy docstring hoặc description của tool
                desc = getattr(tool_obj, "description", None) or getattr(tool_obj, "__doc__", "") or ""
                # Lấy schema parameters nếu có
                params = getattr(tool_obj, "parameters", {})
                tools.append({
                    "name": tool_name,
                    "description": desc.strip(),
                    "parameters": params
                })
        self._tools_cache = tools
        logger.info(f"Đã khám phá động thành công {len(tools)} tools từ MCP Server.")
        return tools
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        if not self._server_instance:
            return "Error: MCP Server chưa sẵn sàng hoặc kết nối bị lỗi."
        try:
            # Tìm hàm thực thi của tool trong server
            tool_fn = None
            if hasattr(self._server_instance, "_tool_manager") and hasattr(self._server_instance._tool_manager, "_tools"):
                t_obj = self._server_instance._tool_manager._tools.get(tool_name)
                if t_obj:
                    tool_fn = getattr(t_obj, "fn", t_obj)
            elif hasattr(self._server_instance, "_tools"):
                t_obj = self._server_instance._tools.get(tool_name)
                if t_obj:
                    tool_fn = getattr(t_obj, "fn", t_obj)
            if not tool_fn:
                return f"Error: Tool '{tool_name}' không tồn tại trên MCP Server."
            # Thực thi hàm với các tham số do LLM yêu cầu
            result = tool_fn(**arguments)
            return str(result)
        except TypeError as te:
            # Lỗi truyền thiếu hoặc thừa tham số từ LLM
            logger.warning(f"Lỗi tham số khi gọi tool '{tool_name}': {te}")
            return f"Error: Tham số gọi tool '{tool_name}' không hợp lệ: {str(te)}"
        except Exception as e:
            # Lỗi ngoại lệ nghiệp vụ khác
            logger.error(f"Lỗi xảy ra trong quá trình thực thi tool '{tool_name}': {e}")
            return f"Error: Ngoại lệ xảy ra trong tool '{tool_name}': {str(e)}"
