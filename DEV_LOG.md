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

## 2026-05-08 Round 7

### Baseline
- Current evaluator baseline passed at `100.0`, checks `36/36`, project `20`, evidence trace length `70`.
- Lowest item: evidence existed and was traceable, but `draft.md` and `review.md` did not distinguish "has evidence" from "ready for final attachment binding". Review only reminded users to backfill page numbers without naming which evidence ids still lacked page or asset location.

### Changes
- Added `asset_paths` to generated `evidence_trace.json` records while keeping source document, heading path, and page hints.
- Expanded the draft evidence index with `页码/资产提示` and `装订状态` columns.
- Added attachment readiness analysis to review generation, separating tender references from bidder-side evidence that is ready or still needs page/asset backfill.
- Added a `## 附件就绪度` section to `review.md`, including bidder evidence readiness counts and per-evidence binding status.
- Added a medium review finding that names bidder-side evidence ids still missing page or asset location.
- Updated `/bid` evidence trace details to show asset paths when present.
- Tightened `eval_bid_assistant.py` from 36 to 40 checks covering trace asset paths, draft attachment readiness, review attachment readiness, and frontend asset-path display.

### Verification
- `backend/venv/bin/python -m py_compile backend/src/api_workbench.py eval_bid_assistant.py`: PASS.
- `cd frontend && pnpm exec eslint src/features/Bidding/BiddingDraftTab.tsx src/services/bidding.ts`: PASS.
- `cd frontend && pnpm run type-check`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `40/40`, project `22`, evidence trace length `70`.
- Artifact spot check: `review.md` reports `附件就绪度：16/19`, names `EVID-42`, `EVID-38`, and `EVID-74` as needing page or asset backfill, and draft evidence index shows concise asset filenames such as `image268.png`.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash missing-token and Node runtime warnings, but exits 0.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: make the generated technical方案正文 less generic by expanding high-value technical requirements into evidence-backed implementation paragraphs instead of one-line bullets.

## 2026-05-08 Round 8

### Baseline
- Current evaluator baseline passed at `100.0`, checks `40/40`, project `22`, evidence trace length `70`.
- Lowest item: `draft.md` technical solution section had complete evidence ids, but section 3.2 still read like one-line response bullets instead of implementation paragraphs that reviewers can reuse in a real technical proposal.

### Changes
- Expanded `draft.md` section 3.2 into one subsection per technical requirement (`T1` through `T10`).
- Added deterministic implementation notes for common private-cloud clause types: image lifecycle, heterogeneous CPU compatibility, EC erasure coding, replica/topology policies, cache/data pool separation, CDP recovery, resource center, data center management, service orchestration, and optimization recommendations.
- Added evidence定位 text that pairs each technical requirement with concrete `EVID-*` ids and cleaned evidence titles.
- Fixed an ordering issue where EC erasure-coding clauses could accidentally match the generic replica-policy note because the requirement also mentioned multiple copies.
- Tightened `eval_bid_assistant.py` from 40 to 42 checks, including clause-specific technical note coverage for 一云多芯, 纠删码, and 服务目录编排.

### Verification
- `backend/venv/bin/python -m py_compile backend/src/api_workbench.py eval_bid_assistant.py`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `42/42`, project `25`, evidence trace length `70`.
- Artifact spot check: `draft.md` now renders `T1`-`T10` as subsections with 响应口径、实现要点、证据定位; `T4` correctly uses 纠删码保护机制 wording.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash missing-token and Node runtime warnings, but exits 0.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: improve scoring-point support in `draft.md` by turning score rows into a score-by-score response checklist with evidence readiness and missing manual signoff.

## 2026-05-08 Round 9

### Baseline
- Current evaluator baseline passed at `100.0`, checks `42/42`, project `25`, evidence trace length `70`.
- Lowest item: `draft.md` scoring section still summarized each scoring row as a short evidence-id line, so reviewers could not directly see response points, readiness, and manual signoff items for scoring materials.

### Changes
- Replaced the scoring-point bullets in `draft.md` section 3.3 with a score-by-score checklist table.
- Added deterministic scoring response notes for体系认证、类似案例、整体架构、技术指标响应程度 and 项目实施/团队 scoring rows.
- Added row-level evidence readiness for scoring rows, distinguishing ready bidder-side evidence, missing page/attachment numbers, no direct evidence, and tender-only references.
- Added manual review prompts for certificate validity, contract amount and dates, architecture consistency, △ screenshot/page alignment, and team certificate/social-security/support materials.
- Tightened `eval_bid_assistant.py` from 42 to 43 checks covering the scoring response checklist.

### Verification
- `backend/venv/bin/python -m py_compile backend/src/api_workbench.py eval_bid_assistant.py`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `43/43`, project `27`, evidence trace length `70`.
- Artifact spot check: `draft.md` section 3.3 now includes columns `评分项`, `响应要点`, `证据定位`, `就绪状态`, and `人工复核`, with certificate validity, contract amount, and team certificate checks.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash missing-token and Node runtime warnings, but exits 0.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: expose review attachment readiness and scoring readiness more clearly in the `/bid` Review tab instead of only inside Markdown artifacts.

## 2026-05-08 Round 10

### Baseline
- Current evaluator baseline passed at `100.0`, checks `43/43`, project `27`, evidence trace length `70`.
- Lowest item: the backend review payload already contained attachment readiness data, but `/bid` Review tab only showed coverage, risk buckets, and findings. Reviewers had to open `review.md` to see bidder-side readiness counts and missing page/asset evidence ids.

### Changes
- Added an Attachment Readiness summary to `/bid` Review tab.
- Displayed bidder-side ready count, missing page/asset count, and tender reference count as compact badges.
- Listed the first missing page/asset evidence records directly in the Review tab so users can act without opening Markdown.
- Tightened `eval_bid_assistant.py` from 43 to 44 checks covering frontend attachment-readiness rendering.

### Verification
- `cd frontend && pnpm exec eslint src/features/Bidding/BiddingReviewTab.tsx`: PASS.
- `cd frontend && pnpm run type-check`: PASS.
- `backend/venv/bin/python -m py_compile eval_bid_assistant.py`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `44/44`, project `29`, evidence trace length `70`.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash missing-token and Node runtime warnings, but exits 0.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: add a compact scoring readiness summary to the Review tab once scoring readiness is exposed in the review API payload.

## 2026-05-08 Round 11

### Baseline
- Current evaluator baseline passed at `100.0`, checks `44/44`, project `31`, evidence trace length `70`.
- Lowest item: `draft.md` already had scoring-row readiness, and `/bid` Review tab showed attachment readiness, but the generated review API payload and `review.md` did not summarize scoring readiness. Reviewers could not see which scoring items were ready versus blocked by bidder-side page/asset backfill without reading the draft checklist.

### Changes
- Added `scoring_readiness` to the review API payload, derived from scoring rows and attachment readiness records.
- Added a `## 评分就绪度` section to `review.md` with ready count, missing page/asset count, bidder-evidence gap count, evidence ids, status, and manual review prompts per scoring item.
- Updated the 评分点风险 bucket and findings so scoring rows that have evidence but lack bidder-side page/asset positioning are reported as actionable `needs_page_hint` issues.
- Added a Scoring Readiness summary to `/bid` Review tab with ready, page/asset, bidder-evidence badges and the first not-ready scoring rows.
- Tightened `eval_bid_assistant.py` from 44 to 46 checks covering review Markdown scoring readiness and frontend scoring-readiness rendering.

