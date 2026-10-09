"""
MODULE CHUNKING TÀI LIỆU QUY CHẾ (YÊU CẦU TUẦN W3)
Yêu cầu:
- Đọc các tài liệu quy chế từ thư mục data/corpus/*.txt
- Bóc tách phần YAML frontmatter (doc_id, title, version, owner, status)
- Chia văn bản thành các Chunk ngữ nghĩa (theo Điều khoản / quy định)
- Gắn metadata header vào từng chunk
- Tham khảo tài liệu: data/chunking_strategy.md
"""
import os
import glob
from typing import List
from ..schemas.rag_types import DocMetadata, Chunk

class DocumentChunker:
    def __init__(self, corpus_dir: str):
        self.corpus_dir = corpus_dir

    def load_and_chunk_all(self) -> List[Chunk]:
        """
        TODO (Thành viên phụ trách RAG):
        1. Duyệt qua tất cả các file .txt trong self.corpus_dir.
        2. Bóc tách frontmatter để tạo đối tượng DocMetadata.
        3. Tách nội dung theo ranh giới điều khoản (ví dụ regex: r'\\n(?=Điều \\d+)').
        4. Tạo danh sách các đối tượng Chunk kèm metadata.
        """
        chunks: List[Chunk] = []

        # TODO: Viết code đọc file và chunking tại đây

        return chunks
