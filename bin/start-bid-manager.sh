#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo 'Usage: bash /root/it-bidding-copilot/bin/start-bid-manager.sh <workspace-name>' >&2
  exit 1
fi

WORKSPACE_NAME="$1"
WORKSPACE_DIR="/root/it-bidding-copilot/workspaces/$WORKSPACE_NAME"
SKILL_PATH="/root/it-bidding-copilot/Bidding-agent/skills/bid-manager/SKILL.md"

if [ ! -d "$WORKSPACE_DIR" ]; then
  echo "Workspace not found: $WORKSPACE_DIR" >&2
  exit 1
fi

cd "$WORKSPACE_DIR"
exec hermes -s "$SKILL_PATH"
