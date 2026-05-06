#!/usr/bin/env bash
set -euo pipefail

# This script is now a shim for bootstrap-stack.sh
# It creates a new project workspace.

if [ "$#" -lt 1 ]; then
  echo 'Usage: bash bin/new-workspace.sh <project-id>' >&2
  exit 1
fi

PROJECT_ID="$1"
BIDDING_AGENT_DIR="/root/it-bidding-copilot/Bidding-agent"

bash "$BIDDING_AGENT_DIR/scripts/bootstrap-stack.sh" "$PROJECT_ID"