### Verification
- `backend/venv/bin/python -m py_compile backend/src/api_workbench.py eval_bid_assistant.py`: PASS.
- `cd frontend && pnpm exec eslint src/features/Bidding/BiddingReviewTab.tsx`: PASS.
- `cd frontend && pnpm run type-check`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `46/46`, project `32`, evidence trace length `70`.
- Artifact spot check: project `32` `review.md` reports `评分就绪度：4/5`; S3 is `needs_page_hint` because bidder evidence `EVID-74` still needs page or asset positioning.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash environment-variable and Node runtime warnings, but exits 0.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: expose scoring and attachment readiness in project list/detail summaries so users can triage projects before opening each artifact.

## 2026-05-08 Round 12

### Baseline
- Current evaluator baseline passed at `100.0`, checks `46/46`, project `34`, evidence trace length `70`.
- Lowest item: scoring and attachment readiness were visible inside single-project Review tab and `review.md`, but `/projects` and the `/bid` project list did not expose a quick readiness signal. Users had to open each project before seeing whether attachment positioning or scoring evidence still needed work.

### Changes
- Added a derived `readiness_summary` to the public project API shape, available from both `/projects` and `/projects/{id}` after review artifacts exist.
- Summarized attachment ready/total, attachment page/asset gaps, scoring ready/total, scoring gaps, bidder-evidence gaps, and review risk statuses without duplicating raw artifacts into project records.
- Updated the frontend project type and bidding store so selecting a project refreshes the cached project-list row with the latest readiness summary.
- Added compact readiness badges to the `/bid` project list: attachment ready count, attachment gap count, scoring ready count, and scoring gap count.
- Tightened `eval_bid_assistant.py` from 46 to 48 checks covering API readiness summary exposure and frontend project-list rendering.

### Verification
- `backend/venv/bin/python -m py_compile backend/src/api_workbench.py eval_bid_assistant.py`: PASS.
- `cd frontend && pnpm exec eslint src/features/Bidding/BiddingWorkbench.tsx src/services/bidding.ts src/store/bidding/index.ts`: PASS.
- `cd frontend && pnpm run type-check`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `48/48`, project `37`, evidence trace length `70`.
- API spot check: `/projects` and `/projects/35` both returned `readiness_summary` with `attachment_ready=16/19`, `attachment_needs_page_hint=3`, `scoring_ready=4/5`, and `scoring_needs_page_hint=1`.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS, including a repeat after the final Python formatting pass.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash environment-variable and Node runtime warnings, but exits 0.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: add a concise missing-action panel in Review tab that merges subject-name blanks, attachment gaps, and scoring gaps into an operator-ready checklist.

## 2026-05-08 Round 13

### Baseline
- Current evaluator baseline passed at `100.0`, checks `48/48`, project `39`, evidence trace length `70`.
- Lowest item: Review tab exposed coverage, readiness, risk buckets, and findings, but operators still had to mentally merge主体信息、商务签核、附件定位 and 评分定位 into next actions.

### Changes
- Added a structured `action_checklist` to the review API payload.
- Generated action items from real review state: missing hard clauses, bidder subject placeholder, high-risk commercial rows, attachment page/asset gaps, scoring readiness gaps, and final signing/material review.
- Added a `## 操作清单` section to `review.md` with priority, action, owner, and evidence/object references.
- Rendered Action Checklist in `/bid` Review tab before the detailed readiness sections.
- Tightened `eval_bid_assistant.py` from 48 to 51 checks covering project API action checklist, review Markdown checklist, and frontend rendering.

### Verification
- `backend/venv/bin/python -m py_compile backend/src/api_workbench.py eval_bid_assistant.py`: PASS.
- `cd frontend && pnpm exec eslint src/features/Bidding/BiddingReviewTab.tsx`: PASS.
- `cd frontend && pnpm run type-check`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `51/51`, project `42`, evidence trace length `70`.
- Artifact spot check: project `40` `review.md` action checklist includes 主体信息, 商务复核, 附件定位 with `EVID-42/EVID-38/EVID-74`, 评分定位 with `S3/EVID-74`, and 终稿复核.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS, including a repeat after the final Python formatting pass.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash environment-variable and Node runtime warnings, but exits 0.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: improve response matrix extraction so the plan/review can distinguish legal qualification documents,商务报价 documents, and technical scoring attachments before draft generation.

## 2026-05-08 Round 14

### Baseline
- Current evaluator baseline passed at `100.0`, checks `51/51`, project `44`, evidence trace length `70`.
- Lowest item: response matrix rows and review artifacts did not yet separate qualification documents, commercial pricing documents, and technical scoring attachments. Operators could see evidence and readiness, but not the material-package ownership before draft generation.

### Changes
- Added material-package classification across plan rows, response matrix rows, generated drafts, review payloads, and review Markdown.
- Grouped rows into `资格证明材料`, `商务报价材料`, and `技术评分附件`, with owners, evidence ids, row ids, missing-row tracking, status, and binding hints.
- Expanded plan material checks for opening price tables, quote details, payment/VAT invoice response, performance bond commitment, and technical architecture/screenshots.
- Added material-package sections to `plan.md`, `response_matrix.md`, `draft.md`, and `review.md`.
- Rendered material groups in `/bid` Review tab so reviewers can see ownership and involved row ids without opening Markdown.
- Tightened `eval_bid_assistant.py` from 51 to 57 checks covering API material groups, all generated artifacts, and frontend rendering.
- Narrowed the architecture/screenshot query rule after verification to avoid regressing scoring readiness while still covering technical scoring attachments.

### Verification
- `backend/venv/bin/python -m py_compile backend/src/api_workbench.py eval_bid_assistant.py`: PASS.
- `cd frontend && pnpm exec eslint src/features/Bidding/BiddingReviewTab.tsx`: PASS.
- `cd frontend && pnpm run type-check`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `57/57`, project `47`, evidence trace length `70`.
- Artifact spot check: project `47` `plan.md`, `response_matrix.md`, `draft.md`, `review.md`, and `project.json` all include the three material groups, with scoring readiness preserved at `4/5`.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash environment-variable and Node runtime warnings, but exits 0.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: add material-group filters in `/bid` artifact and evidence panels so reviewers can drill into qualification, commercial, or technical evidence directly from the generated trace.

## 2026-05-08 Round 15

### Baseline
- Current evaluator baseline passed at `100.0`, checks `57/57`, project `49`, evidence trace length `70`.
- Lowest item: material groups were present in review artifacts, but `evidence_trace.json` did not carry material-group metadata and `/bid` artifact/evidence panels could not drill into qualification, commercial, or technical evidence directly.

### Changes
- Added `material_group_key`, `material_group`, and `material_owner` to each generated `evidence_trace.json` record.
- Added typed `MaterialGroup` and material-group fields to frontend bidding service types.
- Updated `/bid` Draft artifact preview with a persistent Evidence Trace side panel, material group filters, selected-evidence details, and a filtered trace-record list.
- Passed project review/execution material groups from the workbench into the Draft artifact viewer.
- Added Material Group Presets to `/bid` Evidence Search for qualification, commercial, and technical evidence retrieval.
- Tightened `eval_bid_assistant.py` from 57 to 60 checks covering trace material-group metadata and frontend material-group filtering/presets.

