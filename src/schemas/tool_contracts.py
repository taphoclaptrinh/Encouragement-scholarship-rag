"""
Dataclass cho các hợp đồng gọi Tool (W1 & W7)
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class NominationRecord:
    nomination_id: str
    student_id: str
    student_name: str
    faculty: str
    scholarship_tier: str
    status: str            # "SUBMITTED", "VERIFIED", "CANCELLED"
    reason: str
    created_at: str
    verified_at: Optional[str] = None
    cancelled_at: Optional[str] = None

@dataclass
class FacultyBudgetRecord:
    faculty: str
    faculty_name: str
    total_budget_vnd: int
    total_slots: int
    tier_a_slots: int      # Xuất sắc
    tier_b_slots: int      # Giỏi
    tier_c_slots: int      # Khá
    note: str

@dataclass
class ToolResult:
    success: bool
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
