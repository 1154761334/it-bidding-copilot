import { spawnSync } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';

const PNPM_COMMAND = process.platform === 'win32' ? 'pnpm.cmd' : 'pnpm';
const README_PATH = 'scripts/bidding/README.md';
const SAFE_STORAGE_COMMAND =
  'BID_ROUTE_STORAGE_STATE=.auth/bid-route-storage-state.json pnpm run smoke:bid-route:prod';

const tempDir = mkdtempSync(path.join(tmpdir(), 'bid-route-production-docs-'));
const fixtureReadmePath = path.join(tempDir, 'README.md');
const sensitiveEnvName = ['AUTH', 'SECRET'].join('_');
const fixtureValue = ['runtime', 'production', 'docs', 'fixture', Date.now().toString(36)].join(
  '_',
);

try {
  const readme = await readFile(README_PATH, 'utf8');
  if (!readme.includes(SAFE_STORAGE_COMMAND)) {
    throw new Error('Expected production storage-state smoke command was not found.');
  }

  const fixtureReadme = readme.replace(
    SAFE_STORAGE_COMMAND,
    `${sensitiveEnvName}=${fixtureValue} pnpm run smoke:bid-route:prod`,
  );
  writeFileSync(fixtureReadmePath, fixtureReadme, 'utf8');

  const result = spawnSync(
    PNPM_COMMAND,
    ['exec', 'tsx', 'scripts/bidding/testBidRouteProductionDocs.mts'],
    {
      cwd: process.cwd(),
      encoding: 'utf8',
      env: {
        ...process.env,
        BID_ROUTE_PRODUCTION_DOCS_README: fixtureReadmePath,
      },
    },
  );

  const output = `${result.stdout}\n${result.stderr}`;
  if (result.status === 0) {
    throw new Error('Expected production docs guard to fail for the runtime fixture.');
  }
  if (
    !output.includes(`Production command example assigns ${sensitiveEnvName}; list its name only.`)
  ) {
    throw new Error('Expected sensitive production assignment diagnostic was not emitted.');
  }
  if (output.includes(fixtureValue)) {
    throw new Error('Generated production docs fixture value leaked into guard output.');
  }
  if (output.includes('BID_ROUTE_PRODUCTION_DOCS_TEST_PASS')) {
    throw new Error('Production docs pass status should not be emitted for the failure fixture.');
  }

  console.log(
    JSON.stringify(
      {
        fixture: 'runtime-production-docs',
        rejected_env_name: sensitiveEnvName,
        status: 'BID_ROUTE_PRODUCTION_DOCS_FAILURE_TEST_PASS',
      },
      null,
      2,
    ),
  );
} finally {
  rmSync(tempDir, { force: true, recursive: true });
}
