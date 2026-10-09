"""
MCP SERVER DO SINH VIÊN TỰ VIẾT (YÊU CẦU TUẦN W7)
Yêu cầu bắt buộc:
1. Giao thức stdio, STDOUT PHẢI SẠCH: Tuyệt đối không dùng print() ra stdout. Mọi log đẩy ra sys.stderr.
2. Có ít nhất 2 tools (trong đó ít nhất 1 tool ghi thay đổi trạng thái thật - side effect).
3. Cặp bắt buộc: Write Tool -> Read Tool Verify ngay sau đó.
"""
import sys
import os
import json
import logging
from typing import Dict, Any, List

# CẤM PRINT RA STDOUT: Chỉ log ra stderr để stdout giữ nguyên giao thức JSON-RPC của MCP
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [MCPServer] %(message)s"
)
logger = logging.getLogger("ScholarshipMCPServer")

# Khởi tạo MCP Server (tương thích cả FastMCP v1 và MCPServer v2)
try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("ScholarshipManagementServer")
except Exception:
    try:
        from mcp.server.mcpserver import MCPServer
        mcp = MCPServer("ScholarshipManagementServer")
    except Exception:
        class SimpleMCPServer:
            def __init__(self, name):
                self.name = name
                self._tools = {}
            def tool(self):
                def decorator(fn):
                    self._tools[fn.__name__] = fn
                    return fn
                return decorator
        mcp = SimpleMCPServer("ScholarshipManagementServer")

# Đường dẫn DB dữ liệu
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STUDENTS_FILE = os.path.join(BASE_DIR, "data", "database", "students.json")
NOMINATIONS_FILE = os.path.join(BASE_DIR, "data", "database", "nominations.json")

# =======================================================
# TOOL 1: ĐỌC DỮ LIỆU SINH VIÊN (READ TOOL)
# =======================================================
@mcp.tool()
def get_student_academic_record(student_id: str) -> str:
    """
    Tra cứu hồ sơ kết quả học tập và rèn luyện của sinh viên theo mã số sinh viên.
    Trả về thông tin chi tiết: GPA, ĐRL, số tín chỉ, cảnh cáo học vụ, giải thưởng NCKH.
    """
    logger.info(f"Đang tra cứu hồ sơ sinh viên: {student_id}")
    # TODO (Thành viên phụ trách MCP Server):
    # 1. Đọc dữ liệu từ file STUDENTS_FILE.
    # 2. Tìm kiếm sinh viên theo student_id.
    # 3. Trả về JSON chuỗi sinh viên nếu tìm thấy, hoặc chuỗi 'Error: ...' nếu không tìm thấy.
    return "TODO: Triển khai đọc hồ sơ sinh viên"

# =======================================================
# TOOL 2: TẠO ĐƠN ĐỀ CỬ HỌC BỔNG (WRITE TOOL - SIDE EFFECT)
# =======================================================
@mcp.tool()
def submit_scholarship_nomination(student_id: str, scholarship_tier: str, reason: str) -> str:
    """
    [WRITE TOOL] Tạo và ghi nhận hồ sơ đề cử học bổng khuyến khích học tập vào cơ sở dữ liệu.
    Tạo ra thay đổi trạng thái thật (Side effect).
    """
    logger.info(f"[SIDE-EFFECT] Khởi tạo đề cử học bổng cho: {student_id}, loại: {scholarship_tier}")
    # TODO (Thành viên phụ trách MCP Server):
    # 1. Kiểm tra sinh viên có tồn tại trong hệ thống hay không.
    # 2. Sinh mã nomination_id duy nhất (ví dụ: 'NOM_' + timestamp + uuid).
    # 3. Thêm bản ghi mới vào file NOMINATIONS_FILE với trạng thái 'SUBMITTED'.
    # 4. Trả về JSON chứa {"success": True, "nomination_id": nom_id}.
    return "TODO: Triển khai ghi đơn đề cử học bổng"

# =======================================================
# TOOL 3: KIỂM CHỨNG TRẠNG THÁI ĐƠN (READ TOOL - VERIFY)
# =======================================================
@mcp.tool()
def verify_scholarship_nomination(nomination_id: str) -> str:
    """
    [VERIFY TOOL] Đọc lại cơ sở dữ liệu để kiểm tra và xác nhận trạng thái đơn đề cử học bổng.
    Chứng minh trạng thái thật sự đã được thay đổi trong DB. Cập nhật trạng thái thành VERIFIED.
    """
    logger.info(f"[VERIFY] Kiểm tra trạng thái mã đề cử: {nomination_id}")
    # TODO (Thành viên phụ trách MCP Server):
    # 1. Đọc lại file NOMINATIONS_FILE.
    # 2. Tìm bản ghi có nomination_id trùng khớp.
    # 3. Đổi status thành 'VERIFIED' và lưu lại timestamp verified_at.
    # 4. Trả về JSON xác nhận bản ghi đã tồn tại hợp lệ trong cơ sở dữ liệu.
    return "TODO: Triển khai xác minh trạng thái đơn đề cử"

if __name__ == "__main__":
    logger.info("Khởi động MCP Server qua STDIO...")
    if hasattr(mcp, "run"):
        mcp.run()
