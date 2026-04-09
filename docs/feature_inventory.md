# 功能清单与迭代台账

本文档作为当前项目的长期功能台账，目标是解决两个问题：

1. 新开对话时，能快速知道项目已经做到哪里
2. 后续每轮开发后，可以持续更新状态，不必重新梳理全局

建议用法：

- 每完成一轮有效开发，就更新一次本文档
- 优先更新“当前状态”“缺口”“下一步”
- 如果功能被废弃或被替代，也在本文档里显式记录

状态约定：

- `done`: 已完成并至少做过一次验证
- `partial`: 已有主链路，但前端/后端/体验仍未收口
- `planned`: 已确定要做，但还未开始
- `deprecated`: 历史方案，已不再作为当前主线

## 1. 当前主流程

当前产品主流程为：

1. 企业建档与资产沉淀
2. 招标文件识别与质量校验
3. 偏离矩阵确认
4. 章节生成与编标
5. 红队审标
6. 最终导出

## 2. 功能台账

| 模块 | 功能点 | 当前状态 | 当前实现 | 主要缺口 | 下一步 |
|---|---|---|---|---|---|
| Dashboard | 首页统计与上下文 | `done` | `dashboard/stats`、`dashboard/context` 已接通 | 统计口径仍偏简化 | 后续再优化业务化指标 |
| 企业资产中心 | 企业基础信息读写 | `done` | `enterprise/profile`、`trust-score` 已可用 | 字段仍偏基础 | 后续按业务扩展 |
| 企业资产中心 | 通用材料上传 ingest | `done` | `bulk-ingest` 已接通，并已新增“最近导入批次”摘要 | 仍缺更强的本轮待确认工作流 | 后续补批次级确认视图 |
| 企业资产中心 | Obsidian Vault 导入 | `done` | `vault-ingest` 已验证 | 前端未接该入口 | 后续加入口或运维页 |
| 企业资产中心 | 商务技术文件预提资质 | `done` | `business-doc-ingest` 已验证，证书已补等级与日期字段，并新增二次清洗、去重和实名人员拆解 | 发证单位等字段仍未统一 | 后续继续归一化 |
| 企业资产中心 | 手工补录企业信息 | `done` | `ManualProfile` 当前只维护企业主体基础信息，已接 `profile` 读写 | 不再承载资产 CRUD | 保持职责单一 |
| 企业资产中心 | 企业资产结构化展示 | `partial` | 页面已接入 `assets-overview`、`assets-browser`、详情面板与图片预览 | 当前 `EnterpriseAssetService` 返回结构偏简化，与文档口径不完全一致 | 先补服务层与前端契约 |
| 企业资产中心 | 证书/案例/人员维护 | `done` | `EnterpriseAI` 已支持新增、编辑、删除和批量删除 | 暂未覆盖图片与源文件维护 | 后续评估扩展 |
| 招标文件识别 | 上传与异步分析 | `done` | `rfp/analyze`、`status` 已接通 | 历史报告页未做 | 后续补项目历史视图 |
| 招标文件识别 | 分析结果确认建档 | `partial` | `/rfp` 已支持修正项目信息和关键要求后确认建档，`analysis-confirm` 已接通 | 页面仍未拆成评分/资格/技术的分步确认工作台 | 继续收 Phase 2 |
| 招标文件识别 | 质量校验 `analysis-check` | `done` | 已接到 `RFPAnalysis` 页面并支持完整检查项展开 | 历史报告页未做 | 后续补项目历史视图 |
| 招标文件识别 | Go/No-Go 决策展示 | `partial` | 已有基础结果展示 | 解释性和证据链仍偏弱 | 后续增强解释与来源 |
| 偏离矩阵 | 只读偏离矩阵 | `done` | `deviation` 已接通 | 当前更像结果页 | 继续做确认与回写 |
| 偏离矩阵 | 人工修订与确认 | `done` | 已补保存接口、确认接口和前端确认页 | 仍缺更细粒度审核流转 | 后续再做增强 |
| 偏离矩阵 | 导出 Excel | `planned` | 前端按钮占位 | 无真实导出链路 | 放在主流程之后 |
| 编标大厅 | 大纲获取 | `done` | `outline/{project_id}` 已接通 | 目录语义仍偏粗 | 后续按章节策略优化 |
| 编标大厅 | 单章节生成 | `done` | `draft/{draft_id}` 已接通 | 正文展示还可增强 | 后续补证据与状态细节 |
| 编标大厅 | 项目级批量生成 | `done` | 后端 `draft-all`、前端批量生成入口、批次进度展示和“仅重试未完成章节”入口已接通 | 仍缺更细的失败原因分类 | 后续补逐章原因标注 |
| 编标大厅 | 项目素材包确认 | `partial` | 页面与 store 已接入素材包读取、保存、确认和补充材料上传入口 | 当前后端 `materials-pack` 返回结构与前端 `ProjectMaterialsPack` 类型未完全对齐 | 先统一接口契约 |
| 编标大厅 | 在线 Markdown 改稿 | `partial` | 已支持当前章节在线编辑、保存和版本递增 | 选区 AI 改写仍走旧 `/api/v2` 路径，版本回看也未完成 | 继续推进 Phase 4 |
| 编标大厅 | 章节证据链与审稿反馈 | `done` | 已展示当前章节 source fragments 与审稿反馈 | 证据命名仍偏原始 | 后续统一证据表达 |
| 编标大厅 | WebSocket 流式日志 | `partial` | 已可连接和显示 | 角色面板仍偏理想化 | 保留基础日志，先不做复杂协作 |
| 编标大厅 | 版本管理 | `planned` | 页面按钮占位 | 无后端设计 | 放后面 |
| 编标大厅 | “接受采用” | `planned` | 页面按钮占位 | 无状态设计 | 放后面 |
| 红队审标 | 审标结果展示 | `partial` | `bid/review/{project_id}` 已接通，页面已具备基础展示 | 当前 `DraftingReviewService` 为简化实现，返回结构弱于测试与文档预期 | 先恢复服务层完整性 |
| 红队审标 | 证据链查看 | `partial` | 可展示 source fragments | 证据命名与来源仍偏粗 | 后续增强 |
| 红队审标 | 审标后自动修复回写 | `planned` | 前端为禁用占位 | 后端暂无闭环接口 | 高级能力，后置 |
| 终审导出 | 导出 Word | `partial` | `export-docx` 路由已存在，前端有导出入口 | 本次未重新完成端到端导出校验，且 review/readiness 服务实现弱于文档口径 | 先恢复后端基线再重跑联调 |
| 终审导出 | 封标清单 | `partial` | 前端已接入 readiness 展示 | 当前 `build_export_readiness` 仅覆盖基础检查项，尚未与文档所述细项一致 | 补完整 readiness 结构 |
| 设置 | 模型配置保存 | `done` | `/config`、`/config/update` 已可用，支持独立 `EMBEDDING_MODEL` 配置 | 推荐模型策略仍偏工程化 | 后续补推荐配置 |
| 设置 | 模型连通性测试 | `done` | `/config/test-connection` 已可测 chat，配置 embedding 后也会同步校验向量模型 | 结果展示较基础 | 可后续优化 |
| 设置 | 运行时能力展示 | `done` | `/config/capabilities` 已接入设置弹窗 | 展示仍偏工程化 | 后续优化文案与推荐项 |
| 设置 | 模型默认推荐与 Ark 配置一致性 | `done` | 设置弹窗已切到 Ark / Doubao 默认口径 | embedding 推荐项仍偏通用 | 后续补更明确推荐 |
| 全站巡检 | Playwright 浏览器回归 | `partial` | 文档记录中已覆盖主站 8 个页面、设置弹窗、企业资产 CRUD、项目素材包确认、编标改稿保存 | 本次未重跑，且当前后端单测已出现明显回归 | 后端基线恢复后重跑 |

