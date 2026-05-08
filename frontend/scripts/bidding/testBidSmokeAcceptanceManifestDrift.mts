import { spawnSync } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';

const PNPM_COMMAND = process.platform === 'win32' ? 'pnpm.cmd' : 'pnpm';
const MANIFEST_PATH = 'scripts/bidding/bidSmokeAcceptanceManifest.json';
const PACKAGE_PATH = 'package.json';
const PREFLIGHT_SCRIPT_NAME = 'acceptance:bid-smoke:preflight';
const MANIFEST_SELF_TEST_COMMAND = 'pnpm run test:bid-smoke-acceptance-manifest';
const PREFLIGHT_PORT_GUARD_MARKER = 'BID_ACCEPTANCE_PREFLIGHT_ONLY=1';

interface ManifestArtifact {
  command: string;
  id: string;
  source: string;
  status: string;
}

interface Manifest {
  command: string;
  expected_terminal_status: string;
  gate: string;
  mode: string;
  schema_version: number;
  sub_artifacts: ManifestArtifact[];
}

interface PackageJson {
  scripts?: Record<string, string>;
}

interface GuardResult {
  output: string;
  status: number | null;
}

function runManifestGuard(manifestPath: string): GuardResult {
  const result = spawnSync(
    PNPM_COMMAND,
    ['exec', 'tsx', 'scripts/bidding/testBidSmokeAcceptanceManifest.mts'],
    {
      cwd: process.cwd(),
      encoding: 'utf8',
      env: {
        ...process.env,
        BID_SMOKE_ACCEPTANCE_MANIFEST_PATH: manifestPath,
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
    throw new Error(`Expected manifest ${label} drift to fail.`);
  }
  if (!result.output.includes(expected)) {
    throw new Error(`Expected manifest ${label} drift diagnostic was not emitted.`);
  }
  if (result.output.includes('BID_SMOKE_ACCEPTANCE_MANIFEST_TEST_PASS')) {
    throw new Error(`Manifest ${label} drift should not emit the manifest pass status.`);
  }
}

function writeManifest(pathname: string, manifest: Manifest) {
  writeFileSync(pathname, `${JSON.stringify(manifest, null, 2)}\n`, 'utf8');
}

function cloneManifest(manifest: Manifest) {
  return structuredClone(manifest);
}

function artifactById(manifest: Manifest, id: string) {
  const artifact = manifest.sub_artifacts.find((item) => item.id === id);
  if (!artifact) throw new Error(`Manifest fixture is missing ${id}.`);
  return artifact;
}

const tempDir = mkdtempSync(path.join(tmpdir(), 'bid-smoke-acceptance-manifest-drift-'));
const fixtureManifestPath = path.join(tempDir, 'bidSmokeAcceptanceManifest.json');

try {
  const manifest = JSON.parse(await readFile(MANIFEST_PATH, 'utf8')) as Manifest;
  const packageJson = JSON.parse(await readFile(PACKAGE_PATH, 'utf8')) as PackageJson;
  const preflightScript = packageJson.scripts?.[PREFLIGHT_SCRIPT_NAME] ?? '';
  const manifestSelfTestIndex = preflightScript.indexOf(MANIFEST_SELF_TEST_COMMAND);
  const preflightPortGuardIndex = preflightScript.indexOf(PREFLIGHT_PORT_GUARD_MARKER);

  if (manifestSelfTestIndex < 0) {
    throw new Error('Preflight script must include the manifest self-test.');
  }
  if (preflightPortGuardIndex < 0) {
    throw new Error('Preflight script must include the port preflight guard.');
  }
  if (manifestSelfTestIndex > preflightPortGuardIndex) {
    throw new Error('Manifest self-test must run before the port preflight guard.');
  }

  writeManifest(fixtureManifestPath, manifest);
  const passResult = runManifestGuard(fixtureManifestPath);
  if (passResult.status !== 0) {
    throw new Error(`Expected manifest path override fixture to pass.\n${passResult.output}`);
  }
  if (!passResult.output.includes('BID_SMOKE_ACCEPTANCE_MANIFEST_TEST_PASS')) {
    throw new Error('Expected manifest pass status was not emitted for the path override fixture.');
  }

  const statusDriftManifest = cloneManifest(manifest);
  artifactById(statusDriftManifest, 'command_matrix_guard').status =
    'BID_SMOKE_COMMAND_MATRIX_DRIFT_TEST_PASS';
  writeManifest(fixtureManifestPath, statusDriftManifest);
  assertFailure(
    runManifestGuard(fixtureManifestPath),
    'does not emit BID_SMOKE_COMMAND_MATRIX_DRIFT_TEST_PASS',
    'status',
  );

  const commandDriftManifest = cloneManifest(manifest);
  artifactById(commandDriftManifest, 'command_matrix_guard').command =
    'pnpm run test:bid-smoke-command-matrix-drift-missing';
  writeManifest(fixtureManifestPath, commandDriftManifest);
  assertFailure(
    runManifestGuard(fixtureManifestPath),
    'Package script test:bid-smoke-command-matrix-drift-missing is missing.',
    'command',
  );

  console.log(
    JSON.stringify(
      {
        drift_cases: ['status', 'command'],
        fixture: 'runtime-acceptance-manifest-drift',
        preflight_order: 'manifest_self_test_before_port_preflight',
        status: 'BID_SMOKE_ACCEPTANCE_MANIFEST_DRIFT_TEST_PASS',
      },
      null,
      2,
    ),
  );
} finally {
  rmSync(tempDir, { force: true, recursive: true });
}
