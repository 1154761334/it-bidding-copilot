# FastAPI + PostgreSQL/pgvector + React/Vite 收敛计划

> 状态说明：本文档保留为“收敛过程记录”。当前实际状态请以 `docs/current_status.md`、`docs/architecture.md`、`docs/project_structure.md` 为准。

## 1. 决策结论

项目正式收敛到以下唯一技术路线：

- 前端：React + Vite
- 后端：FastAPI
- 数据库：PostgreSQL + pgvector
- 旧栈策略：停止继续兼容 SQLite、停止继续演进 Streamlit

本计划的目标不是“修补演示环境”，而是把当前仓库收敛成一个可启动、可开发、可测试、可上线演进的单一产品基线。

## 1.1 当前执行进展

截至当前仓库状态，以下事项已经完成：

- 唯一技术路线已收敛到 `FastAPI + PostgreSQL/pgvector + React/Vite`
- `/api/v1/*` 已成为当前主接口基线，旧 `/api/*` 仅兼容保留
- PostgreSQL 容器、数据库 schema、Alembic 版本标记已可用
- `pytest` 在当时阶段已能稳定运行，当前最新结果请查看 `docs/current_status.md`
- 前端构建、后端健康检查、Dashboard 上下文、偏离矩阵、审标、导出均已通过本地验证
- 已补充演示数据脚本用于本地联调

当前仍未完全收口的部分：

- 真实 RFP 解析与真实章节生成链路的全流程实文档联调
- 旧表与旧测试产物的彻底退场
- 更强的集成测试与生产化治理

## 2. 收敛边界

### 2.1 保留

- `frontend/`
- `api/`
- `main.py`
- `docker-compose.yml`
- `docs/`
- 必要的 `scripts/` 中数据库初始化、验证、种子数据脚本

### 2.2 冻结并退场

- `legacy_streamlit/`
- 根目录旧版 `app.py` 和旧 `pages/` 体系
- `bidcore.db`
- `bidding_v2.db`
- 所有基于 SQLite 的配置、脚本、文档和运行说明

### 2.3 原则

- 一个后端入口：FastAPI
- 一个前端入口：React/Vite
- 一个持久化方案：PostgreSQL/pgvector
- 一个接口规范：版本化 REST API
- 一个配置来源：环境变量 + `.env`
- 一个数据迁移方式：Alembic

## 3. 目标架构

```text
React/Vite
  -> /api/v1/*
FastAPI
  -> Service Layer
  -> SQLAlchemy 2.0 ORM
  -> PostgreSQL
  -> pgvector
  -> Worker Process (文档解析 / Embedding / 长任务)
```

### 3.1 目标分层

- Router：只做协议转换、鉴权入口、参数校验
- Service：业务编排、事务边界、状态流转
- Repository/Model：数据库访问与模型定义
- Worker：RFP 解析、Embedding、长文本生成、导出等异步任务
- Frontend Store：只消费 typed API，不手写分散路径

### 3.2 明确不再接受的做法

- 路由前缀重复叠加
- 前端硬编码 `project_id=1`、`company_id=1`
- 运行时同时兼容 SQLite 和 PostgreSQL
- 直接在 HTTP 请求里执行重文档解析和长生成任务
- 页面与接口字段“凭印象”对接

## 4. 当前问题归因

当前仓库的问题可以归为五类：

1. 基线分裂
   - 新旧前端并存
   - 新旧数据库并存
   - 文档与真实运行方式不一致
2. 契约失真
   - 前端调用路径、后端实际挂载路径、返回结构三者不一致
3. 数据模型未收敛
   - 旧 `enterprise_profiles/trust_scores` 与新 `companies/source_documents/rfp_projects_v2/...` 两套模型并存
4. 任务模型不实战
   - 解析、检索、生成、导出混在同步接口中
5. 工程治理缺失
   - 构建失败
   - 测试不可运行
   - 依赖清单不完整

## 5. 分阶段实施计划

## Phase 0: 冻结与对齐

目标：停止继续扩散技术债，形成唯一实施基线。

### 核心任务

