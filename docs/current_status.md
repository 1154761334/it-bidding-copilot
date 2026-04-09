# 当前状态与交接

## 1. 当前基线

项目当前有效主基线为：

- 前端：React + Vite
- 后端：FastAPI
- 数据库：PostgreSQL + pgvector
- 接口规范：`/api/v1/*`

已确认旧的 Streamlit / SQLite / 原型型多智能体目录不是当前主运行入口，本轮清理后已从主项目口径中移除。

## 1.1 本次文档校对结论

本次已基于 `docs/` 与当前代码做了一轮交叉核对，结论如下：

- 主线方向没有问题：当前真实入口仍是 `main.py -> api/routers/*` 与 `frontend/src/App.tsx`
- 前端页面层已经基本按产品流程铺开，但部分页面依赖的后端返回结构与文档描述不完全一致
- `EnterpriseAssetService`、`DraftingReviewService` 目前是可运行的简化版实现，能力明显弱于文档中描述的“完整产品化版本”
- 当前 `pytest` 基线已经失真，不能再沿用“`53 passed` / `52 passed`”作为仓库真实状态
- 现有文档中关于 Playwright、真实联调、页面巡检的大部分记录可视为“历史曾完成”，但不应再默认代表当前代码状态
- 当前 GitHub 仓库已推送最新源码基线，但未包含服务器上的全部运行时大资产，尤其是 `models/` 与超大样例文档
- 已新增 `scripts/ops/check_runtime_assets.py`，用于在新机器上快速检查关键运行时资产是否齐备

## 1.2 协作方式补充说明

当前项目并非单一开发代理持续推进，而是由多 AI 协作推进：

- `Codex`：负责方案收敛、状态审查、代码与文档核对、关键实现与验收
- `Antigravity / Gemini Flash`：负责承接较大开发量或高频迭代任务
- `OpenCode`：当前不是主力开发通道

因此，文档在本项目里不是“补充材料”，而是跨代理协作的主控制面。后续默认要求：

- 每轮有效开发前先读 `docs/current_status.md`、`docs/feature_inventory.md`、`docs/development_workflow.md`
- 日常开发优先通过 GitHub commit / PR 留痕
- 中等及以上改动后更新状态文档
- 只有关键轮次才在 `docs/development_logs/` 新增日志
- 若实现与既有文档冲突，必须先修正文档口径再继续推进

## 2. 已完成事项

