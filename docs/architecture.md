# 架构说明

## 目标边界

IT Bidding Copilot 的当前主线是一个可本地运行、可验收、可追溯的投标工作台。系统围绕投标生产的关键风险设计：硬性条款遗漏、评分项材料无法定位、商务响应未经签核、合同义务被模型扩写、历史材料被误当成当前事实。

当前架构刻意保持窄边界：

- `/bid` 是主产品入口。
- FastAPI workbench API 是前后端主合约。
- LangGraph LLM workflow 保留为 legacy/增强路径。
- 证据检索允许 embedding，也必须支持无外部 key 的关键词降级。
- 私有材料和运行态项目不进入 Git。

## 分层视图

```text
UI Layer
  frontend/src/features/Bidding/*
  frontend/src/store/bidding/*
  frontend/src/services/bidding.ts

API Layer
  backend/src/main.py
  backend/src/api_workbench.py

Domain Layer
  tender parsing
  plan generation
  response matrix
  evidence trace
  draft generation
  review and handoff

Retrieval Layer
  backend/src/evidence.py
  backend/src/ingest.py
  PostgreSQL + pgvector
  keyword fallback

Private Knowledge Layer
  vault/
  vault-template/
  obsidian_vault_pipeline/
  Bidding-agent/

Runtime State
  workspaces/api-projects/<project-id>/
```

## 前端架构

前端基于 vendored LobeHub/LobeChat 工作区扩展，核心定制集中在 `/bid`。

- `frontend/src/business/client/BusinessDesktopRoutes.tsx` 注册业务路由。
- `frontend/src/features/Bidding/BiddingWorkbench.tsx` 组合项目列表、流程按钮、Tab 与 Artifact 视图。
- `frontend/src/features/Bidding/*Tab.tsx` 分拆文件、计划、执行、评审、草稿和证据视图。
- `frontend/src/services/bidding.ts` 是 FastAPI client，集中定义 wire contract。
- `frontend/src/store/bidding/index.ts` 使用 Zustand 管理健康检查、项目、Artifact、证据和 workflow action。
- `frontend/scripts/bidding/*` 是 `/bid` 路由 smoke、生产路由 storage-state 和 CI preflight 保护。

前端只做状态展示和用户操作编排，不直接生成投标内容。

## 后端架构

后端主入口是 `backend/src/main.py`。

- `config.py`：集中读取 `.env`，解析仓库相对路径、数据库、LLM、embedding 和本地工作区。
- `main.py`：注册 FastAPI、健康检查、workbench endpoints 和 legacy workflow endpoints。
- `api_workbench.py`：当前 `/bid` 主线，负责项目状态、Artifact 生成、材料包、证据追溯、Review 和 Demo。
- `parser.py`：使用 MarkItDown 与 PyMuPDF4LLM 将 Office/PDF 转为 Markdown。
- `evidence.py`：embedding 检索和关键词 fallback。
- `ingest.py`：把 Vault Markdown 切块、分类、抽取图片和页码提示并写入 Evidence Store。
- `workflow.py`：legacy LangGraph 路径，使用配置化 LLM。
- `models.py`、`database.py`：SQLAlchemy 模型与连接。
- `storage.py`：MinIO legacy 兼容层，目前不是 `/bid` 强依赖。

## 数据流

```text
用户创建项目
  -> POST /projects
  -> workspaces/api-projects/<id>/project.json

用户上传招标文件
  -> POST /projects/<id>/files?purpose=tender
  -> parser 转 Markdown
  -> sources/ 保存原文件
  -> project.json 保存 tender_markdown

Plan
  -> 提取硬性条款、技术指标、评分项
  -> evidence search 匹配材料
  -> artifacts/plan.md

Execute
  -> response matrix
  -> evidence_trace.json
  -> draft.md
  -> project.execution

Review
  -> 附件就绪度
  -> 评分就绪度
  -> 商务证据签核
  -> 合同履约义务
  -> review.md
  -> handoff.md
```

## Artifact 设计思路

Artifact 是用户、前端、后端和后续自动化之间的稳定交接面。

- Markdown Artifact 面向人工阅读、评审和复制到正式投标文件。
- `evidence_trace.json` 面向程序化校验、前端证据 badge 和后续导出。
- `project.json` 保存项目阶段和前端渲染需要的结构化结果。

任何正式稿事实都应能从 `draft.md` 追溯到 `response_matrix.md`，再追溯到 `evidence_trace.json` 中的 `evidence_id`。

## 设计取舍

- 优先做确定性 `/bid` workbench，避免所有验收都被外部 LLM quota 阻塞。
- 保留 LLM workflow，但不把它作为本地 smoke 的必要条件。
- 证据向量化是增强能力，关键词检索是基础可用能力。
- 不把 `vault/` 和 `workspaces/` 提交到 Git，避免泄露客户材料和运行态数据。
- 对 vendored frontend 只维护项目自有定制层，避免批量改写上游大仓。
