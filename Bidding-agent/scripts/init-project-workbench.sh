#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo 'Usage: bash scripts/init-project-workbench.sh <workspace-dir> <project-id>' >&2
  exit 1
fi

WORKSPACE_DIR="$1"
PROJECT_ID="$2"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_DIR="$SCRIPT_DIR/../templates"
PROJECT_DIR="$WORKSPACE_DIR/20-Areas/Programming/Projects/$PROJECT_ID"
CHAPTER_DIR="$PROJECT_DIR/Chapters"
MATERIAL_DIR="$PROJECT_DIR/Materials"

mkdir -p "$CHAPTER_DIR"
mkdir -p "$MATERIAL_DIR"

cat > "$PROJECT_DIR/00-MOC-项目工作台.md" <<EOF
---
title: "项目工作台 - $PROJECT_ID"
date: $(date +%F)
type: project-moc
project_id: $PROJECT_ID
status: working
---

# 项目工作台 - $PROJECT_ID

## 项目工作页

- [[01-项目启动单]]
- [[02-招标解析摘要]]
- [[03-证据检索清单]]
- [[04-评分优先级清单]]
- [[05-评分点-章节-证据映射]]
- [[06-目录占位]]
- [[07-缺失材料清单]]
- [[08-材料组装检查清单]]

## 章节工作文件

- [[Chapters/01-投标函与法定文件]]
- [[Chapters/02-投标人资质与合规证明]]
- [[Chapters/03-平台原厂资质与产品能力]]
- [[Chapters/04-类似项目业绩]]
- [[Chapters/05-总体技术方案]]
- [[Chapters/06-对接方案]]
- [[Chapters/07-需求响应与偏离表]]
- [[Chapters/08-项目团队与实施组织]]
- [[Chapters/09-售后服务与运维保障]]
- [[Chapters/10-商务报价与报价说明]]
- [[Chapters/11-讲标材料]]
EOF

cp "$TEMPLATE_DIR/project-start-sheet.md" "$PROJECT_DIR/01-项目启动单.md"
cat > "$PROJECT_DIR/02-招标解析摘要.md" <<EOF
---
title: "招标解析摘要 - $PROJECT_ID"
date: $(date +%F)
type: tender-parse
project_id: $PROJECT_ID
status: working
---

# 招标解析摘要
EOF
cp "$TEMPLATE_DIR/evidence-retrieval-sheet.md" "$PROJECT_DIR/03-证据检索清单.md"
cp "$TEMPLATE_DIR/score-priority-sheet.md" "$PROJECT_DIR/04-评分优先级清单.md"
cp "$TEMPLATE_DIR/score-chapter-evidence-mapping.md" "$PROJECT_DIR/05-评分点-章节-证据映射.md"
cat > "$PROJECT_DIR/06-目录占位.md" <<EOF
---
title: "目录占位 - $PROJECT_ID"
date: $(date +%F)
type: bid-outline
project_id: $PROJECT_ID
status: working
---

# 目录占位
EOF
cat > "$PROJECT_DIR/07-缺失材料清单.md" <<EOF
---
title: "缺失材料清单 - $PROJECT_ID"
date: $(date +%F)
type: bid-missing-materials
project_id: $PROJECT_ID
status: working
---

# 缺失材料清单
EOF
cp "$TEMPLATE_DIR/material-assembly-checklist.md" "$PROJECT_DIR/08-材料组装检查清单.md"

cp "$TEMPLATE_DIR/legal-form-template.md" "$MATERIAL_DIR/01-法定文件模板稿.md"
cp "$TEMPLATE_DIR/deviation-response-sheet-template.md" "$MATERIAL_DIR/02-偏离表模板稿.md"
cp "$TEMPLATE_DIR/quote-explanation-template.md" "$MATERIAL_DIR/03-商务报价说明框架.md"
cp "$TEMPLATE_DIR/presentation-outline-template.md" "$MATERIAL_DIR/04-讲标提纲框架.md"

for chapter in \
  "01-投标函与法定文件" \
  "02-投标人资质与合规证明" \
  "03-平台原厂资质与产品能力" \
  "04-类似项目业绩" \
  "05-总体技术方案" \
  "06-对接方案" \
  "07-需求响应与偏离表" \
  "08-项目团队与实施组织" \
  "09-售后服务与运维保障" \
  "10-商务报价与报价说明" \
  "11-讲标材料"
do
  cp "$TEMPLATE_DIR/chapter-work-template.md" "$CHAPTER_DIR/$chapter.md"
done

printf 'Initialized project workbench at %s\n' "$PROJECT_DIR"
