#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo 'Usage: bash scripts/run-bid-manager-benchmark.sh <workspace-dir> <project-id>' >&2
  exit 1
fi

WORKSPACE_DIR="$1"
PROJECT_ID="$2"
SKILL_PATH="/root/it-bidding-copilot/Bidding-agent/skills/bid-manager/SKILL.md"
PROMPT_FILE="/root/it-bidding-copilot/Bidding-agent/skills/bid-manager/internal/benchmark-run-prompt.md"
CHECK_SCRIPT="/root/it-bidding-copilot/Bidding-agent/scripts/check-bid-manager-output.sh"

if [ ! -d "$WORKSPACE_DIR" ]; then
  echo "Workspace not found: $WORKSPACE_DIR" >&2
  exit 1
fi

if [ ! -f "$PROMPT_FILE" ]; then
  echo "Benchmark prompt not found: $PROMPT_FILE" >&2
  exit 1
fi

if [ ! -f "$SKILL_PATH" ]; then
  echo "Skill file not found: $SKILL_PATH" >&2
  exit 1
fi

cd "$WORKSPACE_DIR"

PROMPT_CONTENT="$(cat "$PROMPT_FILE")"
hermes chat -Q --yolo -s "$SKILL_PATH" -q "$PROMPT_CONTENT"

cd /root/it-bidding-copilot/Bidding-agent
bash "$CHECK_SCRIPT" "$WORKSPACE_DIR" "$PROJECT_ID"
