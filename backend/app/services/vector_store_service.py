import chromadb
from chromadb.config import Settings
from typing import List, Optional
import uuid

from app.core.config import CHROMA_DIR
from app.services.embedding_service import embed_texts, embed_query

# Chroma 集合名
COLLECTION_TASK = "task"
COLLECTION_LIBRARY = "library"

_chroma_client = None


def _get_client():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return _chroma_client


def _get_collection(name: str):
    client = _get_client()
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def add_blocks_to_task(blocks: List[dict], task_id: int):
    """将文本块加入任务临时索引"""
    if not blocks:
        return
    texts = [b["content"] for b in blocks]
    vectors = embed_texts(texts)
    ids = [f"task_{task_id}_{uuid.uuid4().hex[:12]}" for _ in blocks]
    metadatas = [
        {
            "report_id": str(b["report_id"]),
            "block_id": str(b.get("block_id", "")),
            "section_type": (b.get("section_type") or "")[:64],
        }
        for b in blocks
    ]
    coll = _get_collection(f"{COLLECTION_TASK}_{task_id}")
    coll.add(ids=ids, embeddings=vectors, metadatas=metadatas, documents=texts)


def add_blocks_to_library(blocks: List[dict]):
    """将文本块加入长期底库"""
    if not blocks:
        return
    texts = [b["content"] for b in blocks]
    vectors = embed_texts(texts)
    ids = [f"lib_{uuid.uuid4().hex}" for _ in blocks]
    metadatas = [
        {
            "report_id": str(b["report_id"]),
            "block_id": str(b.get("block_id", "")),
            "section_type": (b.get("section_type") or "")[:64],
        }
        for b in blocks
    ]
    coll = _get_collection(COLLECTION_LIBRARY)
    coll.add(ids=ids, embeddings=vectors, metadatas=metadatas, documents=texts)


def query_similar_task(
    query_vectors: List[List[float]],
    task_id: int,
    top_k: int = 10,
    exclude_report_ids: Optional[set] = None,
) -> List[dict]:
    """在任务索引中检索相似文本。返回列表中每项含 source_index 表示来自第几个查询向量"""
    exclude_report_ids = exclude_report_ids or set()
    coll_name = f"{COLLECTION_TASK}_{task_id}"
    try:
        coll = _get_client().get_collection(coll_name)
    except Exception:
        return []

    results = coll.query(
        query_embeddings=query_vectors,
        n_results=min(top_k * 2, 50),
        include=["documents", "metadatas", "distances"],
    )

    out = []
    seen = set()
    for i in range(len(query_vectors)):
        docs = results["documents"][i] if results["documents"] else []
        metas = results["metadatas"][i] if results["metadatas"] else []
        dists = results["distances"][i] if results["distances"] else []
        for doc, meta, dist in zip(docs, metas, dists):
            rid = int(meta.get("report_id", 0)) if meta.get("report_id") else None
            if rid and rid in exclude_report_ids:
                continue
            key = (i, meta.get("block_id"), rid)
            if key in seen:
                continue
            seen.add(key)
            similarity = 1.0 - dist if dist <= 2 else 0
            out.append({
                "source_index": i,
                "target_text": doc,
                "target_report_id": rid or 0,
                "target_block_id": meta.get("block_id"),
                "similarity": round(similarity, 4),
                "mode": "IN_CLASS",
            })
            if len(out) >= top_k:
                break
        if len(out) >= top_k:
            break
    return out[:top_k]


def query_similar_library(
    query_vectors: List[List[float]],
    top_k: int = 10,
) -> List[dict]:
    """在底库索引中检索相似文本"""
    coll = _get_collection(COLLECTION_LIBRARY)
    n = coll.count()
    if n == 0:
        return []

    results = coll.query(
        query_embeddings=query_vectors,
        n_results=min(top_k, n),
        include=["documents", "metadatas", "distances"],
    )

    out = []
    for i in range(len(query_vectors)):
        docs = results["documents"][i] if results["documents"] else []
        metas = results["metadatas"][i] if results["metadatas"] else []
        dists = results["distances"][i] if results["distances"] else []
        for doc, meta, dist in zip(docs, metas, dists):
            similarity = 1.0 - dist if dist <= 2 else 0
            rid = int(meta.get("report_id", 0)) if meta.get("report_id") else 0
            out.append({
                "source_index": i,
                "target_text": doc,
                "target_report_id": rid,
                "target_block_id": meta.get("block_id"),
                "similarity": round(similarity, 4),
                "mode": "HISTORY",
            })
    return out[:top_k]


def delete_task_collection(task_id: int):
    """删除任务临时索引"""
    try:
        _get_client().delete_collection(f"{COLLECTION_TASK}_{task_id}")
    except Exception:
        pass


def delete_report_from_library(report_id: int):
    """从底库删除某报告的所有向量"""
    coll = _get_collection(COLLECTION_LIBRARY)
    try:
        items = coll.get(where={"report_id": str(report_id)}, include=[])
    except Exception:
        items = {"ids": []}
    if items and items.get("ids"):
        coll.delete(ids=items["ids"])