### Verification
- `backend/venv/bin/python -m py_compile backend/src/api_workbench.py eval_bid_assistant.py`: PASS.
- `cd frontend && pnpm exec eslint src/features/Bidding/BiddingDraftTab.tsx src/features/Bidding/BiddingEvidenceTab.tsx src/features/Bidding/BiddingWorkbench.tsx src/services/bidding.ts`: PASS after auto-fixing prop order.
- `cd frontend && pnpm run type-check`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `60/60`, project `50`, evidence trace length `70`.
- Artifact spot check: project `50` `evidence_trace.json` includes `商务报价材料`, `技术评分附件`, and `资格证明材料`; first trace record includes material group key, label, owner, and asset path field.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash environment-variable and Node runtime warnings, but exits 0.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: add review-side filtering that opens the exact artifact evidence rows for each action checklist item, so operators can jump from a risk/action directly to its supporting evidence ids and missing page/asset records.

## 2026-05-08 Round 16

### Baseline
- Current evaluator baseline passed at `100.0`, checks `60/60`, project `52`, evidence trace length `70`.
- Lowest item: `action_checklist` still exposed only text references. Reviewers could not reliably distinguish evidence ids, response-matrix rows, and artifact names from each action item without manual parsing.

### Changes
- Enriched each review `action_checklist` item with structured `evidence_ids`, `row_ids`, and `artifact_refs`, derived from the existing references without inventing new evidence.
- Added `## 操作证据定位` to `review.md`, mapping each action area to associated rows, evidence ids, and artifacts.
- Updated `/bid` Review tab to render an Action Evidence block inside each action item, including row badges, evidence id badges, artifact refs, and attachment-readiness details from the review payload.
- Tightened `eval_bid_assistant.py` from 60 to 63 checks covering API action evidence links, review Markdown evidence index, and frontend rendering.

### Verification
- `backend/venv/bin/python -m py_compile backend/src/api_workbench.py eval_bid_assistant.py`: PASS.
- `cd frontend && pnpm exec eslint src/features/Bidding/BiddingReviewTab.tsx`: PASS.
- `cd frontend && pnpm run type-check`: PASS after adding explicit `Map<string, any>` typing.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `63/63`, project `53`, evidence trace length `70`.
- Artifact spot check: project `53` `review.md` contains `## 操作证据定位` with `附件定位` evidence `EVID-42/EVID-38/EVID-74` and `评分定位` row `S3` plus `EVID-74`; `project.json` action items expose structured rows, evidence ids, and artifact refs.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash environment-variable and Node runtime warnings, but exits 0.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: add a compact project-level export/readiness handoff artifact that summarizes remaining human actions, material groups, and evidence gaps for commercial trial users.

## 2026-05-08 Round 17

### Baseline
- Current evaluator baseline passed at `100.0`, checks `63/63`, project `55`, evidence trace length `70`.
- Lowest item: review, draft, trace, and project readiness were all available, but there was no compact project-level handoff artifact for commercial trial users to review remaining human actions, material groups, evidence gaps, and artifact purposes in one place.

### Changes
- Added `handoff.md` generation during review, built entirely from the real review payload and project metadata.
- Included trial readiness snapshot, remaining human actions, material-package handoff, evidence gaps, artifact map, and evidence-boundary notes in `handoff.md`.
- Exposed `handoff_artifact: handoff.md` in the review API payload.
- Added `handoff.md` to required demo artifacts and tightened `eval_bid_assistant.py` from 63 to 69 checks.
- Updated `/bid` artifact ordering and review workflow so running Review fetches `handoff.md` as the selected artifact while keeping demo execution opening `draft.md`.

### Verification
- `backend/venv/bin/python -m py_compile backend/src/api_workbench.py eval_bid_assistant.py`: PASS.
- `cd frontend && pnpm exec eslint src/store/bidding/index.ts`: PASS.
- `cd frontend && pnpm run type-check`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `69/69`, project `57`, evidence trace length `70`.
- Artifact spot check: project `57` `handoff.md` shows stage `reviewed`, `## 证据缺口`, `## Artifact Map`, and the evidence boundary note that unsupported content must not be written as provided.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash environment-variable and Node runtime warnings, but exits 0.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: improve draft section polish by adding a dedicated commercial quotation/contract response section that separates报价、付款、保证金 and invoice commitments from the generic商务偏离表.

## 2026-05-08 Round 18

### Baseline
- Current evaluator baseline passed at `100.0`, checks `69/69`, project `59`, evidence trace length `70`.
- Lowest item: `draft.md` still mixed quotation, payment, guarantee, invoice, and contract commitments into the generic commercial deviation table. Trial users lacked a dedicated commercial contract response section for signature review.

### Changes
- Added a dedicated `## 二、报价及合同商务响应` section to `draft.md`, separating bid quotation, payment, performance guarantee, invoice, and contract response commitments from the generic deviation table.
- Added commercial requirement classifiers and response wording helpers, including a priority fix so mixed payment/invoice rows do not fall back to generic quotation wording just because they mention quote attachments.
- Updated execution metadata from four to five draft sections and added `报价及合同商务响应` to the section list.
- Renumbered downstream draft sections and evidence index headings to keep the generated artifact structure coherent.
- Tightened `eval_bid_assistant.py` from 69 to 70 checks covering the new commercial quotation and contract response section.

### Verification
- `backend/venv/bin/python -m py_compile backend/src/api_workbench.py eval_bid_assistant.py`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `70/70`, project `61`, evidence trace length `70`.
- Artifact spot check: project `61` `draft.md` includes the new commercial response section, separate quotation/payment/guarantee/invoice rows, and the renumbered `## 七、证据索引`; `project.json` exposes five draft sections including `报价及合同商务响应`.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `cd frontend && pnpm run type-check`: PASS.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash environment-variable and Node runtime warnings, but exits 0.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: add a review check that flags commercial response rows backed only by tender-side requirements, so bidder-side quotation or contract-commitment evidence can be backfilled before human signature.

## 2026-05-08 Round 19

### Baseline
- Current evaluator baseline passed at `100.0`, checks `70/70`, project `63`, evidence trace length `70`.
- Lowest item: review output had only a generic `商务复核` action. It did not separate tender-side commercial clauses from bidder-side quotation/contract evidence, so operators could not see which quotation, payment, guarantee, or invoice rows still needed bidder-side signature evidence or page/asset backfill.

### Changes
- Added `commercial_evidence_readiness` to review payloads, with per-row status, bidder-side evidence ids, tender-side evidence ids, missing bidder evidence ids, required evidence, and manual check guidance.
- Added commercial readiness fields to project readiness summaries and `/bid` project list badges.
- Added a dedicated `## 商务证据签核` section to `review.md`, including `投标人侧商务证据`, `仅招标依据`, and page/asset gap counts.
- Added `商务证据回填` to the structured action checklist, with row ids and deduplicated evidence ids.
- Added commercial evidence gaps to `handoff.md` so trial handoff highlights H1/H2/H3/H7/H8 as needing bidder-side commercial evidence location backfill.
- Updated `/bid` Review tab with a `Commercial Evidence Readiness` panel showing signed, page/asset, and `tender_only` states.
- Tightened `eval_bid_assistant.py` from 70 to 75 checks covering API payloads, review/handoff artifacts, and frontend rendering.

