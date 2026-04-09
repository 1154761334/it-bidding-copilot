# 前端产品形态与后端承接矩阵

本文档用于回答三个问题：

1. 前端最初设想的产品形态到底包含哪些模块
2. 后端当前已经真实承接到什么程度
3. 下一轮开发应该按什么顺序推进，避免继续前后端错位

## 1. 结论摘要

当前前端已经表达出完整的目标产品流程：

1. 企业建档与资产沉淀
2. 招标文件识别与可投性评估
3. 偏离矩阵确认
4. 章节生成与编标协作
5. 红队审标
6. 最终导出

后端主链路已经基本存在，但前端和后端之间仍有三类错位：

- 有真实后端能力，但前端未完全接入
- 前端已有页面，但交互仍停留在占位或半成品
- 存在重复页面或历史页面，容易误导后续开发

因此，下一阶段不应继续零散补点，而应按“前端目标形态 -> 后端承接矩阵 -> 页面收口 -> 主流程补齐”的方式推进。

## 2. 当前前端模块

### 2.1 主导航中的页面

来自 [frontend/src/App.tsx](/root/it-bidding-copilot/frontend/src/App.tsx) 与 [frontend/src/components/layout/SideNavBar.tsx](/root/it-bidding-copilot/frontend/src/components/layout/SideNavBar.tsx)：

- `/dashboard` -> `Dashboard`
- `/profile` -> `EnterpriseAI`
- `/profile/manual` -> `ManualProfile`
- `/rfp` -> `RFPAnalysis`
- `/bidding` -> `BiddingHall`
- `/deviation` -> `DeviationMatrix`
- `/audit` -> `ReviewCycle`
- `/review` -> `ReviewExport`

### 2.2 已移除的重复页面

以下历史页面已从当前前端代码中移除：

- `Profile.tsx`
- `Export.tsx`

原因：
- 未接入当前主路由
- 与现行主页面职责重叠
- 容易在后续开发中制造重复实现

## 3. 页面级承接矩阵

### 3.1 Dashboard

页面文件：
- [frontend/src/pages/Dashboard.tsx](/root/it-bidding-copilot/frontend/src/pages/Dashboard.tsx)

目标形态：
- 首页总览
- 企业档案完备度
- 快速启动入口
- 近期项目

当前前端依赖：
- `dashboardService.getStats()`
- `dashboardService.getContext()`
- `useEnterpriseStore.fetchProfile()`

后端承接：
- [api/routers/dashboard_v2.py](/root/it-bidding-copilot/api/routers/dashboard_v2.py)
- `GET /api/v1/dashboard/stats`
- `GET /api/v1/dashboard/context`

状态判断：
- 已真实接通
- 但统计口径偏简化，仍偏“系统状态卡片”而不是“项目运营首页”

### 3.2 企业资产中心

页面文件：
- [frontend/src/pages/EnterpriseAI.tsx](/root/it-bidding-copilot/frontend/src/pages/EnterpriseAI.tsx)
- [frontend/src/pages/ManualProfile.tsx](/root/it-bidding-copilot/frontend/src/pages/ManualProfile.tsx)

目标形态：
- 企业基础信息维护
- 资产上传与解析
- 资信评分
- 资质、案例、人员等材料沉淀

当前前端依赖：
- `enterpriseService.getProfile()`
- `enterpriseService.updateProfile()`
- `enterpriseService.getTrustScore()`
- `enterpriseService.bulkIngest()`

后端承接：
- [api/routers/enterprise_v2.py](/root/it-bidding-copilot/api/routers/enterprise_v2.py)
- `GET /api/v1/enterprise/profile`
- `PUT /api/v1/enterprise/profile`
- `GET /api/v1/enterprise/trust-score`
- `POST /api/v1/enterprise/bulk-ingest/{company_id}`
- `POST /api/v1/enterprise/vault-ingest/{company_id}`
- `POST /api/v1/enterprise/business-doc-ingest/{company_id}`
- `GET /api/v1/enterprise/search-assets`

状态判断：
- 主链路已真实存在
- 已补资产分类浏览、详情面板与图片预览
- `ManualProfile` 中“新增证书 / 添加案例”等交互仍未真正落库

建议：
- 以 `EnterpriseAI` 为主页面
- `ManualProfile` 作为补录页保留
- 后续补编辑能力和更细的资产详情页

### 3.3 招标文件识别

页面文件：
- [frontend/src/pages/RFPAnalysis.tsx](/root/it-bidding-copilot/frontend/src/pages/RFPAnalysis.tsx)

