import pytest
from datetime import datetime, timezone
from nexus.models import NormalizedDocument
from nexus.db.queries import upsert_document, get_unembedded_documents
from nexus.db.connection import execute


@pytest.fixture(autouse=True)
def clean_test_docs():
    """Wipe the test document before and after each db test for isolation."""
    execute("DELETE FROM documents WHERE doc_id LIKE 'test::%';")
    yield
    execute("DELETE FROM documents WHERE doc_id LIKE 'test::%';")


def make_doc(updated_at=None, doc_id="test::issue::1"):
    return NormalizedDocument(
        source="test",
        source_native_id="1",
        doc_type="issue",
        url="https://example.com/1",
        title="Test doc",
        raw_text="Hello world content here.",
        updated_at=updated_at or datetime(2024, 1, 1, tzinfo=timezone.utc),
        metadata={},
        doc_id=doc_id,
    )


def test_upsert_document_insert():
    doc = make_doc()
    upsert_document(doc)
    rows = execute("SELECT doc_id FROM documents WHERE doc_id = %s;", (doc.doc_id,))
    assert rows and rows[0][0] == doc.doc_id


def test_upsert_document_update_resets_embedded_at():
    doc = make_doc(updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc))
    upsert_document(doc)
    execute(
        "UPDATE documents SET embedded_at = NOW() WHERE doc_id = %s;",
        (doc.doc_id,),
    )
    newer_doc = make_doc(updated_at=datetime(2024, 6, 1, tzinfo=timezone.utc))
    upsert_document(newer_doc)
    rows = execute("SELECT embedded_at FROM documents WHERE doc_id = %s;", (doc.doc_id,))
    assert rows[0][0] is None


def test_upsert_document_no_update_if_older():
    doc = make_doc(updated_at=datetime(2024, 6, 1, tzinfo=timezone.utc))
    upsert_document(doc)
    execute(
        "UPDATE documents SET title = 'Original' WHERE doc_id = %s;",
        (doc.doc_id,),
    )
    older_doc = make_doc(updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc))
    older_doc.title = "Should not overwrite"
    upsert_document(older_doc)
    rows = execute("SELECT title FROM documents WHERE doc_id = %s;", (doc.doc_id,))
    assert rows[0][0] == "Original"