### Verification
- `backend/venv/bin/python -m py_compile backend/src/api_workbench.py eval_bid_assistant.py`: PASS.
- `cd frontend && pnpm exec eslint src/features/Bidding/BiddingReviewTab.tsx src/features/Bidding/BiddingWorkbench.tsx src/services/bidding.ts`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `75/75`, project `65`, evidence trace length `70`.
- Artifact spot check: project `65` `review.md` shows `商务证据签核：1/6`, `商务证据回填`, H1-H8 commercial page-hint gaps tied to `EVID-42`, and `handoff.md` lists commercial evidence gaps for H1/H2/H3/H7/H8.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `cd frontend && pnpm run type-check`: PASS.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash environment-variable and Node runtime warnings, but exits 0.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: expand review coverage for contract execution obligations such as service period, acceptance, breach liability, subcontracting/transfer, and contract signing conditions so non-pricing contract risks are not hidden behind generic commercial review.

## 2026-05-08 Round 20

### Baseline
- Current evaluator baseline passed at `100.0`, checks `75/75`, project `67`, evidence trace length `70`.
- Lowest item: non-pricing contract execution obligations were still hidden behind generic commercial review. Service period, service response, acceptance, breach liability, transfer/subcontracting, and contract signing conditions were not surfaced as a dedicated readiness/risk view.

### Changes
- Added `contract_obligation_readiness` to review payloads, derived from the real tender contract sections and evidence store search, with C1-C6 row ids for service period, service response, acceptance, breach liability, transfer/subcontracting, and contract signing conditions.
- Merged contract-obligation evidence records into `evidence_trace.json` during Review, preserving evidence_id traceability for review.md and handoff.md references.
- Added `合同履约材料` as a material group and included it in review material-package handoff.
- Added `合同履约风险` risk bucket, `合同义务签核` action item, and `## 合同履约义务复核` section in `review.md`.
- Added contract-obligation gaps to `handoff.md`, including the tender-only breach-liability row C4 and page-hint gaps for C1/C2/C3/C5/C6.
- Updated `/bid` project readiness badges and Review tab with `Contract Obligation Readiness`.
- Tightened `eval_bid_assistant.py` from 75 to 82 checks, including review/handoff evidence_id trace coverage.

### Verification
- `backend/venv/bin/python -m py_compile backend/src/api_workbench.py backend/src/main.py eval_bid_assistant.py`: PASS.
- `cd frontend && pnpm exec eslint src/features/Bidding/BiddingReviewTab.tsx src/features/Bidding/BiddingWorkbench.tsx src/services/bidding.ts`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `82/82`, project `69`, evidence trace length `94`.
- Artifact spot check: project `69` `review.md` shows `合同履约义务复核`, `合同义务签核`, C1 service-period page-hint gaps, C4 tender-only breach-liability evidence, and `合同履约材料`; `handoff.md` lists contract obligation gaps for C1-C6; `evidence_trace.json` contains C-row records with `合同履约材料`.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `cd frontend && pnpm run type-check`: PASS.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash environment-variable and Node runtime warnings, but exits 0.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: add a Draft-side contract response appendix that turns the new C1-C6 contract-obligation readiness into controlled draft language without inventing unsupported legal commitments.

## 2026-05-08 Round 21

### Baseline
- Current evaluator baseline passed at `100.0`, checks `82/82`, project `71`, evidence trace length `94`.
- Lowest item: Review surfaced C1-C6 contract-obligation readiness, but `draft.md` still had no controlled contract response appendix. Trial users could see the review gaps but had no safe draft-side language for service period, service response, acceptance, breach liability, transfer/subcontracting, or contract signing conditions.

### Changes
- Added a generated `## 八、合同履约响应附录` to `draft.md` during Review, converting C1-C6 readiness rows into controlled draft language.
- Added explicit drafting boundaries so unsupported legal commitments, unsigned deadlines, amounts, liquidated damages, and subcontracting conditions are not expanded without bidder evidence and legal signoff.
- Added contract appendix response/gap helpers that distinguish ready rows, page/asset backfill rows, tender-only rows, and missing-evidence rows.
- Updated project draft metadata so `合同履约响应附录` is exposed as a sixth draft section after Review.
- Tightened `eval_bid_assistant.py` from 82 to 84 checks covering the draft appendix and project metadata.

### Verification
- `backend/venv/bin/python -m py_compile backend/src/api_workbench.py eval_bid_assistant.py`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `84/84`, project `72`, evidence trace length `94`.
- Artifact spot check: project `72` `draft.md` includes `合同履约响应附录`, C1 service-period page-hint gaps, C4 tender-only breach-liability language, and the unsupported-commitment drafting boundary; `project.json` exposes six draft sections including `合同履约响应附录`.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `cd frontend && pnpm run type-check`: PASS.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash environment-variable and Node runtime warnings, but exits 0.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: update the draft evidence index/material package view to include Review-stage C-row contract evidence under `合同履约材料`, so appendix evidence is visible in the draft's own evidence index rather than only in trace/review/handoff artifacts.

## 2026-05-08 Round 22

### Baseline
- Current evaluator baseline passed at `100.0`, checks `84/84`, project `74`, evidence trace length `94`.
- Lowest item: `draft.md` had the contract response appendix, but its own `## 七、证据索引` still only reflected Execute-stage matrix evidence. Review-stage C-row contract evidence was visible in trace/review/handoff and appendix prose, but not as a `合同履约材料` row or contract evidence detail inside the draft evidence index.

### Changes
- Added a Review-stage draft evidence-index enhancer that inserts `合同履约材料` into `### 7.1 材料包视图` with C1-C6 row ids, contract evidence ids, pending signoff rows, and C4 tender-only boundary.
- Added missing C-row contract evidence records into `### 7.2 证据明细`, sourced from `evidence_trace.json`, while avoiding duplicate evidence detail rows already present from Execute-stage evidence.
- Passed the merged Review evidence trace into draft enhancement so draft index, contract appendix, review, handoff, and trace stay aligned.
- Kept the contract appendix idempotent by rebuilding it from the pre-appendix draft and replacing any prior `合同履约材料` material row.
- Tightened `eval_bid_assistant.py` from 84 to 86 checks, explicitly covering contract material-package visibility and contract-only evidence detail rows in `draft.md`.

### Verification
- `backend/venv/bin/python -m py_compile backend/src/api_workbench.py eval_bid_assistant.py`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `86/86`, project `75`, evidence trace length `94`.
- Artifact spot check: project `75` `draft.md` shows `合同履约材料` in `7.1` with C1-C6 and `仅招标依据：C4`, plus `EVID-131`, `EVID-137`, `EVID-199`, and `EVID-200` in `7.2` evidence details; `project.json` still exposes six draft sections including `合同履约响应附录`.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `cd frontend && pnpm run type-check`: PASS.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash environment-variable and Node runtime warnings, but exits 0.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: make the `/bid` Draft or Evidence tab expose an artifact-local material-package summary/jump target for `合同履约材料`, so operators can move from the visible draft index row to the corresponding trace details without scanning the Markdown manually.

## 2026-05-08 Round 23

