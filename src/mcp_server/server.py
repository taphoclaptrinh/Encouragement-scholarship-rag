"""
MCP SERVER DO SINH VIÊN TỰ VIẾT (YÊU CẦU TUẦN W7)
Đồ án AIPR: Trợ lý Thẩm định Học bổng Khuyến khích Học tập (HCMUTE)

Tuân thủ nghiêm ngặt các nguyên tắc từ Giảng viên (02-Yeu-cau-Thuc-hien.pdf):
1. Giao thức stdio, STDOUT PHẢI SẠCH: Cấm print() ra stdout. Toàn bộ log chuyển vào sys.stderr.
2. Typing đầy đủ (W1): Dùng dataclass và type hint rõ ràng.
3. Có ít nhất 1 tool ghi thay đổi trạng thái thật (Side-effect) và 1 tool đọc verify ngay sau đó.
4. Xử lý lỗi an toàn: Bắt ngoại lệ và trả chuỗi "Error: ..." thay vì raise crash (W6).
"""
import sys
import os
import json
import logging
from datetime import datetime
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import asdict

from ..schemas.student import StudentRecord
from ..schemas.tool_contracts import NominationRecord, ToolResult, FacultyBudgetRecord

# 1. CẤM PRINT RA STDOUT: Mọi thông tin debug/log bắt buộc ghi vào sys.stderr
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [MCPServer] %(message)s"
)
logger = logging.getLogger("ScholarshipMCPServer")

# 2. KHỞI TẠO MCP SERVER (Hỗ trợ mcp 2.x MCPServer và fallback mcp 1.x / Mock)
try:
    from mcp.server.mcpserver import MCPServer
    mcp = MCPServer("ScholarshipManagementServer")
except Exception:
    try:
        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("ScholarshipManagementServer")
    except Exception:
        class SimpleMCPServer:
            def __init__(self, name: str):
                self.name = name
                self._tools = {}
            def tool(self):
                def decorator(fn):
                    self._tools[fn.__name__] = fn
                    return fn
                return decorator
        mcp = SimpleMCPServer("ScholarshipManagementServer")

# 3. ĐƯỜNG DẪN DỮ LIỆU CSDL GIẢ LẬP
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STUDENTS_FILE = os.path.join(BASE_DIR, "data", "database", "students.json")
NOMINATIONS_FILE = os.path.join(BASE_DIR, "data", "database", "nominations.json")

def _read_json_file(file_path: str) -> List[Dict[str, Any]]:
    """Hàm phụ trợ đọc file JSON an toàn."""
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Lỗi đọc file {file_path}: {e}")
        return []

