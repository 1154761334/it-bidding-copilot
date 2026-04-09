# 项目目录结构

本文档描述当前仓库各目录的职责，以及哪些目录属于运行期产物而非长期源码。

## 顶层目录

### `api/`
FastAPI 后端主目录。

包含：
- `core/`: 配置、数据库、日志、WebSocket
- `models/`: SQLAlchemy 数据模型
- `routers/`: HTTP / WebSocket 路由
- `schemas/`: Pydantic schema
- `services/`: 业务服务与工作流
- `utils/`: 后端内部辅助工具
- `agents/`: 当前仅保留 WebSocket 回调等轻量运行时辅助

### `frontend/`
React + Vite 前端。

包含：
- `src/pages/`: 业务页面
- `src/components/`: 公共组件
- `src/store/`: Zustand 状态管理
- `src/services/`: API client

### `utils/`
仓库级通用能力层，不直接承担路由职责。

主要用于：
- 文档解析
- 资质抽取
- RFP 分析
- 检索匹配
- DOCX 导出辅助

### `scripts/`
脚本目录，仅保留以下三类脚本：

- 初始化与迁移辅助
- 演示数据与种子数据
- 真实联调与验证脚本

不再在这里保留旧阶段 POC、一次性实验脚本。

当前子目录：
- `scripts/ops/`: 初始化、修表、盘点、运维辅助
- `scripts/seed/`: 演示数据与结构化种子
- `scripts/verify/`: 真实联调与链路验证

其中：
- `scripts/ops/check_runtime_assets.py` 用于检查 `models/`、样例文档、模板等关键运行时资产是否存在

### `tests/`
`pytest` 测试目录。

### `docs/`
项目文档目录。

当前建议长期保留：
- `current_status.md`
- `architecture.md`
- `development_workflow.md`
- `project_structure.md`
- `runtime_execution_design.md`
- `multi_round_extraction_strategy.md`
- `development_logs/`

`docs/` 下的 `.docx` 样例文件当前同时承担真实联调用例。

### `alembic/`
数据库迁移目录。

### `assets/`
运行期派生产物目录。

当前主要用于文档解析后落地的图片等文件。它属于运行时资产，不是核心源码目录。

### `data/`
当前保留的运行期资产目录。这里已有一批历史解析结果，仍可能被当前数据库记录引用，因此本轮未清空。

### `models/`
本地模型与解析器依赖目录。

当前主要包含：
- `magic-pdf` 相关模型
- OCR / Layout / Formula / Table 识别模型
- 部分 embedding / 解析运行时模型文件

该目录当前体积约 `18G`，属于大体积运行时依赖，不纳入当前 GitHub 仓库版本控制。
后续如需在新机器完整复现文档解析能力，需要额外同步该目录或按部署说明重新准备。

## 运行期目录

以下目录属于运行时产物，不应作为源码的一部分来理解：

- `uploads/`
- `exports/`
- `logs/`
- `.run/`
- `models/`
- `frontend/dist/`
- `frontend/node_modules/`
- `assets/extracted_images/`

这些目录已加入 `.gitignore` 或按运行时目录处理。

其中：
- `assets/extracted_images/` 为文档解析时自动提取的图片缓存
- `data/assets/` 为当前保留的运行期图片/文档资产
- `data/enterprises/`、`data/knowledge_base/`、`data/sessions/` 仍属于历史运行期目录，后续建议继续收敛到统一 runtime 目录
- `models/` 为本地模型权重和解析器运行时依赖，不随 GitHub 仓库同步

## 本轮已删除的历史目录

以下内容已从当前主项目中清出：

- `legacy_streamlit/`
- 根级 `agents/`
- 根级 `workflows/`
- `knowledge/`
- 旧 `api/workflows/`
- 旧 POC / phase 脚本
- 旧 `README_PRODUCTION.md`
- 旧 SQLite 数据库文件
- 旧 Stitch 原型与压缩包

## 保留原则

后续新增文件建议遵循：

1. 业务代码优先进入 `api/` 或 `frontend/`
2. 通用解析与抽取能力优先进入 `utils/`
3. 一次性验证走 `scripts/`
4. 运行时产物不要长期留在仓库根目录
5. 旧实验性实现如果不再接入当前主线，直接删除，不再长期共存
6. 每轮重大开发结束后更新状态文档；关键轮次再补 `docs/development_logs/` 日志，日常留痕优先走 GitHub commit / PR