### Baseline
- Current evaluator baseline passed at `100.0`, checks `86/86`, project `77`, evidence trace length `94`.
- Lowest item: `/bid` Draft already rendered Markdown tables and had a right-side material-group trace filter, but operators still had to scan the artifact body or the trace panel manually to jump from a visible material package such as `合同履约材料` to its evidence trace details.

### Changes
- Added an `Artifact Material Packages` strip above the Draft artifact preview, derived from the current artifact text, `material_groups`, and loaded `evidence_trace.json`.
- Added package buttons with row, evidence, trace, and missing-row counts; clicking a package selects the corresponding material-group filter and opens the first matching evidence trace record.
- Highlighted the contract execution package via the `contract_execution_documents` group key without hardcoding generated evidence ids.
- Added a lucide package icon for the package strip and kept the existing Markdown/table/evidence badge rendering path unchanged.
- Tightened `eval_bid_assistant.py` from 86 to 87 checks covering the Draft tab package jump surface.

### Verification
- `backend/venv/bin/python -m py_compile eval_bid_assistant.py`: PASS.
- `cd frontend && pnpm exec eslint src/features/Bidding/BiddingDraftTab.tsx`: PASS after import-sort autofix.
- `cd frontend && pnpm run type-check`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `87/87`, project `78`, evidence trace length `94`.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash environment-variable and Node runtime warnings, but exits 0.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: add a focused `/bid` smoke test or Playwright check for the Draft material-package strip so the UI behavior is verified by rendering, not only by static source checks and production build.

## 2026-05-08 Round 24

### Baseline
- Current evaluator baseline passed at `100.0`, checks `87/87`, project `80`, evidence trace length `94`.
- Lowest item: the Draft material-package strip had static source/evaluator coverage and production build coverage, but no rendering-level smoke test proving the `合同履约材料` package button opens the matching evidence trace.

### Changes
- Added a focused Testing Library/Vitest component test for `BiddingDraftTab`.
- The test renders a Draft artifact with the `Artifact Material Packages` strip, verifies the `合同履约材料` row/evidence/trace/missing counters, clicks the package button, and confirms `Selected Evidence` opens the matching `EVID-131` trace record.
- Tightened `eval_bid_assistant.py` from 87 to 88 checks by requiring the Draft material-package render smoke test to exist.

### Verification
- `cd frontend && pnpm exec vitest run src/features/Bidding/BiddingDraftTab.test.tsx`: PASS, 1 test.
- `backend/venv/bin/python -m py_compile eval_bid_assistant.py`: PASS.
- `cd frontend && pnpm exec eslint src/features/Bidding/BiddingDraftTab.tsx src/features/Bidding/BiddingDraftTab.test.tsx`: PASS.
- `cd frontend && pnpm run type-check`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `88/88`, project `81`, evidence trace length `94`.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash environment-variable and Node runtime warnings, but exits 0.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: add an end-to-end `/bid` rendering smoke against the running frontend/backend path, so the route-level store integration for artifact package jumps is covered beyond the isolated component test.

## 2026-05-08 Round 25

### Baseline
- Current evaluator baseline passed at `100.0`, checks `88/88`, project `83`, evidence trace length `94`.
- Lowest item: `/bid` had a component-level render smoke for the Draft material-package strip, but no route/workbench-level smoke proving the LobeChat SPA route, Zustand store, real Bidding-agent API, generated artifacts, and package trace jump work together.

### Changes
- Added `frontend/scripts/bidding/smokeBidRoute.mts`, a Playwright smoke that targets the LobeChat SPA `/bid` route, preflights the real Bidding-agent `/health`, clicks `Demo Real Case`, waits for `draft.md` artifact rendering, verifies `Artifact Material Packages`, and opens the `合同履约材料` trace panel.
- Tightened `eval_bid_assistant.py` from 88 to 89 checks by requiring the real `/bid` route artifact smoke script.
- Fixed an existing `packages/utils/src/imageToBase64.test.ts` type-check failure by replacing the broad `document.createElement` mock return with a typed implementation that only intercepts `canvas` creation.

### Verification
- `cd frontend && pnpm exec tsx scripts/bidding/smokeBidRoute.mts`: PASS against `http://127.0.0.1:9876/bid`, API status `ok`, evidence count `253`; temporary FastAPI and SPA dev servers were stopped after the smoke.
- `backend/venv/bin/python -m py_compile eval_bid_assistant.py`: PASS.
- `cd frontend && pnpm exec eslint packages/utils/src/imageToBase64.test.ts scripts/bidding/smokeBidRoute.mts src/features/Bidding/BiddingDraftTab.test.tsx`: PASS.
- `cd frontend && pnpm exec vitest run src/features/Bidding/BiddingDraftTab.test.tsx`: PASS, 1 test.
- `cd frontend && pnpm --filter @lobechat/utils exec vitest run src/imageToBase64.test.ts`: PASS, 5 tests.
- `cd frontend && pnpm run type-check`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `89/89`, project `87`, evidence trace length `94`.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash environment-variable and Node runtime warnings, but exits 0.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: add an authenticated production-route `/spa/.../bid` e2e smoke once the LobeChat auth/database bootstrap is standardized for local trial runs; current smoke covers the SPA route and real Bidding-agent integration directly.

## 2026-05-08 Round 26

### Baseline
- Current evaluator baseline passed at `100.0`, checks `89/89`, project `90`, evidence trace length `94`.
- Lowest item: the structured review `action_checklist` exposed evidence ids and row ids, but most non-final action items still had empty `artifact_refs`. Operators could see what to fix, but had to infer whether the work belonged in `draft.md`, `review.md`, `handoff.md`, or `response_matrix.md`.

### Changes
- Extended `_review_action` to accept explicit artifact references and recognize Markdown anchors plus JSON artifacts as structured `artifact_refs`.
- Added artifact mappings for subject-info, commercial review, commercial evidence backfill, contract-obligation signoff, attachment positioning, scoring positioning, disqualification-risk, and final-review actions.
- Kept evidence ids and row ids derived only from existing references, while adding artifact refs to both API payloads and generated `review.md` / `handoff.md` action tables.
- Tightened `eval_bid_assistant.py` from 89 to 91 checks by requiring action checklist artifact refs in the project payload and visible artifact refs in the review action index.

### Verification
- `backend/venv/bin/python -m py_compile backend/src/api_workbench.py eval_bid_assistant.py`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `91/91`, project `92`, evidence trace length `94`.
- `git diff --check`: PASS.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `cd frontend && pnpm run type-check`: PASS.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash environment-variable and Node runtime warnings, but exits 0.

### Artifacts
- Project `92` `review.md` now maps `商务复核` to `draft.md#二、报价及合同商务响应`, `合同义务签核` to `draft.md#八、合同履约响应附录` and `review.md#合同履约义务复核`, `附件定位` to `review.md#附件就绪度`, and `评分定位` to `response_matrix.md`.
- Project `92` `handoff.md` carries the same artifact refs in the remaining-actions table, including `evidence_trace.json` for final cross-reference review.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: standardize a local authenticated production-route `/spa/.../bid` bootstrap so the existing route smoke can be promoted from direct SPA coverage to full Next/auth coverage without committing local secrets.

## 2026-05-08 Round 27

