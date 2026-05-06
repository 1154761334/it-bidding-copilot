#!/usr/bin/env bash
set -euo pipefail

# Validate the company knowledge vault

STACK_ROOT="/root/it-bidding-copilot"
VAULT_DIR="${VAULT_DIR:-$STACK_ROOT/vault}"

if [ ! -d "$VAULT_DIR" ]; then
  echo "Vault not found: $VAULT_DIR" >&2
  echo "Run bash Bidding-agent/scripts/init-vault.sh first." >&2
  exit 1
fi

ovp --check --vault-dir "$VAULT_DIR"
