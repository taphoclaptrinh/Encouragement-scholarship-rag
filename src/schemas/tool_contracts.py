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
    status: str            # "SUBMITTED", "VERIFIED"
    reason: str
    created_at: str
    verified_at: Optional[str] = None

@dataclass
class ToolResult:
    success: bool
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