### Baseline
- Current evaluator baseline passed at `100.0`, checks `91/91`, project `94`, evidence trace length `94`.
- Lowest item: the `/bid` smoke covered the unauthenticated Vite SPA route, but running it against the production `/spa/.../bid` path still lacked a standard local-auth bootstrap contract. The script could fail on auth redirects without telling operators which safe env names or stored browser state were needed.

### Changes
- Extended `frontend/scripts/bidding/smokeBidRoute.mts` with optional `BID_ROUTE_STORAGE_STATE` support so an authenticated Playwright storage state can be reused for production-route smoke runs.
- Added auth-redirect detection for `/signin` and `/signup`, returning a structured `BID_ROUTE_AUTH_REQUIRED` diagnostic when `BID_ROUTE_ALLOW_AUTH_REQUIRED=1`.
- The diagnostic lists required environment variable names only, not values, and leaves the default unauthenticated Vite `/bid` smoke path unchanged.
- Tightened `eval_bid_assistant.py` from 91 to 92 checks by requiring the route smoke auth-bootstrap diagnostic support.

### Verification
- `backend/venv/bin/python -m py_compile eval_bid_assistant.py`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `92/92`, project `97`, evidence trace length `94`.
- `cd frontend && pnpm exec eslint scripts/bidding/smokeBidRoute.mts`: PASS.
- `cd frontend && pnpm exec tsx scripts/bidding/smokeBidRoute.mts`: PASS against `http://127.0.0.1:9876/bid`, API status `ok`, evidence count `253`, auth mode `not_required`; temporary FastAPI and SPA dev servers were stopped after the smoke.
- `git diff --check && git -C frontend diff --check`: PASS.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `cd frontend && pnpm run type-check`: PASS.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash environment-variable and Node runtime warnings, but exits 0.

### Artifacts
- The route smoke now emits `BID_ROUTE_SMOKE_PASS` with an `auth` field for normal `/bid` runs.
- When pointed at an auth-protected production route without storage state, the same script can emit `BID_ROUTE_AUTH_REQUIRED` with only bootstrap env var names, keeping local secrets out of logs and commits.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: add a documented helper for creating the Playwright storage state from an already-running local production instance, so the production-route smoke can be run repeatably without embedding credentials in the repo.

## 2026-05-08 Round 28

### Baseline
- Current evaluator baseline passed at `100.0`, checks `92/92`, project `99`, evidence trace length `94`.
- Lowest item: the production-route smoke could consume `BID_ROUTE_STORAGE_STATE`, but there was no standardized helper for creating that Playwright storage state from an already-running local instance without writing credentials into repo files or logs.

### Changes
- Added `frontend/scripts/bidding/captureBidRouteStorageState.mts` to open the configured `/bid` route, wait for the real Bidding Assistant view, and write a Playwright storage-state file.
- The capture helper reports `BID_ROUTE_LOGIN_REQUIRED` with environment variable names only when it lands on `/signin` or `/signup`, then allows an operator to complete login in headed mode before capture.
- Added the `capture:bid-storage-state` package script and ignored the default `.auth/` storage-state directory.
- Tightened `eval_bid_assistant.py` from 92 to 93 checks by requiring the capture helper, safe diagnostics, ignored default storage path, and package script.

### Verification
- `backend/venv/bin/python -m py_compile eval_bid_assistant.py`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `93/93`, project `103`, evidence trace length `94`.
- `cd frontend && pnpm exec eslint scripts/bidding/captureBidRouteStorageState.mts scripts/bidding/smokeBidRoute.mts`: PASS.
- `cd frontend && BID_FRONTEND_BASE_URL=http://127.0.0.1:9876 BID_ROUTE_STORAGE_STATE=/tmp/bid-route-storage-state-round28.json HEADLESS=true pnpm exec tsx scripts/bidding/captureBidRouteStorageState.mts`: PASS, emitted `BID_ROUTE_STORAGE_STATE_READY`; the temporary `/tmp` storage-state file was removed after the run.
- `cd frontend && pnpm exec tsx scripts/bidding/smokeBidRoute.mts`: PASS against `http://127.0.0.1:9876/bid`, API status `ok`, evidence count `253`, auth mode `not_required`; temporary FastAPI and SPA dev servers were stopped after the smoke.
- `git diff --check` and `git -C frontend diff --check`: PASS.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `cd frontend && pnpm run type-check`: PASS.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash environment-variable and Node runtime warnings, but exits 0.

### Artifacts
- The new capture helper emits `BID_ROUTE_LOGIN_REQUIRED` for auth bootstrap guidance and `BID_ROUTE_STORAGE_STATE_READY` once a reusable storage-state file has been written.
- The default storage-state artifact path is `.auth/bid-route-storage-state.json`, and `.auth/` is ignored so local browser state stays out of commits.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: run the `/spa/.../bid` smoke against an authenticated local Next instance using the captured storage state, then promote that production-route path into the regular acceptance gates if it is stable in CI-like environments.

## 2026-05-08 Round 29

### Baseline
- Current evaluator baseline passed at `100.0`, checks `93/93`, project `104`, evidence trace length `94`.
- Lowest item: the production `/spa/.../bid` route smoke could be assembled from env vars, but there was no package-level entrypoint tying the production route path and local Next port together. Operators still had to remember the exact `BID_FRONTEND_BASE_URL` and `BID_ROUTE_PATH` values.

### Changes
- Added `smoke:bid-route` as the default Vite `/bid` smoke entrypoint.
- Added `smoke:bid-route:prod` for the local Next production path at `http://127.0.0.1:3210/spa/desktop/bid`.
- Added `capture:bid-storage-state:prod` so storage-state capture and production-route smoke share the same route preset.
- Tightened `eval_bid_assistant.py` from 93 to 94 checks by requiring the production smoke/capture package scripts and the storage-state/auth diagnostic support.

### Verification
- `backend/venv/bin/python -m py_compile eval_bid_assistant.py`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `94/94`, project `106`, evidence trace length `94`.
- `cd frontend && pnpm exec prettier --check package.json`: PASS.
- `git diff --check` and `git -C frontend diff --check`: PASS.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `cd frontend && pnpm run type-check`: PASS.
- `cd frontend && pnpm run smoke:bid-route`: PASS against `http://127.0.0.1:9876/bid`, API status `ok`, evidence count `253`, auth mode `not_required`; temporary FastAPI and SPA dev servers were stopped after the smoke.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash environment-variable and Node runtime warnings, but exits 0.

### Artifacts
- `pnpm run smoke:bid-route` now gives a stable default acceptance command for the Vite `/bid` route.
- `pnpm run smoke:bid-route:prod` and `pnpm run capture:bid-storage-state:prod` now encode the local production route preset without storing credentials or storage state in the repo.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: add a non-secret local production-route runbook that sequences Next startup, storage-state capture, and `smoke:bid-route:prod`, including the expected auth-required diagnostic when storage state is absent.

## 2026-05-08 Round 30

### Baseline
- Current evaluator baseline passed at `100.0`, checks `94/94`, project `109`, evidence trace length `94`.
- Lowest item: production-route smoke commands were standardized, but operators still lacked a non-secret runbook that explained the local sequence for Vite smoke, Next production-route storage-state capture, and production-route smoke without exposing credentials.

