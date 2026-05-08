# IT Bidding Copilot V1

IT Bidding Copilot is an intelligent bidding drafting workbench designed to look like a modern chat interface while acting as a rigorous, workflow-driven bidding engine.

## Current Status

As of 2026-05-08, the commercial-trial track is focused on the `/bid` workbench, deterministic bidding artifacts, evidence traceability, and repeatable local acceptance.

- The backend evaluator is green at `100.0`, `115/115` checks, with `253` evidence chunks discoverable from the local Vault-derived source and latest generated `evidence_trace.json` length `94`.
- The `/bid` workflow generates `plan.md`, `response_matrix.md`, `draft.md`, `review.md`, `handoff.md`, `evidence_trace.json`, and `project.json`.
- Review output now covers material packages, attachment readiness, scoring readiness, commercial evidence signature gaps, contract obligation readiness, action evidence links, and handoff summaries.
- The frontend workbench renders Markdown artifacts, evidence badges, material-package filters, action checklists, readiness panels, and route smoke surfaces.
- Local acceptance is standardized through `pnpm run acceptance:bid-smoke:preflight` and `pnpm run acceptance:bid-smoke:local`.
- The legacy LLM RAG script remains blocked until `LLM_API_KEY` and provider quota are supplied by the environment.

## Architecture Overview

The current commercial-trial architecture stays deliberately narrow:

- **Frontend (`frontend/`)**: a customized LobeChat/LaboChat workspace tracked in this repository as ordinary source files. The local working copy may still keep its own `.git/` metadata for upstream LobeChat history, but that metadata is ignored by the top-level repo. The `/bid` route displays real projects, evidence search results, response matrices, drafts, reviews, handoff artifacts, and Markdown evidence traces.
- **Backend (`backend/`)**: a FastAPI service for tender parsing, Plan, Execute, Review, evidence retrieval, and Markdown artifact generation.
  - **Workflow engine**: the existing LangGraph path remains available for LLM-driven runs.
  - **Workbench API**: stable `/bid` endpoints expose project state, evidence traceability, real-case demo artifacts, readiness summaries, and generated Markdown files.
  - **Evidence store**: uses the existing Vault/Obsidian-derived material source and database records. Embeddings are optional; keyword retrieval remains available without external model quota.
- **Optional local services**: Docker services can help local development, but MinIO, Hermes, OVP, and new vector/object-store stacks are not required strong dependencies for the current phase.

## Directory Structure

```text
/root/it-bidding-copilot/
├── frontend/             # Nested LobeChat fork checkout for the /bid workbench
├── backend/              # FastAPI + LangGraph Orchestrator
│   └── src/
│       ├── main.py       # API Entrypoint
│       ├── workflow.py   # LangGraph BidState and Nodes
│       ├── parser.py     # MarkItDown and PyMuPDF4LLM wrappers
│       ├── api_workbench.py
│       ├── models.py     # SQLAlchemy DB Models
│       └── storage.py    # MinIO Client
├── docker-compose.yml    # Optional local services
├── eval_bid_assistant.py # Deterministic acceptance evaluator
├── DEV_LOG.md            # Development progress log
└── README.md             # This file
```

## Quick Start

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

Install dependencies and start the direct SPA route:

```bash
cd /root/it-bidding-copilot/frontend
pnpm install
pnpm dev:spa --host 127.0.0.1
```

The production-style local Next route uses `pnpm run start` on port `3210` after a successful build. See `frontend/scripts/bidding/README.md` in the frontend checkout for storage-state capture and production-route smoke commands.

## Core Workflow

1. **Plan mode**: the user uploads a tender document. The agent parses it, extracts key requirements, identifies missing materials, and proposes a drafting plan.
2. **Human confirmation**: the workflow pauses while the user reviews generated artifacts in the `/bid` workbench and approves the plan.
3. **Execute mode**: the agent builds a response matrix, evidence trace, material package view, commercial response section, and draft Markdown artifacts.
4. **Review mode**: QA checks hard clauses, scoring items, commercial evidence, contract obligations, missing materials, attachment readiness, and evidence boundaries.
5. **Handoff mode**: `handoff.md` summarizes remaining human actions, material groups, evidence gaps, artifact purpose, and unsupported-content boundaries for trial users.

## Acceptance Commands

Run these from the repository root unless noted:

```bash
backend/venv/bin/python eval_bid_assistant.py
```

```bash
cd frontend
pnpm run acceptance:bid-smoke:preflight
pnpm run acceptance:bid-smoke:local
```

`acceptance:bid-smoke:preflight` is service-free and checks secret hygiene, runtime fixtures, command matrix drift, acceptance manifest drift, preflight summary failure cases, production route docs/storage-state guards, and terminal port-guard identity. `acceptance:bid-smoke:local` starts temporary FastAPI and Vite processes, runs the route smoke against `/bid`, and tears them down.

## Parsing Supported Formats

- `.docx`, `.xlsx`, `.pptx` -> Markdown via `MarkItDown`
- `.pdf` -> Markdown via `PyMuPDF4LLM` with table-focused extraction

## Source Control Notes

- The top-level repository tracks backend code, frontend source, evaluator code, operator docs, templates, and optional service definitions.
- `frontend/` source is vendored into this repository from frontend commit `ad8e4bb968` on `canary`; local dependency/build/auth files remain ignored.
- Generated backend smoke output under `backend/tests/output/` and large Office source documents are local artifacts and are intentionally not tracked by the top-level repo.
