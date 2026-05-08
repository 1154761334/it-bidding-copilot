# 技术债与维护索引

本文档记录已知问题、处理状态和后续维护优先级。详细历史仍保留在 `DEV_LOG.md`。

## P0 已处理

| 问题 | 状态 | 说明 |
| --- | --- | --- |
| GitHub 主仓库缺少前端源码 | 已处理 | `frontend/` 已作为普通源码 vendored 到顶层仓库，忽略本地 `.git/`、依赖、构建和 auth state。 |
| 后端绝对路径绑定本机目录 | 已处理 | `config.py` 统一解析仓库相对路径，`api_workbench.py`、`main.py`、`ingest.py` 已改为配置化路径。 |
| API 根路径写死模型名称 | 已处理 | 根接口返回配置化 `llm_model` 和 OpenAI-compatible provider 信息。 |
| Compose 使用过时 `version` 字段 | 已处理 | 已移除并改为 `${VAR:-default}` 本地默认值。 |
| 缺少环境变量模板 | 已处理 | 新增 `.env.example` 和 `backend/.env.example`。 |
| 前端 README 是上游大仓说明 | 已处理 | 上游说明移动到 `frontend/README.upstream.md`，本项目维护入口写入 `frontend/README.md`。 |

## P1 当前限制

| 问题 | 影响 | 建议 |
| --- | --- | --- |
| `/bid` 项目状态存为文件和进程内缓存 | 单机可用，多实例不一致 | 后续迁移到数据库项目表和 Artifact 表。 |
| `api_workbench.py` 文件较大 | Review 和生成逻辑集中，长期维护成本高 | 拆分为 `project_store`、`artifact_writer`、`review_readiness`、`markdown_renderers`。 |
| MinIO 仍是 legacy optional | 当前主线不依赖，容易误解 | 若后续不用，应移除或明确迁移到 Artifact object store。 |
| LangGraph workflow 与 `/bid` deterministic workflow 并存 | 维护者容易混淆主线 | 继续文档化主线边界，后续统一 state contract。 |
| Vault 私有材料缺失时 Demo 不可跑 | 新环境无法直接复现真实案例 | 提供脱敏 sample vault 或测试 fixture。 |

## P2 后续增强

| 方向 | 建议 |
| --- | --- |
| API schema | 引入 Pydantic response models，生成 OpenAPI 对照文档。 |
| 数据库迁移 | 增加 Alembic 或等价 migration 管理。 |
| Artifact schema | 为 `evidence_trace.json` 增加 JSON Schema 和版本字段。 |
| 前端 UI | 将 inline style 的 `/bid` 工作台逐步迁移到现有设计系统组件。 |
| 权限与审计 | 为项目、Artifact、证据检索增加用户和操作日志。 |
| 导出 | 将 Markdown Artifact 转 DOCX/PDF，并保留证据页码索引。 |
| CI | 将 `acceptance:bid-smoke:preflight` 和后端 py_compile 纳入 GitHub Actions。 |

## 维护规则

- 新增问题先进入本文件，再决定是否写入 `DEV_LOG.md` 的当轮进度。
- P0 是阻断后续维护、发布或安全边界的问题。
- P1 是当前可接受但需要计划处理的问题。
- P2 是增强项，不应阻断主线验收。
- 不把上游 vendored frontend 的无关格式化问题算作本项目 P0。
