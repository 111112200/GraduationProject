<div align="center">

# 🛡️ 实验报告智能语义查重与溯源分析系统
### (Academic Report Plagiarism Detection & Traceability System)

[![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=24&pause=1000&color=00F0FF&center=true&vCenter=true&width=800&lines=基于+LangChain+的智能语义分析;文档结构智能解析与动态切片;多维向量空间深度查重引擎;全链路溯源与可视化验证;构建纯净公平的学术级生态)](https://git.io/typing-svg)

<p align="center">
  <img src="https://img.shields.io/badge/version-v1.2.5-00F0FF?style=for-the-badge&logo=github" alt="version">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vuedotjs&logoColor=4FC08D" alt="Vue3">
  <img src="https://img.shields.io/badge/ChromaDB-FF4F00?style=for-the-badge&logo=chroma&logoColor=white" alt="ChromaDB">
</p>

**基于 Vue3 + FastAPI + LangChain 构建的极简黑科技风语义查重引擎，让学术抄袭无所遁形。**

</div>

---

## ⚡ 核心架构与功能 (Core Features)

- **📄 智能解析与动态切片 (LangChain)**
  支持 Word/PDF 等大规模实验报告的高效解析，结合上下文语义进行智能 Chunking，在保证切片效率的同时精准保留核心文本的逻辑完整性。
- **🧠 向量化深度查重引擎 (ChromaDB)**
  引入高维向量检索技术（Vector Embeddings）与本地 ChromaDB 向量数据库，突破传统基于字词比对的查重限制，实现基于“深层语义理解”的精准检测。
- **🔗 全链路溯源与可视化分析**
  强大的后台异步任务队列引擎，支持查重结果的精准反向映射回切，提供直观的**左右双屏比对视图**与学术级客观判定证据，一目了然。
- **📊 全生命周期任务管控**
  涵盖基础数据（课程/班级/实验）管理、自定义底库（语料靶标库）构建、查重任务自动化分发，到最终多维度查重报告导出的全流程闭环管控。



## 🛠️ 技术栈 (Tech Stack)

<div align="center">
  <a href="https://skillicons.dev">
    <img src="https://skillicons.dev/icons?i=vue,vite,js,html,css,python,fastapi,sqlite,git&theme=dark" alt="Skill Icons"/>
  </a>
</div>

<br>

<details>
<summary><b>🔥 点击展开详细技术架构</b></summary>

- **前端 (Frontend):** 
  - **框架:** Vue 3, Vite, Vue-Router
  - **UI 风格:** 采用原生 CSS 深度定制的极简极客风、沉浸式卡片 UI，拒绝臃肿的第三方组件库。
- **后端 (Backend):** 
  - **核心框架:** Python 3.10+, FastAPI (高性能异步 REST API)
  - **数据存储:** SQLite (关系型元数据存储)
- **AI 算法引擎 (Core Engine):** 
  - **语义分析:** LangChain
  - **向量数据库:** ChromaDB
  - **模型架构:** 本地预加载 Embedding 向量模型，自定义 Document Parser 处理器
</details>

## 🚀 快速启动 (Quick Start)

### 1. 环境准备
确保您的系统已安装 [Python 3.10+](https://www.python.org/) 和 [Node.js 18+](https://nodejs.org/)。

### 2. 克隆项目
```bash
git clone https://github.com/111112200/GraduationProject.git
cd GraduationProject
```

### 3. 后端服务运行
```bash
cd backend
# 推荐使用虚拟环境进行隔离
python -m venv venv
source venv/bin/activate  # Windows 用户: venv\Scripts\activate
pip install -r requirements.txt

# 启动核心 API 服务（附带 SQLite 自动建表与基础数据初始化）
uvicorn app.main:app --reload
```

### 4. 前端界面启动
```bash
cd frontend
npm install
npm run dev
```
> 🎉 此时可通过浏览器访问 `http://localhost:5173` 体验极简黑科技界面！

## 🎯 核心应用场景

- 👨‍🏫 **高校教务评估**：针对计算机/理工科学生提交的雷同实验代码和报告，进行批量高维语义查重，显著提升教务评估的公平性。
- 👩‍🎓 **学生自查助手**：帮助学生在提交作业前自查原创率，规范学术引用的良好习惯。
- 💻 **开发者参考范例**：为您提供一套完整的 **Vue3 前端 + FastAPI 后端 + LangChain 语义检索** 的轻量级实战脚手架。

## 🤝 贡献与支持

欢迎提交 Issues 和 Pull Requests！如果您觉得这个毕业设计/项目为您提供了优秀的思路和代码参考，请给一个 ⭐️ **Star** 支持一下！

<div align="center">

*Empowering Academic Integrity with Tech | Designed with ❤️*

</div>