- 修复并统一了后端主入口 [main.py](/root/it-bidding-copilot/main.py) 的 API 挂载方式
- 前端 API client 与 WebSocket 已切到 `/api/v1/*`
- 修复企业档案路由顺序问题，`/profile` 与 `/trust-score` 已可正常访问
- 修复设置页保存配置时误清空 API Key 的问题
- 修复编标工作流中 `audit_logs`、`winning_points`、`source_fragments` 的落库结构不一致问题
- 新增稳定模型入口 `api/models/__init__.py`
- 新增演示数据脚本 `scripts/seed/seed_demo_data.py`
- README、架构说明、目录结构文档已更新到当前收敛口径
- 已新增前端产品形态与后端承接矩阵文档：`docs/frontend_backend_alignment.md`
- 已新增长期功能台账文档：`docs/feature_inventory.md`
- 已将 `RFPAnalysis` 页面接入真实 `analysis-check` 结果与阶段状态展示
- 已删除前端重复历史页面 `Profile.tsx`、`Export.tsx`
- 已为企业资产中心新增真实资产汇总接口 `GET /api/v1/enterprise/assets-overview/{company_id}`
- 已将企业资产中心接入真实证书、案例、人员、源文件展示
- 已为偏离矩阵新增保存接口 `PUT /api/v1/rfp/projects/{project_id}/deviation`
- 已为偏离矩阵新增确认接口 `POST /api/v1/rfp/projects/{project_id}/deviation/confirm`
- 已将偏离矩阵页面升级为可保存、可确认的确认页
- 已将编标大厅接入项目级批量生成入口与批次进度展示
- 已将编标大厅接入“仅重试未完成章节”项目级重试入口
- 已将编标大厅接入章节完成、待复核、未生成统计
- 已将编标大厅接入当前章节证据链与审稿反馈展示
- 已为审标页面补齐“存在待复核章节”的前置提示
- 已将审标页面主要文案和证据链展示切换为中文产品化表达
- 已为终审导出页面补齐“未完成章节禁止导出”的前端约束
- 已为企业资产中心新增分类筛选、详情浏览与图片预览
- 已将企业资产中心升级为统一资产管理页，支持证书/案例/人员的新增、编辑、删除和批量删除
- 已将设置弹窗接入 `/config/capabilities`
- 已将 `RFPAnalysis` 页面接入完整 `analysis-check` 检查项展开
- 已在采购 requirement 抽取阶段过滤公告/购标流程/表格清单噪声
- 已为采购 requirement 抽取补充去重、联系人/报名流程噪声过滤、背景叙述过滤
- 已为商务技术文件证书提取补齐 `cert_level`、`issue_date`、`expiry_date`
- 已补独立 `EMBEDDING_MODEL` 前后端配置入口
- 已将 `ReviewExport` 静态封标清单替换为真实导出 readiness 检查
- 已新增 `scripts/verify/verify_embedding_runtime.py` 用于独立验证 chat/embedding 连通性
- 已增强导出器：优先使用采购文件 docx 作为母版、回填正文图片标记、附加章节证据附录
- 已增强导出器：证据附录中的 `[IMAGE:...]` 也会按图片证据渲染
- 已修复导出器对“文字说明 + 图片标记”混合证据片段的处理，现可在章节证据附录中同时保留说明文字并插入佐证图片
- 已让章节生成链路把证书图片、社保图片作为 `[IMAGE:...]` 证据写入上下文
- 已新增 `GET /api/v1/rfp/projects/{project_id}`，支持前端在刷新后恢复当前项目分析结果
- 已修复 `/rfp` 页面刷新后丢失 `analysis-check` 与分析结果的问题
- 已修复 `/deviation` 页面错误依赖内存态 `analysisResult` 的问题
- 已为设置弹窗补齐 `Escape` 关闭能力
- 已为前端接入 Playwright 并补齐全站巡检用例
- 已新增全站巡检文档：`docs/site_function_audit.md`
- 已新增设计要求对照文档：`docs/design_requirement_matrix.md`
- 已新增主流程执行清单文档：`docs/main_flow_task_list.md`
- 已新增文档解析栈设计文档：`docs/document_parsing_stack_design.md`
- 已新增外部协作总方案文档：`docs/opus_collaboration_brief.md`
- 已收紧商务技术文件预提资质的数据治理逻辑，减少“方案说明段落误入人员/证书库”和重复沉淀
- 已为商务技术文件预提资质新增人员名单拆解能力，可从“实施团队成员资质证书”一类章节拆出明确姓名
- 已增强导出前检查，新增“采购母版是否可复用”“图片证据是否进入导出上下文”“哪些章节因状态或审标意见被拦截”信号
- 已为企业资产中心新增“企业建库确认”检查区，明确企业资料是否具备新建投标项目条件
- 已为企业资产中心新增“本轮新入库资产待确认”批次摘要，区分最新导入批次与历史资产
- 已为采购文件识别新增“分析结果确认保存”接口与前端确认区，支持修正项目信息和关键要求后正式确认建档
- 已将 `/deviation` 页面接入“分析未确认禁止进入下一步”的步骤提示
- 已将编标大厅接入“项目素材包”步骤，可在起草前确认资质、案例、人员与补充材料
- 已为编标大厅新增素材智能推荐、补充材料上传和素材确认前生成拦截
- 已为编标大厅新增在线 Markdown 编辑工作区，可对当前章节正文直接修改并保存
- 已新增 `PUT /api/v1/bid/draft/{draft_id}/content`，支持章节正文保存、版本递增与状态回收
- 已修复 `start_app.sh` 的 PID 记录错误，避免重启后仍命中旧前后端进程
- `ManualProfile` 当前已明确收口为“企业主体基础信息维护页”，不再承载证书/案例/人员的新增维护职责
- `EnterpriseAI` 当前已承接企业资产浏览、筛选、详情查看以及证书/案例/人员 CRUD 主入口
- `RFPAnalysis` 真实接入了项目恢复、`analysis-check` 展开和分析确认建档
- `BiddingHall` 当前已接入章节大纲、项目级批量生成、素材包读取、在线正文保存和补充材料上传入口

