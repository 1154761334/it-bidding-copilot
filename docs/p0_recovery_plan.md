# P0 收口与可信基线恢复计划

本文档用于把 `2026-04-09` 这一轮“查漏补缺评估”收敛成可执行的开发计划，目标不是继续加新功能，而是先恢复主流程的可信状态。

当前判断依据来自三部分：

- 当前核心文档：`docs/current_status.md`、`docs/feature_inventory.md`、`docs/frontend_backend_alignment.md`
- 当前代码：`api/routers/*`、`api/services/*`、`frontend/src/pages/*`、`frontend/src/services/api.ts`
- 本次重新核验结果：`./venv/bin/python -m pytest -q --maxfail=12` -> `9 failed, 44 passed`

## 1. 计划目标

本轮目标只有一个：

- 把“企业建库 -> RFP 解析 -> 偏离确认 -> 素材确认 -> 编标 -> 审标 -> 导出”主流程恢复到可验证、可回归、可继续扩展的状态

具体来说，要解决的是：

1. 后端关键服务返回结构弱化，已经落后于前端页面和测试预期
2. 前端类型定义和后端真实返回结构存在漂移
3. 页面中仍残留旧接口路径和半截历史实现
4. 历史联调结论已不能代表当前仓库真实基线

## 2. 本轮不做什么

为了防止继续扩散范围，本轮明确不做以下事项：

- 不新增大的产品模块
- 不继续扩写复杂协作 UI
- 不优先做版本管理、接受采用、审标自动修复、Excel 导出等高级能力
- 不把重点放在新一轮模型调优或 requirement 抽取增强上

这些能力并非不重要，而是必须建立在可信服务层和稳定契约之上。

## 3. 当前已确认的高风险漂移点

### 3.1 审标与导出

- `DraftingReviewService.run_red_team_review` 当前只返回最基础的 `section_reviews`
- `DraftingReviewService.build_export_readiness` 当前只做两项基础检查
- `/audit` 与 `/review` 页面已经依赖更完整的返回结构
- 当前单测明确证明审标结果结构和导出前检查结构已经回退

涉及文件：

- `api/services/drafting_review_service.py`
- `api/routers/drafting_v2.py`
- `frontend/src/pages/ReviewCycle.tsx`
- `frontend/src/pages/ReviewExport.tsx`
- `frontend/src/services/api.ts`

### 3.2 企业资产中心

- `assets-overview` 当前只稳定返回 `counts + certificates`
- `latest-ingest-batch` 当前只返回最近日期和源文件列表
- `intake-readiness` 返回结构弱于前端类型与文档口径
- 当前单测证明这些能力已经无法满足既有预期

涉及文件：

- `api/services/enterprise_asset_service.py`
- `api/routers/enterprise_v2.py`
- `frontend/src/pages/EnterpriseAI.tsx`
- `frontend/src/store/useEnterpriseStore.ts`
- `frontend/src/services/api.ts`

### 3.3 项目素材包

- 前端把素材包当成编标前关键确认步骤
- 后端 `materials-pack` 仍是简化结构，缺少 `project_id`、`selection`、`selected`、`summary`、`materials` 等完整字段
- 页面能显示，但契约不稳定，后续任何增强都容易继续漂移

涉及文件：

- `api/services/drafting_material_service.py`
- `api/routers/drafting_v2.py`
- `frontend/src/store/useBiddingStore.ts`
- `frontend/src/pages/BiddingHall.tsx`
- `frontend/src/services/api.ts`

### 3.4 编标大厅残留旧接口

- `BiddingHall` 选区 AI 改写仍调用旧 `/api/v2/drafting/...`
- 当前真实后端接口已是 `/api/v1/bid/draft/{draft_id}/rewrite`
- 这属于明确的收口缺口，不应继续保留

涉及文件：

- `frontend/src/pages/BiddingHall.tsx`
- `api/routers/drafting_v2.py`

### 3.5 历史残留实现混入当前主线

- `api/routers/drafting_v2.py` 顶部保留了一段半截 `build_materials_pack()` 旧实现
- 该实现依赖未定义辅助函数且没有返回值
- 虽然当前路由实际走 service，但这类死代码会持续误导后续开发

涉及文件：

- `api/routers/drafting_v2.py`

## 4. 总体执行顺序

本轮建议严格按下面顺序推进，不要并行打散：

1. 先修审标与导出前检查
2. 再修企业资产中心服务层
3. 再统一项目素材包契约
4. 再清理前端旧接口和历史残留代码
5. 最后恢复 pytest 与页面回归基线

原因：

- 审标与导出是主流程最后的质量闸门，收益最高
- 企业资产中心是主流程输入底座，影响后续推荐与证据链
- 素材包是编标前的关键拦截点，必须在主流程中稳定
- 接口清理和死代码清理属于低成本高收益项，应夹在主修复之后完成
- 回归验证必须放在结构修复之后，否则只会反复记录漂移

## 5. 分工作流详细计划

## Workstream A：审标结果与导出前检查收口

### 目标

