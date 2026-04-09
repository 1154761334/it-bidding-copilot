# Runtime Execution Design

## 1. 本轮目标

本轮不是继续扩表，而是在现有 `FastAPI + PostgreSQL/pgvector + React/Vite` 基线上，补齐三类运行时能力：

- 模型与 embedding 配置的统一运行时探测
- RFP 分析与 Draft 生成的 trace 输出
- 在模型不完全兼容时的 deterministic fallback

## 2. 设计原则

- 不因为单个模型或解析器异常阻断整条投标链路
- 在不新增高风险表结构的前提下，把 trace 优先放入任务结果和现有 JSON 字段
- 明确区分 `chat model` 与 `embedding model`
- 真实联调优先于“纸面正确”

## 3. 运行时能力层

新增 `api/services/model_runtime_service.py`，统一输出：

- `provider`
- `base_url`
- `llm_model`
- `embedding_model`
- `chat_enabled`
- `embedding_enabled`
- `fallbacks`
- `compatibility_notes`

当前通过 `/api/v1/config/capabilities` 可直接查看运行时能力。

## 4. 文档解析策略

`utils/docling_wrapper.py` 当前采用分层策略：

- `.docx`：本地轻量解析，提取标题、段落、表格
- `.txt/.md`：直接文本读取
- 其他格式：继续走 Docling

目标是优先保证 ingest / analyze 可用，而不是要求所有格式都先依赖重解析器。

## 5. RFP 分析 Trace

`/api/v1/rfp/analyze -> status` 的结果中新增 `analysis_trace`，包含：

- `model_runtime`
- `parser`
- `requirements`
- `assets`

这让前端和脚本能看见本次分析究竟用了什么模型配置、什么解析方式、提取了多少需求、关联了多少资产。

## 6. Draft 生成 Trace

Draft 工作流在现有 `audit_logs` JSON 中附带 `workflow_trace`，当前包含：

- `model_runtime`
- `requirements_count`
- `context_materials_count`
- `enterprise_context_count`
- `case_hits`
- `certificate_hits`
- `chunk_hits`
- `draft_content_length`
- `audit_feedback_length`
- `approved`

同时 `/api/v1/bid/draft/status/{task_id}` 的任务结果也会返回 `workflow_trace`。

## 7. Fallback 策略

当前已落地的 fallback：

- `RFPAnalyzer` 结构化提取失败时，回落到规则抽取
- `QueryRewriter` LLM 不可用时，回落到启发式结构化查询
- `DraftingWorkflow` 的 winning points、写作、审计、润色在模型失败时回落到确定性文本生成
- 未配置 `EMBEDDING_MODEL` 时，向量检索回落到零向量排序

这保证链路“先跑通”，但不等同于最终最优质量。

## 8. 后续建议

下一轮建议继续做：

1. 为 trace 补数据库持久化字段和 Alembic 迁移
2. 前端将 `analysis_trace` / `workflow_trace` 可视化
3. 将 `Auto` 替换为显式可兼容模型名后再做一轮真实质量复核
4. 给 `verify_real_workflows.py` 增加断言版集成测试
