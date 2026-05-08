# API 与 Artifact 合约

## 健康检查

`GET /health`

返回：

- `status`
- `version`
- `data_dir`
- `core_available`
- `evidence_store_available`
- `evidence_count`
- `project_count`
- `timestamp`

## 项目 API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/projects` | 创建项目。 |
| `GET` | `/projects` | 列出项目。 |
| `GET` | `/projects/{project_id}` | 获取项目详情。 |
| `POST` | `/projects/{project_id}/files?purpose=tender` | 上传并解析文件。 |
| `POST` | `/projects/{project_id}/plan` | 生成 Plan。 |
| `POST` | `/projects/{project_id}/approve-plan` | 人工确认 Plan。 |
| `POST` | `/projects/{project_id}/execute` | 生成响应矩阵、证据追溯和草稿。 |
| `POST` | `/projects/{project_id}/review` | 生成评审、交接和合同履约附录。 |
| `GET` | `/projects/{project_id}/artifacts` | 列出 Artifact。 |
| `GET` | `/projects/{project_id}/artifacts/{artifact_name}` | 读取 Artifact 文本。 |
| `GET` | `/evidence/search` | 检索证据。 |
| `POST` | `/demo/real-case` | 运行真实案例 Demo。 |

## 项目阶段

| 阶段 | 含义 |
| --- | --- |
| `created` | 项目已创建。 |
| `planned` | Plan 已生成。 |
| `approved` | 用户确认 Plan。 |
| `executed` | Execute Artifact 已生成。 |
| `reviewed` | Review 和 Handoff 已生成。 |

## Artifact 清单

| Artifact | 用途 | 主要读者 |
| --- | --- | --- |
| `plan.md` | 项目信息、硬性条款、技术指标、评分项、缺失材料、证据检索、材料包分工。 | 投标负责人、技术负责人 |
| `response_matrix.md` | 条款/评分项、响应策略、证据 ID、覆盖状态。 | 起草人、评审人 |
| `draft.md` | 受控投标文件草稿、商务响应、技术方案、证据索引、合同履约附录。 | 起草人、商务、法务 |
| `review.md` | 风险分桶、附件就绪度、评分就绪度、商务和合同义务复核。 | 质检、项目经理 |
| `handoff.md` | 剩余人工动作、材料包交接、证据缺口和 Artifact Map。 | 交付负责人 |
| `evidence_trace.json` | 机器可读证据链。 | 前端、自动化检查 |
| `project.json` | 项目状态和结构化结果。 | 后端、前端 |

## evidence_trace.json 字段

| 字段 | 说明 |
| --- | --- |
| `row_id` | 响应矩阵行 ID，如 `H1`、`T3`、`S2`、`C1`。 |
| `evidence_id` | 证据 ID，如 `EVID-12`。 |
| `title` | 证据标题。 |
| `source_doc` | 来源文件。 |
| `heading_path` | 来源章节路径。 |
| `page_hint` | 页码、页段或人工定位提示。 |
| `asset_paths` | 关联图片或附件路径。 |
| `material_group_key` | 材料包机器名。 |
| `material_group` | 材料包中文名。 |
| `material_owner` | 材料责任人。 |

## Readiness Summary

项目列表返回 `readiness_summary`，用于前端显示快速风险 badge。

核心维度：

- `attachment_ready` / `attachment_total`
- `attachment_needs_page_hint`
- `scoring_ready` / `scoring_total`
- `scoring_needs_page_hint`
- `scoring_needs_bidder_evidence`
- `commercial_ready` / `commercial_total`
- `commercial_needs_page_hint`
- `commercial_tender_only`
- `contract_ready` / `contract_total`
- `contract_needs_page_hint`
- `contract_tender_only`
- `risk_statuses`

## 兼容性规则

- 新增字段优先使用可选字段，避免破坏前端旧渲染。
- Artifact 文件名是公共合约，修改前必须同步前端默认排序和 smoke。
- `evidence_id` 格式保持 `EVID-<number>`。
- 任何路径型字段不能泄露未授权私有目录到外部服务。
- 正式稿不能把缺证据行写成已满足。