恢复 `/audit` 与 `/review` 页面背后的服务层完整性，使审标结果、导出拦截和测试预期重新对齐。

### 必做项

1. 重构 `run_red_team_review`
2. 补全 `build_export_readiness`
3. 修正导出器对图片证据附录的处理

### 具体改动

#### A1. 统一 `ReviewResult` 契约

后端应补齐至少以下字段：

- `project_id`
- `win_rate`
- `critical_risks`
- `optimization_suggestions`
- `winning_highlights`
- `section_reviews`
- `total_drafts`
- `approved_drafts`
- `round`

`section_reviews` 内至少应稳定返回：

- `draft_id`
- `section_title`
- `verdict`
- `feedback`
- `source_fragments`
- `generation_status`

### 设计要求

- `generation_status != COMPLETED` 的章节必须判为 `REJECTED`
- 空内容章节必须明确标记为不可导出
- `feedback` 不应只返回原始 `audit_logs.final_feedback`，需要对未完成场景给出产品化提示

#### A2. 补全 `ExportReadiness` 契约

后端应补齐至少以下结构：

- `project_id`
- `project_name`
- `project_status`
- `ready`
- `checks`
- `rejected_sections`

`checks` 至少包含：

- `all_drafts_completed`
- `project_status_valid`
- `master_template_available`
- `image_evidence_ready`

`rejected_sections` 至少包含：

- `draft_id`
- `section_title`
- `generation_status`
- `audit_feedback`

### 设计要求

- readiness 不能只看项目状态，必须看章节状态和证据状态
- 如果章节未完成、待复核或被审标判为拒绝，必须进入 `rejected_sections`
- 如果存在采购母版 docx，应明确标记母版可用
- 如果内容正文和证据片段中包含图片证据，应统计并写入 detail

#### A3. 修正导出器图片证据附录

当前导出器追加附录时，图片证据可能只留下原始 `[IMAGE:...]` 标记。

需要补齐：

- 证据附录中的图片证据可读化文案
- 图片证据文件名展示
- 文本证据与图片证据并存时不丢信息

### 涉及文件

- `api/services/drafting_review_service.py`
- `api/services/bid_exporter.py`
- `api/routers/drafting_v2.py`
- `frontend/src/services/api.ts`

### 验收标准

1. 当前失败的审标相关单测全部通过
2. `/audit` 页面能稳定显示章节 verdict、状态、证据链
3. `/review` 页面 readiness 检查项与被拦截章节可稳定展示
4. 不合格项目仍被前后端双重拦截，不能导出

### 推荐执行者

- `Codex` 主导设计、服务层和验收
- `Antigravity` 可承接具体实现和前端契约对齐

## Workstream B：企业资产中心服务层收口

### 目标

让企业资产中心从“能显示部分数据”提升到“可稳定作为主流程素材底座”。

### 必做项

1. 补全 `assets-overview`
2. 补全 `latest-ingest-batch`
3. 稳定 `intake-readiness`
4. 保证 `assets-browser` 对空值和弱数据安全

### 具体改动

#### B1. 补全 `assets-overview`

后端应稳定返回：

- `counts`
- `certificates`
- `cases`
- `personnel`
- `source_documents`
- `images`

每类条目至少要满足当前前端类型中声明的核心字段，不要求一次把所有业务字段做到极致，但必须稳定一致。

#### B2. 补全 `latest-ingest-batch`

后端应稳定返回：

- `company_id`
- `has_batch`
- `batch_date`
- `source_documents`
- `counts`
- `notes`

`counts` 至少统计：

- `source_documents`
- `certificates`
- `cases`
- `images`

如果没有批次，应返回结构完整的空态，而不是只返回极简字段。

#### B3. 稳定 `intake-readiness`

后端应确保：

- `ready`
- `checks`
- `warnings`

三者结构稳定，避免前端继续做弱兼容猜测。

#### B4. 修正 `assets-browser` 的空数据健壮性

当前服务层对测试桩和弱数据不够稳，遇到 `None` 项会直接抛错。

需要补齐：

- 空列表安全处理
- 条目字段缺失时的兜底
- 查询和排序过程中的弱数据容错

### 涉及文件

- `api/services/enterprise_asset_service.py`
- `api/routers/enterprise_v2.py`
- `frontend/src/services/api.ts`
- `frontend/src/store/useEnterpriseStore.ts`
- `frontend/src/pages/EnterpriseAI.tsx`

### 验收标准

1. 当前失败的企业资产相关单测全部通过
2. 企业资产中心首页摘要、建库确认、最近导入批次都可稳定展示
3. 资产浏览不因个别弱数据或空字段崩溃
4. 前端无需再针对缺字段做过多兜底猜测

### 推荐执行者

- `Antigravity` 负责服务层补全与前端对齐
- `Codex` 负责接口契约审查与回归验收

## Workstream C：项目素材包契约统一

### 目标

把素材包从“半成品返回结构”升级为当前编标主流程可依赖的稳定协议。

### 必做项

