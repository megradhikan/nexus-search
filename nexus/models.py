from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import numpy as np


@dataclass
class RawDocument:
    source: str
    source_native_id: str
    doc_type: str
    url: str
    raw_text: str
    updated_at: datetime
    title: Optional[str] = None
    created_at: Optional[datetime] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class NormalizedDocument(RawDocument):
    doc_id: str = ""


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    position: int
    text: str
    token_count: int
    source: str
    url: str
    title: Optional[str] = None
    embedding: Optional[np.ndarray] = None
