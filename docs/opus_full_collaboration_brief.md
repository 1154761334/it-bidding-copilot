# IT Bidding Copilot — 联合研发总方案

> 本文档面向外部协作者（Opus），用于在一份文档内完整了解：产品定位、功能进度、代码架构现状、架构问题诊断、技术思路评估、可借鉴的开源模式、以及推荐路线。

---

## 一、项目定位

面向政企 IT 投标场景，建立从"企业资质建库 → 采购文件识别 → 偏离矩阵确认 → 章节生成 → 红队审标 → 最终导出"的完整工作流。

| 维度 | 选型 |
|---|---|
| 前端 | React + Vite（HashRouter） |
| 后端 | FastAPI（uvicorn） |
| 数据库 | PostgreSQL + pgvector |
| AI | LangChain `ChatOpenAI` + LangGraph（章节生成工作流） |
| 接口规范 | `/api/v1/*` |
| 当前验证 | 53 pytest passed · 22 Playwright passed |

---

## 二、产品主线与详细进度

### A. 企业资料建库 — 完成度 ≈ 85%

**已完成：**
- 企业基础信息 CRUD（`/api/v1/enterprise/profile`）
- 通用材料上传 `bulk-ingest`、Obsidian Vault 导入 `vault-ingest`
- 商务技术文件预提资质：`DoclingWrapper` 解析 → `BusinessDocAssetExtractor` 规则切块 → `BusinessAssetLLMExtractor` LLM 标准化 → 后端校验入库
- 二次清洗、去重、实名人员拆解
- 企业资产结构化展示、分类浏览、图片预览
- 证书/案例/人员 新增/编辑/删除/批量删除
- 企业建库确认检查区 + 本轮新入库批次摘要

**缺口：**
- 批次级确认/回退工作台未做
- 发证单位等字段归一化不完整
- 图片与文本证据绑定粒度可提升

