# ---
# id: TEST-RETRIEVAL-0001
# title: Test Local Retrieval Scaffold
# type: TEST
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: retrieval
# repo: ovis-runtime
# path: tests/test_retrieval.py
# owner: Owen Vitae
# created: '2026-06-17'
# last_updated: '2026-06-17'
# registry: ovis-blueprint/REGISTRIES/entries/TEST-RETRIEVAL-0001.yaml
# module_id: MOD-RETRIEVAL-LAYER-0001
# module_slug: retrieval_layer
# system_id: SYS-RETRIEVAL-MEMORY-0001
# system_slug: retrieval_memory
# ---
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_retrieval import (  # noqa: E402
    InMemoryRetrievalIndex,
    RetrievalDocument,
    RetrievalQuery,
    chunk_document,
    lexical_score,
    tokenize,
)


def test_document_creation_preserves_source_and_metadata() -> None:
    document = RetrievalDocument(
        document_id="doc_001",
        source_ref="repo://README.md",
        title="Readme",
        text="Local retrieval only.",
        metadata={"kind": "doc"},
    )

    assert document.document_id == "doc_001"
    assert document.source_ref == "repo://README.md"
    assert document.metadata["kind"] == "doc"


def test_chunking_is_deterministic_and_preserves_word_spans() -> None:
    document = RetrievalDocument(
        document_id="doc_001",
        source_ref="repo://notes.md",
        text="alpha beta gamma delta epsilon",
    )

    chunks = chunk_document(document, max_words=3, overlap_words=1)

    assert chunks == (
        chunks[0],
        chunks[1],
    )
    assert [chunk.chunk_id for chunk in chunks] == ["doc_001:chunk_0000", "doc_001:chunk_0001"]
    assert [chunk.text for chunk in chunks] == ["alpha beta gamma", "gamma delta epsilon"]
    assert [(chunk.start_word, chunk.end_word) for chunk in chunks] == [(0, 3), (2, 5)]
    assert chunk_document(document, max_words=3, overlap_words=1) == chunks


@pytest.mark.parametrize(
    ("max_words", "overlap_words", "message"),
    [
        (0, 0, "max_words"),
        (3, -1, "overlap_words"),
        (3, 3, "less than max_words"),
    ],
)
def test_chunking_rejects_invalid_parameters(max_words: int, overlap_words: int, message: str) -> None:
    document = RetrievalDocument(document_id="doc_001", source_ref="repo://notes.md", text="alpha beta")

    with pytest.raises(ValueError, match=message):
        chunk_document(document, max_words=max_words, overlap_words=overlap_words)


def test_empty_document_produces_no_chunks() -> None:
    document = RetrievalDocument(document_id="doc_empty", source_ref="repo://empty.md", text=" \n\t ")

    assert chunk_document(document) == ()


def test_tokenize_and_score_are_case_insensitive_and_lexical() -> None:
    assert tokenize("Alpha, beta_BETA! 42") == ("alpha", "beta_beta", "42")
    assert lexical_score("alpha beta", "Alpha alpha gamma beta") == 3


def test_in_memory_index_adds_documents_and_returns_ranked_results() -> None:
    index = InMemoryRetrievalIndex(max_words=20)
    index.add_document(
        RetrievalDocument(
            document_id="doc_b",
            source_ref="repo://b.md",
            text="retrieval retrieval local deterministic",
        )
    )
    index.add_document(
        RetrievalDocument(
            document_id="doc_a",
            source_ref="repo://a.md",
            text="retrieval local",
        )
    )

    results = index.query("retrieval")

    assert [result.chunk.document_id for result in results] == ["doc_b", "doc_a"]
    assert [result.score for result in results] == [2, 1]


def test_query_limit_empty_query_and_non_matches_are_stable() -> None:
    index = InMemoryRetrievalIndex(max_words=20)
    index.add_document(RetrievalDocument(document_id="doc_001", source_ref="repo://a.md", text="alpha beta"))

    assert index.query("   ") == ()
    assert index.query(RetrievalQuery(text="alpha", limit=0)) == ()
    assert index.query("missing") == ()
    assert len(index.query(RetrievalQuery(text="alpha beta", limit=1))) == 1


def test_results_preserve_citations_and_chunk_source() -> None:
    index = InMemoryRetrievalIndex(max_words=3)
    index.add_document(
        RetrievalDocument(
            document_id="doc_001",
            source_ref="repo://guide.md",
            text="alpha beta gamma delta",
        )
    )

    result = index.query("beta")[0]

    assert result.citation.document_id == "doc_001"
    assert result.citation.source_ref == "repo://guide.md"
    assert result.citation.chunk_id == "doc_001:chunk_0000"
    assert result.citation.start_word == 0
    assert result.citation.end_word == 3
    assert result.citation.text == "alpha beta gamma"


def test_index_is_local_and_does_not_register_gateway_capabilities() -> None:
    import ovis_retrieval
    from ovis_tool_gateway import DEFAULT_CAPABILITY_REGISTRY

    assert ovis_retrieval.InMemoryRetrievalIndex is InMemoryRetrievalIndex
    assert DEFAULT_CAPABILITY_REGISTRY.get("retrieval.query") is None
