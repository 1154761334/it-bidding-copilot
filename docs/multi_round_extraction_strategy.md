# 多轮识别与校验策略

## 1. 设计目标

当前项目不采用“全链路重型多智能体”方案，而采用：

- 单主工作流
- 局部多轮校验
- `Generate -> Critique -> Repair` 统一范式

目标是同时满足：

- 提高采购文件、企业资质、标书生成的准确率
- 保持后端架构简单，可调试
- 在需要时用更多 token 换取更高准确率

## 2. 推荐适用范围

### 2.1 采购文件识别

这是最值得做多轮校验的环节，因为后续偏离矩阵、章节生成、终审都依赖它。

建议流程：

1. `Extractor`
   - 提取 `project_info`
   - 提取 `requirements`
   - 提取 `scoring_items`
   - 提取 `fatal_items`
2. `Reviewer`
   - 只检查，不直接重写明细
   - 检查项目名称、预算、截止时间、评分章节覆盖、资格章节覆盖
3. `Resolver`
   - 只修正元信息和覆盖标志
   - requirements 明细仍由第一轮和规则补全负责

当前实现：

- `utils/rfp_analyzer.py`
- 第一轮抽取后会进入轻量 reviewer
- reviewer trace 落在 `analysis_trace.review_round`
- 如果 reviewer 超时或失败，不阻断主链路

### 2.2 企业资质提取

建议采用轻量双阶段：

1. `Parser`
   - 规则切块
   - 图片证据关联
   - 候选证书 / 人员 / 案例 / 授权 / 社保提取
2. `Normalizer`
   - LLM 标准化
   - 字段归一
   - 去重
   - 校验后入库

当前实现：

- `utils/business_doc_asset_extractor.py`
- `utils/business_asset_llm_extractor.py`
- `api/services/enterprise_ingest_service.py`

### 2.3 标书生成

建议保留单主工作流，不拆成过多 agent。

推荐角色：

1. `Planner`
   - 章节任务规划
   - 素材分配
2. `Writer`
   - 章节正文生成
3. `Auditor`
   - 是否命中要求
   - 是否缺证据
   - 是否存在幻觉或空章节

当前项目已经具备较接近该模式的工作流基础：

- `api/services/drafting_workflow.py`
- `review -> revise` 已具备闭环雏形

## 3. 为什么不做全链路重型多智能体

原因：

- 调试复杂
- 成本更高
- 时延更大
- 结果漂移更难定位
- 不利于接口和数据库契约稳定

因此当前策略是：

- 用 service / workflow 保持业务主链清晰
- 只在高风险节点增加 reviewer
- reviewer 失败时不能阻断主流程

## 4. 当前推荐落地方式

### 4.1 采购文件识别

优先级最高，建议继续增强：

- 评分项抽取
- 废标项抽取
- 资格项与证明材料映射
- 项目元信息复核

### 4.2 企业资质

继续增强：

- 证书编号
- 发证日期 / 有效期
- 颁发单位
- 人员与社保、案例的关联

### 4.3 标书生成

继续增强：

- 章节级证据链
- 章节级审稿修正
- 未通过章节禁止导出最终版

## 5. 当前结论

最适合本项目的方案不是“更多 agent”，而是：

- 简单主流程
- 关键节点多轮校验
- reviewer 只做高价值复核
- 失败自动 fallback

这是当前在准确率、复杂度、可维护性之间最平衡的路线。