**关键代码：**
- 路由层：[enterprise_v2.py](file:///root/it-bidding-copilot/api/routers/enterprise_v2.py)（902 行，含大量应下沉的业务逻辑）
- 服务层：[enterprise_ingest_service.py](file:///root/it-bidding-copilot/api/services/enterprise_ingest_service.py)（669 行，核心 ingest 引擎）
- 工具层：[docling_wrapper.py](file:///root/it-bidding-copilot/utils/docling_wrapper.py)、[business_doc_asset_extractor.py](file:///root/it-bidding-copilot/utils/business_doc_asset_extractor.py)、[business_asset_llm_extractor.py](file:///root/it-bidding-copilot/utils/business_asset_llm_extractor.py)
- 前端：[EnterpriseAI.tsx](file:///root/it-bidding-copilot/frontend/src/pages/EnterpriseAI.tsx)（52KB 单文件）

---

### B. 采购文件识别 — 完成度 ≈ 80%

**已完成：**
- 上传 + 异步分析 → `analysis-check` 质量校验
- LLM 首轮抽取 → Reviewer 复核 → Resolver 修正 → 规则补全评分表
- 项目元信息、要求、废标项、评分项提取
- 前端确认建档（修正项目信息后确认）
- 偏离矩阵前置确认

**缺口：**
- 未拆成评分/资格/技术的分步确认工作台
- 不同招标文件结构差异导致泛化质量不稳定
- 隐性废标项识别不稳定

**关键代码：**
- 核心引擎：[rfp_analyzer.py](file:///root/it-bidding-copilot/utils/rfp_analyzer.py)（538 行，含 `Extractor → Reviewer → Resolver` 多轮链路）
- 服务层：[rfp_analysis_service.py](file:///root/it-bidding-copilot/api/services/rfp_analysis_service.py)
- 路由层：[rfp_v2.py](file:///root/it-bidding-copilot/api/routers/rfp_v2.py)

---

### C. 偏离矩阵 — 完成度 ≈ 90%

**已完成：** 展示、编辑、保存、确认全链路

**缺口：** 更细粒度审核流转、Excel 导出

---

### D. 编标工作台 — 完成度 ≈ 75%

**已完成：**
- 大纲生成、单章生成、项目级批量生成、"仅重试未完成"
- 项目素材包：智能推荐 + 人工勾选 + 确认前拦截
- 在线 Markdown 编辑 + 保存 + 版本递增
- 证据链 + 审稿反馈展示
- 章节生成工作流：LangGraph `StateGraph`（`Researcher → Writer → Auditor → Refiner`）

**缺口：**
- 选区 AI 改写、整章补强/压缩/对齐评分点
- 版本回看
- 更成熟的 Markdown 编辑器

**关键代码：**
- 核心引擎：[drafting_workflow.py](file:///root/it-bidding-copilot/api/services/drafting_workflow.py)（503 行，LangGraph 状态图编排）
- 路由层：[drafting_v2.py](file:///root/it-bidding-copilot/api/routers/drafting_v2.py)（631 行，含素材包构建和导出 readiness 等业务逻辑）
- 前端：[BiddingHall.tsx](file:///root/it-bidding-copilot/frontend/src/pages/BiddingHall.tsx)（33KB 单文件）

---

### E. 审标与导出 — 完成度 ≈ 70%

**已完成：**
- 红队审标（逐章 verdict + 证据链）
- 未完成章节前置拦截
- DOCX 导出（母版优先、图片回填、证据附录）
- 导出前 readiness 检查

**缺口：**
- 模板保样式增强
- 正文精确图片插入
- 审标后自动修复闭环

---

## 三、架构问题诊断

> [!CAUTION]
> 以下是经过代码级审查确认的架构问题，**建议在继续功能开发前先做一轮收敛**。

### 🔴 高优先级

| # | 问题 | 现状 | 影响 |
|---|---|---|---|
| 1 | **Router 臃肿** | `enterprise_v2.py` 902 行、`drafting_v2.py` 631 行，5+ 个 `build_*` 业务函数 + 10 个 Pydantic schema 直接写在路由中 | 业务逻辑无法单元测试；service 层被架空 |
| 2 | **双配置系统** | 根级 `config.py`（`os.getenv` + `OPENAI_API_KEY`）vs `api/core/config.py`（`pydantic-settings` + `LLM_API_KEY`）互不引用 | "改了配置没生效"幽灵 bug |
| 3 | **utils/ vs api/services/ 边界模糊** | `utils/rfp_analyzer.py`（538 行核心引擎）本应在 service 层 | "核心逻辑在哪"无唯一答案 |
| 4 | **同步 DB + async FastAPI** | `create_engine` 同步引擎，所有 `db.query()` 阻塞线程池 | 并发受限，与 `ainvoke` 混用易 stall |

### 🟡 中优先级

| # | 问题 | 影响 |
|---|---|---|
| 5 | 前端页面过大（`EnterpriseAI.tsx` 52KB、`BiddingHall.tsx` 33KB） | 每次改动都痛 |
| 6 | Pydantic schema 散落在 router 中（`api/schemas/` 只 1 文件） | 复用需反向 import |
| 7 | 素材包状态用 JSON 文件 + 硬编码路径 | 多实例/容器化丢失 |
| 8 | `crewai`、`langgraph`、`faiss-cpu` 等重型依赖未实际使用 | 拖慢安装 |
| 9 | 双 API 前缀注册（`/api/v1/*` + `/api/*`） | OpenAPI 文档翻倍 |
| 10 | Embedding 维度 `Vector(1536)` 硬编码 | 换模型需改表 |

---

## 四、文档解析栈现状与设计

### 4.1 当前实现

| 组件 | 定位 | 文件 |
|---|---|---|
| `DoclingWrapper` | DOCX 解析主引擎（python-docx + docling 混合） | [docling_wrapper.py](file:///root/it-bidding-copilot/utils/docling_wrapper.py) |
| `BusinessDocAssetExtractor` | 规则切块：按编号层级拆章节 → 识别证书/案例/人员 | [business_doc_asset_extractor.py](file:///root/it-bidding-copilot/utils/business_doc_asset_extractor.py) |
| `BusinessAssetLLMExtractor` | LLM 标准化：证书类型/等级/有效期归一 | [business_asset_llm_extractor.py](file:///root/it-bidding-copilot/utils/business_asset_llm_extractor.py) |
| `word_chunker` | 简单 Word 文本切块 | [word_chunker.py](file:///root/it-bidding-copilot/utils/word_chunker.py) |
| `word_engine` | Word 回写/导出辅助 | [word_engine.py](file:///root/it-bidding-copilot/utils/word_engine.py) |

**问题：** 没有统一解析门面层。`DoclingWrapper` 同时承担了 docx 解析和 docling 调用，业务代码直接耦合。

### 4.2 已设计但未实现的目标架构

详见 [document_parsing_stack_design.md](file:///root/it-bidding-copilot/docs/document_parsing_stack_design.md)：

```
           ┌─────────────────────────────────┐
           │   document_parse_service.py      │  ← 统一门面
           │   parse(file, type_hint, mode)   │
           └──────────┬──────────────────────┘
                      │
        ┌─────────────┼─────────────┬──────────────┐
        ▼             ▼             ▼              ▼
   python-docx     MinerU     Unstructured      OCR
   + OOXML        (PDF/复杂)   (多格式兜底)    (图片证照)
                      │
                      ▼
              统一元素输出 schema
   { sections, tables, images, raw_markdown, quality_report }
                      │
                      ▼
              AI 语义抽取层
   (证书/评分/资格/人员/案例 → 结构化入库)
```

---

## 五、可借鉴的开源模式

> [!IMPORTANT]
> 没有一个现成仓库能直接抄成投标系统。但可以组合借鉴。

### 5.1 值得借鉴的项目

| 项目 | 抄什么 | 不抄什么 |
|---|---|---|
| **MinerU** | 文档→Markdown/JSON、复杂版面恢复、OCR融合、PDF解析质量 | 它不做投标业务 |
| **Unstructured** | 统一 `partition` 接口、多格式元素切分、元素类型体系 | 偏通用，不做业务抽取 |
| **RAGFlow / Dify / FastGPT** | 异步任务状态机（queued→parsing→parsed→failed）、文档入库→切块→检索的管道设计 | 对投标场景的业务抽取和Word回写仍要自己做 |

### 5.2 值得抄的 4 个架构模式

#### 模式 1：附件统一接入层
- 上传后统一变成任务对象
- 有完整状态机：`queued → parsing → parsed → failed`
- **当前项目缺口：** `SourceDocument` 只有 `file_type` 字段，没有解析状态

#### 模式 2：文档解析门面
- 所有外部解析器走同一入口
- 业务代码不直接耦合具体解析库
- **当前项目缺口：** `DoclingWrapper` 直接被 `EnterpriseIngestService` 调用，无门面

#### 模式 3：元素级输出（而非一整坨文本）
- 输出结构：段落、表格、图片、标题层级、坐标/来源
- **当前项目实现：** `DoclingWrapper` 已输出 `{markdown, images, coordinates}`，但 markdown 是一整坨，未拆成元素列表

#### 模式 4：解析与业务抽取分离
- 不把"解析"和"资质识别/评分识别"混在一起
- **当前项目实现：** 已部分分离（`DoclingWrapper` → `BusinessDocAssetExtractor` → `BusinessAssetLLMExtractor`），但未有统一抽象

---

## 六、当前关键技术思路评估

### 6.1 章节生成工作流

当前使用 LangGraph `StateGraph` 编排 4 个节点：

```
Researcher(RAG检索) → Writer(LLM写稿) → Auditor(LLM审稿) → Refiner(LLM润色)
                                            ↓ 不通过则循环，最多3轮
```

**评估：** 设计合理，但 `langgraph` + `crewai` 两个重型依赖并存。实际只用了 `langgraph` 的 `StateGraph`。建议清理 `crewai`。

### 6.2 LLM 使用方式

- `LLMClient`（`api/core/llm_client.py`）：统一适配层，按 role 支持分模型
- 所有 LLM 调用都有 deterministic fallback，LLM 失败不阻断主链路
- 当前使用 `Doubao-Seed-Code`（火山引擎 Ark Coding Plan）

**评估：** fallback 机制设计正确。但存在双配置问题（根级 `config.py` 的 `get_llm()` 和 `api/core/llm_client.py` 的 `LLMClient` 并存）。

### 6.3 向量检索

- `HybridRetriever`（`utils/hybrid_retriever.py`）：支持证书/案例/人员/分块检索
- 未配置 `EMBEDDING_MODEL` 时静默降级为零向量
- 当前实际处于降级状态

**评估：** 降级策略正确（先保主链路），但不是生产态。需要选定兼容的 embedding 模型。

---

## 七、数据库模型概览

| 模型 | 表名 | 核心字段 | 文件 |
|---|---|---|---|
| `Company` | `companies` | 公司名、信用代码、法人 | [assets_v2.py](file:///root/it-bidding-copilot/api/models/assets_v2.py) |
| `SourceDocument` | `source_documents` | 文件名、类型、本地路径 | 同上 |
| `EnterpriseCertificate` | `enterprise_certificates_v2` | 证书名、类型、等级、有效期、embedding(1536) | 同上 |
| `EnterpriseCase` | `enterprise_cases_v2` | 项目名、行业、合同额、embedding(1536) | 同上 |
| `EnterprisePersonnel` | `enterprise_personnel` | 姓名、角色、经验年限、社保图片 | 同上 |
| `CompanyAsset` | `company_assets` | 资产名、类型、标签、本地路径 | 同上 |
| `AssetChunk` | `asset_chunks_v2` | 分块类型、内容、embedding(1536) | 同上 |
| `RFPProject` | `rfp_projects_v2` | 项目名、预算、截止日、状态 | [rfp_v2.py](file:///root/it-bidding-copilot/api/models/rfp_v2.py) |
| `RFPRequirement` | `rfp_requirements_v2` | 章节、分类、描述、是否废标、分值 | 同上 |
| `BidDraft` | `bid_drafts_v2` | 章节标题、Markdown正文、生成状态、审计日志(JSON)、证据(JSON) | [bid_draft_v2.py](file:///root/it-bidding-copilot/api/models/bid_draft_v2.py) |
| `ProjectMaterial` | `project_materials_v2` | 项目临时物料 | 同上 |

---

## 八、推荐执行路线

### Sprint 0：架构收敛（3-5 天）

> **必须在功能开发前完成，否则后续改造成本只会更高。**

| Phase | 内容 | 估时 |
|---|---|---|
| 0a | 废弃根级 `config.py`，统一到 `api/core/config.py` | 0.5d |
| 0b | Router 业务逻辑下沉到 service 层 + schema 移到 `api/schemas/` | 1-2d |
| 0c | 前端大页面拆组件 + `api.ts` 按模块拆分 | 1-2d |
| 0d | 素材包状态迁入 DB；清理 `crewai`/`faiss-cpu` 依赖；去掉双 API 前缀 | 0.5d |

### Sprint 1：解析层统一（Phase A）

1. 抽出 `api/services/document_parse_service.py` 统一门面
2. 定义标准元素输出 schema
3. 接入 MinerU 作为 PDF/复杂文档增强后端
4. 接入 OCR（PaddleOCR/RapidOCR）处理图片证据
5. 给 `SourceDocument` 加解析状态字段

### Sprint 2：项目建档确认增强（Phase B）

1. 采购文件确认界面拆成评分/资格/技术三区
2. 继续收紧 requirement 噪声
3. 为 Ark 选定兼容的 `EMBEDDING_MODEL`
4. 恢复真实向量检索

### Sprint 3：编标工作台增强（Phase C）

1. 选择并接入开源 Markdown 编辑器组件
2. 支持选区 AI 改写
3. 章节版本管理

### Sprint 4：成品导出增强（Phase D）

1. 模板保样式导出
2. 正文精确图片插入
3. 审标后自动修复闭环评估

---

## 九、建议外部协作者优先研究的问题

1. **解析门面层设计**：`document_parse_service` 的接口、输出 schema、质量回退策略是否足够稳
2. **MinerU + OCR + LLM 的职责边界**：能否进一步简化，减少解析器之间的冗余
3. **采购文件确认建档界面**：如何拆成更高效的人工复核流程
4. **Markdown 编辑器选型**：`Milkdown`、`ByteMD`、`Tiptap` 哪个更适合改造成编标工作台
5. **导出版式质量**：如何在不引入过高复杂度的前提下提升到正式交标级

---

## 十、建议阅读顺序

| 顺序 | 文档 | 作用 |
|---|---|---|
| 1 | 本文档 | 全局概览 |
| 2 | [architecture_evaluation.md](file:///root/.gemini/antigravity/brain/54753030-b249-4a57-bc12-c52b4e6bacf5/architecture_evaluation.md) | 代码级架构诊断详情 |
| 3 | [current_status.md](file:///root/it-bidding-copilot/docs/current_status.md) | 逐项开发记录与验证结果 |
| 4 | [feature_inventory.md](file:///root/it-bidding-copilot/docs/feature_inventory.md) | 功能台账与优先级 |
| 5 | [document_parsing_stack_design.md](file:///root/it-bidding-copilot/docs/document_parsing_stack_design.md) | 文档解析栈目标架构 |
| 6 | [frontend_backend_alignment.md](file:///root/it-bidding-copilot/docs/frontend_backend_alignment.md) | 前后端承接矩阵 |
| 7 | [main_flow_task_list.md](file:///root/it-bidding-copilot/docs/main_flow_task_list.md) | 主流程任务清单 |
| 8 | [design_requirement_matrix.md](file:///root/it-bidding-copilot/docs/design_requirement_matrix.md) | 设计要求对照 |

---

## 十一、总结

| 维度 | 判断 |
|---|---|
| 主流程闭环 | ✅ 85-90%，已跑通真实文档联调 |
| 页面产品化 | ⚠️ 75-80%，大页面未拆、部分占位交互 |
| 导出成品质量 | ⚠️ 60-70%，可用但不是正式交标级 |
| 代码架构 | ❌ 存在结构性问题，需先做收敛再继续功能开发 |
| 解析栈 | ⚠️ 有设计但未实现统一门面，当前 docling 直接耦合 |
| 向量检索 | ⚠️ 降级可用，未配置真实 embedding 模型 |

**核心结论：项目已过"能不能做成"阶段，进入"如何做稳"阶段。建议先完成架构收敛（Sprint 0），再按 Sprint 1-4 推进功能。**
