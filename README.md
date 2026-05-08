# IT Bidding Copilot

IT Bidding Copilot 是面向 IT、系统集成、私有云和企业软件项目的投标辅助工作台。它的目标不是生成一段通用标书文本，而是把招标文件、投标人材料、厂商材料、历史投标知识和人工复核动作组织成可追溯的投标生产流程。

当前主线是 `/bid` 商业试用工作台：前端提供项目、文件、计划、执行、评审、草稿和证据视图；后端负责招标文件解析、证据检索、受控起草、质检和交付 Artifact 生成。

## 当前状态

截至 2026-05-08，主线能力聚焦在可维护、可验收的投标工作流闭环。

- 后端确定性评估为 `100.0`，`115/115` 检查通过，真实 Vault 来源可发现 `253` 个证据块，最近 `evidence_trace.json` 长度为 `94`。
- `/bid` 流程生成 `plan.md`、`response_matrix.md`、`draft.md`、`review.md`、`handoff.md`、`evidence_trace.json` 和 `project.json`。
- Review 覆盖材料包、附件就绪度、评分就绪度、商务证据签核、合同履约义务、操作清单和交接摘要。
- 前端源代码已经 vendored 到顶层仓库，不再依赖单独的嵌套 Git 仓库才能还原项目。
- LLM 路径是 OpenAI-compatible 配置化调用。默认配置文档以 `kimi-k2.6` 为示例模型，实际模型由环境变量决定。

## 快速启动

复制环境变量模板：

```bash
cp .env.example .env
cp backend/.env.example backend/.env
```

启动可选本地服务：

```bash
docker compose up -d
```

启动后端：

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

启动前端直接 SPA 路由：

```bash
cd frontend
pnpm install
pnpm dev:spa --host 127.0.0.1
```

默认前端访问后端 `http://localhost:8000`。如需改后端地址，设置 `NEXT_PUBLIC_BIDDING_API_BASE_URL`。

## 架构总览

```text
Browser / /bid workbench
        |
        v
frontend/
  React + TypeScript + Zustand + LobeHub/LobeChat workspace
        |
        | REST, Markdown artifacts, evidence JSON
        v
backend/
  FastAPI + SQLAlchemy + parser + workflow + evidence search
        |
        +--> PostgreSQL + pgvector       optional local evidence store
        +--> Redis                       optional local service
        +--> MinIO                       legacy optional object storage
        +--> vault/                      private source material, gitignored
        +--> workspaces/api-projects/    generated project state, gitignored
```

主流程分为五步：

1. **Files**：创建项目，上传招标文件或加载真实案例。
2. **Plan**：解析招标要求，提取硬性条款、技术指标、评分项和缺失材料。
3. **Approve**：人工确认计划后进入执行。
4. **Execute**：生成响应矩阵、证据追溯、材料包分工和标书草稿。
5. **Review / Handoff**：检查废标风险、评分风险、商务和合同义务缺口，输出交接摘要。

## 主要组件

| 路径 | 责任 |
| --- | --- |
| `frontend/` | 定制化 LobeHub/LobeChat 前端工作区，新增 `/bid` 工作台、状态管理、API client 和 smoke acceptance。 |
| `backend/` | FastAPI 服务、招标解析、证据检索、确定性 workbench API、LangGraph LLM workflow。 |
| `vault/` | 私有招标和投标知识来源，默认不提交到 Git。 |
| `workspaces/` | API 项目状态、上传源文件和生成 Artifact，默认不提交到 Git。 |
| `Bidding-agent/` | Hermes/Obsidian/OVP 方向的投标经理技能包，作为可选长期知识工作流层。 |
| `obsidian_vault_pipeline/` | Obsidian Vault 知识流水线，作为可选知识编排子系统。 |
| `vault-template/` | 公司长期知识 Vault 的推荐骨架。 |
| `eval_bid_assistant.py` | 后端确定性验收评估器。 |
| `docker-compose.yml` | 本地 PostgreSQL/pgvector、Redis、MinIO 服务。 |

更多细节见：

- [架构说明](docs/architecture.md)
- [配置说明](docs/configuration.md)
- [开发指南](docs/development.md)
- [运行维护](docs/operations.md)
- [API 与 Artifact 合约](docs/api-and-artifacts.md)
- [技术债与维护索引](docs/technical-debt.md)

## 模型与检索

本项目不把模型写死在业务代码里。

- `LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL` 控制 OpenAI-compatible chat-completions 调用。
- 默认示例为 `kimi-k2.6`，当前 legacy LangGraph 工作流需要真实 `LLM_API_KEY` 和供应商额度。
- `/bid` 主线可以在没有 LLM key 的情况下跑确定性工作流和验收。
- `EMBEDDING_BASE_URL`、`EMBEDDING_API_KEY`、`EMBEDDING_MODEL` 控制证据向量化。没有 embedding key 时会降级到关键词检索。
- 默认 embedding 示例为 `Pro/BAAI/bge-m3`，维度 `1024`。

## 验收命令

后端：

```bash
backend/venv/bin/python -m py_compile eval_bid_assistant.py backend/src/config.py backend/src/main.py backend/src/api_workbench.py backend/src/ingest.py backend/src/llm.py backend/src/workflow.py
backend/venv/bin/python eval_bid_assistant.py
cd backend && venv/bin/python -m src.ingest --dry-run
cd backend && venv/bin/python tests/api_smoke.py
```

前端：

```bash
cd frontend
pnpm run type-check
pnpm run build
pnpm run acceptance:bid-smoke:preflight
pnpm run acceptance:bid-smoke:local
```

基础仓库检查：

```bash
git diff --check -- . ':(exclude)frontend'
docker compose config
```

说明：vendored upstream frontend 中可能存在上游空白或 snapshot 风格差异，避免为本项目改动批量格式化整个上游代码树。

## 源码与数据边界

提交到 Git：

- 后端、前端定制源代码、投标工作台 smoke 脚本、文档、模板、评估器和 Compose 配置。

不提交到 Git：

- `vault/` 私有材料
- `workspaces/` 项目运行态
- `backend/tests/output/`
- `frontend/.git/`
- `frontend/node_modules/`
- `frontend/.next/`
- `frontend/public/_spa/`
- `frontend/.auth/`
- `.env` 和真实密钥
- 大型 Office 原始文件

## 后续维护原则

- 先维护 API/Artifact 合约，再调整 UI 或模型策略。
- 所有正式稿事实必须能回链到 `response_matrix.md` 和 `evidence_trace.json`。
- 生成稿不能把招标依据写成投标人已承诺。
- 商务金额、税率、账户、页码、签章状态和法务结论必须由人工回填或签核。
- 文档更新应同步更新 README、`docs/technical-debt.md`、`DEV_LOG.md` 和相关子目录 README。
