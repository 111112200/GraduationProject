from typing import List, Optional

import chromadb

from app.core.config import CHROMA_DIR, CHUNK_VERSION
from app.services.embedding_service import embed_texts


# Versioned names prevent old raw-block embeddings from being mixed with the
# token-aware chunk format. Legacy names are retained only for cleanup.
COLLECTION_TASK = f"task_{CHUNK_VERSION}"
COLLECTION_LIBRARY_PREFIX = f"library_user_{CHUNK_VERSION}"
LEGACY_COLLECTION_TASK = "task"
LEGACY_COLLECTION_LIBRARY_PREFIX = "library_user"

_chroma_client = None


def _get_client():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return _chroma_client


def _get_collection(name: str):
    return _get_client().get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def _library_collection_name(user_id: int, legacy: bool = False) -> str:
    prefix = LEGACY_COLLECTION_LIBRARY_PREFIX if legacy else COLLECTION_LIBRARY_PREFIX
    return f"{prefix}_{user_id}"


def _get_library_collection(user_id: int):
    return _get_collection(_library_collection_name(user_id))


def _get_existing_collection(name: str):
    try:
        return _get_client().get_collection(name)
    except Exception:
        return None


def _get_existing_library_collection(user_id: int, legacy: bool = False):
    return _get_existing_collection(_library_collection_name(user_id, legacy=legacy))