### Changes
- Added `frontend/scripts/bidding/README.md` with the default Vite route smoke sequence and the local production-route sequence.
- The runbook lists environment variable names only, states that secret values must not be written into the repo, and points browser state to the ignored `.auth/bid-route-storage-state.json` artifact.
- Tightened `eval_bid_assistant.py` from 94 to 95 checks by requiring the non-secret production-route smoke runbook content.

### Verification
- `backend/venv/bin/python -m py_compile eval_bid_assistant.py`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `95/95`, project `112`, evidence trace length `94`.
- `cd frontend && pnpm exec prettier --check scripts/bidding/README.md package.json`: PASS.
- `git diff --check` and `git -C frontend diff --check`: PASS.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `cd frontend && pnpm run type-check`: PASS.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash environment-variable and Node runtime warnings, but exits 0.

### Artifacts
- `frontend/scripts/bidding/README.md` now documents the safe operator path for `smoke:bid-route`, `capture:bid-storage-state:prod`, and `smoke:bid-route:prod`.
- The documented local storage-state artifact remains `.auth/bid-route-storage-state.json`, which is ignored by git.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: add a lightweight CI-safe static check that fails if future bidding smoke docs or diagnostics start including credential-shaped literal values instead of environment variable names.

## 2026-05-08 Round 31

### Baseline
- Current evaluator baseline passed at `100.0`, checks `95/95`, project `113`, evidence trace length `94`.
- Lowest item: the non-secret bidding smoke convention was documented, but there was no executable CI-safe guard to fail if future docs or smoke diagnostics accidentally include credential-shaped literal values instead of environment variable names.

### Changes
- Added `frontend/scripts/bidding/checkBidRouteSmokeSecrets.mts` to scan bidding smoke docs, package smoke/bid scripts, and route smoke helpers for credential-shaped literals.
- The checker emits `BID_ROUTE_SMOKE_SECRET_CHECK_PASS` or `BID_ROUTE_SMOKE_SECRET_CHECK_FAIL`, and failure findings are redacted before logging.
- Added the `check:bid-smoke-secrets` package script.
- Tightened `eval_bid_assistant.py` from 95 to 96 checks by requiring the executable secret guard and package entrypoint.

### Verification
- `backend/venv/bin/python -m py_compile eval_bid_assistant.py`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `96/96`, project `117`, evidence trace length `94`.
- `cd frontend && pnpm run check:bid-smoke-secrets`: PASS, emitted `BID_ROUTE_SMOKE_SECRET_CHECK_PASS`.
- `cd frontend && pnpm exec eslint scripts/bidding/checkBidRouteSmokeSecrets.mts scripts/bidding/captureBidRouteStorageState.mts scripts/bidding/smokeBidRoute.mts`: PASS.
- `cd frontend && pnpm exec prettier --check package.json scripts/bidding/README.md scripts/bidding/checkBidRouteSmokeSecrets.mts`: PASS.
- `git diff --check` and `git -C frontend diff --check`: PASS.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `cd frontend && pnpm run type-check`: PASS.
- `cd frontend && pnpm run smoke:bid-route`: PASS against `http://127.0.0.1:9876/bid`, API status `ok`, evidence count `253`, auth mode `not_required`; temporary FastAPI and SPA dev servers were stopped after the smoke.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash environment-variable and Node runtime warnings, but exits 0.

### Artifacts
- `pnpm run check:bid-smoke-secrets` now provides a lightweight static acceptance artifact for the bidding smoke/runbook secret boundary.
- Guard failure logs include only file, line, rule, and redacted excerpts.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: add a small fixture-based check for the guard's failure mode without storing any credential-like literal directly in tracked files.

## 2026-05-08 Round 32

### Baseline
- Current evaluator baseline passed at `100.0`, checks `96/96`, project `120`, evidence trace length `94`.
- Lowest item: the bidding smoke secret guard had a passing static scan, but no failure-path self-test proving that credential-shaped findings are detected and redacted without storing a credential-like fixture in tracked files.

### Changes
- Extended `frontend/scripts/bidding/checkBidRouteSmokeSecrets.mts` with `BID_ROUTE_SMOKE_SECRET_CHECK_TARGETS` so tests can scan runtime-generated fixtures outside the repo.
- Added `frontend/scripts/bidding/testBidRouteSmokeSecrets.mts`, which creates a temporary credential-shaped fixture at runtime, expects the guard to fail, verifies the failure status, and asserts the generated value is not present in output.
- Added the `test:bid-smoke-secrets` package script.
- Tightened `eval_bid_assistant.py` from 96 to 97 checks by requiring the target override, runtime fixture test, redaction assertion, cleanup, and package entrypoint.

### Verification
- `backend/venv/bin/python -m py_compile eval_bid_assistant.py`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `97/97`, project `122`, evidence trace length `94`.
- `cd frontend && pnpm run check:bid-smoke-secrets`: PASS, emitted `BID_ROUTE_SMOKE_SECRET_CHECK_PASS`.
- `cd frontend && pnpm run test:bid-smoke-secrets`: PASS, emitted `BID_ROUTE_SMOKE_SECRET_TEST_PASS`.
- `cd frontend && pnpm exec eslint scripts/bidding/checkBidRouteSmokeSecrets.mts scripts/bidding/testBidRouteSmokeSecrets.mts scripts/bidding/captureBidRouteStorageState.mts scripts/bidding/smokeBidRoute.mts`: PASS.
- `cd frontend && pnpm exec prettier --check package.json scripts/bidding/checkBidRouteSmokeSecrets.mts scripts/bidding/testBidRouteSmokeSecrets.mts`: PASS.
- `git diff --check` and `git -C frontend diff --check`: PASS.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `cd frontend && pnpm run type-check`: PASS.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash environment-variable and Node runtime warnings, but exits 0.
- `cd frontend && pnpm run smoke:bid-route`: PASS against `http://127.0.0.1:9876/bid`, API status `ok`, evidence count `253`, auth mode `not_required`; temporary FastAPI and SPA dev servers were stopped after the smoke.

### Artifacts
- `pnpm run test:bid-smoke-secrets` now validates the guard's failure mode using a runtime-only fixture and redacted output.
- `BID_ROUTE_SMOKE_SECRET_CHECK_TARGETS` provides a safe test path for future CI fixtures without expanding the default repo scan surface.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: add a single package-level acceptance preset that chains `check:bid-smoke-secrets`, `test:bid-smoke-secrets`, and the route smoke so CI can invoke the bidding smoke gate consistently.

## 2026-05-08 Round 33

### Baseline
- Current evaluator baseline passed at `100.0`, checks `97/97`, project `125`, evidence trace length `94`.
- Lowest item: bid smoke had separate package scripts for the secret guard, failure fixture, and route smoke, but no single package-level acceptance preset that CI or operators could invoke consistently once FastAPI and Vite are running.

### Changes
- Added `acceptance:bid-smoke` to `frontend/package.json`, chaining `check:bid-smoke-secrets`, `test:bid-smoke-secrets`, and `smoke:bid-route`.
- Updated `frontend/scripts/bidding/README.md` to document the full local smoke gate and its requirement that FastAPI and Vite already be running.
- Tightened `eval_bid_assistant.py` from 97 to 98 checks by requiring the package preset and runbook text.