## 2.1 代码核对后确认的现实约束

以下内容不是“未做”，而是“当前代码实现比文档口径更弱或更简化”：

- `DraftingReviewService.run_red_team_review` 当前是同步简化实现，仅返回基础 `section_reviews`，没有文档中描述的完整结构化审标摘要
- `DraftingReviewService.build_export_readiness` 当前仅检查章节完成与项目状态，尚未覆盖文档中提到的采购母版、图片证据、被拦截章节详情等完整 readiness 细项
- `EnterpriseAssetService.build_assets_overview` 当前只稳定返回 counts 和证书列表，尚未达到文档中“证书/案例/人员/源文件/图片完整汇总”的详细结构
- `EnterpriseAssetService.build_latest_ingest_batch` 当前只返回最近批次日期和源文件列表，尚未稳定返回文档中提到的批次统计摘要
- `DraftingMaterialService.build_materials_pack` 当前返回结构是 `state/recommendations/available` 的简化版，和前端 `ProjectMaterialsPack` 类型定义并未完全对齐
- `BiddingHall` 中选区 AI 改写仍调用 `/api/v2/drafting/...`，与当前后端 `/api/v1/bid/draft/{draft_id}/rewrite` 不一致，说明该能力仍未真正收口

## 3. 已验证结果

文档中以下验证记录代表“此前已做过的联调/巡检历史”，其中相当一部分本次未重跑：

- `npm run build` -> 通过
- `cd frontend && PLAYWRIGHT_BASE_URL='http://127.0.0.1:20031' npx playwright test` -> `22 passed`
- `cd frontend && PLAYWRIGHT_BASE_URL='http://127.0.0.1:20031' npx playwright test tests/e2e/project-flow-audit.spec.ts tests/e2e/site-smoke.spec.ts` -> `19 passed`
- `cd frontend && PLAYWRIGHT_BASE_URL='http://127.0.0.1:20031' npx playwright test tests/e2e/project-flow-audit.spec.ts` -> `11 passed`
- `GET /healthz` -> 数据库可达
- `GET /api/v1/dashboard/context` -> 可返回当前公司、项目、草稿上下文
- `GET /api/v1/rfp/projects/1/deviation` -> 可返回偏离矩阵
- `GET /api/v1/bid/outline/1` -> 可返回章节大纲
- `POST /api/v1/bid/review/1` -> 可返回终审结果
- `POST /api/v1/bid/export-docx/1` -> 可导出真实 `.docx`
- `LLM_API_KEY=53598855-b050-4230-96d4-72b986d6a887 LLM_BASE_URL=https://ark.cn-beijing.volces.com/api/coding/v3 LLM_MODEL=Auto EMBEDDING_MODEL='' ./venv/bin/python scripts/verify/verify_real_workflows.py` -> 已跑通真实文档联调
- `LLM_API_KEY=53598855-b050-4230-96d4-72b986d6a887 LLM_BASE_URL=https://ark.cn-beijing.volces.com/api/coding/v3 LLM_MODEL=Doubao-Seed-Code EMBEDDING_MODEL='' ./venv/bin/python scripts/verify/verify_real_workflows.py` -> 已跑通真实文档联调
- `./venv/bin/python scripts/verify/verify_obsidian_vault_flow.py` -> 已跑通 Obsidian Vault 企业资质导入
- `LLM_API_KEY=53598855-b050-4230-96d4-72b986d6a887 LLM_BASE_URL=https://ark.cn-beijing.volces.com/api/coding/v3 LLM_MODEL=Doubao-Seed-Code EMBEDDING_MODEL='' ./venv/bin/python scripts/verify/verify_business_doc_ingest_flow.py` -> 已跑通商务技术文件预提资质入库
- `LLM_API_KEY=53598855-b050-4230-96d4-72b986d6a887 LLM_BASE_URL=https://ark.cn-beijing.volces.com/api/coding/v3 LLM_MODEL=Doubao-Seed-Code EMBEDDING_MODEL='' ./venv/bin/python scripts/verify/verify_rfp_analysis_quality.py` -> 已跑通真实采购文件识别与质量校验
- `./venv/bin/python scripts/verify/verify_rfp_analysis_quality.py` -> 已验证历史项目源文件路径失效时 `analysis-check` 可回退，不再直接崩溃
- `GET /api/v1/config/capabilities` -> 可返回当前 chat / embedding / fallback 运行时能力
- `./venv/bin/python scripts/verify/verify_embedding_runtime.py` -> 当前默认环境因 `gpt-4o` 不兼容 Ark Coding Plan 而返回 `UnsupportedModel`

