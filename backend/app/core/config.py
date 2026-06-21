import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
CHROMA_DIR = BASE_DIR / "chroma_db"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'app.db'}")
MAX_FILE_SIZE_MB = 20
ALLOWED_EXTENSIONS = {".docx"}

# 传统的后备关键字匹配
TARGET_SECTION_KEYWORDS = [
    "设计思路", "心得体会", "实验总结", "个人体会", "总结", "感悟", "体会", "收获", 
    "架构设计", "方案设计", "总体方案", "模块设计", "思考题"
]
# 需排除的模板段落关键字
TEMPLATE_NOISE_KEYWORDS = ["实验目的", "实验原理", "实验环境", "实验步骤", "实验内容", "实验要求"]

# ===== 语义抓取配置 (智能提取) =====
# 预设的概念锚点文本，将会被转为高维向量和未知标题进行余弦碰撞
SEMANTIC_ANCHORS_DESIGN = ["系统设计思路", "总体架构设计方案", "软件模块核心构思"]
SEMANTIC_ANCHORS_REFLECTION = ["本次实验的心得体会", "个人总结与反思", "实训感悟与收获", "对课程设计的深刻思考"]
# 语义相似度判决阈值 (超过该值即被认为是该分类)
HEADING_SIMILARITY_THRESHOLD = 0.65
# ==================================

# 相似度阈值默认值
DEFAULT_HIGH_RISK_THRESHOLD = 0.8
DEFAULT_SIMILAR_THRESHOLD = 0.5

# 文本分块参数
CHUNK_SIZE = 200
CHUNK_OVERLAP = 80
# ===== JWT Authentication =====
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-graduation-project-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
