# IT Bidding Copilot V1

IT Bidding Copilot is an intelligent bidding drafting workbench designed to look like a modern Chat interface but act as a rigorous, workflow-driven bidding engine.

## 🌟 Architecture Overview

The current commercial-trial track keeps the architecture deliberately narrow:

- **Frontend (`frontend/`)**: a customized LobeChat/LaboChat workspace. The `/bid` route is the bidding workbench and displays real projects, evidence search results, response matrices, drafts, reviews, and Markdown artifacts.
- **Backend (`backend/`)**: a FastAPI service for tender parsing, Plan, Execute, Review, Evidence retrieval, and Markdown artifact generation.
  - **Workflow Engine**: the existing LangGraph path remains available for LLM-driven runs.
  - **Workbench API**: stable `/bid` endpoints expose project state, evidence traceability, real-case demo artifacts, and generated Markdown files.
  - **Evidence Store**: uses the existing Vault/Obsidian-derived material source and database records. Embeddings are optional; keyword retrieval remains available without external model quota.
- **Optional local services**: Docker services can help local development, but MinIO, Hermes, OVP, and new vector/object-store stacks are not required strong dependencies for the current phase.

## 📂 Directory Structure

```text
/root/it-bidding-copilot/
├── frontend/             # LobeChat fork (Next.js)
├── backend/              # FastAPI + LangGraph Orchestrator
│   └── src/
│       ├── main.py       # API Entrypoint
│       ├── workflow.py   # LangGraph BidState and Nodes
│       ├── parser.py     # MarkItDown & PyMuPDF4LLM wrappers
│       ├── models.py     # SQLAlchemy DB Models
│       └── storage.py    # MinIO Client
├── docker-compose.yml    # Optional local services
└── README.md             # This file
```

## 🚀 Quick Start

### 1. Start Optional Local Services
Start local services if you need the existing database-backed Evidence Store:
```bash
cd /root/it-bidding-copilot
docker-compose up -d
```

### 2. Start Backend
Install dependencies and run the FastAPI server:
```bash
cd /root/it-bidding-copilot/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Start Frontend
Install dependencies and start LobeChat development server:
```bash
cd /root/it-bidding-copilot/frontend
npm install
npm run dev
```

## 🔄 Core Workflow

1. **Plan Mode**: The user uploads a Tender Document. The Agent parses it (via the `/parse/` endpoint), extracts key requirements, missing materials, and proposes a drafting plan.
2. **Human Confirmation**: The workflow pauses. The user reviews the artifacts in the LobeChat `/bid` workbench and approves the plan.
3. **Execute Mode**: The agent builds a response matrix, evidence trace, and draft Markdown artifacts.
4. **Review Mode**: QA checks against hard clauses, scoring items, missing materials, and evidence boundaries.

## 🛠 Parsing Supported Formats

- `.docx`, `.xlsx`, `.pptx` -> Markdown via `MarkItDown`
- `.pdf` -> Markdown via `PyMuPDF4LLM` (Optimized for tables)
