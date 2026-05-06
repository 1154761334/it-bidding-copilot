# Setup stack: Hermes + Obsidian + OVP

This document explains the intended product stack for this repository.

The stack has three layers:
1. Hermes = agent runtime
2. Obsidian = human-facing vault viewer/editor
3. Obsidian Vault Pipeline (OVP) = self-managed knowledge-layer engine

## 1. Architecture decision

Recommended architecture:
- `bid-manager` remains the bidding manager agent and workflow engine
- Obsidian is not the main application UI; it is the vault interface
- `obsidian_vault_pipeline` is used as the knowledge-layer management engine
- this repo adds bidding-domain skills, templates, and lightweight helper capabilities around OVP/Hermes

This means:
- Hermes runs the bidding workflow
- OVP manages compiled vault knowledge
- Obsidian is used to inspect and maintain the vault
- current project tender packages are handled as project-run inputs, not default long-term wiki assets

## 2. Required components

### A. Hermes
Purpose:
- run `bid-manager`
- coordinate sub-agents
- drive workflow states and output generation

Install:
```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
hermes doctor
```

### B. Obsidian
Purpose:
- open and inspect the vault locally
- review `inbox / raw / wiki / output / logs`
- manually navigate knowledge pages and artifacts

Note:
- Obsidian is a desktop application, not required for CLI-only runtime
- if Obsidian is not installed, the system can still run in CLI mode

Install:
- install Obsidian Desktop manually from https://obsidian.md/
- open the generated vault folder after workspace initialization

### C. Obsidian Vault Pipeline (OVP)
Purpose:
- self-managed vault compilation
- raw markdown processing
- registry / lint / knowledge index / pack runtime

Recommended source:
- development fork: `https://github.com/1154761334/obsidian_vault_pipeline`

## 3. OVP dependency findings

Based on upstream metadata, the key runtime requirements are:
- Python >= 3.10
- hatchling build backend
- anthropic>=0.21.0
- openai>=1.0.0
- litellm>=1.0.0
- python-dotenv>=1.0.0
- requests>=2.28.0
- pyyaml>=6.0
- feedparser>=6.0.0
- beautifulsoup4>=4.12.0
- tiktoken>=0.5.0
- watchdog>=3.0.0
- networkx>=3.0

Useful optional local tools:
- `pandoc` for `.docx -> markdown + extracted media`
- `pdftotext` and OCR tooling for PDF assistance

## 4. OVP installation options

### Option A: install from local fork checkout (recommended)
```bash
git clone https://github.com/1154761334/obsidian_vault_pipeline.git /root/it-bidding-copilot/obsidian_vault_pipeline
cd /root/it-bidding-copilot/Bidding-agent
bash scripts/install-ovp.sh local
```

The helper script retries with `--break-system-packages` automatically if plain `pip install --user` is blocked by an externally managed Python environment.

### Option B: install from fork URL directly
```bash
bash scripts/install-ovp.sh fork
```

### Option C: install from PyPI
```bash
python3 -m pip install --user obsidian-vault-pipeline
```

## 5. OVP environment requirements

Important finding from prior testing:
- `ovp --check --vault-dir <vault>` expects a `.env` in the vault root
- do not assume only global shell env is enough

Typical `.env` values are provider/model-related, for example:
- `AUTO_VAULT_API_KEY`
- `AUTO_VAULT_API_BASE`
- `AUTO_VAULT_MODEL`
- optional proxy settings

The exact field names come from the OVP layer, not Hermes.

## 6. Recommended installation sequence for users

### Step 1: install Hermes
```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
hermes doctor
```

### Step 2: install OVP
Recommended:
```bash
git clone https://github.com/1154761334/obsidian_vault_pipeline.git /root/it-bidding-copilot/obsidian_vault_pipeline
cd /root/it-bidding-copilot/Bidding-agent
bash scripts/install-ovp.sh local
```

### Step 3: install Obsidian Desktop
- install manually from the official website
- later open your vault folder in Obsidian

### Step 4: initialize the bid workspace
```bash
bash scripts/init-workspace.sh /root/it-bidding-copilot/workspaces/my-bid-project
```

### Step 5: create a current project input folder
```bash
bash scripts/new-project-inbox.sh /root/it-bidding-copilot/workspaces/my-bid-project project-001
```

### Step 6: create vault `.env`
Inside:
```text
/root/it-bidding-copilot/workspaces/my-bid-project/bid-vault/.env
```
Add the OVP-required model settings.

### Step 7: open the vault in Obsidian
Open:
```text
/root/it-bidding-copilot/workspaces/my-bid-project/bid-vault/
```

### Step 8: start Hermes manager
```bash
cd /root/it-bidding-copilot/workspaces/my-bid-project
hermes -s bid-manager
```

## 7. How data enters the system

This is critical. Separate current project input from reusable knowledge assets.

### Current project input

Create a project folder under:
```text
bid-vault/inbox/projects/<project-id>/
```

Recommended layout:
```text
bid-vault/inbox/projects/<project-id>/
├── PROJECT-INPUT.md
├── tender/
├── company-inputs/
├── vendor-inputs/
└── notes/
```

The current tender package belongs here.
It should be parsed for the current run, but not treated as default long-term reusable knowledge.

### Reusable knowledge assets

#### Historical bids
Place under:
```text
bid-vault/raw/historical-bids/
```

#### Company credentials
Place under:
```text
bid-vault/raw/company-credentials/
```

#### Vendor/original-manufacturer materials
Place under:
```text
bid-vault/raw/vendor-solutions/
```

### Lightweight helper recommendation
For Office materials, prefer:
```bash
bash scripts/convert-docx.sh input.docx /root/it-bidding-copilot/workspaces/my-bid-project/docx-bundle
```

This repo intentionally keeps these helpers lightweight.
The main product value is the bidding-domain skill and workflow conventions layered on top of OVP/Hermes.

## 8. How users run the system

There are two practical operating modes.

### Mode A: manager-first workflow (recommended)
User starts Hermes and works through the bid workflow:
```bash
cd /root/it-bidding-copilot/workspaces/my-bid-project
hermes -s bid-manager
```

Suggested prompt:
```text
请作为投标经理读取当前项目输入文件夹和 bid-vault 中的长期知识材料，先完成项目启动咨询，再解析招标文件、整理证据、建立评分点-章节-证据映射、生成目录占位，并在需要时启用内部 sub agent。
```

### Mode B: knowledge-layer maintenance first
If the user first wants to normalize and maintain the vault layer, they can use OVP commands directly.
Examples from upstream include:
```bash
ovp --check --vault-dir /root/it-bidding-copilot/workspaces/my-bid-project/bid-vault
ovp-doctor --pack research-tech --json
ovp-packs
```

But for this product, OVP is not the user-facing workflow center.
Hermes remains the main interaction layer.

## 9. Recommended product framing for the repo

The repository should explain the stack like this:
- Hermes = runtime and orchestration
- bid-manager = user-facing product entry
- Obsidian = vault viewing/editing surface
- OVP = self-managed knowledge-layer engine
- helper scripts = optional convenience wrappers for file normalization

## 10. Known limitations right now

- the project input model is convention-driven rather than enforced by a full custom bridge
- reusable knowledge promotion is still guided by templates and skill rules, not a dedicated bid pack
- complex PDF/OCR handling is intentionally lightweight in this version