最新一次真实联调结果：

- 真实企业资产 ingest：`docs/商务技术文件.docx` -> `ingested`
- 真实企业资产分块：`chunks_count=1715`
- 真实 RFP analyze -> status -> deviation：`project_id=2`，偏离矩阵 `deviation_count=80`
- 真实 bid draft 章节生成：自动生成目录 `outline_count=24`
- 真实 review：`approved_drafts=24/24`，`win_rate=90.0`
- 真实 export-docx：成功导出 `Bid_Project_2.docx`
- 显式模型 `Doubao-Seed-Code` 实测也已跑通整条真实链路，当前比 `Auto` 更适合作为默认配置
- 已新增运行时设计文档：`docs/runtime_execution_design.md`
- 商务技术文件预提资质：`docs/商务技术文件.docx`
- 预提结构结果：`sections_total=319`
- 商务技术文件图片提取并入库：`images_registered=341`
- LLM 辅助标准化：`llm_trace.mode=llm_standardized`
- 预提入库结果：`certificates_created=5`，`personnel_created=15`，`text_assets_created=5`
- 当前已确认 `Obsidian Vault` 可作为企业知识源导入主库
- 真实采购文件识别：`docs/定稿-招标文件-浙江省财务开发有限责任公司私有云项目.docx`
- 最新真实项目建档：`project_id=13`
- 采购文件质量校验：`quality_report.status=passed`
- 采购文件要求总数：`requirements_total=93`
- 最新评分项抽取：`scoring_count=17`
- 采购文件识别链路已新增轻量 `Extractor -> Reviewer -> Resolver` 多轮校验，trace 落在 `analysis_trace.review_round`
- 采购文件识别链路现已对联系人、报名流程、背景叙述、重复 requirement 做额外降噪
- 已新增多轮识别方案文档：`docs/multi_round_extraction_strategy.md`
- 编标大厅现已可直接触发 `POST /api/v1/bid/projects/{project_id}/draft-all`
- 编标大厅现已支持通过 `only_incomplete=true` 仅重试未完成章节
- 终审导出页面现已按 review 结果拦截未完成或未通过审标的项目导出
- 终审导出页面现已展示真实导出 readiness 检查，而非静态封标清单
- 终审导出页面现已将 readiness 细节转成可读文本，而非裸 JSON
- 全站主页面 `/dashboard`、`/profile`、`/profile/basics`、`/rfp`、`/deviation`、`/bidding`、`/audit`、`/review` 已完成一次真实浏览器巡检
- 企业资产中心真实浏览器动作 `新增 -> 搜索 -> 编辑 -> 删除` 已跑通
- 设置弹窗与 `/config/capabilities` 已完成真实浏览器巡检
- 编标大厅“项目素材包”确认、智能推荐与补充材料上传入口已完成浏览器巡检
- 编标大厅“在线编辑 -> 保存改稿”已完成真实浏览器巡检
- 导出器样例验证：混合证据片段导出后 `word/media` 已包含图片媒体文件

## 3.1 本次重新核验结果

