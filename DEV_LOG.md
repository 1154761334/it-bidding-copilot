# DEV_LOG

## 2026-05-07 Round 1

### Baseline
- Lowest item: `/bid` frontend contract was ahead of the FastAPI backend. Frontend called `/health`, `/projects`, `/evidence/search`, `/projects/{id}/artifacts`, and `/demo/real-case`, while backend only exposed legacy `/api/project/*` and plugin routes.
- Evidence keyword fallback used repeated filters, which made multi-keyword searches such as `ISO9001 营业执照 授权书` return 0 results.
- Frontend `pnpm run build` failed because the default script required `bun`; direct Next build also failed before SPA templates were generated.
- Existing LLM workflow could not be accepted as green after removing hardcoded credentials; it now requires `LLM_API_KEY` from the environment. No token/API key was written to code or logs.

### Changes
- Added a real `/bid` FastAPI adapter with project lifecycle, file upload, plan/approve/execute/review, evidence search, artifact listing/reading, and real-case demo endpoints.
- Generated real Markdown artifacts under ignored workspace storage: `plan.md`, `response_matrix.md`, `draft.md`, `review.md`, and `evidence_trace.json`.
- Added stable `EVID-{id}` evidence IDs to API payloads, LLM evidence context, response matrix rows, draft references, and evidence trace JSON.
- Fixed keyword evidence search to use OR-style recall across title, text, and tags, while keeping optional semantic search when an embedding key is configured.
- Removed hardcoded LLM and embedding API keys from backend config. Provider base URLs, model names, and environment variable names remain configurable.
- Added `backend/tests/api_smoke.py` and root `eval_bid_assistant.py`.
- Updated frontend build scripts to use `pnpm`; build-time server env is generated locally by `scripts/buildNextWithEnv.mts` without committing fixed token/API key values.
- Updated README to describe the current LobeChat `/bid` + FastAPI + Vault/Evidence Store architecture and mark MinIO/OVP/Hermes-style stacks as non-required for this phase.

### Verification
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `18/18`, evidence trace length `64`.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash missing-token warnings during static collection, but exits 0.
- `cd frontend && pnpm run build:next`: PASS with generated build-time env.

### Blockers / Next
- Legacy LLM RAG script `cd backend && venv/bin/python tests/test_rag_workflow.py` is blocked until `LLM_API_KEY` is provided via environment and provider quota is available. It now fails closed instead of using hardcoded credentials.
- Next useful iteration: improve deterministic tender parsing precision and make review findings more granular for missing materials versus scoring-risk evidence.

## 2026-05-07 Round 2

### Baseline
- Lowest item: generated artifact quality. Baseline acceptance passed, but manual inspection showed `draft.md` could emit malformed Markdown table rows when requirements contained `|`, `response_matrix.md` could mark a generic `▲`实质性条款 as `missing_evidence`, and `review.md` did not consistently flag form/completeness risks.
- The evaluator was too permissive for document quality: it checked artifact existence and broad sections, but did not validate table shape, trace completeness, missing-evidence leakage, or review risk specificity.

### Changes
- Escaped Markdown table cells and normalized extracted requirements before writing response matrices, drafts, bullets, and evidence indexes.
- Expanded deterministic evidence query mapping for generic substantive clauses, clear-response clauses, quotation/payment/guarantee terms, and existing qualification keywords.
- Added a `## 六、证据索引` section to generated drafts, linking every cited `EVID-*` item to title, source file, and source heading.
- Made review findings include the exact missing requirement when evidence is absent, and always report subject/signature and material-index completion risks for formal filing.
- Tightened `eval_bid_assistant.py` from 18 to 28 checks covering Markdown table integrity, hard/technical/scoring coverage counts, absence of `missing_evidence`, full evidence trace linkage, source metadata, evidence index, and review risk areas.

### Verification
- `cd backend && venv/bin/python -m py_compile src/api_workbench.py ../eval_bid_assistant.py`: PASS.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `28/28`, project `9`, evidence trace length `70`.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash missing-token and Node runtime warnings, but exits 0.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: compare generated draft language against the real tender scoring table clause by clause and add stronger acceptance checks for commercial quotation and delivery-period consistency.

## 2026-05-07 Round 3

### Baseline
- Lowest item: `/bid` frontend real-case display loop. Backend artifacts were valid, but the workbench only exposed "Demo Real Case" after a project was selected, did not auto-select the generated demo project, did not auto-open `draft.md`, and could keep a stale artifact body while switching projects.
- The evaluator did not cover this frontend behavior, so a regression could still pass backend-only artifact checks.

### Changes
- Made `runDemo` return the generated project id, refresh projects, select the generated project, and fetch the default artifact with `draft.md` preferred.
- Reset artifact list/content when switching projects to avoid stale artifact display.
- Kept "Demo Real Case" available without a selected project and switched the workbench to the Draft tab after a successful demo run.
- Added selected artifact state, active artifact styling, file size, modified time, and evidence-id count to the Draft artifact viewer.
- Tightened `eval_bid_assistant.py` to check `/bid` route wiring, demo-to-artifact auto-open behavior, and selected artifact metadata display.

### Verification
- `backend/venv/bin/python -m py_compile eval_bid_assistant.py`: PASS.
- `cd frontend && pnpm run type-check`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `31/31`, project `10`, evidence trace length `70`.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash missing-token and Node runtime warnings, but exits 0.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: make the Draft tab render Markdown tables more readably or add an artifact-level evidence trace drill-down for each `EVID-*` reference.
