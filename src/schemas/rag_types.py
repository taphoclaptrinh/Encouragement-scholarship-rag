"""
YÊU CẦU TUẦN W1 & W5: Dataclass định nghĩa cấu trúc Chunk, SearchResult, UsageMetric
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class DocMetadata:
    doc_id: str
    title: str
    date: str
    version: str
    owner: str
    status: str
    faculty: Optional[str] = None

@dataclass
class Chunk:
    chunk_id: str
    text: str
    metadata: DocMetadata
    token_count: int = 0

@dataclass
class SearchResult:
    chunk: Chunk
    score: float
    retrieval_mode: str  # "dense", "bm25", "hybrid"

@dataclass
class UsageMetric:
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    max_prompt_tokens: int = 0
    latency_seconds: float = 0.0

    def add(self, prompt: int, completion: int, latency: float = 0.0):
        self.calls += 1
        self.prompt_tokens += prompt
        self.completion_tokens += completion
        self.total_tokens += (prompt + completion)
        if prompt > self.max_prompt_tokens:
            self.max_prompt_tokens = prompt
        self.latency_seconds += latency