- 冻结 `legacy_streamlit/`，标记为归档目录
- 在 README 和运行文档中明确“唯一运行方式”
- 盘点并标记所有 SQLite 相关脚本、文档、配置
- 确认 v1 产品最小闭环

### 交付物

- 收敛说明文档
- 目录保留/删除清单
- MVP 范围清单

### 验收标准

- 团队内部不再以 Streamlit 为默认入口
- 新开发不再向 SQLite 写任何功能逻辑
- 需求、研发、测试统一认可 MVP 闭环范围

## Phase 1: 工程基线重建

目标：让项目具备稳定启动、构建、测试能力。

### 核心任务

- 统一配置
  - `DATABASE_URL` 作为唯一数据库配置
  - 统一 LLM 配置命名，不再混用 `OPENAI_*` / `LLM_*` / `MODEL_NAME`
- 重建依赖
  - 补齐 FastAPI、Uvicorn、SQLAlchemy、Alembic、psycopg、pgvector、pytest 等依赖
  - 拆分 `requirements.txt` 或升级为 `pyproject.toml`
- 重建数据库基线
  - 新建 `alembic/`
  - 以 PostgreSQL 为唯一目标生成初始迁移
  - 删除 import 时自动建表逻辑
- 重建前端基线
  - 补 `tsconfig.json`
  - 修复 `npm run build`
  - 清理未使用和冲突页面
- 重建启动链
  - `docker-compose` 负责拉起 PostgreSQL/pgvector
  - 后端和前端分别通过明确命令启动

### 交付物

- 可执行的后端启动命令
- 可执行的前端构建命令
- Alembic 初始迁移
- 更新后的依赖与环境模板

### 验收标准

- `docker compose up -d` 可拉起数据库
- 后端可启动并通过健康检查
- 前端 `npm run build` 成功
- 测试框架可运行最小 smoke tests

## Phase 2: 数据模型收敛

目标：建立唯一业务模型，消除旧表和临时表的并存状态。

### 核心任务

- 定义统一领域模型
  - 公司
  - 资产源文件
  - 资产分块
  - RFP 项目
  - RFP 需求点
  - 项目物料
  - 标书章节草稿
  - 任务表
- 设计状态流转
  - `RFPProject.status`
  - `BidDraft.generation_status`
  - `Task.status`
- 移除旧 `enterprise_profiles/trust_scores`
- 把仪表盘统计改为基于新模型计算

### 交付物

- ER 图
- 字段字典
- 状态机文档
- 数据迁移脚本

### 验收标准

- 数据库中不存在业务上仍被引用的旧表
- Dashboard、档案、RFP、编标页面都只依赖新模型
- 所有状态字段都有明确来源和含义

## Phase 3: API 契约重建

目标：前后端以同一套接口协议开发，不再靠手工猜测。

### 核心任务

- 统一 API 前缀为 `/api/v1`
- 按领域拆分接口
  - `/api/v1/companies`
  - `/api/v1/assets`
  - `/api/v1/rfp-projects`
  - `/api/v1/drafts`
  - `/api/v1/reviews`
  - `/api/v1/system`
- 为每个接口定义请求/响应 DTO
- 前端改为统一 API client 调用
- 清除 store/page 中散落的 `fetch('/api/...')`
- WebSocket 路径和代理规则收敛为单一路径规范

### 交付物

- OpenAPI 契约
- 前端 typed API client
- 前后端字段映射表

### 验收标准

- 页面不再直接拼接任意路径
- 所有核心页面的数据模型来自统一 DTO
- OpenAPI 可作为联调与测试的唯一协议基线

## Phase 4: MVP 业务闭环打通

目标：形成第一个可实战验证的最小可用版本。

### MVP 闭环 A：企业档案

- 创建公司主体
- 上传资产源文件
- 自动分类
- 生成分块和向量
- 可查询公司详情和资产清单

### MVP 闭环 B：RFP 解析

- 上传 RFP
- 创建解析任务
- 解析结果入库
- 形成项目与需求点
- 输出偏离矩阵基础数据

### MVP 闭环 C：编标与导出

- 生成章节大纲
- 对指定章节触发生成
- 保存草稿与审计日志
- 执行终审
- 导出 docx

### 实现策略

