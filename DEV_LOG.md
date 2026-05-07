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