## 3. 当前建议优先级

### P0：先恢复可信基线

1. 修复 `DraftingReviewService` 与 `EnterpriseAssetService` 的测试回归
2. 对齐前端类型和后端返回结构
3. 清理 `BiddingHall` 中旧 `/api/v2` 残留接口
4. 重新建立可信的 pytest 与页面巡检基线
5. 再继续做采购 requirement 降噪、素材包体验和 embedding 联调
说明：当前独立验证脚本仍有价值，但在服务层回归未修复前，不宜继续把历史联调结果当成当前稳定基线。

## 3.1 当前实施计划

### Iteration 1：主流程产品化收口

1. 企业资产中心补分类筛选、详情面板、图片预览
2. 编标大厅补失败章节重试与证据来源视图
3. `RFPAnalysis` 展开完整 `analysis-check` 检查项
4. 设置弹窗接入 `/config/capabilities`
5. 完成回归测试与文档更新
结果：已完成，包括“仅重试未完成章节”项目级能力

### Iteration 2：生成质量提升

1. 继续清理采购文件 requirement 噪声
2. 增强商务技术文件入库字段归一化
3. 为 Ark 选定兼容的 `EMBEDDING_MODEL`
4. 恢复真实向量检索验证
当前进度：已完成 requirement 初步降噪、证书等级与日期字段归一化、embedding 配置入口；待完成真实 embedding 模型联调。

### Iteration 3：成品导出增强

1. 模板保样式导出
2. 图片证据回填 Word
3. 导出前检查项与封标清单产品化
4. 审标自动修复回写评估
当前进度：已完成导出前检查项产品化、图片标记回填、证据附录；模板保样式仍需继续增强。

### Iteration 4：全站功能巡检与状态恢复收口

1. 接入 Playwright 并覆盖主站页面 smoke
2. 覆盖企业资产 CRUD、偏离矩阵保存、审标记录与导出拦截
3. 修复 `/rfp` 刷新后丢失分析结果
4. 修复 `/deviation` 错误依赖内存态
5. 为设置弹窗补 `Escape` 关闭
结果：已完成，详见 `docs/site_function_audit.md`

### P1：产品化增强

1. 审标页文案和证据链表达统一
2. 企业资产中心补更深的编辑与预览能力
3. 采购文件历史报告页
4. 设置页推荐配置优化

### P2：高级能力

1. 审标自动修复回写
2. 模板保样式导出
3. 图片证据自动回填
4. 版本管理
5. Excel 导出

## 4. 当前已废弃或已移除

| 项 | 状态 | 说明 |
|---|---|---|
| `Profile.tsx` | `deprecated` | 与 `EnterpriseAI` 职责重叠，已删除 |
| `Export.tsx` | `deprecated` | 与 `ReviewExport` 职责重叠，已删除 |
| `legacy_streamlit/` | `deprecated` | 旧界面体系，已移除 |
| 根级 `agents/` / `workflows/` / `knowledge/` | `deprecated` | 历史实现，已移除 |

## 5. 文档关系

建议后续按下面方式查阅：

- 当前真实状态：`docs/current_status.md`
- 前后端承接矩阵：`docs/frontend_backend_alignment.md`
- 功能台账与优先级：`docs/feature_inventory.md`
- 全站巡检记录：`docs/site_function_audit.md`
- 设计要求对照：`docs/design_requirement_matrix.md`
- 架构与目录：`docs/architecture.md`、`docs/project_structure.md`

## 6. 下次开发前优先阅读

如果后续新开对话，建议优先阅读：

1. `docs/current_status.md`
2. `docs/frontend_backend_alignment.md`
3. `docs/feature_inventory.md`