本次仅对关键代码与后端单测基线做了重新核验，结果如下：

- `./venv/bin/python -m pytest -q --maxfail=8` -> `8 failed, 8 passed`
- 当前最明显的失败集中在两组：
- `DraftingReviewService` / `drafting_v2`：测试期望的审标摘要、导出前检查、辅助函数接口与当前实现不一致
- `EnterpriseAssetService`：测试期望的资产总览、资产浏览、建库 readiness、最新批次摘要能力强于当前实现

本次未重新执行以下验证，因此不再把它们视为“当前代码已再次确认通过”：

- 全量 Playwright 巡检
- 真实 Ark 模型联调
- 导出 `.docx` 端到端文件落地校验

## 4. 当前演示数据

可通过以下命令重建演示数据：

```bash
./venv/bin/python scripts/seed/seed_demo_data.py
```

当前演示数据包含：

- 公司：`测试演示公司`
- 项目：`演示私有云项目`
- 已存在的偏离矩阵、章节草稿、审标结果与导出链路

## 4.1 当前可用大模型联调配置

用户已提供一套可用于真实链路联调的模型接入参数，当前按 OpenAI 兼容协议记录如下：

- `LLM_API_KEY=53598855-b050-4230-96d4-72b986d6a887`
- `LLM_BASE_URL=https://ark.cn-beijing.volces.com/api/coding/v3`
- `LLM_MODEL=Doubao-Seed-Code`

补充说明：

- 如需切换 Anthropic 兼容协议地址，可使用 `https://ark.cn-beijing.volces.com/api/coding`
- 当前更适合本项目后端 `ChatOpenAI` 适配层的地址为 `https://ark.cn-beijing.volces.com/api/coding/v3`
- 用户当前可选模型包括：`Doubao-Seed-2.0-Code`、`Doubao-Seed-2.0-pro`、`Doubao-Seed-2.0-lite`、`Doubao-Seed-Code`、`MiniMax-M2.5`、`Kimi-K2.5`、`GLM-4.7`、`DeepSeek-V3.2`
- 当前建议默认先用 `Doubao-Seed-Code` 跑 ingest / analyze / draft 的真实联调
- 但实际验证表明：在当前 `ChatOpenAI` 兼容层下，`Auto` 在部分结构化分析调用上会返回 `UnsupportedModel`
- 实测 `Doubao-Seed-Code` 可稳定完成真实联调，但不保证支持所有 OpenAI JSON 模式扩展，因此当前 `RFPAnalyzer` 已去掉对 `response_format=json_object` 的硬依赖
- 当前后端已补 deterministic fallback，因此即使结构化 LLM 调用失败，`ingest -> analyze -> deviation -> draft -> review -> export-docx` 仍可完整跑通
- 当前商务技术文件预提资质链路已采用“规则切块 + LLM 标准化 + 后端校验后入库”模式，不让模型直接写库
- 当前商务技术文件预提资质链路已新增二次清洗与去重，优先保留明确证书、历史案例、实名人员，过滤功能说明、方案叙述和重复资产
- 当前采购文件识别链路已采用“LLM 首轮抽取 + reviewer 复核 + resolver 修正 + 规则补全评分表”的轻量多轮模式
- 如需提高分析/生成质量，下一步建议改用用户可用模型列表中的显式模型名，并单独配置 `EMBEDDING_MODEL`

## 5. 已知未收口项