1. 统一 `ProjectMaterialsPack` 返回结构
2. 补齐 `selection`、`selected`、`summary`
3. 把项目材料 `materials` 纳入统一结构

### 具体改动

后端 `materials-pack` 建议至少稳定返回：

- `project_id`
- `project_name`
- `project_status`
- `confirmed`
- `drafting_notes`
- `selection`
- `recommended`
- `available`
- `selected`
- `summary`

其中：

- `selection` 反映当前已保存的 ID 选择
- `selected` 返回已选条目的完整展示对象
- `available.materials` 需要纳入项目补充材料
- `summary` 至少包含需求总数和各类已选数量

### 设计要求

- 不要求本轮就做复杂推荐理由
- 但必须把前端正在消费的对象结构稳定下来
- 保存接口和读取接口必须返回同一套结构

### 涉及文件

- `api/services/drafting_material_service.py`
- `api/routers/drafting_v2.py`
- `frontend/src/services/api.ts`
- `frontend/src/store/useBiddingStore.ts`
- `frontend/src/pages/BiddingHall.tsx`

### 验收标准

1. `BiddingHall` 素材包区域不再依赖弱兼容字段
2. 素材读取、保存、确认、上传后刷新均走同一结构
3. 素材未确认时，单章节生成和整项目生成拦截逻辑保持正常

### 推荐执行者

- `Antigravity` 主实现
- `Codex` 审核契约和验收

## Workstream D：旧接口与历史残留清理

### 目标

清掉确定性错误和误导性残留，降低后续协作噪音。

### 必做项

1. 清理 `BiddingHall` 旧 `/api/v2` 改写接口调用
2. 清理 `drafting_v2.py` 顶部半截 `build_materials_pack()` 死代码
3. 检查是否还有其他显式 `/api/v2` 残留

### 涉及文件

- `frontend/src/pages/BiddingHall.tsx`
- `api/routers/drafting_v2.py`

### 验收标准

1. 前端不再出现旧 `/api/v2` 请求
2. 路由文件中不再存在半截旧实现
3. 搜索结果中不再存在主流程残留旧接口

### 推荐执行者

- `Antigravity` 或 `Codex` 均可

## Workstream E：可信回归基线恢复

### 目标

重新建立“当前仓库状态”的可信验收口径，避免继续引用历史联调成绩。

### 必做项

1. 先恢复后端单测
2. 再重跑关键页面 smoke
3. 最后更新状态文档

### 推荐验证顺序

1. `./venv/bin/python -m pytest -q`
2. `npm run build --prefix frontend`
3. 条件允许时重跑主流程 Playwright smoke
4. 条件允许时重跑最小真实链路联调

### 文档更新要求

完成本轮后至少更新：

- `docs/current_status.md`
- `docs/feature_inventory.md`

如改动较大，再补：

- `docs/development_logs/YYYY-MM-DD-agent-name.md`

### 验收标准

1. 本轮已知 9 个失败用例全部修复
2. 前后端主流程页面在当前仓库状态下可再次说明“哪些已重跑、哪些未重跑”
3. 文档不再继续引用已经过时的成功记录来掩盖当前回归

### 推荐执行者

- `Codex` 主导验收与文档

## 6. 建议分两轮落地

为了降低合并风险，建议按两轮提交，而不是一次大改到底。

### Iteration 1：恢复主流程后半段闸门

范围：

- Workstream A
- Workstream D

目标：

- 先恢复审标与导出可信度
- 同时清掉旧接口和残留死代码

建议提交结果：

- 一组服务层修复
- 一组前端接口路径修复
- 一组测试恢复

### Iteration 2：恢复主流程输入与编标前契约

范围：

- Workstream B
- Workstream C
- Workstream E

目标：

- 恢复企业资产中心和素材包的契约稳定性
- 重建本轮可信基线

建议提交结果：

- 一组企业资产服务层修复
- 一组素材包契约统一
- 一组回归验证与文档更新

## 7. 对 Antigravity 的执行要求

如果把本轮实现交给 `Antigravity`，建议明确以下约束：

1. 先读 `docs/current_status.md`、`docs/frontend_backend_alignment.md`、`docs/p0_recovery_plan.md`
2. 不要新增大功能，只按当前计划修复漂移和契约
3. 修改返回结构时必须同步更新前端类型
4. 不要保留旧接口兼容分支，直接收口到 `/api/v1/*`
5. 完成后必须附上已执行的验证命令和结果
6. 中等及以上改动后要更新状态文档

## 8. 完成定义

只有满足下面条件，本轮才算真正完成：

1. `DraftingReviewService` 与 `EnterpriseAssetService` 回到和前端类型一致的口径
2. `materials-pack` 返回结构稳定，不再是简化版临时对象
3. `BiddingHall` 不再访问旧 `/api/v2` 接口
4. 当前已知 `pytest` 失败项清零
5. 文档明确写清本轮重新验证过的真实结果

在满足这些条件之前，不建议继续往版本管理、自动修复回写、模板保样式增强等高级能力上扩展。
