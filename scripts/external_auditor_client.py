"""
HOST / CLIENT ĐỘC LẬP THỨ HAI (INTEROPERABILITY AUDITOR)
Chứng minh MCP Server do nhóm xây dựng có tính tương thích (interoperable),
có thể được gọi từ một client hoàn toàn độc lập khác để phục vụ kiểm toán hồ sơ.
(+1 ĐIỂM CỘNG THEO YÊU CẦU MỤC 3)
"""
import os
import json
import logging

def run_external_audit():
    print("=== BẮT ĐẦU PHIÊN KIỂM TOÁN TỪ CLIENT ĐỘC LẬP THỨ HAI ===")
    # TODO (Điểm cộng +1):
    # 1. Khởi tạo MCP client kết nối tới src/mcp_server/server.py.
    # 2. Khám phá động tools từ MCP server.
    # 3. Gọi get_student_academic_record('SV2024001').
    # 4. Gọi submit_scholarship_nomination(...) và sau đó verify_scholarship_nomination(...).
    print("TODO: Triển khai kiểm toán từ client thứ hai tại đây.")

if __name__ == "__main__":
    run_external_audit()