- RFP 上传后的真实异步解析链路已完成显式模型 `Doubao-Seed-Code` 的实文档联调，但当前仍未验证 embedding 模型
- 章节生成已完成显式模型 `Doubao-Seed-Code` 的真实联调，后续仍建议与 `Doubao-Seed-2.0-pro` 做质量对比
- 数据库中仍存在旧表 `enterprise_profiles`、`trust_scores`，虽然当前主链路不依赖它们，但尚未正式退场
- 前端仍有少量演示型文案和非核心占位交互，尚未完全产品化
- 当前向量检索已支持在未配置 `EMBEDDING_MODEL` 时静默降级为零向量，便于先打通流程，但这不等于最终生产配置
- 商务技术文件预提资质已能沉淀证书、人员、授权、社保证明，但案例抽取和字段归一化仍可继续加强
- 商务技术文件图片已可从 docx 包内提取并入 `CompanyAsset`，但导出链路尚未把这些图片自动回填到最终投标书
- 当前章节证据附录已可带出企业资质/社保证明等图片佐证，但“按采购文件原章节模板精准插入到正文指定位置”仍待继续增强
- 采购文件识别虽然已通过质量校验，但普通 requirement 中仍存在噪声条目，后续仍需继续收紧
- 文档、前端类型定义与后端服务返回结构存在漂移，当前最明显的是：
- `materials-pack`
- `export-readiness`
- `assets-overview`
- `latest-ingest-batch`
- 后端单元测试已明确暴露 review/export 与 enterprise asset service 的能力回退，当前不能再把这些模块视为“稳定完成”
- `BiddingHall` 的选区 AI 改写接口路径仍是旧口径，属于未收口功能
- `docs/site_function_audit.md`、`docs/feature_inventory.md` 中个别状态描述已落后于当前代码，需要以本轮更新后的版本为准
- 当前远端仓库不包含本机 `models/` 大目录，也不包含超大的 `docs/商务技术文件.docx`
- 因此新机器 clone 后可以得到最新代码，但不能直接等价复现本机全部文档解析运行能力
- 后续需要补一份“模型资产准备说明”或下载脚本，解决跨环境复现问题
- 当前可先通过 `./venv/bin/python scripts/ops/check_runtime_assets.py` 判断本机是否缺少模型目录、样例文档和模板

## 5.1 本轮结构清理

本轮已完成以下仓库清理与标准化动作：

- 删除旧的 `legacy_streamlit/` 历史界面目录
- 删除旧的 `agents/`、`workflows/`、`knowledge/` 根级历史实现
- 删除失效的 `api/workflows/` 原型编排文件
- 删除过时的 POC / phase 脚本、旧压缩包、SQLite 文件、运行日志与导出产物
- 将 `scripts/` 重组为 `scripts/ops/`、`scripts/seed/`、`scripts/verify/`
- 补充目录职责文档：`docs/project_structure.md`
- 重写 `README.md` 与 `docs/architecture.md`，统一到当前真实主线

当前保留目录以 `api/`、`frontend/`、`utils/`、`scripts/`、`tests/`、`docs/` 为核心。

## 5.2 本轮 GitHub 推送说明

本轮已将当前前后端分离主线源码推送到 GitHub 私有仓库。

已推送：

- 当前 `FastAPI + React + PostgreSQL/pgvector` 主线代码
- 文档、脚本、测试、模板与迁移文件

未推送：

- `models/` 本地模型目录
- 超大样例文档 `docs/商务技术文件.docx`
- 运行期上传、导出、日志和缓存产物

因此，当前远端仓库应理解为“最新源码基线”，不是“服务器完整运行时镜像”。

## 6. 下一步建议

下一轮工作建议按下面顺序推进：

1. 先修复 `DraftingReviewService`、`EnterpriseAssetService` 与对应路由辅助函数的测试回归，恢复一个可信的后端基线
2. 对齐前端类型、页面使用方式与后端真实返回结构，优先收 `materials-pack`、`export-readiness`、`assets-overview`
3. 修正 `BiddingHall` 中仍残留的旧接口路径和未闭环交互，避免“页面有入口但功能未真正可用”
4. 在回归恢复后，再继续收紧采购文件 requirement 噪声，提升偏离矩阵和章节生成输入质量
5. 继续加强“商务技术文件 -> 企业资质库”字段归一化，补证书编号、有效期、颁发单位
6. 为 Ark 单独选定一个兼容的 `EMBEDDING_MODEL`，恢复真实向量检索能力
7. 推进模板保样式导出，并把已提取的图片证据插入最终文档
8. 在代码和测试重新稳定后，再补“真实上传采购文件 / 整项目自动续写 / 最终导出文件落地”浏览器用例
