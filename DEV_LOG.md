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

## 2026-05-07 Round 4

### Baseline
- Lowest item: artifact readability in `/bid`. Round 3 made the real-case flow open generated artifacts, but the Draft tab still displayed Markdown as a raw `<pre>`, making response matrices and draft tables hard to inspect during trial use.

### Changes
- Added a lightweight in-place Markdown artifact preview for `.md` artifacts without adding dependencies or changing the backend contract.
- Rendered headings, bullet lists, and Markdown tables as readable UI elements, while leaving JSON artifacts in a raw code block.
- Highlighted `EVID-*` references inline so reviewers can visually track evidence-backed claims inside draft and matrix artifacts.
- Tightened `eval_bid_assistant.py` with a frontend check that the Draft tab contains table-aware Markdown artifact rendering.

### Verification
- `backend/venv/bin/python -m py_compile eval_bid_assistant.py`: PASS.
- `cd frontend && pnpm run type-check`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `32/32`, project `15`, evidence trace length `70`.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash missing-token and Node runtime warnings, but exits 0.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: add artifact evidence trace drill-down from highlighted `EVID-*` references to source document, heading path, and asset hints.

## 2026-05-08 Round 5

### Baseline
- Lowest item: evidence trace usability in `/bid`. Round 4 highlighted `EVID-*` references, but reviewers still had to open `evidence_trace.json` manually to see source document, heading path, row id, and page/asset hint.
- The evaluator did not cover whether the frontend actually loaded trace metadata for displayed artifact evidence ids.

### Changes
- Added an `EvidenceTraceRecord` frontend type matching generated `evidence_trace.json`.
- Lazily loaded `evidence_trace.json` when opening non-JSON artifacts, cached the parsed trace in the bidding store, and reset trace state when switching projects.
- Made traced `EVID-*` badges clickable in Markdown artifact previews.
- Added an evidence trace panel showing row id, cleaned title, source document, heading path, and page/asset hint for the selected evidence id.
- Tightened `eval_bid_assistant.py` with checks for trace loading and clickable evidence-detail rendering.

### Verification
- `cd frontend && pnpm exec eslint src/features/Bidding/BiddingDraftTab.tsx src/store/bidding/index.ts src/features/Bidding/BiddingWorkbench.tsx src/services/bidding.ts`: PASS.
- `cd frontend && pnpm run type-check`: PASS.
- `backend/venv/bin/python -m py_compile eval_bid_assistant.py`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `34/34`, project `16`, evidence trace length `70`.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash missing-token and Node runtime warnings, but exits 0.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: improve generated `review.md` severity model so high-risk commercial terms, missing主体信息, and scoring-risk evidence are separated into explicit actionable buckets.

## 2026-05-08 Round 6

### Baseline
- Lowest item: generated `review.md` severity model. Round 5 made evidence trace usable, but review findings still mixed disqualification risk, commercial-term signoff, scoring evidence, and signature/material completion into a flat list.
- The evaluator did not verify that the generated review artifact or `/bid` Review tab exposed actionable risk buckets.

### Changes
- Parsed response matrix Markdown into structured rows before review generation, including escaped table separators.
- Split review output into explicit risk buckets: 废标风险, 商务条款风险, 评分点风险, and 签章与材料风险.
- Added commercial-term signoff checks for quotation, payment, guarantee, invoice, and bid-validity clauses while preserving evidence IDs.
- Kept hard-clause and scoring coverage based on parsed matrix rows instead of string heuristics.
- Rendered review risk buckets in the `/bid` Review tab with bucket status and item details.
- Tightened `eval_bid_assistant.py` with checks for bucketed review Markdown and frontend risk bucket rendering.

### Verification
- `backend/venv/bin/python -m py_compile backend/src/api_workbench.py eval_bid_assistant.py`: PASS.
- `cd frontend && pnpm exec eslint src/features/Bidding/BiddingReviewTab.tsx`: PASS.
- `cd frontend && pnpm run type-check`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `36/36`, project `18`, evidence trace length `70`.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash missing-token and Node runtime warnings, but exits 0.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: add page/attachment readiness scoring so review buckets can distinguish evidence exists from final bindery-ready evidence.
