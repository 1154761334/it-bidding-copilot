#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo 'Usage: bash scripts/check-bid-manager-output.sh <workspace-dir> <project-id>' >&2
  exit 1
fi

WORKSPACE_DIR="$1"
PROJECT_ID="$2"
PROJECT_DIR="$WORKSPACE_DIR/20-Areas/Programming/Projects/$PROJECT_ID"

if [ ! -d "$PROJECT_DIR" ]; then
  echo "Project directory not found: $PROJECT_DIR" >&2
  exit 1
fi

python3 - "$WORKSPACE_DIR" "$PROJECT_DIR" <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1]).resolve()
project_dir = Path(sys.argv[2]).resolve()

required_suffixes = [
    "项目工作台.md",
    "项目启动单.md",
    "招标解析摘要.md",
    "证据检索清单.md",
    "评分优先级清单.md",
    "评分点-章节-证据映射.md",
    "目录占位.md",
    "缺失材料清单.md",
    "材料组装检查清单.md",
]

errors: list[str] = []
warnings: list[str] = []

project_markdowns = list(project_dir.glob("*.md"))

for suffix in required_suffixes:
    if not any(path.name.endswith(suffix) for path in project_markdowns):
        errors.append(f"missing required artifact matching: *{suffix}")

materials_dir = project_dir / "Materials"
chapters_dir = project_dir / "Chapters"
if not materials_dir.exists() or not any(materials_dir.glob("*.md")):
    errors.append("missing template material drafts")
if not chapters_dir.exists() or not any(chapters_dir.glob("*.md")):
    errors.append("missing chapter work files")

path_pattern = re.compile(r"(?:10-Knowledge|20-Areas|50-Inbox|60-Logs)/[^\s`|，,]+")
for md_file in project_dir.rglob("*.md"):
    if md_file.name.endswith("运行验收记录.md"):
        continue
    text = md_file.read_text(encoding="utf-8")
    for raw_match in path_pattern.findall(text):
        candidate_text = raw_match.rstrip(")]}>.,;:!\"'")
        candidate = (workspace / candidate_text).resolve()
        if not candidate.exists():
            errors.append(f"{md_file.name}: referenced path does not exist -> {candidate_text}")

    for forbidden in [
        "已拿到",
        "注册资本12000万元",
        "阿里云授权函.pdf",
        "营业执照.pdf",
        "软件企业证书.pdf",
        "ISO27001.pdf",
    ]:
        if forbidden in text:
            warnings.append(f"{md_file.name}: contains high-risk literal -> {forbidden}")

if errors:
    print("FAIL")
    for item in errors:
        print(f"- {item}")
else:
    print("PASS")

if warnings:
    print("WARNINGS")
    for item in warnings:
        print(f"- {item}")
PY
