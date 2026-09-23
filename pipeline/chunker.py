import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter

from nexus.models import NormalizedDocument, Chunk

_encoder = tiktoken.get_encoding("cl100k_base")


def chunk_document(doc: NormalizedDocument) -> list[Chunk]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=64,
        length_function=lambda t: len(_encoder.encode(t)),
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    texts = splitter.split_text(doc.raw_text)
    chunks = []
    for i, text in enumerate(texts):
        if len(text.strip()) < 20:
            continue
        chunks.append(Chunk(
            chunk_id=f"{doc.doc_id}::chunk::{i}",
            doc_id=doc.doc_id,
            position=i,
            text=text,
            token_count=len(_encoder.encode(text)),
            source=doc.source,
            url=doc.url,
            title=doc.title,
            embedding=None,
        ))
    return chunks
