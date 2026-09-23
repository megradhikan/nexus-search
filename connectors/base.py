from abc import ABC, abstractmethod
from datetime import datetime

from nexus.models import RawDocument, NormalizedDocument


class BaseConnector(ABC):
    @abstractmethod
    def fetch_all(self) -> list[NormalizedDocument]:
        ...

    @abstractmethod
    def fetch_updated_since(self, since: datetime) -> list[NormalizedDocument]:
        ...

    def normalize(self, raw: RawDocument) -> NormalizedDocument:
        doc_id = f"{raw.source}::{raw.doc_type}::{raw.source_native_id}"
        return NormalizedDocument(
            source=raw.source,
            source_native_id=raw.source_native_id,
            doc_type=raw.doc_type,
            url=raw.url,
            title=raw.title,
            raw_text=raw.raw_text,
            created_at=raw.created_at,
            updated_at=raw.updated_at,
            metadata=raw.metadata,
            doc_id=doc_id,
        )