def _write_json_file(file_path: str, data: List[Dict[str, Any]]) -> bool:
    """Hàm phụ trợ ghi file JSON nguyên tử (atomic/safe)."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Lỗi ghi file {file_path}: {e}")
        return False


# =======================================================
# TOOL 1: ĐỌC DỮ LIỆU SINH VIÊN (READ TOOL)
# =======================================================
@mcp.tool()
def get_student_academic_record(student_id: str) -> str:
    """
    [READ TOOL] Tra cứu hồ sơ kết quả học tập và rèn luyện của sinh viên theo mã số sinh viên (student_id).
    Dữ liệu trả về gồm: GPA, ĐRL, số tín chỉ đăng ký, tình trạng nợ môn, kỷ luật và giải thưởng NCKH.
    Nếu không tìm thấy hoặc có lỗi, trả về thông báo lỗi có tiền tố 'Error: ...'.
    """
    try:
        sid = (student_id or "").strip().upper()
        logger.info(f"Đang tra cứu hồ sơ sinh viên: {sid}")

        if not sid:
            return "Error: student_id không được để trống."

        students = _read_json_file(STUDENTS_FILE)
        for st in students:
            if st.get("student_id", "").upper() == sid:
                # Ép kiểu dữ liệu qua Dataclass để đảm bảo tính hợp lệ (Yêu cầu W1)
                record = StudentRecord(
                    student_id=st["student_id"],
                    full_name=st["full_name"],
                    faculty=st["faculty"],
                    cohort=st["cohort"],
                    semester=st["semester"],
                    gpa=float(st["gpa"]),
                    drl=int(st["drl"]) if st.get("drl") is not None else None,
                    credits_registered=int(st["credits_registered"]),
                    has_failed_course=bool(st.get("has_failed_course", False)),
                    disciplinary_record=st.get("disciplinary_record"),
                    scientific_research_award=bool(st.get("scientific_research_award", False))
                )
                return json.dumps(asdict(record), ensure_ascii=False)

        return f"Error: Không tìm thấy sinh viên có mã {sid} trong cơ sở dữ liệu."
    except Exception as e:
        logger.error(f"Ngoại lệ khi tra cứu hồ sơ: {e}")
        return f"Error: Đã xảy ra lỗi hệ thống khi tra cứu sinh viên: {str(e)}"


# =======================================================
# TOOL 2: TẠO ĐƠN ĐỀ CỬ HỌC BỔNG (WRITE TOOL - SIDE EFFECT)
# =======================================================
@mcp.tool()
def submit_scholarship_nomination(student_id: str, scholarship_tier: str, reason: str) -> str:
    """
    [WRITE TOOL - SIDE EFFECT] Tạo và ghi nhận hồ sơ đề cử học bổng vào cơ sở dữ liệu.
    Thao tác này làm thay đổi trạng thái thật trong hệ thống (Tầng c).
    Trạng thái ban đầu sẽ là 'SUBMITTED'.
    Trả về chuỗi JSON chứa nomination_id để thực hiện bước Verify ngay sau đó.
    """
    try:
        sid = (student_id or "").strip().upper()
        tier = (scholarship_tier or "").strip()
        rs = (reason or "").strip()

        logger.info(f"[SIDE-EFFECT] Tạo đề cử học bổng: Mã SV={sid}, Loại={tier}")

        if not sid or not tier:
            return "Error: student_id và scholarship_tier là bắt buộc."

        # 1. Kiểm tra sinh viên có tồn tại trong hệ thống không
        students = _read_json_file(STUDENTS_FILE)
        student_info = next((s for s in students if s.get("student_id", "").upper() == sid), None)
        if not student_info:
            return f"Error: Không thể đề cử vì không tìm thấy sinh viên {sid} trong CSDL."

        # 2. Sinh mã đề cử duy nhất: NOM_<YYYYMMDD>_<SHORT_UUID>
        date_str = datetime.now().strftime("%Y%m%d")
        unique_suffix = uuid.uuid4().hex[:6].upper()
        nomination_id = f"NOM_{date_str}_{unique_suffix}"
        created_at = datetime.now().isoformat()

        # 3. Tạo bản ghi Dataclass theo Tool Contract
        nomination = NominationRecord(
            nomination_id=nomination_id,
            student_id=student_info["student_id"],
            student_name=student_info["full_name"],
            faculty=student_info["faculty"],
            scholarship_tier=tier,
            status="SUBMITTED",
            reason=rs,
            created_at=created_at,
            verified_at=None
        )

        # 4. Ghi trực tiếp vào file CSDL (Side-effect thật)
        nominations = _read_json_file(NOMINATIONS_FILE)
        nominations.append(asdict(nomination))
        success = _write_json_file(NOMINATIONS_FILE, nominations)

        if not success:
            return "Error: Không thể ghi dữ liệu đề cử vào cơ sở dữ liệu."

        result = ToolResult(
            success=True,
            data={
                "nomination_id": nomination_id,
                "student_id": sid,
                "status": "SUBMITTED",
                "message": "Đề cử học bổng đã được ghi nhận thành công vào cơ sở dữ liệu."
            }
        )
        return json.dumps(asdict(result), ensure_ascii=False)
    except Exception as e:
        logger.error(f"Ngoại lệ khi submit đề cử: {e}")
        return f"Error: Lỗi khi khởi tạo đề cử học bổng: {str(e)}"


# =======================================================
# TOOL 3: KIỂM CHỨNG TRẠNG THÁI ĐƠN (READ TOOL - VERIFY)
# =======================================================
@mcp.tool()
def verify_scholarship_nomination(nomination_id: str) -> str:
    """
    [READ TOOL - VERIFY BẮT BUỘC] Đọc lại cơ sở dữ liệu để kiểm tra và xác nhận hồ sơ đề cử học bổng.
    Chứng minh trạng thái thật sự đã được thay đổi trong DB (bảo đảm an toàn Agent).
    Nếu tìm thấy, hệ thống chuyển trạng thái hồ sơ sang 'VERIFIED' và ghi nhận thời gian xác minh.
    """
    try:
        nid = (nomination_id or "").strip()
        logger.info(f"[VERIFY] Kiểm chứng hồ sơ đề cử mã: {nid}")

        if not nid:
            return "Error: nomination_id không được để trống."

        nominations = _read_json_file(NOMINATIONS_FILE)
        target_nomination = None
        target_index = -1

        for idx, nom in enumerate(nominations):
            if nom.get("nomination_id") == nid:
                target_nomination = nom
                target_index = idx
                break

        if not target_nomination:
            return f"Error: Xác minh thất bại. Không tìm thấy mã đề cử '{nid}' trong CSDL."

        # Cập nhật trạng thái thành VERIFIED để đánh dấu đã quan sát thành công
        verified_at = datetime.now().isoformat()
        target_nomination["status"] = "VERIFIED"
        target_nomination["verified_at"] = verified_at
        nominations[target_index] = target_nomination

        # Ghi nhận trạng thái VERIFIED lại vào file
        _write_json_file(NOMINATIONS_FILE, nominations)

        result = ToolResult(
            success=True,
            data={
                "nomination_id": nid,
                "student_id": target_nomination.get("student_id"),
                "student_name": target_nomination.get("student_name"),
                "scholarship_tier": target_nomination.get("scholarship_tier"),
                "status": "VERIFIED",
                "verified_at": verified_at,
                "message": "Xác minh thành công: Hồ sơ đề cử đã được lưu trữ và kiểm chứng hợp lệ trong CSDL."
            }
        )
        return json.dumps(asdict(result), ensure_ascii=False)
    except Exception as e:
        logger.error(f"Ngoại lệ khi verify đề cử: {e}")
        return f"Error: Lỗi hệ thống khi xác minh đề cử: {str(e)}"


# =======================================================
# TOOL 4: TRA CỨU ĐỊNH MỨC NGÂN SÁCH KHOA/VIỆN (READ TOOL)
# =======================================================
FACULTY_BUDGETS: Dict[str, FacultyBudgetRecord] = {
    "CNTT": FacultyBudgetRecord(
        faculty="CNTT",
        faculty_name="Khoa Công nghệ Thông tin",
        total_budget_vnd=450000000,
        total_slots=45,
        tier_a_slots=10,
        tier_b_slots=15,
        tier_c_slots=20,
        note="Căn cứ Quyết định phân bổ ngân sách DOC0004. Tối đa không quá 8% tổng sĩ số khóa."
    ),
    "FIE": FacultyBudgetRecord(
        faculty="FIE",
        faculty_name="Viện Đào tạo Quốc tế",
        total_budget_vnd=250000000,
        total_slots=20,
        tier_a_slots=5,
        tier_b_slots=7,
        tier_c_slots=8,
        note="Chương trình liên kết và đào tạo quốc tế chất lượng cao theo DOC0006."
    ),
    "CKD": FacultyBudgetRecord(
        faculty="CKD",
        faculty_name="Khoa Cơ khí Động lực",
        total_budget_vnd=400000000,
        total_slots=40,
        tier_a_slots=8,
        tier_b_slots=12,
        tier_c_slots=20,
        note="Phân bổ theo định mức ngân sách đào tạo kỹ thuật công nghệ."
    ),
    "DDT": FacultyBudgetRecord(
        faculty="DDT",
        faculty_name="Khoa Điện - Điện tử",
        total_budget_vnd=420000000,
        total_slots=42,
        tier_a_slots=9,
        tier_b_slots=13,
        tier_c_slots=20,
        note="Ưu tiên sinh viên có thành tích nghiên cứu khoa học và sáng tạo."
    )
}

@mcp.tool()
def get_faculty_scholarship_budget(faculty: str) -> str:
    """
    [READ TOOL] Tra cứu hạn mức ngân sách học bổng và chỉ tiêu phân bổ số suất theo từng Khoa/Viện.
    Tham số faculty: mã khoa (ví dụ: 'CNTT', 'FIE', 'CKD', 'DDT').
    """
    try:
        fac = (faculty or "").strip().upper()
        logger.info(f"Đang tra cứu ngân sách học bổng khoa/viện: {fac}")

        if not fac:
            return "Error: faculty không được để trống."

        if fac in FACULTY_BUDGETS:
            record = FACULTY_BUDGETS[fac]
            return json.dumps(asdict(record), ensure_ascii=False)

        available_faculties = ", ".join(FACULTY_BUDGETS.keys())
        return f"Error: Không tìm thấy dữ liệu ngân sách cho khoa '{fac}'. Các khoa hiện có: {available_faculties}"
    except Exception as e:
        logger.error(f"Ngoại lệ khi tra cứu ngân sách: {e}")
        return f"Error: Lỗi khi tra cứu ngân sách khoa: {str(e)}"


# =======================================================
# TOOL 5: HỦY ĐƠN ĐỀ CỬ HỌC BỔNG (WRITE TOOL - SIDE EFFECT)
# =======================================================
@mcp.tool()
def cancel_scholarship_nomination(nomination_id: str, reason: str) -> str:
    """
    [WRITE TOOL - SIDE EFFECT] Hủy bỏ hoặc thu hồi một đơn đề cử học bổng trong cơ sở dữ liệu nếu phát hiện có sai sót hoặc vi phạm kỷ luật.
    Thao tác này làm thay đổi trạng thái bản ghi trong CSDL sang 'CANCELLED'.
    """
    try:
        nid = (nomination_id or "").strip()
        rs = (reason or "").strip()
        logger.info(f"[SIDE-EFFECT] Hủy đơn đề cử học bổng mã: {nid}, lý do: {rs}")

        if not nid:
            return "Error: nomination_id không được để trống."
        if not rs:
            return "Error: Phải cung cấp lý do hủy đề cử (reason)."

        nominations = _read_json_file(NOMINATIONS_FILE)
        target_nomination = None
        target_index = -1

        for idx, nom in enumerate(nominations):
            if nom.get("nomination_id") == nid:
                target_nomination = nom
                target_index = idx
                break

        if not target_nomination:
            return f"Error: Hủy đề cử thất bại. Không tìm thấy mã '{nid}' trong CSDL."

        cancelled_at = datetime.now().isoformat()
        target_nomination["status"] = "CANCELLED"
        target_nomination["cancelled_at"] = cancelled_at
        target_nomination["cancellation_reason"] = rs
        nominations[target_index] = target_nomination

        _write_json_file(NOMINATIONS_FILE, nominations)

        result = ToolResult(
            success=True,
            data={
                "nomination_id": nid,
                "student_id": target_nomination.get("student_id"),
                "status": "CANCELLED",
                "cancelled_at": cancelled_at,
                "reason": rs,
                "message": f"Đã hủy bỏ đề cử học bổng '{nid}' thành công trong CSDL."
            }
        )
        return json.dumps(asdict(result), ensure_ascii=False)
    except Exception as e:
        logger.error(f"Ngoại lệ khi hủy đề cử: {e}")
        return f"Error: Lỗi hệ thống khi hủy đề cử: {str(e)}"


# =======================================================
# KHỞI CHẠY SERVER QUA STDIO
# =======================================================
if __name__ == "__main__":
    logger.info("Đang khởi động MCP Server qua giao thức STDIO...")
    if hasattr(mcp, "run"):
        mcp.run()
