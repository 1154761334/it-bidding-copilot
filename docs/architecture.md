# System Architecture

## Overview

IT Bidding Copilot 当前已经收敛到单一生产基线：

- Frontend: `React + Vite`
- Backend: `FastAPI`
- Database: `PostgreSQL + pgvector`
- API Prefix: `/api/v1/*`

历史 `Streamlit / SQLite / 重型原型编排` 已不再是当前产品基线。

## Runtime Layers

### 1. Presentation Layer

前端位于 `frontend/`，负责：
- 企业资质库页面
- 采购文件识别页面
- 偏离矩阵页面
- 编标大厅
- 终审与导出
- 系统配置

### 2. API Layer

后端入口是 [main.py](/root/it-bidding-copilot/main.py)，核心路由位于 `api/routers/`：
- `enterprise_v2.py`: 企业资产导入、检索、资质预提
- `rfp_v2.py`: 采购文件分析、任务查询、偏离矩阵、质量校验
- `drafting_v2.py`: 章节生成、项目批量生成、终审、导出
- `dashboard_v2.py`: 首页上下文
- `config_v2.py`: 运行时能力与模型配置

### 3. Service Layer

主要业务编排位于 `api/services/`：
- `enterprise_ingest_service.py`: 企业资质导入与标准化入库
- `rfp_analysis_service.py`: 采购文件分析、项目建档、质量校验
- `drafting_workflow.py`: 单章节生成工作流
- `drafting_task_service.py`: 章节任务与项目批量生成
- `bid_exporter.py`: 导出 `.docx`
- `model_runtime_service.py`: chat / embedding / fallback 能力探测

### 4. Utility Layer

`utils/` 负责可复用能力：
- 文档解析：`docling_wrapper.py`
- 企业资质提取：`business_doc_asset_extractor.py`
- LLM 标准化：`business_asset_llm_extractor.py`
- RFP 识别：`api/engines/rfp_analyzer.py`
- 检索与匹配：`hybrid_retriever.py`、`asset_matcher.py`
- 偏离与导出辅助：`api/engines/deviation_engine.py`、`docx_exporter.py`

当前文档解析栈的后续演进方案见：

- `docs/document_parsing_stack_design.md`

## Core Workflows

### Enterprise Asset Workflow

```text
source files / Obsidian Vault
-> parse & classify
-> LLM normalize
-> backend validate
-> PostgreSQL + pgvector
```

### RFP Analysis Workflow

```text
RFP upload
-> parse document
-> extract project meta / requirements / fatal items / scoring
-> reviewer / resolver validation
-> project persistence
-> analysis-check
```

### Drafting Workflow

```text
project + requirements + enterprise assets
-> outline
-> chapter drafting
-> audit / refine
-> review
-> export-docx
```

## Design Principles

- 单一主线：只维护 FastAPI + PostgreSQL/pgvector + React/Vite
- AI 参与但不裸写库：先抽取，再校验，再落库
- 多轮校验只放在高风险节点，不做全链路重型多智能体
- 所有关键结果尽量带 trace，便于复核
- 文档解析采用分层与门面模式，不让单个外部解析器渗透到业务层

## Current Verified State

- 当前本地重新核验结果：
- `./venv/bin/python -m pytest -q --maxfail=8` -> `54 passed`
- `cd frontend && npm run build` -> 通过
- 审标、导出 readiness、企业资产汇总和素材包主契约已恢复到当前前端可用水平
- Playwright 与真实模型端到端联调仍以历史记录为主，本次未重新执行
- 因此当前更准确的表述是：“主流程基线已恢复，可继续推进 RFP 确认工作台与主流程产品化收口”
