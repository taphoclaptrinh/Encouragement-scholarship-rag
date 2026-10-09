"""
YÊU CẦU TUẦN W1: Tool schema và Models khai báo bằng dataclass có type hint, không dùng dict thô.
grep -n "@dataclass" src/schemas/student.py
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class StudentRecord:
    student_id: str
    full_name: str
    faculty: str
    cohort: str
    semester: str
    gpa: float
    drl: Optional[int]
    credits_registered: int
    has_failed_course: bool
    disciplinary_record: Optional[str] = None
    scientific_research_award: bool = False

@dataclass
class ScholarshipDecision:
    student_id: str
    is_eligible: bool
    tier: Optional[str]               # "Xuất sắc", "Giỏi", "Khá"
    benefit_percentage: Optional[int] # 125, 110, 100
    reason: str
    referenced_doc_id: str
