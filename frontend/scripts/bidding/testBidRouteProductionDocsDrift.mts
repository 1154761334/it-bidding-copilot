import { spawnSync } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';

const PNPM_COMMAND = process.platform === 'win32' ? 'pnpm.cmd' : 'pnpm';
const SOURCE_PATHS = {
  capture: 'scripts/bidding/captureBidRouteStorageState.mts',
  gitignore: '.gitignore',
  readme: 'scripts/bidding/README.md',
  smoke: 'scripts/bidding/smokeBidRoute.mts',
};
const STORAGE_STATE_DIR = '.auth/';
const STORAGE_STATE_PATH = '.auth/bid-route-storage-state.json';
const CAPTURE_DEFAULT_MARKER = `DEFAULT_STORAGE_STATE_PATH = '${STORAGE_STATE_PATH}'`;
const SMOKE_AUTH_MARKER = "auth: storageStatePath ? 'storage_state' : 'not_required'";

interface FixtureFiles {
  capture: string;
  gitignore: string;
  readme: string;
  smoke: string;
}

interface GuardResult {
  output: string;
  status: number | null;
}

function runGuard(files: FixtureFiles): GuardResult {
  const result = spawnSync(
    PNPM_COMMAND,
    ['exec', 'tsx', 'scripts/bidding/testBidRouteProductionDocs.mts'],
    {
      cwd: process.cwd(),
      encoding: 'utf8',
      env: {
        ...process.env,
        BID_ROUTE_PRODUCTION_DOCS_CAPTURE_SCRIPT: files.capture,
        BID_ROUTE_PRODUCTION_DOCS_GITIGNORE: files.gitignore,
        BID_ROUTE_PRODUCTION_DOCS_README: files.readme,
        BID_ROUTE_PRODUCTION_DOCS_SMOKE_SCRIPT: files.smoke,
      },
    },
  );

  return {
    output: `${result.stdout}\n${result.stderr}`,
    status: result.status,
  };
}

function assertFailure(result: GuardResult, expected: string, label: string) {
  if (result.status === 0) {
    throw new Error(`Expected ${label} drift to fail.`);
  }
  if (!result.output.includes(expected)) {
    throw new Error(`Expected ${label} drift diagnostic was not emitted.`);
  }
  if (result.output.includes('BID_ROUTE_PRODUCTION_DOCS_TEST_PASS')) {
    throw new Error(`${label} drift should not emit the production docs pass status.`);
  }
}

const tempDir = mkdtempSync(path.join(tmpdir(), 'bid-route-production-docs-drift-'));

try {
  const sourceText = {
    capture: await readFile(SOURCE_PATHS.capture, 'utf8'),
    gitignore: await readFile(SOURCE_PATHS.gitignore, 'utf8'),
    readme: await readFile(SOURCE_PATHS.readme, 'utf8'),
    smoke: await readFile(SOURCE_PATHS.smoke, 'utf8'),
  };
  const fixtureFiles = {
    capture: path.join(tempDir, 'captureBidRouteStorageState.mts'),
    gitignore: path.join(tempDir, '.gitignore'),
    readme: path.join(tempDir, 'README.md'),
    smoke: path.join(tempDir, 'smokeBidRoute.mts'),
  };

  for (const [key, value] of Object.entries(sourceText)) {
    writeFileSync(fixtureFiles[key as keyof FixtureFiles], value, 'utf8');
  }

  const passResult = runGuard(fixtureFiles);
  if (passResult.status !== 0) {
    throw new Error(`Expected path override fixture to pass.\n${passResult.output}`);
  }
  if (!passResult.output.includes('BID_ROUTE_PRODUCTION_DOCS_TEST_PASS')) {
    throw new Error('Expected path override pass status was not emitted.');
  }

  writeFileSync(
    fixtureFiles.gitignore,
    sourceText.gitignore
      .split(/\r?\n/)
      .filter((line) => line.trim() !== STORAGE_STATE_DIR)
      .join('\n'),
    'utf8',
  );
  assertFailure(
    runGuard(fixtureFiles),
    `${STORAGE_STATE_DIR} must stay ignored before storage state capture is documented.`,
    'gitignore',
  );
  writeFileSync(fixtureFiles.gitignore, sourceText.gitignore, 'utf8');

  writeFileSync(
    fixtureFiles.capture,
    sourceText.capture.replace(
      CAPTURE_DEFAULT_MARKER,
      "DEFAULT_STORAGE_STATE_PATH = '.auth/drift.json'",
    ),
    'utf8',
  );
  assertFailure(
    runGuard(fixtureFiles),
    `capture script default storage-state path is missing ${CAPTURE_DEFAULT_MARKER}`,
    'capture path',
  );
  writeFileSync(fixtureFiles.capture, sourceText.capture, 'utf8');

  writeFileSync(
    fixtureFiles.smoke,
    sourceText.smoke.replace(
      SMOKE_AUTH_MARKER,
      "auth: storageStatePath ? 'drift' : 'not_required'",
    ),
    'utf8',
  );
  assertFailure(
    runGuard(fixtureFiles),
    `smoke script storage-state auth artifact is missing ${SMOKE_AUTH_MARKER}`,
    'smoke auth',
  );

  console.log(
    JSON.stringify(
      {
        drift_cases: ['gitignore', 'capture_path', 'smoke_auth'],
        fixture: 'runtime-path-overrides',
        status: 'BID_ROUTE_PRODUCTION_DOCS_DRIFT_TEST_PASS',
        storage_state_path: STORAGE_STATE_PATH,
      },
      null,
      2,
    ),
  );
} finally {
  rmSync(tempDir, { force: true, recursive: true });
}
