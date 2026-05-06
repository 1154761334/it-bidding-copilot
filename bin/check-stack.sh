#!/usr/bin/env bash
set -euo pipefail

STACK_ROOT="/root/it-bidding-copilot"
BIDDING_AGENT_DIR="$STACK_ROOT/Bidding-agent"
OVP_DIR="${OVP_LOCAL_PATH:-$STACK_ROOT/obsidian_vault_pipeline}"
WORKSPACES_DIR="$STACK_ROOT/workspaces"

echo '== bid-stack check =='
echo

printf '%-20s%s\n' 'stack root:' "$STACK_ROOT"
printf '%-20s%s\n' 'Bidding-agent:' "$BIDDING_AGENT_DIR"
printf '%-20s%s\n' 'OVP source:' "$OVP_DIR"
printf '%-20s%s\n' 'workspaces:' "$WORKSPACES_DIR"
echo

printf '%-20s' 'Bidding-agent dir:'
if [ -d "$BIDDING_AGENT_DIR/.git" ]; then
  echo 'ok'
else
  echo 'missing'
fi

printf '%-20s' 'OVP source dir:'
if [ -d "$OVP_DIR/.git" ]; then
  echo 'ok'
else
  echo 'missing'
fi

printf '%-20s' 'workspaces dir:'
if [ -d "$WORKSPACES_DIR" ]; then
  echo 'ok'
else
  echo 'missing'
fi

printf '%-20s' 'hermes:'
if command -v hermes >/dev/null 2>&1; then
  hermes --version | head -n 1
else
  echo 'missing'
fi

printf '%-20s' 'ovp:'
if command -v ovp >/dev/null 2>&1; then
  ovp --help >/dev/null 2>&1 && echo 'installed'
else
  echo 'missing'
fi

printf '%-20s' 'pandoc:'
if command -v pandoc >/dev/null 2>&1; then
  pandoc --version | head -n 1
else
  echo 'missing'
fi

echo
echo 'Workspaces:'
if [ -d "$WORKSPACES_DIR" ]; then
  find "$WORKSPACES_DIR" -maxdepth 1 -mindepth 1 -type d | sort || true
fi
