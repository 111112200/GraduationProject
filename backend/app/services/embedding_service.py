import os
from typing import List

from app.core.config import CHROMA_DIR

# 如果模型已缓存到本地，使用离线模式避免在后台线程中发起网络请求
# （网络请求在 Starlette BackgroundTask 线程中会因 httpx client 关闭而失败）
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

# 使用小型多语言模型，支持中文，首次运行会下载约 400MB
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

_embedding_model = None
_embedding_tokenizer = None
_tokenizer_unavailable = False


def _get_device() -> str:
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        # Keep heavyweight ML imports lazy so document parsing and unit tests do
        # not fail merely because the optional model runtime is unavailable.
        from langchain_community.embeddings import HuggingFaceEmbeddings

        _embedding_model = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": _get_device()},
        )
    return _embedding_model


def get_embedding_tokenizer():
    """Load the embedding tokenizer without downloading at request time."""
    global _embedding_tokenizer, _tokenizer_unavailable
    if _embedding_tokenizer is not None or _tokenizer_unavailable:
        return _embedding_tokenizer
    try:
        from transformers import AutoTokenizer

        _embedding_tokenizer = AutoTokenizer.from_pretrained(
            EMBEDDING_MODEL,
            local_files_only=True,
        )
    except Exception:
        # A character fallback keeps the splitter deterministic in minimal
        # installations. Production startup should still preload the model and
        # expose the dependency error rather than silently scoring with it.
        _tokenizer_unavailable = True
    return _embedding_tokenizer


def count_embedding_tokens(text: str) -> int:
    tokenizer = get_embedding_tokenizer()
    if tokenizer is None:
        return len(text or "")
    try:
        return len(tokenizer.encode(text or "", add_special_tokens=True, truncation=False))
    except Exception:
        return len(text or "")


def preload_model():
    """在应用启动时预加载模型，避免在后台线程中首次加载时出现网络问题"""
    print("[Embedding] 预加载 embedding 模型...")
    get_embedding_model()
    print("[Embedding] 模型加载完成。")


def embed_texts(texts: List[str]) -> List[List[float]]:
    """将文本列表转为向量列表"""
    if not texts:
        return []
    model = get_embedding_model()
    return model.embed_documents(texts)


def embed_query(text: str) -> List[float]:
    """单条查询文本转向量"""
    model = get_embedding_model()
    return model.embed_query(text)
