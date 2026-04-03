# IT Bidding Copilot (IT 租赁与服务投标助手)

🚀 **2026 年最先进的 Agentic AI 投标全流程辅助系统**

基于 Python + Streamlit + CrewAI + LangGraph 开发，专为政企 IT 基础设施服务（机房租赁、云服务、系统集成）打造的“拆标-编标-审标”一体化助手。通过多智能体协作与闭环审标机制，大幅提升投标文件的质量与合规性。

## ✨ 核心特性

- **🤖 多智能体协同 (CrewAI)**: 内置标书分析专家、商务合规管家、技术方案主笔，多角色协同作业。
- **🔄 闭环循环审标 (LangGraph)**: 自动红脸评审机制，`审查 -> 判定 -> 整改` 自动化闭环，规避废标风险。
- **📚 企业 RAG 知识库 (FAISS)**: 语义级搜索历史标书、资质文件，自动匹配最佳素材。
- **📋 智能 RFP 拆解**: 毫秒级提取废标条款、商务加分项、技术响应点。
- **📦 一键导出规范标书**: 自动生成符合招投标规范的 Word 文档（封面、目录、多级标题）。

## 🤖 智能体说明 (Agent Roles)

本系统采用 CrewAI 框架，构建了四个核心 Agent 角色，分工明确：

1. **需求统筹与拆标专家 (Bid Analyst)**:
   - **目标**: 全面拆解招标文件，动态提取核心采购需求、商务门槛、废标条款及评分标准。
   - **职责**: 确保后续编标环节零遗漏、零误读，识别潜在雷区。

2. **商务合规管家 (Commercial Specialist)**:
   - **目标**: 撰写《商务响应表》，精准匹配并梳理公司商务资质与合规材料。
   - **职责**: 标注证书编号、有效期，识别缺失资质，绝不捏造信息。

3. **首席技术主笔 (Technical Architect)**:
   - **目标**: 结合知识库与 RFP 要求，撰写高质量的《技术与服务响应方案》。
   - **职责**: 逐条响应技术参数，提供具体的落地方案，打磨 SLA 服务保障与应急预案。

4. **红脸评标组长 (Chief Reviewer)**:
   - **目标**: 对照废标条款和评分表，进行“吹毛求疵”式的交叉审查。
   - **职责**: 输出结构化《整改意见》，标注问题等级（废标风险/扣分风险/优化建议）。

## 🔄 智能审标工作流 (LangGraph Review Workflow)

系统利用 LangGraph 构建了一个循环审标回路，支持 `Review → Decide → Revise` 自动化流程，最多可进行 3 轮迭代：

- **Review 节点**: 模拟评委视角，对生成的标书内容进行严苛审计。
- **Decide 路由**: 判断标书是否通过。若有严重废标项或未达标，则指向 Revise 节点。
- **Revise 节点**: 根据审查意见，自动调整标书内容，确保 100% 响应 RFP 要求。

## 🛠️ 技术栈

- **前端/后端**: [Streamlit](https://streamlit.io/) (1.40+)
- **Agent 编排**: [CrewAI](https://github.com/joaomador/crewAI)
- **状态机/流**: [LangGraph](https://github.com/langchain-ai/langgraph)
- **向量数据库**: FAISS (支持 RAG)
- **大模型**: GPT-4o & Text-Embedding-3-Small
- **文档处理**: python-docx

## 🚀 快速开始

### 1. 环境准备
使用 Python 3.10+ 环境。

```bash
git clone https://github.com/1154761334/it-bidding-copilot.git
cd it-bidding-copilot
pip install -r requirements.txt
```

### 2. 配置秘钥
在项目根目录创建 `.env` 文件并填入您的 API Key：
```bash
OPENAI_API_KEY=your_openai_api_key_here
# 其他配置（如需）
```

### 3. 启动应用
```bash
streamlit run app.py
```

## 📂 项目结构

```text
├── agents/             # CrewAI Agent 定义 (Analyst, Specialist, Architect, Reviewer)
├── workflows/          # LangGraph 循环状态机与任务链定义
├── knowledge/          # 向量库构建、Embedding 与 RAG 模块
├── utils/              # PDF 解析、Word 导出、RFP 提取等工具类
├── pages/              # Streamlit 多页面 UI (企业档案、RFP 拆解、协作编标、循环审标等)
├── data/               # 存储企业档案、向量索引 (Git 已忽略)
├── templates/          # 标书 Word 模板
├── app.py              # 主程序入口（侧边栏导航）
└── config.py           # 全局 LLM 设置与业务参数配置
```

## 📄 License

MIT License
