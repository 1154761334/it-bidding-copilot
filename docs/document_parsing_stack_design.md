# 文档解析栈设计

## 1. 目标

本设计解决当前项目在 `docx / pdf / 图片证据` 上的高强度解析需求，同时保持整体架构：

- 鲁棒
- 简约
- 可替换
- 与现有 `FastAPI + PostgreSQL + React/Vite` 主线兼容

不追求“一个库包打天下”，而是让不同解析组件承担明确职责。

## 2. 背景判断

以 [商务技术文件.docx](/root/it-bidding-copilot/docs/商务技术文件.docx) 为代表的真实投标文件，具有以下特征：

- Word 样式弱：大多数段落是 `Normal`
- 编号结构强：`一、`、`4.2.1`、`8.2.1` 这类层级清晰
- 表格多
- 图片多
- 存在扫描件、证照页、授权书、社保页

因此：

1. 不能只靠 LLM 直接读全文
2. 不能只靠简单规则
3. 必须先做结构解析，再做 AI 语义抽取

## 3. 设计原则

### 3.1 单一内部抽象

无论输入来自 `python-docx`、`MinerU`、`Unstructured` 还是 OCR，最后都统一输出到项目内部的标准结构：

- `document_meta`
- `sections`
- `tables`
- `images`
- `evidence_links`
- `raw_markdown`

外部解析器可替换，内部消费层不变。

### 3.2 解析与语义分离

文档解析层负责：

- 顺序
- 层级
- 表格
- 图片
- 坐标/来源

AI 语义层负责：

- 证书抽取
- 人员抽取
- 案例抽取
- 评分项识别
- 资格要求识别
- 废标项识别
- 字段归一化

### 3.3 先轻后重

优先使用最轻、最稳定的解析路径。

只有当文档类型或质量需要时，才进入更重的解析器或 OCR。

### 3.4 主链路可降级

任一解析器失败时，不阻断整条业务链。系统应允许：

- 解析降级
- OCR 降级
- 语义抽取降级

但必须保留 trace，方便人工复核。

## 4. 解析栈分层

## 4.1 第一层：DOCX 原生解析层

主工具：

- `python-docx`
- `OOXML(zip+xml)` 直读

职责：

- 提取段落顺序
- 提取表格
- 提取图片关系
- 基于编号规则重建章节树
- 保留与 Word 导出链路一致的结构语义

适用：

- 真实 `docx` 投标文件
- 商务技术文件
- 招标文件 Word 版本

这是当前项目必须保留的主解析层，不能被外部库完全替代。

## 4.2 第二层：复杂文档增强层

主工具：

- `MinerU`

职责：

- 复杂 PDF 解析
- 扫描件识别
- 复杂图文混排恢复
- 复杂表格恢复
- 输出高质量 Markdown / JSON

适用：

- PDF 招标文件
- 扫描版资质文件
- 多栏/版式复杂的材料
- `docx` 原生解析效果不佳时的增强通道

引入方式：

- 作为可选解析后端
- 不直接替换当前 `docx` 主解析逻辑
- 仅在需要时被路由选中

## 4.3 第三层：通用分区与兜底层

主工具：

- `Unstructured`

职责：

- 多格式统一入口
- 文档元素切分
- 作为通用 fallback

适用：

- `pptx`
- `html`
- 非核心但仍需 ingest 的材料格式
- 特定格式下 MinerU 不适合时的兜底

定位：

- 不是主精度引擎
- 是统一入口和兜底层

## 4.4 第四层：OCR 层

主工具建议：

- `PaddleOCR` 或 `RapidOCR`

职责：

- 图片证照 OCR
- 社保证明 OCR
- 身份证 / 营业执照 / 授权书扫描件 OCR
- 解析器未能抽取的图片页识别

说明：

- OCR 不与文档解析器强耦合
- OCR 结果作为图片证据的附加文本输入到语义抽取层

## 4.5 第五层：AI 语义抽取层

主工具：

- 当前项目 LLM 适配层

职责：

- 章节级语义识别
- 结构化字段标准化
- 评分项/资格项/废标项抽取
- 企业资产归一化

输入来源：

- 第一层到第四层的结构化结果

## 5. 推荐路由策略

### 5.1 文件类型路由

#### DOCX

默认走：

- `python-docx + OOXML`

若解析质量不足，再走：

- `MinerU DOCX`

#### PDF

默认走：

- `MinerU`

若为轻量文本型 PDF，可保留当前轻路径作为备用。

#### 图片

默认走：

- `OCR`

#### 其他办公格式

默认走：

- `Unstructured`

## 5.2 质量回退路由

如果主解析结果不满足基础质量阈值：

- 章节数过少
- 表格缺失
- 图片未提取
- 纯文本占比异常

则自动切换备用解析器，并记录 trace。

## 6. 项目内建议的统一接口

建议新增解析门面层，例如：

- `api/services/document_parse_service.py`

统一入口：

- `parse(file_path, doc_type_hint=None, parse_mode="auto")`

统一输出：

- `parser`
- `backend`
- `quality_report`
- `document_meta`
- `sections`
- `tables`
- `images`
- `raw_markdown`
- `trace`

业务层只调用这个门面，不直接依赖具体解析器。

## 7. 与现有架构的关系

## 7.1 不改主基线

本方案不改变：

- React + Vite
- FastAPI
- PostgreSQL + pgvector
- `/api/v1/*`

## 7.2 建议目录归位

建议逐步形成如下结构：

- `api/services/document_parse_service.py`
- `utils/parsers/docx_ooxml_parser.py`
- `utils/parsers/mineru_parser.py`
- `utils/parsers/unstructured_parser.py`
- `utils/parsers/ocr_service.py`

当前已有 `utils/docling_wrapper.py`，后续建议将其演进为统一解析适配层的一部分，而不是继续承担所有格式。

## 7.3 与导出链路协同

由于最终仍要导出 Word：

- `docx` 原生结构必须保留
- 图片关系必须保留
- 表格结构必须尽量保留

这也是不建议完全依赖外部 Markdown 解析器作为唯一真相源的原因。

## 8. 服务器可行性

当前服务器资源：

- `48 vCPU`
- `61 GiB RAM`
- `75 GiB` 可用磁盘

结论：

- 纯 CPU 跑 OCR 可行
- 纯 CPU 跑 `MinerU pipeline` 可行
- 适合后台批处理与异步解析
- 不适合追求极端低延迟的实时秒回

这与本项目的投标场景匹配。

## 9. 推荐实施顺序

### Phase A

- 统一内部解析结果 schema
- 抽出 `document_parse_service`
- 保持现有 `docx` 解析主链稳定

### Phase B

- 接入 `MinerU` 作为 PDF/复杂文档增强后端
- 增加解析质量回退路由

### Phase C

- 接入 OCR 处理图片证据
- 将 OCR 结果纳入企业资产抽取和采购文件解析

### Phase D

- 接入 `Unstructured` 作为多格式兜底层
- 用于补齐 `pptx/html/其他材料`

## 10. 最终建议

最终推荐方案不是：

- 只接 `MinerU`
- 或只接 `Unstructured`

而是：

- `DOCX 主线 = python-docx + OOXML`
- `复杂解析增强 = MinerU`
- `多格式兜底 = Unstructured`
- `图片识别 = OCR`
- `字段抽取 = LLM`

这套方案在当前项目里最稳，复杂度也可控。
