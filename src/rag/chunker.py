"""
MODULE CHUNKING TÀI LIỆU QUY CHẾ (YÊU CẦU TUẦN W3)
Triển khai DocumentChunker:
- Đọc tài liệu quy chế từ thư mục data/corpus/*.txt
- Bóc tách phần YAML frontmatter (doc_id, title, version, owner, status)
- Tách văn bản thành các Chunk ngữ nghĩa theo Điều khoản 
- Gắn Header metadata đầy đủ vào từng Chunk
"""
import os
import glob
import re
from typing import List, Dict, Any, Optional
from ..schemas.rag_types import DocMetadata, Chunk

class DocumentChunker:
    def __init__(self, corpus_dir: str):
        self.corpus_dir = corpus_dir

    def _parse_frontmatter(self, content: str) -> tuple[DocMetadata, str]:
        """Tách YAML frontmatter ở đầu file văn bản."""
        meta = {
            "doc_id": "UNKNOWN",
            "title": "Không có tiêu đề",
            "date": "2024-01-01",
            "version": "1.0",
            "owner": "Phòng CTSV",
            "status": "ACTIVE_CURRENT",
            "faculty_scope": None
        }

        body = content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                yaml_text = parts[1]
                body = parts[2].strip()
                for line in yaml_text.strip().splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        k = k.strip()
                        v = v.strip()
                        if k in meta:
                            meta[k] = v

        doc_meta = DocMetadata(
            doc_id=meta["doc_id"],
            title=meta["title"],
            date=meta["date"],
            version=meta["version"],
            owner=meta["owner"],
            status=meta["status"],
            faculty=meta.get("faculty_scope") or meta.get("faculty")
        )
        return doc_meta, body

    def chunk_document(self, file_path: str) -> List[Chunk]:
        """Chia một tài liệu thành các chunks ngữ nghĩa theo điều khoản."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return []

        doc_meta, body = self._parse_frontmatter(content)
        sections = re.split(r'\n(?=Điều \d+)', body)

        chunks: List[Chunk] = []
        for idx, sec in enumerate(sections):
            sec_text = sec.strip()
            if not sec_text:
                continue

            full_chunk_text = (
                f"[Tài liệu: {doc_meta.doc_id} - {doc_meta.title} (Phiên bản: {doc_meta.version})]\n"
                f"[Trạng thái: {doc_meta.status} | Đơn vị: {doc_meta.owner}]\n"
                f"{sec_text}"
            )

            chunk = Chunk(
                chunk_id=f"{doc_meta.doc_id}_c{idx+1:02d}",
                text=full_chunk_text,
                metadata=doc_meta
            )
            chunks.append(chunk)

        return chunks

    def load_and_chunk_all(self) -> List[Chunk]:
        """Duyệt qua tất cả các file .txt trong corpus_dir và tạo danh sách chunks."""
        chunks: List[Chunk] = []
        files = glob.glob(os.path.join(self.corpus_dir, "*.txt"))
        for file_path in sorted(files):
            doc_chunks = self.chunk_document(file_path)
            chunks.extend(doc_chunks)
        return chunks
