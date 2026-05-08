# Bidding route smoke

This directory contains local acceptance helpers for the Bidding Assistant route. Keep credentials and browser state out of git; the scripts only print environment variable names when authentication setup is missing.

## Default Vite route

Run these from separate shells when checking the direct SPA route:

```bash
cd backend
venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 8000
```

```bash
cd frontend
pnpm dev:spa --host 127.0.0.1
```

```bash
cd frontend
pnpm run smoke:bid-route
```

The expected success status is `BID_ROUTE_SMOKE_PASS` with `auth` set to `not_required`.

For the full local smoke gate, keep the FastAPI and Vite commands above running, then run:

```bash
cd frontend
pnpm run acceptance:bid-smoke
```

This preset runs the non-secret static guard, its runtime fixture self-test, the local runner preflight self-test, the command matrix self-test, the compact acceptance manifest self-test, its drift fixture, the preflight CI summary export, its failure fixture, the preflight command order fixture, the production-route docs/storage-state guard, its runtime failure fixture, its path override drift fixture, and the real `/bid` route smoke in sequence.

## Command matrix

| Scenario                       | Command                                   | Services started                                                                                                                              | Expected artifacts                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| ------------------------------ | ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Service-free CI/preflight      | `pnpm run acceptance:bid-smoke:preflight` | None; it checks docs, scripts, runtime fixtures, manifest drift, CI summary export/failure, command ordering, and runner port preflight only. | `BID_ROUTE_SMOKE_SECRET_CHECK_PASS`, `BID_ROUTE_SMOKE_SECRET_TEST_PASS`, `BID_SMOKE_ACCEPTANCE_RUNNER_TEST_PASS`, `BID_SMOKE_COMMAND_MATRIX_TEST_PASS`, `BID_SMOKE_ACCEPTANCE_MANIFEST_TEST_PASS`, `BID_SMOKE_ACCEPTANCE_MANIFEST_DRIFT_TEST_PASS`, `BID_SMOKE_PREFLIGHT_SUMMARY_TEST_PASS`, `BID_SMOKE_PREFLIGHT_SUMMARY_FAILURE_TEST_PASS`, `BID_SMOKE_PREFLIGHT_ORDER_TEST_PASS`, `BID_ROUTE_PRODUCTION_DOCS_TEST_PASS`, `BID_ROUTE_PRODUCTION_DOCS_FAILURE_TEST_PASS`, `BID_ROUTE_PRODUCTION_DOCS_DRIFT_TEST_PASS`, `BID_SMOKE_ACCEPTANCE_PREFLIGHT_PASS` |
| Local managed services         | `pnpm run acceptance:bid-smoke:local`     | Temporary FastAPI and Vite are started and stopped by the helper.                                                                             | `BID_ROUTE_SMOKE_PASS`, `BID_SMOKE_ACCEPTANCE_LOCAL_PASS`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| Already-running FastAPI + Vite | `pnpm run acceptance:bid-smoke`           | None; keep FastAPI on `127.0.0.1:8000` and Vite on `127.0.0.1:9876` running before invoking it.                                               | `BID_ROUTE_SMOKE_PASS`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |

The matrix is checked by `pnpm run test:bid-smoke-command-matrix`.

The compact acceptance manifest is `scripts/bidding/bidSmokeAcceptanceManifest.json` and is checked by `pnpm run test:bid-smoke-acceptance-manifest`; status/command drift is checked by `pnpm run test:bid-smoke-acceptance-manifest-drift`. The single preflight CI summary JSON is emitted by `pnpm run test:bid-smoke-preflight-summary` and exposes terminal artifact id/source/command separately for the port preflight guard; missing runbook statuses, missing preflight commands, and terminal artifact identity drift are checked by `pnpm run test:bid-smoke-preflight-summary-failure`; exact preflight command ordering is checked by `pnpm run test:bid-smoke-preflight-order`, which derives the service-free command list from the manifest and proves the terminal port guard cannot be omitted, duplicated, or moved away from the end of the manifest.

To run the same gate with temporary services managed for you:

```bash
cd frontend
pnpm run acceptance:bid-smoke:local
```

This helper starts temporary FastAPI and Vite processes, waits for them to serve the Bidding API and `/bid`, runs `acceptance:bid-smoke`, and tears them down on success or failure. Set `BID_ACCEPTANCE_PREFLIGHT_ONLY=1` to validate configured ports without starting services; the expected status is `BID_SMOKE_ACCEPTANCE_PREFLIGHT_PASS`.

## Local production route

Use the production route preset after a local Next instance is already running on `http://127.0.0.1:3210`. Configure required values through the environment only; do not write secret values into this repo. The relevant environment variable names are:

- `APP_URL`
- `DATABASE_DRIVER`
- `DATABASE_URL`
- `AUTH_SECRET`
- `KEY_VAULTS_SECRET`
- `NEXT_PUBLIC_BIDDING_API_BASE_URL`
- `BID_ROUTE_STORAGE_STATE`

## Production command matrix

| Scenario                  | Command                                                                                    | Services started                                                      | Expected artifacts                                                                                                           |
| ------------------------- | ------------------------------------------------------------------------------------------ | --------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Capture storage state     | `pnpm run capture:bid-storage-state:prod`                                                  | None; keep local Next running on `127.0.0.1:3210` before invoking it. | `BID_ROUTE_LOGIN_REQUIRED` when login is required, then `.auth/bid-route-storage-state.json` after browser state is captured |
| Smoke with captured state | `BID_ROUTE_STORAGE_STATE=.auth/bid-route-storage-state.json pnpm run smoke:bid-route:prod` | None; keep local Next running on `127.0.0.1:3210` before invoking it. | `BID_ROUTE_SMOKE_PASS` with `auth` set to `storage_state`                                                                    |

The production route docs/storage-state guard is checked by `pnpm run test:bid-route-production-docs`. Its runtime failure fixture is checked by `pnpm run test:bid-route-production-docs-failure`, and its path override drift fixture is checked by `pnpm run test:bid-route-production-docs-drift`.

Capture storage state after logging in:

```bash
cd frontend
pnpm run capture:bid-storage-state:prod
```

If login is still required, the helper emits `BID_ROUTE_LOGIN_REQUIRED` and lists environment variable names only. Complete login in the opened browser window; the default artifact path is `.auth/bid-route-storage-state.json`, and `.auth/` is ignored.

Run the production route smoke with the captured state:

```bash
cd frontend
BID_ROUTE_STORAGE_STATE=.auth/bid-route-storage-state.json pnpm run smoke:bid-route:prod
```

The expected success status is `BID_ROUTE_SMOKE_PASS` with `auth` set to `storage_state`.
