import logging
import asyncio
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
        """
        Khám phá động danh sách tools từ MCP Server:
        Trả về danh sách dict: [{"name": ..., "description": ..., "parameters": ...}]
        """
        # Nếu đã discover trước đó thì dùng lại từ cache
        if self._tools_cache is not None:
            return self._tools_cache

        tools = []
        if not self._server_instance:
            return []

        try:
            # 1. Hỗ trợ chuẩn MCP 2.x (async list_tools)
            if hasattr(self._server_instance, "list_tools"):
                async def _fetch():
                    raw = await self._server_instance.list_tools()
                    res = []
                    for t in raw:
                        res.append({
                            "name": t.name,
                            "description": (t.description or "").strip(),
                            "parameters": getattr(t, "input_schema", {})
                        })
                    return res
                tools = asyncio.run(_fetch())
            # 2. Hỗ trợ FastMCP 1.x / SimpleMock
            else:
                tool_dict = {}
                if hasattr(self._server_instance, "_tool_manager") and hasattr(self._server_instance._tool_manager, "_tools"):
                    tool_dict = self._server_instance._tool_manager._tools
                elif hasattr(self._server_instance, "_tools"):
                    tool_dict = self._server_instance._tools

                for tool_name, tool_obj in tool_dict.items():
                    desc = getattr(tool_obj, "description", None) or getattr(tool_obj, "__doc__", "") or ""
                    params = getattr(tool_obj, "parameters", {})
                    tools.append({
                        "name": tool_name,
                        "description": desc.strip(),
                        "parameters": params
                    })

            self._tools_cache = tools
            logger.info(f"Đã khám phá động thành công {len(tools)} tools từ MCP Server.")
            return tools
        except Exception as e:
            logger.error(f"Lỗi khi khám phá tools từ MCP Server: {e}")
            return []

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        1. Gọi tool tương ứng với tham số arguments.
        2. Bắt lỗi ngoại lệ (TypeError, Exception) -> Trả về f"Error: {e}" thay vì crash run.
        """
        if not self._server_instance:
            return "Error: MCP Server chưa sẵn sàng hoặc kết nối bị lỗi."

        try:
            # 1. Hỗ trợ chuẩn MCP 2.x (async call_tool)
            if hasattr(self._server_instance, "call_tool"):
                async def _invoke():
                    res = await self._server_instance.call_tool(tool_name, arguments)
                    if hasattr(res, "content") and res.content:
                        return res.content[0].text
                    return str(res)
                return asyncio.run(_invoke())

            # 2. Fallback gọi trực tiếp hàm Python
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

            result = tool_fn(**arguments)
            return str(result)

        except TypeError as te:
            logger.warning(f"Lỗi tham số khi gọi tool '{tool_name}': {te}")
            return f"Error: Tham số gọi tool '{tool_name}' không hợp lệ: {str(te)}"
        except Exception as e:
            logger.error(f"Lỗi xảy ra trong quá trình thực thi tool '{tool_name}': {e}")
            return f"Error: Ngoại lệ xảy ra trong tool '{tool_name}': {str(e)}"

    def get_tools_description_text(self) -> str:
        """
        Định dạng danh sách tools thành văn bản để gắn vào Prompt của Agent Loop.
        """
        tools = self.discover_tools()
        lines = []
        for t in tools:
            lines.append(f"- {t['name']}: {t['description']}")
        return "\n".join(lines)
