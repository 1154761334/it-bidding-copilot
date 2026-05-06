#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="${1:-$(pwd)}"
VAULT_DIR="$TARGET_DIR"

mkdir -p \
  "$VAULT_DIR/50-Inbox/01-Raw/current-tender" \
  "$VAULT_DIR/50-Inbox/01-Raw/historical-bid" \
  "$VAULT_DIR/50-Inbox/01-Raw/company-credentials" \
  "$VAULT_DIR/50-Inbox/01-Raw/vendor-solutions" \
  "$VAULT_DIR/50-Inbox/01-Raw/attachments" \
  "$VAULT_DIR/50-Inbox/02-Processing" \
  "$VAULT_DIR/50-Inbox/03-Processed" \
  "$VAULT_DIR/10-Knowledge/Atlas" \
  "$VAULT_DIR/10-Knowledge/Evergreen/_Candidates" \
  "$VAULT_DIR/20-Areas/Programming/Topics" \
  "$VAULT_DIR/20-Areas/Queries" \
  "$VAULT_DIR/60-Logs/link-resolution" \
  "$VAULT_DIR/60-Logs/transactions"

cat > "$VAULT_DIR/README.md" <<'EOF'
# OVP Workspace

This workspace follows the OVP-native structure:
- 50-Inbox = source documents and processing pipeline
- 10-Knowledge = curated reusable knowledge
- 20-Areas = interpreted notes and queries
- 60-Logs = knowledge.db and runtime traces
EOF

printf 'Initialized workspace at %s\n' "$TARGET_DIR"