### Verification
- `backend/venv/bin/python -m py_compile eval_bid_assistant.py`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `98/98`, project `126`, evidence trace length `94`.
- `cd frontend && pnpm exec prettier --check package.json scripts/bidding/README.md`: PASS.
- `cd frontend && pnpm run check:bid-smoke-secrets`: PASS, emitted `BID_ROUTE_SMOKE_SECRET_CHECK_PASS`.
- `cd frontend && pnpm run test:bid-smoke-secrets`: PASS, emitted `BID_ROUTE_SMOKE_SECRET_TEST_PASS`.
- `git diff --check` and `git -C frontend diff --check`: PASS.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `cd frontend && pnpm run type-check`: PASS.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash environment-variable and Node runtime warnings, but exits 0.
- `cd frontend && pnpm run acceptance:bid-smoke`: PASS against `http://127.0.0.1:9876/bid`, API status `ok`, evidence count `253`, auth mode `not_required`; temporary FastAPI and SPA dev servers were stopped after the smoke.

### Artifacts
- `pnpm run acceptance:bid-smoke` is now the single local acceptance command for the non-secret guard, runtime fixture self-test, and real `/bid` route smoke.
- The runbook now documents the full local gate while continuing to list environment names only for production-route auth setup.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: reduce route-smoke setup friction by adding a lightweight orchestration helper that starts temporary FastAPI and Vite, runs `acceptance:bid-smoke`, and reliably tears both processes down.

## 2026-05-08 Round 34

### Baseline
- Current evaluator baseline passed at `100.0`, checks `98/98`, project `129`, evidence trace length `94`.
- Lowest item: local bid smoke acceptance still required operators to manually start and stop FastAPI and Vite before invoking the package-level gate.

### Changes
- Added `frontend/scripts/bidding/runBidSmokeAcceptance.mts`, a local acceptance orchestrator that checks ports, starts temporary FastAPI and Vite processes, waits for backend health and `/bid`, runs `acceptance:bid-smoke`, and tears both processes down.
- Added `acceptance:bid-smoke:local` to `frontend/package.json`.
- Updated `frontend/scripts/bidding/README.md` with the one-command local acceptance path.
- Tightened `eval_bid_assistant.py` from 98 to 99 checks by requiring the local runner, package entrypoint, runbook text, process teardown, readiness polling, and safe environment-variable names.

### Verification
- `backend/venv/bin/python -m py_compile eval_bid_assistant.py`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `99/99`, project `134`, evidence trace length `94`.
- `cd frontend && pnpm exec prettier --check package.json scripts/bidding/README.md scripts/bidding/runBidSmokeAcceptance.mts`: PASS.
- `cd frontend && pnpm exec eslint scripts/bidding/runBidSmokeAcceptance.mts scripts/bidding/checkBidRouteSmokeSecrets.mts scripts/bidding/testBidRouteSmokeSecrets.mts scripts/bidding/smokeBidRoute.mts`: PASS.
- `git diff --check` and `git -C frontend diff --check`: PASS.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `cd frontend && pnpm run type-check`: PASS.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash environment-variable and Node runtime warnings, but exits 0.
- `cd frontend && pnpm run acceptance:bid-smoke:local`: PASS, emitted `BID_SMOKE_ACCEPTANCE_LOCAL_PASS` after secret guard, guard self-test, and `/bid` route smoke passed; no FastAPI, Vite, or Next process remained afterward.

### Artifacts
- `pnpm run acceptance:bid-smoke:local` now provides the one-command local acceptance artifact for the bidding smoke gate.
- The local runner exposes only safe operator environment names: `BID_BACKEND_DIR`, `BID_ACCEPTANCE_READY_TIMEOUT_MS`, and `BID_ACCEPTANCE_VERBOSE`.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: add a CI-safe preflight/failure-path check for the local acceptance runner, covering port-in-use handling without starting real services.

## 2026-05-08 Round 35

### Baseline
- Current evaluator baseline passed at `100.0`, checks `99/99`, project `135`, evidence trace length `94`.
- Lowest item: the local acceptance runner managed services successfully, but its port preflight and failure path were not covered by a CI-safe self-test that avoids starting real FastAPI or Vite services.

### Changes
- Added `BID_ACCEPTANCE_PREFLIGHT_ONLY=1` to `frontend/scripts/bidding/runBidSmokeAcceptance.mts`, allowing operators and CI to validate configured ports without starting services.
- Added `frontend/scripts/bidding/testBidSmokeAcceptanceRunner.mts`, which uses runtime-only local TCP ports to verify preflight success on free ports and failure on an occupied backend port.
- Added `test:bid-smoke-acceptance-runner` and included it in `acceptance:bid-smoke`.
- Expanded the bid smoke secret guard's default scan surface to cover the local runner and its preflight self-test.
- Updated the bid smoke runbook to document the local runner preflight self-test and expected preflight status.
- Tightened `eval_bid_assistant.py` from 99 to 100 checks by requiring the preflight mode, self-test script, package entrypoint, and runbook text.

### Verification
- `backend/venv/bin/python -m py_compile eval_bid_assistant.py`: PASS.
- `backend/venv/bin/python eval_bid_assistant.py`: PASS, score `100.0`, checks `100/100`, project `139`, evidence trace length `94`.
- `cd frontend && pnpm exec prettier --check package.json scripts/bidding/README.md scripts/bidding/runBidSmokeAcceptance.mts scripts/bidding/testBidSmokeAcceptanceRunner.mts`: PASS.
- `cd frontend && pnpm exec eslint scripts/bidding/runBidSmokeAcceptance.mts scripts/bidding/testBidSmokeAcceptanceRunner.mts scripts/bidding/checkBidRouteSmokeSecrets.mts scripts/bidding/testBidRouteSmokeSecrets.mts scripts/bidding/smokeBidRoute.mts`: PASS.
- `cd frontend && pnpm run test:bid-smoke-acceptance-runner`: PASS, emitted `BID_SMOKE_ACCEPTANCE_RUNNER_TEST_PASS`.
- `git diff --check` and `git -C frontend diff --check`: PASS.
- `docker compose ps`: db, redis, and optional minio containers up.
- `cd backend && venv/bin/python -m src.ingest --dry-run`: PASS, 253 chunks discoverable from real Vault markdown sources.
- `cd backend && venv/bin/python tests/api_smoke.py`: PASS.
- `cd frontend && pnpm run type-check`: PASS.
- `cd frontend && pnpm run build`: PASS. Build still prints upstream QStash environment-variable and Node runtime warnings, but exits 0.
- `cd frontend && pnpm run acceptance:bid-smoke:local`: PASS, emitted `BID_SMOKE_ACCEPTANCE_RUNNER_TEST_PASS`, `BID_ROUTE_SMOKE_PASS`, and `BID_SMOKE_ACCEPTANCE_LOCAL_PASS`; no FastAPI, Vite, or Next process remained afterward.

### Artifacts
- `pnpm run test:bid-smoke-acceptance-runner` now provides a service-free preflight artifact for the local acceptance runner.
- `BID_ACCEPTANCE_PREFLIGHT_ONLY=1` emits `BID_SMOKE_ACCEPTANCE_PREFLIGHT_PASS` on free configured ports and fails early on occupied ports.

### Blockers / Next
- Legacy LLM RAG script remains blocked until `LLM_API_KEY` is provided via environment and provider quota is available.
- Next useful iteration: add a short CI/runbook matrix showing which bid smoke command to use for service-free checks, local managed services, and already-running service checks.