- 文档解析、Embedding、生成走异步任务
- HTTP 接口只负责提交任务与查询任务状态
- 前端全部改为轮询/订阅任务状态，而不是等待长请求返回

### 交付物

- 3 条闭环的联调脚本
- 演示数据集
- 可复现的端到端流程文档

### 验收标准

- 新用户从零开始可完成一次完整投标流程演示
- 每一步都有数据库记录和状态变更
- 失败能定位到任务、日志和具体阶段

## Phase 5: 生产化补强

目标：从“能跑”提升到“能持续交付”。

### 核心任务

- 权限与租户隔离
- 文件存储规范化
- 操作日志和审计日志
- 错误追踪与告警
- 数据备份与迁移策略
- CI/CD
- 回归测试
- 压测与长任务稳定性验证

### 交付物

- 鉴权方案
- 监控与日志方案
- CI 配置
- 上线检查清单

### 验收标准

- 核心接口、关键任务和导出链路有监控
- 每次合并都自动跑测试
- 发布流程不依赖手工试错

## 6. 旧栈退场计划

### 6.1 立即执行

- README 去除 Streamlit 作为主入口的描述
- 所有新任务禁止在 `legacy_streamlit/` 下开发
- 停止向 SQLite 写数据

### 6.2 Phase 2 后执行

- 删除旧页面目录、旧入口脚本、旧 SQLite 初始化逻辑
- 从 CI 和脚本中移除 SQLite 相关命令

### 6.3 Phase 4 稳定后执行

- 将 `legacy_streamlit/` 移入 `archive/`
- 删除根目录历史测试产物与无效 demo 文件

## 7. 任务分工建议

## 7.1 后端负责人

- 数据模型收敛
- Alembic
- API 契约
- 异步任务框架
- 导出链路

## 7.2 前端负责人

- 路由和页面收敛
- API client 重构
- 状态管理简化
- 任务状态页和错误反馈

## 7.3 AI/文档处理负责人

- Docling 解析链
- 资产分类
- RFP 结构化输出
- 检索与生成质量

## 7.4 平台/测试负责人

- Docker 与环境模板
- CI
- 测试基线
- 发布脚本

## 8. 管理节奏建议

### 每周固定节奏

- 周一：冻结本周目标和接口变更
- 周三：联调检查，只看闭环是否真的通
- 周五：演示一个完整流程，不接受只演示局部页面

### 必须执行的治理动作

- 所有接口改动先改 DTO 再改实现
- 所有数据库变更必须走 Alembic
- 所有页面联调必须附真实接口截图或日志
- 所有“模拟返回”“占位逻辑”“硬编码 ID”必须建清理任务

## 9. 里程碑建议

### M1：工程可启动

- 时间：1 周
- 标志：数据库、后端、前端均可稳定启动

### M2：档案与 RFP 闭环

- 时间：2 周
- 标志：完成资产入库和 RFP 解析入库

### M3：编标与导出闭环

- 时间：3 到 4 周
- 标志：完成从项目创建到 docx 导出

### M4：生产候选版

- 时间：5 到 6 周
- 标志：具备测试、监控、发布、回归能力

## 10. Definition of Done

只有同时满足以下条件，才算收敛完成：

- 仓库中只有一个被支持的产品入口
- 所有核心页面都走真实 FastAPI 接口
- 所有业务数据都落 PostgreSQL
- pgvector 检索链路可用
- 旧 SQLite/旧 Streamlit 不再是运行依赖
- 前后端构建通过
- 核心闭环有自动化测试
- README 与真实运行方式一致

## 11. 下一步执行建议

建议按以下顺序直接开工：

1. 建立 `convergence` 分支，冻结旧栈继续演进
2. 先完成 Phase 1，不要并行做页面新功能
3. Phase 2 和 Phase 3 并行推进，但以数据模型和 DTO 为主线
4. 只以 MVP 闭环是否打通来判断阶段完成，不以页面视觉完成度判断

---

这份计划的核心不是“把问题列出来”，而是强制项目回到单基线、单模型、单契约、单运行方式。只要继续允许新旧体系并存，项目会持续失真，无法进入实战状态。