目标形态：
- 上传 RFP
- 观察分析进度
- 展示商务、技术、废标、评分结果
- 给出 Go/No-Go 建议

当前前端依赖：
- `rfpService.analyze()`
- `rfpService.getTaskStatus()`
- `useRfpStore`

后端承接：
- [api/routers/rfp_v2.py](/root/it-bidding-copilot/api/routers/rfp_v2.py)
- `POST /api/v1/rfp/analyze`
- `GET /api/v1/rfp/status/{task_id}`
- `GET /api/v1/rfp/projects/{project_id}/analysis-check`

状态判断：
- 真实分析链路已存在
- 采购文件识别、评分项、质量校验都已有真实结果
- 当前页面已经接入 `analysis-check`
- 当前页面已经补齐主要任务阶段文案
- 当前页面已经补齐完整检查项展开
- 当质量校验为 `needs_review` 时，页面会阻止直接进入下一步

建议：
- 继续保留当前方向
- 后续补“查看历史报告”

### 3.4 偏离矩阵

页面文件：
- [frontend/src/pages/DeviationMatrix.tsx](/root/it-bidding-copilot/frontend/src/pages/DeviationMatrix.tsx)

目标形态：
- 点对点要求响应矩阵
- 查看匹配状态
- 人工修订应答
- 确认后进入编标

当前前端依赖：
- `rfpService.getDeviationMatrix()`
- `useRfpStore.analysisResult`

后端承接：
- [api/routers/rfp_v2.py](/root/it-bidding-copilot/api/routers/rfp_v2.py)
- `GET /api/v1/rfp/projects/{project_id}/deviation`

状态判断：
- 已有真实结果接口
- 编辑、保存、确认、回写都已实现
- “导出 Excel” 仍是占位

建议：
- 当前已经是项目要求确认页
- 后续补更细粒度的审核流转和 Excel 导出

### 3.5 编标大厅

页面文件：
- [frontend/src/pages/BiddingHall.tsx](/root/it-bidding-copilot/frontend/src/pages/BiddingHall.tsx)

目标形态：
- 左侧目录树
- 中间章节编辑区
- 右侧实时日志 / 智能协作面板
- 单章生成、逐章推进、版本与采用

当前前端依赖：
- `biddingService.getOutline()`
- `biddingService.startDrafting()`
- `biddingService.getDraftTaskStatus()`
- WebSocket `/api/v1/bid/stream/{draft_id}`
- `useBiddingStore`

后端承接：
- [api/routers/drafting_v2.py](/root/it-bidding-copilot/api/routers/drafting_v2.py)
- `GET /api/v1/bid/outline/{project_id}`
- `POST /api/v1/bid/draft/{draft_id}`
- `GET /api/v1/bid/draft/status/{task_id}`
- `POST /api/v1/bid/projects/{project_id}/draft-all`
- `WS /api/v1/bid/stream/{draft_id}`

状态判断：
- 基础主链路已接通
- 已接入项目级批量生成入口与批次进度展示
- 已接入“仅重试未完成章节”项目级重试入口
- 已接入章节完成、待复核、未生成统计
- 已接入当前章节证据链和审稿反馈展示
- 但页面仍存在较多“产品形态先行”的占位能力：
- “版本”
- “接受采用”
- 多角色协作面板
- 真正的章节正文持久化展示还比较弱

建议：
- 当前应把本页重新定义成“章节生成与查看页”
- 暂不继续扩展复杂协作 UI
- 下一步优先补失败原因细分与版本管理，而不是再扩复杂协作 UI

### 3.6 红队审标

页面文件：
- [frontend/src/pages/ReviewCycle.tsx](/root/it-bidding-copilot/frontend/src/pages/ReviewCycle.tsx)

目标形态：
- 发起审标
- 查看章节级 verdict
- 查看证据链
- 应用修复并重跑

当前前端依赖：
- `biddingService.getReview()`

后端承接：
- [api/routers/drafting_v2.py](/root/it-bidding-copilot/api/routers/drafting_v2.py)
- `POST /api/v1/bid/review/{project_id}`

状态判断：
- 已经能跑真实 review
- 但“Apply AI Fixes & Regenerate Draft” 仍是禁用占位
- 已补“存在未完成或待复核章节”提示，避免误把半成品当最终稿
- 页面中的英文产品语言和当前中文产品语言也未完全统一

建议：
- 审标结果、证据链可保留
- 后续需要决定是否补“按审标意见回写并重新生成”

### 3.7 终审与导出

页面文件：
- [frontend/src/pages/ReviewExport.tsx](/root/it-bidding-copilot/frontend/src/pages/ReviewExport.tsx)

