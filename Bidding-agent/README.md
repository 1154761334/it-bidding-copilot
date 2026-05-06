# Bidding-agent

Hermes-based bidding/tender agent system for IT/system-integrator projects.

This repository packages a single external entrypoint, `bid-manager`, that presents as a "投标经理 Agent" while internally coordinating sub-agents for evidence handling, technical drafting, and review.
It is intended to be a bidding-domain integration layer on top of:
- Hermes Agent
- Obsidian
- OVP (`obsidian_vault_pipeline`)

## Product positioning

This is not a generic writing bot.
It is a tender-production workflow for projects where the bidder often acts as:
- prime contractor
- system integrator
- vendor-collaboration lead

The system is designed around five principles:
1. single external manager agent
2. evidence-first bid production
3. strict separation between bidder capability and vendor/original-manufacturer capability
4. Obsidian-style AI-managed knowledge base with `inbox / raw / wiki / output / logs`
5. current tender packages are project-run inputs, not default long-term knowledge assets

## Stack model

This product is intended to run as a stack:
- Hermes = runtime and orchestration
- bid-manager = user-facing bidding agent
- Obsidian = local vault viewing/editing surface
- OVP (`obsidian_vault_pipeline`) = self-managed knowledge-layer engine
- helper capabilities = lightweight wrappers around tools such as `pandoc`, PDF extraction, and OCR

## What is in this repo

- `skills/bid-manager/SKILL.md` — main Hermes skill and product entrypoint
- `docs/` — architecture, workflow, deployment, repository boundary, stack setup, sub-agent model
- `docs/bid-manager-blueprint.md` — bid-manager capability blueprint
- `docs/bid-manager-manual-acceptance.md` — manual acceptance checklist
- `docs/bid-manager-modules/` — internal module contracts for bid-manager
- `templates/` — reusable markdown templates for intake, evidence, mapping, and review
- `templates/workspace/` — recommended workspace skeleton
- `templates/ovp-vault.env.example` — sample vault `.env` for OVP
- `scripts/init-workspace.sh` — initialize a clean bid workspace
- `scripts/new-project-inbox.sh` — scaffold a current project input folder
- `scripts/convert-docx.sh` — lightweight DOCX normalization helper
- `scripts/init-project-workbench.sh` — scaffold bid-manager project work artifacts inside an OVP workspace
- `scripts/run-bid-manager-benchmark.sh` — run a fixed benchmark prompt against a workspace and validate outputs
- `scripts/check-prereqs.sh` — check local prerequisites
- `scripts/install-ovp.sh` — install OVP from your local fork / fork URL / PyPI
- `examples/demo-project/` — lightweight sanitized demo materials

## Intended runtime model

External presentation:
- one agent only: `bid-manager`
- one identity only: 投标经理 Agent

Internal execution:
- manager agent
- evidence sub-agent
- technical sub-agent
- optional review sub-agent

The user should feel like they are talking to one bid manager, not manually orchestrating multiple tools.

## Recommended workspace layout

```text
/root/it-bidding-copilot/
├── Bidding-agent/
├── obsidian_vault_pipeline/
└── workspaces/
    └── <workspace>/
        ├── 50-Inbox/
        ├── 10-Knowledge/
        ├── 20-Areas/
        └── 60-Logs/
```

## Safe publishing policy used in this repo

This repository intentionally excludes:
- current project input folders
- raw tender source files
- exported `.docx` / `.zip` deliverables
- certificate images and other evidence attachments
- large intermediate conversion bundles
- experimental vaults and heavyweight reference data

Only product-facing docs, templates, scripts, and skill definitions are published by default.

## Main workflow

1. project folder intake
2. project intake questions
3. workspace check
4. current tender/package parsing
5. reusable-knowledge retrieval
6. evidence organization
7. score-point / chapter / evidence mapping
8. outline generation
9. user confirmation gate
10. drafting
11. review
12. formal-delivery conversion
13. knowledge backflow

## Installation order

### 1. Check prerequisites
```bash
bash scripts/check-prereqs.sh
```

### 2. Install Hermes
```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
hermes doctor
```

### 3. Install OVP
```bash
git clone https://github.com/1154761334/obsidian_vault_pipeline.git /root/it-bidding-copilot/obsidian_vault_pipeline
cd /root/it-bidding-copilot/Bidding-agent
bash scripts/install-ovp.sh local
```

