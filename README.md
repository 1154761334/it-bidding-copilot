# IT Bidding Copilot

面向政企 IT 投标场景的前后端分离系统，当前唯一有效主线为 `FastAPI + PostgreSQL/pgvector + React/Vite`。

## 当前基线

- 前端：React + Vite
- 后端：FastAPI
- 数据库：PostgreSQL + pgvector
- 接口前缀：`/api/v1/*`
- 当前测试与联调状态请以 `docs/current_status.md` 为准
- 当前前端浏览器巡检状态请以 `docs/site_function_audit.md` 为准

当前项目已完成并验证的主链路包括：
- 企业资产导入与检索
- `docs/商务技术文件.docx` 资质预提与图片入库
- 真实采购文件识别与 `analysis-check`
- 偏离矩阵
- 章节生成与终审
- DOCX 导出

补充设计文档：
- 文档解析栈方案：`docs/document_parsing_stack_design.md`
- 外部协作总方案：`docs/opus_collaboration_brief.md`
- 多 AI 协作与开发日志规范：`docs/development_workflow.md`

## 功能范围

### 1. 企业资质库
- 支持企业材料导入、分类、切块、向量检索
- 支持 `Obsidian Vault` 作为知识源导入主库
- 支持对 `docs/商务技术文件.docx` 做“规则切块 + LLM 标准化 + 后端校验后入库”
- 支持对商务技术文件预提结果做二次清洗与去重，优先保留明确证书、历史案例和实名人员
- 支持展示最近一轮企业材料导入批次，便于人工确认本轮新入库资产
- 支持在企业资产中心对证书、案例、人员做新增、修改、删除和批量删除

### 2. 采购文件识别
- 支持真实采购文件上传、异步分析、项目建档
- 支持项目元信息、要求、废标项、评分项提取
- 支持 `analysis-check` 质量校验
- 支持在 `/rfp` 页面修正项目信息与关键要求后确认建档
- 支持历史项目源文件路径失效时回退校验，不再因上传目录缺失直接报错
- 当前识别策略为“首轮抽取 + Reviewer/Resolver 复核 + 评分表规则补全”

### 3. 编标与导出
- 支持按项目生成目录和章节草稿
- 支持在编标前确认“项目素材包”，对资质、案例、人员和补充材料做智能推荐与人工确认
- 支持在编标大厅中对当前章节进行在线 Markdown 改稿并保存
- 支持单章节生成、整项目自动续写、仅重试未完成章节
- 支持终审与风险汇总
- 支持按审标结果拦截不合格项目导出 `.docx`
- 支持在导出前检查中显示采购母版、图片证据和被拦截章节详情

## 快速开始

### 1. 安装依赖

```bash
git clone https://github.com/1154761334/it-bidding-copilot.git
cd it-bidding-copilot
pip install -r requirements.txt
npm install --prefix frontend
```

### 2. 配置环境

```bash
cp .env.example .env
```

最小配置：

```bash
DATABASE_URL=postgresql://root:bidcore_password123@localhost:5432/bidcore_enterprise
LLM_API_KEY=your_llm_api_key_here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
EMBEDDING_MODEL=
```

如使用当前已验证的 Ark Coding 配置：

```bash
LLM_API_KEY=53598855-b050-4230-96d4-72b986d6a887
LLM_BASE_URL=https://ark.cn-beijing.volces.com/api/coding/v3
LLM_MODEL=Doubao-Seed-Code
EMBEDDING_MODEL=
```

说明：
- 当前默认推荐显式模型为 `Doubao-Seed-Code`
- `LLM_MODEL=Auto` 在当前兼容层的部分结构化调用上可能返回 `UnsupportedModel`
- 未配置 `EMBEDDING_MODEL` 时，系统会对向量能力静默降级，便于先打通流程

## 仓库内容与运行时资产说明

当前 GitHub 仓库保存的是“可协作的源码基线”，不是服务器上的全部运行时资产快照。

已推送到仓库的主要是：

- 前后端源码
- Alembic 迁移
- 脚本、测试、模板
- 轻量文档和配置

未推送到仓库的主要是：

- `models/`
- 超大样例文档 `docs/商务技术文件.docx`
- 运行期目录中的上传、导出、日志、缓存和解析产物

原因：

- `models/` 目录当前约 `18G`，主要是 `magic-pdf`、OCR、版面分析、公式识别等本地模型权重，属于运行时依赖，不适合直接进入 Git 仓库
- `docs/商务技术文件.docx` 当前约 `124MB`，超过常规 GitHub 单文件可接受范围

这意味着：

- clone 仓库后可以拿到当前主线代码
- 但如果要完整复现本机上的文档解析能力，仍需要额外补齐本地模型资产和部分样例文件

当前建议把 `models/` 视为“部署资产”而不是“源码”：