目标形态：
- 汇总终审结果
- 封标前检查
- 导出正式文档

当前前端依赖：
- `biddingService.getReview()`
- `biddingService.exportDocx()`

后端承接：
- [api/routers/drafting_v2.py](/root/it-bidding-copilot/api/routers/drafting_v2.py)
- `POST /api/v1/bid/review/{project_id}`
- `POST /api/v1/bid/export-docx/{project_id}`

状态判断：
- 已可真实导出
- 导出已增加“未完成章节禁止导出”的约束
- 但“封标清单”仍是纯前端静态项

建议：
- 先保留静态封标清单
- 后面可考虑把必交材料检查做成真实配置

## 4. 页面去重状态

当前已完成：

- 删除 `Profile.tsx`
- 删除 `Export.tsx`

当前主页面集已经收口为：

- `Dashboard`
- `EnterpriseAI`
- `ManualProfile`
- `RFPAnalysis`
- `DeviationMatrix`
- `BiddingHall`
- `ReviewCycle`
- `ReviewExport`

## 5. 状态管理层判断

### `useProjectContextStore`

文件：
- [frontend/src/store/useProjectContextStore.ts](/root/it-bidding-copilot/frontend/src/store/useProjectContextStore.ts)

作用：
- 维护“当前公司 / 当前项目 / 当前草稿”

判断：
- 这是当前前端主流程的核心上下文 store
- 应继续保留

### `useEnterpriseStore`

作用：
- 企业档案与上传状态

判断：
- 当前功能偏弱
- 后续需要补“资产列表 / 结构化结果 / 分类结果”

### `useRfpStore`

作用：
- RFP 上传、轮询、结果缓存

判断：
- 当前最需要做的是把任务阶段名和质量校验结果统一

### `useBiddingStore`

作用：
- 大纲、WebSocket、章节生成、流式日志

判断：
- 当前设计已体现最终编标大厅结构
- 但应收缩到真实可维护的交互集

### `useSettingsStore`

作用：
- 模型配置、连通性测试

判断：
- 需要补 `/config/capabilities` 的前端展示

## 6. 页面与后端承接总体判断

### 已经可以进入“产品化收口”的模块

- Dashboard
- 企业档案基础读写
- RFP 分析主链路
- 偏离矩阵只读版
- 章节生成主链路
- 终审与导出主链路

### 当前最明显的错位点

1. 页面主集合已基本收口
- 当前主要问题不再是重复页面，而是主页面内部仍有部分占位交互

2. 页面中存在较多未接后的理想化交互
- 版本管理
- 接受采用
- 导出 Excel
- 审标自动修复
- 静态封标清单

3. 页面状态机和后端状态机尚未完全统一
- RFP 分析阶段名
- Draft 生成状态
- Review / Export 的前置条件

## 7. 建议的整体方案

建议按三层推进。

### 第一层：页面收口

先收产品信息架构，不急着加新功能：

1. 明确主页面
- 保留：`Dashboard`、`EnterpriseAI`、`ManualProfile`、`RFPAnalysis`、`DeviationMatrix`、`BiddingHall`、`ReviewCycle`、`ReviewExport`
- 已移除历史重复页面：`Profile`、`Export`

2. 收口文案和状态机
- 统一前端和后端阶段命名
- 去掉仍明显指向旧架构的表达

### 第二层：主流程补齐

按真实闭环顺序开发：

1. 企业资产中心
- 展示已入库的证书、案例、人员、图片证据

2. RFP 识别页
- 接 `analysis-check`
- 让用户知道“是否可进入下一步”

3. 偏离矩阵页
- 支持人工修订和确认
- 这是下一阶段最值得做的产品节点

4. 编标大厅
- 补真实章节内容展示
- 补项目级批量生成入口

5. 审标与导出
- 用更真实的完成条件驱动导出按钮

### 第三层：高级能力

- 审标意见自动修复回写
- 模板化导出增强
- 图片证据回填
- 版本管理
- Excel 导出

## 8. 推荐的下一步开发顺序

如果要开始进入下一轮开发，我建议顺序固定为：

1. 企业资产中心补“已入库结果展示”
2. 偏离矩阵升级成“确认页”
3. 编标大厅接项目级批量生成
4. 审标与导出前置条件收严
5. 后续再补高级交互

## 9. 一句话判断

前端已经把最终产品形态定义出来了，后端也已经有了可运行主链路。现在最需要的不是再零散加接口，而是按这份承接矩阵把页面逐个收口，让“理想形态”变成“真实可交付形态”。