def _as_int(value):
    try:
        return int(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _metadata_for_chunk(chunk: dict, user_id: Optional[int] = None) -> dict:
    metadata = {
        "report_id": str(chunk.get("report_id") or ""),
        "block_id": str(chunk.get("block_id") or ""),
        "section_type": (chunk.get("section_type") or "GENERAL")[:64],
        "section_title": (chunk.get("section_title") or "")[:256],
        "source_kind": (chunk.get("source_kind") or "")[:32],
        "source_location": str(chunk.get("source_location") or "")[:512],
        "start_char": str(chunk.get("start_char") if chunk.get("start_char") is not None else ""),
        "end_char": str(chunk.get("end_char") if chunk.get("end_char") is not None else ""),
        "chunk_version": str(chunk.get("chunk_version") or CHUNK_VERSION),
        "is_fallback": "1" if chunk.get("is_fallback") else "0",
    }
    if user_id is not None:
        metadata["user_id"] = str(user_id)
    return metadata


def add_blocks_to_task(blocks: List[dict], task_id: int):
    """Add canonical chunks to a versioned temporary task index."""
    if not blocks:
        return
    texts = [b["content"] for b in blocks]
    vectors = embed_texts(texts)
    ids = [f"task_{task_id}_{b.get('chunk_id') or index}" for index, b in enumerate(blocks)]
    coll = _get_collection(f"{COLLECTION_TASK}_{task_id}")
    coll.add(
        ids=ids,
        embeddings=vectors,
        metadatas=[_metadata_for_chunk(b) for b in blocks],
        documents=texts,
    )


def add_blocks_to_library(blocks: List[dict], user_id: int):
    """Add canonical chunks to the user's versioned long-term index."""
    if not blocks:
        return
    texts = [b["content"] for b in blocks]
    vectors = embed_texts(texts)
    ids = [f"lib_{b.get('chunk_id') or index}" for index, b in enumerate(blocks)]
    coll = _get_library_collection(user_id)
    coll.add(
        ids=ids,
        embeddings=vectors,
        metadatas=[_metadata_for_chunk(b, user_id=user_id) for b in blocks],
        documents=texts,
    )


def _query_collection(
    coll,
    query_vectors: List[List[float]],
    top_k: int,
    mode: str,
    exclude_report_ids: Optional[set] = None,
    where: Optional[dict] = None,
) -> List[dict]:
    if not query_vectors or top_k <= 0 or coll.count() == 0:
        return []
    exclude_report_ids = exclude_report_ids or set()
    n_results = min(max(top_k * 2, top_k), 50)
    query_kwargs = {
        "query_embeddings": query_vectors,
        "n_results": min(n_results, coll.count()),
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        query_kwargs["where"] = where
    results = coll.query(**query_kwargs)

    out = []
    seen = set()
    for source_index in range(len(query_vectors)):
        docs = results.get("documents", [])[source_index] if results.get("documents") else []
        metas = results.get("metadatas", [])[source_index] if results.get("metadatas") else []
        distances = results.get("distances", [])[source_index] if results.get("distances") else []
        for doc, metadata, distance in zip(docs, metas, distances):
            report_id = _as_int(metadata.get("report_id"))
            if report_id is not None and report_id in exclude_report_ids:
                continue
            block_id = _as_int(metadata.get("block_id"))
            start_char = _as_int(metadata.get("start_char"))
            end_char = _as_int(metadata.get("end_char"))
            distance = float(distance)
            similarity = max(0.0, min(1.0, 1.0 - distance)) if distance <= 2 else 0.0
            key = (source_index, report_id, block_id, start_char, end_char)
            if key in seen:
                continue
            seen.add(key)
            out.append(
                {
                    "source_index": source_index,
                    "target_text": doc,
                    "target_report_id": report_id or 0,
                    "target_block_id": block_id,
                    "target_start": start_char,
                    "target_end": end_char,
                    "similarity": round(similarity, 4),
                    "mode": mode,
                }
            )
    out.sort(
        key=lambda match: (
            -match["similarity"],
            match["source_index"],
            match["target_report_id"],
            match["target_block_id"] or -1,
            match["target_start"] if match["target_start"] is not None else -1,
            match["target_end"] if match["target_end"] is not None else -1,
        )
    )
    return out[:top_k]


def query_similar_task(
    query_vectors: List[List[float]],
    task_id: int,
    top_k: int = 10,
    exclude_report_ids: Optional[set] = None,
) -> List[dict]:
    """Return the globally highest-ranked task matches across source chunks."""
    coll = _get_existing_collection(f"{COLLECTION_TASK}_{task_id}")
    if coll is None:
        return []
    return _query_collection(coll, query_vectors, top_k, "IN_CLASS", exclude_report_ids)


def query_similar_library(
    query_vectors: List[List[float]],
    user_id: int,
    top_k: int = 10,
    exclude_report_ids: Optional[set] = None,
) -> List[dict]:
    """Return the globally highest-ranked library matches across source chunks."""
    coll = _get_existing_library_collection(user_id)
    if coll is None:
        return []
    return _query_collection(
        coll,
        query_vectors,
        top_k,
        "HISTORY",
        exclude_report_ids=exclude_report_ids,
        where={"user_id": str(user_id)},
    )


def delete_task_collection(task_id: int):
    """Delete both current and legacy temporary collections."""
    for name in (f"{COLLECTION_TASK}_{task_id}", f"{LEGACY_COLLECTION_TASK}_{task_id}"):
        try:
            _get_client().delete_collection(name)
        except Exception:
            pass


def is_report_indexed_in_library(report_id: int, user_id: int) -> bool:
    """Check whether the report has chunks in the current index version."""
    coll = _get_existing_library_collection(user_id)
    if coll is None:
        return False
    try:
        items = coll.get(where={"report_id": str(report_id)}, include=[])
    except Exception:
        return False
    return bool(items and items.get("ids"))


def delete_report_from_library(report_id: int, user_id: int):
    """Delete a report from current and legacy user collections."""
    for coll in (
        _get_existing_library_collection(user_id),
        _get_existing_library_collection(user_id, legacy=True),
    ):
        if coll is None:
            continue
        try:
            items = coll.get(where={"report_id": str(report_id)}, include=[])
        except Exception:
            items = {"ids": []}
        if items and items.get("ids"):
            coll.delete(ids=items["ids"])
