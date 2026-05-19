import os
from typing import List

import torch
from langchain_community.embeddings import HuggingFaceEmbeddings
from app.core.config import CHROMA_DIR

# 如果模型已缓存到本地，使用离线模式避免在后台线程中发起网络请求
# （网络请求在 Starlette BackgroundTask 线程中会因 httpx client 关闭而失败）
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# 使用小型多语言模型，支持中文，首次运行会下载约 400MB
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

_embedding_model = None


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": _DEVICE},
        )
    return _embedding_model


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
