import { spawnSync } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

const tempDir = mkdtempSync(path.join(tmpdir(), 'bid-route-secret-check-'));
const fixturePath = path.join(tempDir, 'fixture.txt');

const credentialName = ['api', 'key'].join('_');
const credentialValue = ['runtime', 'fixture', 'value', 'must', 'redact', '1234567890'].join('_');

try {
  writeFileSync(fixturePath, `${credentialName}="${credentialValue}"\n`, 'utf8');

  const result = spawnSync(
    'pnpm',
    ['exec', 'tsx', 'scripts/bidding/checkBidRouteSmokeSecrets.mts'],
    {
      cwd: process.cwd(),
      encoding: 'utf8',
      env: {
        ...process.env,
        BID_ROUTE_SMOKE_SECRET_CHECK_TARGETS: fixturePath,
      },
    },
  );

  const output = `${result.stdout}\n${result.stderr}`;
  if (result.status === 0) {
    throw new Error('Expected secret guard to fail for the runtime fixture.');
  }
  if (!output.includes('BID_ROUTE_SMOKE_SECRET_CHECK_FAIL')) {
    throw new Error('Expected failure status was not emitted.');
  }
  if (!output.includes('<redacted>')) {
    throw new Error('Expected redacted excerpt was not emitted.');
  }
  if (output.includes(credentialValue)) {
    throw new Error('Generated credential fixture leaked into guard output.');
  }

  console.log(
    JSON.stringify(
      {
        fixture: 'runtime-generated',
        status: 'BID_ROUTE_SMOKE_SECRET_TEST_PASS',
      },
      null,
      2,
    ),
  );
} finally {
  rmSync(tempDir, { force: true, recursive: true });
}
