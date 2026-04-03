# IT Bidding Copilot (IT 租赁与服务投标助手)

🚀 **2026 年最先进的 Agentic AI 投标全流程辅助系统**

基于 Python + Streamlit + CrewAI + LangGraph 开发，专为政企 IT 基础设施服务（机房租赁、云服务、系统集成）打造的“拆标-编标-审标”一体化助手。

## ✨ 核心特性

- **🤖 多智能体协同 (CrewAI)**: 内置标书分析专家、商务合规管家、技术方案主笔，多角色协同作业。
- **🔄 闭环循环审标 (LangGraph)**: 自动红脸评审机制，`审查 -> 判定 -> 整改` 自动化闭环，规避废标风险。
- **📚 企业 RAG 知识库 (FAISS)**: 语义级搜索历史标书、资质文件，自动匹配最佳素材。
- **📋 智能 RFP 拆解**: 毫秒级提取废标条款、商务加分项、技术响应点。
- **📦 一键导出规范标书**: 自动生成符合招投标规范的 Word 文档（封面、目录、多级标题）。

## 🛠️ 技术栈

- **UI & Backend**: Streamlit (1.40+)
- **Agent Orchestrator**: CrewAI
- **Workflow State Machine**: LangGraph
- **Vector Database**: FAISS (RAG Support)
- **Document Model**: GPT-4o & Text-Embedding-3-Small
- **Word Processor**: python-docx

## 🚀 快速开始

### 1. 环境准备
使用 Python 3.10+ 环境。

```bash
git clone <your-repo-url>
cd it-bidding-copilot
pip install -r requirements.txt
```

### 2. 配置秘钥
复制 `.env.example` 为 `.env` 并填入您的 API Key：
```bash
cp .env.example .env
# 编辑 .env 填入 OPENAI_API_KEY
```

### 3. 启动应用
```bash
streamlit run app.py
```

## 📂 项目结构

```text
├── agents/             # CrewAI Agent 定义
├── workflows/          # LangGraph 与任务链定义
├── knowledge/          # 向量库与 Embedding 模块
├── utils/              # PDF、Word 处理工具类
├── pages/              # Streamlit 多页面 UI
├── data/               # 存储企业档案、向量索引 (Git 忽略)
├── app.py              # 主程序入口
└── config.py           # 全局配置
```

## 🤝 贡献说明

欢迎提交 Issue 或 Pull Request 来完善此项目。

## 📄 License

MIT License
