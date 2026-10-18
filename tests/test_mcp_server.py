"""
BỘ KIỂM THỬ TỰ ĐỘNG CHO MCP SERVER VÀ DYNAMIC MCP CLIENT
Tuân thủ tiêu chí đánh giá W6 & W7 của môn AIPR:
1. Test tra cứu sinh viên hợp lệ và không hợp lệ.
2. Test tool ghi có side-effect thật (tạo nomination_id duy nhất và lưu vào DB).
3. Test tool verify đọc lại CSDL và cập nhật trạng thái VERIFIED.
4. Test tính an toàn (Không raise exception làm crash hệ thống, trả về 'Error: ...').
5. Test tính năng Dynamic Discovery của DynamicMCPClient.
"""
import unittest
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mcp_server.server import (
    get_student_academic_record,
    submit_scholarship_nomination,
    verify_scholarship_nomination,
    get_faculty_scholarship_budget,
    cancel_scholarship_nomination,
    NOMINATIONS_FILE
)
from src.agent.mcp_client import DynamicMCPClient

class TestMCPServerAndClient(unittest.TestCase):
    def setUp(self):
        self.client = DynamicMCPClient("src/mcp_server/server.py")

    def test_01_get_student_record_success(self):
        """Kiểm tra đọc hồ sơ sinh viên hợp lệ"""
        raw = get_student_academic_record("23110101")
        data = json.loads(raw)
        self.assertEqual(data["student_id"], "23110101")
        self.assertEqual(data["full_name"], "Nguyễn Văn An")
        self.assertAlmostEqual(data["gpa"], 3.88)
        self.assertEqual(data["drl"], 95)

    def test_02_get_student_record_not_found(self):
        """Kiểm tra xử lý an toàn khi không tìm thấy sinh viên (trả về Error:, không crash)"""
        res = get_student_academic_record("99999999")
        self.assertTrue(res.startswith("Error:"), "Phải trả về chuỗi thông báo Error")

    def test_03_submit_nomination_side_effect(self):
        """Kiểm tra Tool ghi làm thay đổi trạng thái thật trong DB (Side-effect)"""
        res_str = submit_scholarship_nomination(
            student_id="24110137",
            scholarship_tier="Xuất sắc",
            reason="Điểm GPA 3.86 và ĐRL 93 đạt chuẩn xuất sắc"
        )
        res = json.loads(res_str)
        self.assertTrue(res["success"])
        nomination_id = res["data"]["nomination_id"]
        self.assertTrue(nomination_id.startswith("NOM_"))
        self.assertEqual(res["data"]["status"], "SUBMITTED")

        # Kiểm chứng dữ liệu đã thật sự ghi vào file DB
        with open(NOMINATIONS_FILE, "r", encoding="utf-8") as f:
            nominations = json.load(f)
        found = any(n["nomination_id"] == nomination_id for n in nominations)
        self.assertTrue(found, "Bản ghi phải thực sự tồn tại trong file CSDL nominations.json")

    def test_04_verify_nomination(self):
        """Kiểm tra Tool verify đọc lại DB và cập nhật trạng thái VERIFIED"""
        # 1. Tạo đơn trước
        create_res = json.loads(submit_scholarship_nomination(
            student_id="23110102",
            scholarship_tier="Giỏi",
            reason="GPA 3.72 và ĐRL 84"
        ))
        nom_id = create_res["data"]["nomination_id"]

        # 2. Gọi tool verify
        verify_res_str = verify_scholarship_nomination(nom_id)
        verify_res = json.loads(verify_res_str)
        self.assertTrue(verify_res["success"])
        self.assertEqual(verify_res["data"]["status"], "VERIFIED")
        self.assertIsNotNone(verify_res["data"]["verified_at"])

    def test_05_dynamic_tool_discovery(self):
        """Kiểm tra Client tự động khám phá được 3 tools mà không hard-code"""
        tools = self.client.discover_tools()
        self.assertGreaterEqual(len(tools), 3)
        tool_names = [t["name"] for t in tools]
        self.assertIn("get_student_academic_record", tool_names)
        self.assertIn("submit_scholarship_nomination", tool_names)
        self.assertIn("verify_scholarship_nomination", tool_names)

    def test_06_safe_client_call_error_handling(self):
        """Kiểm tra gọi sai tên tool qua client không làm crash ứng dụng"""
        res = self.client.call_tool("invalid_tool_name", {})
        self.assertTrue(res.startswith("Error:"))

    def test_07_get_faculty_scholarship_budget(self):
        """Kiểm tra tra cứu định mức ngân sách học bổng của Khoa/Viện (Tool 4)"""
        # Test hợp lệ cho Viện FIE
        raw_fie = get_faculty_scholarship_budget("FIE")
        data_fie = json.loads(raw_fie)
        self.assertEqual(data_fie["faculty"], "FIE")
        self.assertEqual(data_fie["total_slots"], 20)
        self.assertEqual(data_fie["tier_a_slots"], 5)

        # Test hợp lệ cho Khoa CNTT
        raw_cntt = get_faculty_scholarship_budget("CNTT")
        data_cntt = json.loads(raw_cntt)
        self.assertEqual(data_cntt["faculty"], "CNTT")
        self.assertEqual(data_cntt["total_slots"], 45)

        # Test an toàn khi nhập khoa không tồn tại
        res_err = get_faculty_scholarship_budget("UNKNOWN_FACULTY")
        self.assertTrue(res_err.startswith("Error:"))

    def test_08_cancel_scholarship_nomination(self):
        """Kiểm tra hủy đơn đề cử học bổng và đổi trạng thái CANCELLED (Tool 5)"""
        # 1. Tạo một đơn đề cử mới
        create_res = json.loads(submit_scholarship_nomination(
            student_id="24110137",
            scholarship_tier="Xuất sắc",
            reason="Test hủy đề cử do khiếu nại"
        ))
        nom_id = create_res["data"]["nomination_id"]

        # 2. Gọi tool hủy đơn
        cancel_res_raw = cancel_scholarship_nomination(nom_id, "Sinh viên có khiếu nại kỷ luật đột xuất")
        cancel_res = json.loads(cancel_res_raw)
        self.assertTrue(cancel_res["success"])
        self.assertEqual(cancel_res["data"]["status"], "CANCELLED")

        # 3. Đối soát lại trong file CSDL
        with open(NOMINATIONS_FILE, "r", encoding="utf-8") as f:
            nominations = json.load(f)
        record = next((n for n in nominations if n["nomination_id"] == nom_id), None)
        self.assertIsNotNone(record)
        self.assertEqual(record["status"], "CANCELLED")
        self.assertIsNotNone(record.get("cancelled_at"))

if __name__ == "__main__":
    unittest.main()
