import chromadb
from chromadb.config import Settings
from typing import List, Optional
import uuid

from app.core.config import CHROMA_DIR
from app.services.embedding_service import embed_texts, embed_query

# Chroma 集合名
COLLECTION_TASK = "task"
COLLECTION_LIBRARY_PREFIX = "library_user"

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


def _library_collection_name(user_id: int) -> str:
    """返回用户专属的长期底库集合名。"""
    return f"{COLLECTION_LIBRARY_PREFIX}_{user_id}"


def _get_library_collection(user_id: int):
    return _get_collection(_library_collection_name(user_id))


def _get_existing_library_collection(user_id: int):
    try:
        return _get_client().get_collection(_library_collection_name(user_id))
    except Exception:
        return None


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


def add_blocks_to_library(blocks: List[dict], user_id: int):
    """将文本块加入用户专属的长期底库。"""
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
            "user_id": str(user_id),
        }
        for b in blocks
    ]
    coll = _get_library_collection(user_id)
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
            block_id = meta.get("block_id")
            block_id = int(block_id) if block_id not in (None, "") else None
            if rid and rid in exclude_report_ids:
                continue
            key = (i, block_id, rid)
            if key in seen:
                continue
            seen.add(key)
            similarity = 1.0 - dist if dist <= 2 else 0
            out.append({
                "source_index": i,
                "target_text": doc,
                "target_report_id": rid or 0,
                "target_block_id": block_id,
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
    user_id: int,
    top_k: int = 10,
) -> List[dict]:
    """仅在当前用户的底库索引中检索相似文本。"""
    coll = _get_library_collection(user_id)
    n = coll.count()
    if n == 0:
        return []

    results = coll.query(
        query_embeddings=query_vectors,
        n_results=min(top_k, n),
        where={"user_id": str(user_id)},
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
            block_id = meta.get("block_id")
            block_id = int(block_id) if block_id not in (None, "") else None
            out.append({
                "source_index": i,
                "target_text": doc,
                "target_report_id": rid,
                "target_block_id": block_id,
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


def is_report_indexed_in_library(report_id: int, user_id: int) -> bool:
    """检查报告是否已经写入用户专属底库索引。"""
    coll = _get_existing_library_collection(user_id)
    if coll is None:
        return False
    try:
        items = coll.get(
            where={"report_id": str(report_id)},
            include=[],
        )
    except Exception:
        return False
    return bool(items and items.get("ids"))


def delete_report_from_library(report_id: int, user_id: int):
    """从用户专属底库删除某报告的所有向量。"""
    coll = _get_existing_library_collection(user_id)
    if coll is None:
        return
    try:
        items = coll.get(
            where={"report_id": str(report_id)},
            include=[],
        )
    except Exception:
        items = {"ids": []}
    if items and items.get("ids"):
        coll.delete(ids=items["ids"])
