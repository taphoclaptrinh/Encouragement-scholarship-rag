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

    def discover_tools(self) -> List[Dict[str, Any]]:
        """
        TODO (Thành viên phụ trách Agent & MCP):
        Khám phá động danh sách tools từ MCP Server:
        Trả về danh sách dict: [{"name": ..., "description": ..., "parameters": ...}]
        """
        if self._tools_cache is not None:
            return self._tools_cache
        return []

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        TODO (Thành viên phụ trách Agent & MCP):
        1. Gọi tool tương ứng với tham số arguments.
        2. Bắt lỗi ngoại lệ (TypeError, Exception) -> Trả về f"Error: {e}" thay vì crash run.
        """
        return "TODO: Triển khai gọi tool qua client"
