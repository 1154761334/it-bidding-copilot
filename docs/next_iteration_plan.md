# 2026-04-10 下一轮执行计划

## 1. 本轮目标

本轮不再把重点放在“修服务回归”，而是基于当前已恢复的可信基线，继续收主流程中仍明显半成品的确认环节。

补充约束：

- 后续对“企业资质解析”和“采购文件解析”的验收，不再以“有结果输出”为主，而以“是否具备实战作用”为主
- 质量标准见 `docs/parsing_quality_bar.md`

本轮主目标：

1. 把“企业资质解析”和“采购文件解析”提升到实战可用标准，而不是停留在“有结构化结果”
2. 把 `/rfp` 从“可编辑结果页”收口为“分析确认工作台”
3. 规划并启动多公司 / 多项目上下文收口
4. 在不扩高级能力的前提下，守住当前 `54 passed + frontend build 通过` 的基线
5. 在页面改动后补回针对性回归验证，并决定是否继续进入真实模型端到端联调

## 2. 本轮范围

### In Scope

- 文档基线校准
- 解析质量门槛定义
- 企业资质解析质量验证与修正
- 采购文件解析真实任务验证与修正
- `RFPAnalysis` 确认工作台 Phase A
- 多公司 / 多项目上下文方案收口
- `/rfp -> /deviation` 步骤状态收口
- 相关文档、回归结果与任务状态同步
- 针对性 `pytest`、前端 `build`、局部 Playwright 回归

### Out of Scope

- 编标大厅版本管理
- “接受采用”状态流转
- 审标后自动修复回写
- 偏离矩阵 Excel 导出
- 采购文件历史报告页

这些能力都不是当前主流程最薄弱的点，继续前置只会把范围重新打散。

## 3. 排期

### 2026-04-10

- Workstream 0：校准文档与任务基线
- Workstream Q：定义解析质量门槛
- Workstream A：验证并修复解析链路中的真实阻塞点
- Workstream 1：启动 `RFPAnalysis` 确认工作台改造

### 2026-04-11

- Workstream 1：完成页面结构收口、状态表达和下一步引导
- Workstream 2：补充必要的前端交互守卫与文案
- Workstream M：启动多公司 / 多项目上下文设计与入口收口

### 2026-04-12

- Workstream 3：执行回归验证
- 优先顺序：`pytest` -> `frontend build` -> 相关 Playwright 用例

### 2026-04-13

- Workstream 4：若页面和回归稳定，再执行真实模型链路抽样联调
- 同步更新 `docs/current_status.md`、`docs/feature_inventory.md`、开发日志

## 4. 工作流拆分

### Workstream 0：文档与基线校准

状态：`completed`

任务：

1. 修正仍写着 `8 failed, 8 passed` 的旧状态文档
2. 新增本轮执行计划文档
3. 把下一轮优先级统一到“RFP 确认工作台优先”

验收：

- `docs/architecture.md`
- `docs/site_function_audit.md`
- `docs/feature_inventory.md`
- `docs/main_flow_task_list.md`

以上文档口径与当前代码、测试结果一致

### Workstream Q：解析质量门槛

状态：`completed`

目标：

- 明确“实战可用”不是“只要有结构化输出”
- 后续所有解析能力改动都按统一质量门槛验收

产出：

- `docs/parsing_quality_bar.md`

验收：

- 已明确企业资质解析和采购文件解析的最低可用标准、不可接受情况和后续验收方式

### Workstream A：解析链路真实验证与修正

状态：`completed`

目标：

- 不再依赖历史样例结果，直接验证新任务是否真的能跑完
- 修复阻断“企业资质解析”和“采购文件解析”实战可用性的真实 bug

已完成：

1. 修复 `DocumentParseService` 与 `RFPAnalysisService` 的字段兼容问题
2. 修复 `AssetMatcher` 异步检索调用错误
3. 修复商务技术文件图片未注册进资产库的问题
4. 修复采购文件质量验证脚本对历史项目 fallback 过宽的问题

当前实测：

- 商务技术文件真实 ingest：证书、案例、人员、图片均可入库
- 真实采购文件 analyze：新任务可真实完成并落项目、requirements 和 quality report

### Workstream 1：RFP 确认工作台 Phase A

状态：`in_progress`

目标：

- 让用户在 `/rfp` 明确知道当前是“预览态”还是“正式建档基线”
- 把项目确认、要求确认、质量校验、进入下一步的关系表达清楚

任务：

1. 强化状态卡和阶段提示
2. 拆出更清晰的确认视图，而不是只有一块大编辑区
3. 补齐要求数量、修改数量、质量警告的可见性
4. 明确下一步 CTA 的禁用条件和提示文案

验收：

- `/rfp` 能清晰区分“未确认”和“已确认”
- 用户能看懂为什么当前不能进入偏离矩阵
- `analysis-check` 的 warning 不再只是孤立信息块
- 当前进展：已完成第一阶段页面收口，并重新通过 `pytest` 与前端 `build`

### Workstream 2：RFP 工作台收尾

状态：`pending`

任务：

1. 统一标签、状态文案和按钮语义
2. 去掉继续误导开发的纯占位交互
3. 必要时补最小接口契约调整

### Workstream M：多公司 / 多项目上下文

状态：`pending`

目标：

- 让“企业资质解析”和“采购文件解析”不再默认绑定主公司 / 最新项目
- 为围标、多主体并行、多个项目切换提供产品层支撑

任务：

1. 梳理当前 `primary company / latest project` 依赖点
2. 为前端补公司选择和项目选择上下文
3. 让 ingest / analyze / bidding 等流程绑定当前选中主体
4. 明确项目列表、公司列表和当前上下文的接口责任

### Workstream 3：回归验证

状态：`pending`

任务：

1. `./venv/bin/python -m pytest -q --maxfail=8`
2. `cd frontend && npm run build`
3. 与 `/rfp` 相关的 Playwright 用例或等价浏览器回归

验收：

- 后端单测继续稳定通过
- 前端 build 继续通过
- `/rfp -> /deviation` 主链无明显回退

### Workstream 4：真实模型抽样联调

状态：`pending`

任务：

1. 选择一个真实采购文件样本
2. 走 analyze -> confirm -> deviation 的抽样链路
3. 记录显式模型名和结果

前提：

- Workstream 1-3 已通过

## 5. 当前执行顺序

1. 先完成 Workstream 0
2. 先用 Workstream A 守住解析链路真实可用
3. 继续推进 Workstream 1
4. 再进入 Workstream M
5. 页面稳定后再做 Workstream 3
6. 最后视情况决定是否执行 Workstream 4

## 6. 当前决策

本轮明确不优先做 `BiddingHall` 版本管理，原因是：

- 当前只有 `BidDraft.version` 计数，没有版本快照模型
- 前端“版本”按钮仍是纯占位
- 这类能力需要新的数据结构、接口和回滚策略，不适合插在主流程确认链路之前

因此，本轮先收 `/rfp`，再考虑编标大厅的更深能力。