- 开发协作时不进 Git
- 新机器部署时单独补齐
- 后续如需迁移环境，建议补一份模型资产准备说明或下载脚本

### 3. 启动服务

```bash
./start_app.sh start
```

启动后：
- 前端：`http://127.0.0.1:20031/`
- 后端：`http://127.0.0.1:8000`
- 健康检查：`http://127.0.0.1:8000/healthz`

常用命令：

```bash
./start_app.sh status
./start_app.sh stop
./start_app.sh restart
```

## 常用验证脚本

```bash
./venv/bin/python scripts/ops/check_runtime_assets.py
./venv/bin/python scripts/seed/seed_demo_data.py
./venv/bin/python scripts/verify/verify_obsidian_vault_flow.py
./venv/bin/python scripts/verify/verify_business_doc_ingest_flow.py
./venv/bin/python scripts/verify/verify_rfp_analysis_quality.py
./venv/bin/python scripts/verify/verify_real_workflows.py
./venv/bin/python scripts/verify/verify_project_autorun_flow.py
./venv/bin/python scripts/verify/verify_embedding_runtime.py
```

建议：

- 新机器 clone 后先执行 `./venv/bin/python scripts/ops/check_runtime_assets.py`
- 如果缺少 `models/` 或超大样例文档，说明当前环境拿到的是“源码基线”，不是“服务器完整运行镜像”

## 关键接口

- `GET /healthz`
- `GET /api/v1/dashboard/context`
- `POST /api/v1/enterprise/vault-ingest/{company_id}`
- `POST /api/v1/enterprise/business-doc-ingest/{company_id}`
- `GET /api/v1/enterprise/assets-overview/{company_id}`
- `GET /api/v1/enterprise/intake-readiness/{company_id}`
- `GET /api/v1/enterprise/latest-ingest-batch/{company_id}`
- `POST /api/v1/rfp/analyze`
- `GET /api/v1/rfp/tasks/{task_id}`
- `GET /api/v1/rfp/projects/{project_id}/analysis-check`
- `GET /api/v1/rfp/projects/{project_id}`
- `POST /api/v1/rfp/projects/{project_id}/analysis-confirm`
- `GET /api/v1/rfp/projects/{project_id}/deviation`
- `PUT /api/v1/rfp/projects/{project_id}/deviation`
- `POST /api/v1/rfp/projects/{project_id}/deviation/confirm`
- `POST /api/v1/bid/projects/{project_id}/draft-all`
- `POST /api/v1/bid/review/{project_id}`
- `POST /api/v1/bid/export-docx/{project_id}`
- `GET /api/v1/config/capabilities`

## 项目结构

详细目录职责见 [docs/project_structure.md](/root/it-bidding-copilot/docs/project_structure.md)。

当前核心目录：

```text
api/         FastAPI 路由、模型、服务与运行时能力
frontend/    React/Vite 前端
utils/       文档解析、抽取、检索与导出工具
scripts/     按 ops / seed / verify 分类的脚本目录
tests/       pytest 测试
docs/        架构、状态、策略与样例文档
alembic/     数据库迁移
assets/      运行期提取图片等派生产物
data/        当前保留的运行期资产目录
```

补充说明：

- `models/` 不在当前 GitHub 仓库版本控制中，属于大体积本地运行时资产
- `assets/`、`data/` 中的内容也以运行期产物为主，不保证远端仓库包含服务器上的全部现状

## 相关文档

- [docs/current_status.md](/root/it-bidding-copilot/docs/current_status.md)
- [docs/architecture.md](/root/it-bidding-copilot/docs/architecture.md)
- [docs/development_workflow.md](/root/it-bidding-copilot/docs/development_workflow.md)
- [docs/feature_inventory.md](/root/it-bidding-copilot/docs/feature_inventory.md)
- [docs/frontend_backend_alignment.md](/root/it-bidding-copilot/docs/frontend_backend_alignment.md)
- [docs/project_structure.md](/root/it-bidding-copilot/docs/project_structure.md)
- [docs/runtime_execution_design.md](/root/it-bidding-copilot/docs/runtime_execution_design.md)
- [docs/multi_round_extraction_strategy.md](/root/it-bidding-copilot/docs/multi_round_extraction_strategy.md)
- [docs/site_function_audit.md](/root/it-bidding-copilot/docs/site_function_audit.md)
- [docs/design_requirement_matrix.md](/root/it-bidding-copilot/docs/design_requirement_matrix.md)
- [docs/main_flow_task_list.md](/root/it-bidding-copilot/docs/main_flow_task_list.md)
- [docs/p0_recovery_plan.md](/root/it-bidding-copilot/docs/p0_recovery_plan.md)
- [docs/development_logs/README.md](/root/it-bidding-copilot/docs/development_logs/README.md)

## License

MIT License
