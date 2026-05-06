# Deployment

## Runtime stack

This product is designed as a stack, not a single binary:

1. Hermes
   - agent runtime
   - runs `bid-manager`
   - coordinates sub-agents and workflow states

2. Obsidian
   - local vault viewer/editor
   - used by humans to inspect `inbox / raw / wiki / output / logs`
   - optional for CLI-only operation, but recommended

3. Obsidian Vault Pipeline (OVP)
   - self-managed vault knowledge engine
   - manages compiled markdown knowledge and derived views
   - should remain the knowledge layer, not the user-facing bid workflow center

## Prerequisites

Required:
- Python 3.10+
- Hermes installed

Recommended:
- pandoc
- pdftotext
- tesseract
- Obsidian Desktop
- OVP installed

Quick local check:
```bash
bash scripts/check-prereqs.sh
```

## Install sequence

### 1. Install Hermes
```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
hermes doctor
```

### 2. Install OVP
From your local fork checkout (recommended):
```bash
git clone https://github.com/1154761334/obsidian_vault_pipeline.git /root/it-bidding-copilot/obsidian_vault_pipeline
cd /root/it-bidding-copilot/Bidding-agent
bash scripts/install-ovp.sh local
```

On Debian/Ubuntu-style systems with externally managed Python, the helper script will retry with `--break-system-packages` automatically.

From your fork URL:
```bash
bash scripts/install-ovp.sh fork
```

From PyPI:
```bash
bash scripts/install-ovp.sh pypi
```

### 3. Install Obsidian Desktop
Install manually from:
- https://obsidian.md/

This repo does not automate the desktop installation.

### 4. Initialize workspace
```bash
bash scripts/init-workspace.sh /root/it-bidding-copilot/workspaces/my-bid-project
```

### 5. Create a current project input folder
```bash
bash scripts/new-project-inbox.sh /root/it-bidding-copilot/workspaces/my-bid-project my-project-id
```

### 6. Create vault `.env`
Copy:
```bash
cp templates/ovp-vault.env.example /root/it-bidding-copilot/workspaces/my-bid-project/bid-vault/.env
```

Then fill in the real model settings required by OVP.

## Workspace setup

Initialize a workspace with the helper script:

```bash
bash scripts/init-workspace.sh /root/it-bidding-copilot/workspaces/my-bid-project
```

This creates:

```text
/root/it-bidding-copilot/workspaces/my-bid-project/
└── bid-vault/
    ├── 00-Schema/
    ├── inbox/
    ├── raw/
    ├── wiki/
    ├── output/
    └── logs/
```

## Recommended material placement

Current project input:

```text
bid-vault/inbox/projects/<project-id>/
├── tender/
├── company-inputs/
├── vendor-inputs/
└── notes/
```

Reusable knowledge:

```text
bid-vault/raw/
├── historical-bids/
├── company-credentials/
├── vendor-solutions/
└── attachments/
```

## Ingestion recommendation

For bid/tender work, separate the current tender package from the reusable knowledge layer.
Preferred pattern:
1. place the current tender package under `inbox/projects/<project-id>/`
2. place reusable company/vendor materials under `raw/`
3. optionally normalize Office files with the helper scripts
4. let OVP manage the knowledge layer
5. let Hermes `bid-manager` run the tender workflow above it

Recommended DOCX helper:
```bash
bash scripts/convert-docx.sh input.docx /root/it-bidding-copilot/workspaces/my-bid-project/docx-bundle
```

## Main usage model

Run Hermes with the main skill:

```bash
hermes -s bid-manager
```

Or for a single-shot task:

```bash
hermes chat -s bid-manager -q "请作为投标经理读取当前项目输入文件夹并启动投标流程"
```

## OVP usage model

OVP is the knowledge-layer engine, not the main user-facing workflow center.

Useful commands include:
```bash
ovp --check --vault-dir /root/it-bidding-copilot/workspaces/my-bid-project/bid-vault
ovp-doctor --pack research-tech --json
ovp-packs
```

## Internal sub-agent policy

Sub-agents are internal implementation details.
The user should not normally invoke them directly.

Recommended internal roles:
- evidence-agent
- technical-agent
- review-agent

## Safe publishing boundary

This repository is product-focused.
Do not publish the following by default:
- real project input folders
- real tender source files
- exported bid deliverables
- scanned certificates and identity-sensitive evidence
- large conversion bundles
- project-specific raw vaults

## Suggested future packaging

Possible next steps:
- package `bid-manager` as an installable Hermes skill bundle
- add richer PDF/OCR helper scripts if the lightweight layer proves insufficient
- evaluate a true `bid` domain pack for OVP later