The install helper retries with `--break-system-packages` automatically on Debian/Ubuntu-style externally managed Python environments.

### 4. Install Obsidian Desktop
Install manually from:
- https://obsidian.md/

### 5. Initialize workspace
```bash
bash scripts/init-workspace.sh /root/it-bidding-copilot/workspaces/my-bid-project
```

### 6. Create a current project input folder
```bash
bash scripts/new-project-inbox.sh /root/it-bidding-copilot/workspaces/my-bid-project project-001
```

### 7. Create vault `.env`
```bash
cp templates/ovp-vault.env.example /root/it-bidding-copilot/workspaces/my-bid-project/.env
```

### 8. Start the manager skill in Hermes
```bash
cd /root/it-bidding-copilot/workspaces/my-bid-project
hermes -s bid-manager
```

Fallback without a local checkout:
```bash
cd /root/it-bidding-copilot/Bidding-agent
bash scripts/install-ovp.sh fork
```

## Project input and knowledge model

Current project input:
- current tender package -> `50-Inbox/01-Raw/current-tender/<project-id>/tender/`
- project-only bidder supplements -> `50-Inbox/01-Raw/current-tender/<project-id>/company-inputs/`
- project-only vendor supplements -> `50-Inbox/01-Raw/current-tender/<project-id>/vendor-inputs/`

Reusable knowledge assets:
- historical bids -> `50-Inbox/01-Raw/historical-bid/`
- company credentials -> `50-Inbox/01-Raw/company-credentials/`
- vendor materials -> `50-Inbox/01-Raw/vendor-solutions/`
- shared attachments -> `50-Inbox/01-Raw/attachments/`

Recommended DOCX helper:
```bash
bash scripts/convert-docx.sh input.docx /root/it-bidding-copilot/workspaces/my-bid-project/docx-bundle
```

OVP should be treated as the vault knowledge layer.
Current tender packages should be treated as project-run inputs unless you intentionally promote reusable facts or patterns into `wiki/`.

## Core public assets in this version

### Main skill
- `skills/bid-manager/SKILL.md`
- `skills/bid-manager/internal/` — internal module prompts and benchmark prompt

### Product docs
- `docs/architecture.md`
- `docs/workflow.md`
- `docs/subagents.md`
- `docs/deployment.md`
- `docs/repository-boundary.md`
- `docs/setup-stack.md`

### Reusable templates
- `templates/project-start-sheet.md`
- `templates/project-input-manifest.md`
- `templates/evidence-retrieval-sheet.md`
- `templates/score-priority-sheet.md`
- `templates/score-chapter-evidence-mapping.md`
- `templates/chapter-work-template.md`
- `templates/material-assembly-checklist.md`
- `templates/legal-form-template.md`
- `templates/deviation-response-sheet-template.md`
- `templates/quote-explanation-template.md`
- `templates/presentation-outline-template.md`
- `templates/evidence-page-template.md`
- `templates/review-checklist.md`
- `templates/ovp-vault.env.example`

### Demo
- `examples/demo-project/README.md`
- `examples/demo-project/session-example.md`

## Why this architecture

Compared with a normal “write the bid for me” agent, this system adds:
- project-input vs reusable-knowledge separation
- score-point / chapter / evidence mapping
- rejection-risk awareness
- vendor-vs-integrator capability boundary control
- formal-delivery cleanup rules
- reusable knowledge accumulation in an Obsidian-style vault structure

## Example startup prompt

```text
请作为投标经理读取当前 OVP workspace 中的项目输入文件和长期知识材料，先完成项目启动咨询，再解析招标文件、整理证据、建立评分点-章节-证据映射、生成目录占位，并在需要时启用内部 sub agent。
```

## Key rules

- do not enter chapter drafting before outline confirmation
- do not output formal qualification claims without evidence
- do not mix vendor capability with bidder-owned capability
- do not fabricate page numbers for unfinished sections
- do not leak internal process text into formal delivery drafts
- do not treat historical bid facts as current formal facts without confirmation
- do not treat the current tender package as canonical long-term reusable knowledge by default

## Repository status

This repo is being consolidated from an earlier local prototype workspace that already validated:
- bid-vault knowledge layout
- 2+1 sub-agent orchestration
- evidence-page concept
- review-loop concept
- internal-vs-formal draft separation concerns

See `docs/` for the cleaned product architecture.
