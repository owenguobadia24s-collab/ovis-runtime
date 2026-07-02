"""Adapters from chat ingestion records to local refinement chunks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ovis_chat_ingestion import ChatSegment, ChatSource, ImportManifest
from ovis_retrieval import RetrievalChunk, RetrievalDocument, chunk_document, tokenize


REFINEMENT_SEGMENT_VERSION = "refinement-segment-v0"
REFINEMENT_CHUNK_VERSION = "refinement-chunk-v0"


@dataclass(frozen=True)
class RefinementSegment:
    segment_id: str
    source_id: str
    message_id: str | None
    speaker: str
    text: str
    start_index: int
    end_index: int
    segment_index: int
    source_path: str
    manifest_ref: str | None = None


@dataclass(frozen=True)
class RefinementChunk:
    chunk_id: str
    segment_id: str
    source_id: str
    message_id: str | None
    speaker: str
    text: str
    chunk_index: int
    start_word: int
    end_word: int
    normalized_terms: tuple[str, ...]
    source_path: str
    manifest_ref: str | None = None


def adapt_chat_segments(
    source: ChatSource,
    segments: Iterable[ChatSegment],
    *,
    manifest: ImportManifest | None = None,
) -> tuple[RefinementSegment, ...]:
    manifest_ref = manifest.raw_path if manifest is not None else None
    adapted: list[RefinementSegment] = []
    for segment in segments:
        if segment.source_id != source.source_id:
            raise ValueError("segment source_id does not match ChatSource source_id")
        adapted.append(
            RefinementSegment(
                segment_id=segment.segment_id,
                source_id=segment.source_id,
                message_id=segment.message_id,
                speaker=segment.speaker,
                text=segment.text,
                start_index=segment.start_index,
                end_index=segment.end_index,
                segment_index=segment.segment_index,
                source_path=source.path,
                manifest_ref=manifest_ref,
            )
        )
    return tuple(adapted)


def to_retrieval_document(segment: RefinementSegment) -> RetrievalDocument:
    return RetrievalDocument(
        document_id=segment.segment_id,
        source_ref=segment.source_path,
        text=segment.text,
        title=None,
        metadata={
            "source_id": segment.source_id,
            "message_id": segment.message_id,
            "speaker": segment.speaker,
            "segment_index": segment.segment_index,
            "manifest_ref": segment.manifest_ref,
            "refinement_segment_version": REFINEMENT_SEGMENT_VERSION,
        },
    )


def to_retrieval_chunks(
    segment: RefinementSegment,
    *,
    max_words: int = 120,
    overlap_words: int = 0,
) -> tuple[RetrievalChunk, ...]:
    return chunk_document(
        to_retrieval_document(segment),
        max_words=max_words,
        overlap_words=overlap_words,
    )


def chunk_refinement_segment(
    segment: RefinementSegment,
    *,
    max_words: int = 120,
    overlap_words: int = 0,
) -> tuple[RefinementChunk, ...]:
    retrieval_chunks = to_retrieval_chunks(segment, max_words=max_words, overlap_words=overlap_words)
    return tuple(
        RefinementChunk(
            chunk_id=retrieval_chunk.chunk_id,
            segment_id=segment.segment_id,
            source_id=segment.source_id,
            message_id=segment.message_id,
            speaker=segment.speaker,
            text=retrieval_chunk.text,
            chunk_index=index,
            start_word=retrieval_chunk.start_word,
            end_word=retrieval_chunk.end_word,
            normalized_terms=tokenize(retrieval_chunk.text),
            source_path=segment.source_path,
            manifest_ref=segment.manifest_ref,
        )
        for index, retrieval_chunk in enumerate(retrieval_chunks)
    )


def chunk_refinement_segments(
    segments: Iterable[RefinementSegment],
    *,
    max_words: int = 120,
    overlap_words: int = 0,
) -> tuple[RefinementChunk, ...]:
    chunks: list[RefinementChunk] = []
    for segment in segments:
        chunks.extend(chunk_refinement_segment(segment, max_words=max_words, overlap_words=overlap_words))
    return tuple(chunks)
