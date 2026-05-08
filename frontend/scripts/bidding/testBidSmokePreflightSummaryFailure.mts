import { spawnSync } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';

const PNPM_COMMAND = process.platform === 'win32' ? 'pnpm.cmd' : 'pnpm';
const MANIFEST_PATH = 'scripts/bidding/bidSmokeAcceptanceManifest.json';
const README_PATH = 'scripts/bidding/README.md';
const PACKAGE_PATH = 'package.json';
const SUMMARY_SCRIPT = 'scripts/bidding/testBidSmokePreflightSummary.mts';
const SUMMARY_COMMAND = 'pnpm run test:bid-smoke-preflight-summary';
const SUMMARY_STATUS = 'BID_SMOKE_PREFLIGHT_SUMMARY_TEST_PASS';
const FAILURE_STATUS = 'BID_SMOKE_PREFLIGHT_SUMMARY_FAILURE_TEST_PASS';

interface GuardResult {
  output: string;
  status: number | null;
}

interface FixtureFiles {
  manifest: string;
  packageJson: string;
  readme: string;
}

interface ManifestArtifact {
  command: string;
  id: string;
  source: string;
  status: string;
}

interface Manifest {
  expected_terminal_status: string;
  sub_artifacts: ManifestArtifact[];
}

interface PackageJson {
  scripts?: Record<string, string>;
}

function runSummaryGuard(files: FixtureFiles) {
  const result = spawnSync(PNPM_COMMAND, ['exec', 'tsx', SUMMARY_SCRIPT], {
    cwd: process.cwd(),
    encoding: 'utf8',
    env: {
      ...process.env,
      BID_SMOKE_PREFLIGHT_SUMMARY_MANIFEST: files.manifest,
      BID_SMOKE_PREFLIGHT_SUMMARY_PACKAGE: files.packageJson,
      BID_SMOKE_PREFLIGHT_SUMMARY_README: files.readme,
    },
  });

  return {
    output: `${result.stdout}\n${result.stderr}`,
    status: result.status,
  };
}

function assertFailure(result: GuardResult, expected: string, label: string) {
  if (result.status === 0) {
    throw new Error(`Expected preflight summary ${label} fixture to fail.`);
  }
  if (!result.output.includes(expected)) {
    throw new Error(`Expected preflight summary ${label} diagnostic was not emitted.`);
  }
  if (result.output.includes(SUMMARY_STATUS)) {
    throw new Error(`Preflight summary ${label} fixture should not emit the summary pass status.`);
  }
}

function cloneManifest(manifest: Manifest) {
  return structuredClone(manifest);
}

function terminalArtifact(manifest: Manifest) {
  const artifacts = manifest.sub_artifacts.filter(
    (artifact) => artifact.status === manifest.expected_terminal_status,
  );
  if (artifacts.length !== 1) {
    throw new Error('Expected source manifest to have exactly one terminal artifact.');
  }
  return artifacts[0];
}

function writeManifestFixture(files: FixtureFiles, manifest: Manifest) {
  writeFileSync(files.manifest, `${JSON.stringify(manifest, null, 2)}\n`, 'utf8');
}

const tempDir = mkdtempSync(path.join(tmpdir(), 'bid-smoke-preflight-summary-failure-'));

try {
  const sourceText = {
    manifest: await readFile(MANIFEST_PATH, 'utf8'),
    packageJson: await readFile(PACKAGE_PATH, 'utf8'),
    readme: await readFile(README_PATH, 'utf8'),
  };
  const sourceManifest = JSON.parse(sourceText.manifest) as Manifest;
  const fixtureFiles = {
    manifest: path.join(tempDir, 'bidSmokeAcceptanceManifest.json'),
    packageJson: path.join(tempDir, 'package.json'),
    readme: path.join(tempDir, 'README.md'),
  };

  for (const [key, value] of Object.entries(sourceText)) {
    writeFileSync(fixtureFiles[key as keyof typeof fixtureFiles], value, 'utf8');
  }

  const passResult = runSummaryGuard(fixtureFiles);
  if (passResult.status !== 0) {
    throw new Error(
      `Expected preflight summary path override fixture to pass.\n${passResult.output}`,
    );
  }
  if (!passResult.output.includes(SUMMARY_STATUS)) {
    throw new Error('Expected preflight summary pass status was not emitted.');
  }

  writeFileSync(
    fixtureFiles.readme,
    sourceText.readme.replaceAll(FAILURE_STATUS, 'BID_SMOKE_PREFLIGHT_SUMMARY_STATUS_MISSING'),
    'utf8',
  );
  assertFailure(
    runSummaryGuard(fixtureFiles),
    `Runbook service-free artifact row is missing statuses: ${FAILURE_STATUS}`,
    'runbook status',
  );
  writeFileSync(fixtureFiles.readme, sourceText.readme, 'utf8');

  const missingSummaryPackage = JSON.parse(sourceText.packageJson) as PackageJson;
  missingSummaryPackage.scripts ??= {};
  missingSummaryPackage.scripts['acceptance:bid-smoke:preflight'] = (
    missingSummaryPackage.scripts['acceptance:bid-smoke:preflight'] ?? ''
  ).replace(SUMMARY_COMMAND, 'pnpm run test:bid-smoke-preflight-summary-missing');
  writeFileSync(fixtureFiles.packageJson, `${JSON.stringify(missingSummaryPackage, null, 2)}\n`);
  assertFailure(
    runSummaryGuard(fixtureFiles),
    'Preflight package script does not invoke test:bid-smoke-preflight-summary.',
    'preflight command',
  );
  writeFileSync(fixtureFiles.packageJson, sourceText.packageJson, 'utf8');

  const terminalIdDrift = cloneManifest(sourceManifest);
  terminalArtifact(terminalIdDrift).id = 'preflight_port_guard_drift';
  writeManifestFixture(fixtureFiles, terminalIdDrift);
  assertFailure(
    runSummaryGuard(fixtureFiles),
    'Summary terminal artifact id drifted.',
    'terminal artifact id',
  );

  const terminalSourceDrift = cloneManifest(sourceManifest);
  terminalArtifact(terminalSourceDrift).source = 'scripts/bidding/smokeBidRoute.mts';
  writeManifestFixture(fixtureFiles, terminalSourceDrift);
  assertFailure(
    runSummaryGuard(fixtureFiles),
    'Summary terminal artifact source drifted.',
    'terminal artifact source',
  );

  const terminalCommandDrift = cloneManifest(sourceManifest);
  const terminalCommandArtifact = terminalArtifact(terminalCommandDrift);
  terminalCommandArtifact.command = terminalCommandArtifact.command.replace(
    'BID_ACCEPTANCE_PREFLIGHT_ONLY=1',
    'BID_ACCEPTANCE_PREFLIGHT_ONLY=0',
  );
  writeManifestFixture(fixtureFiles, terminalCommandDrift);
  assertFailure(
    runSummaryGuard(fixtureFiles),
    'Summary terminal artifact command drifted.',
    'terminal artifact command',
  );

  console.log(
    JSON.stringify(
      {
        failure_cases: [
          'runbook_status',
          'preflight_command',
          'terminal_artifact_id',
          'terminal_artifact_source',
          'terminal_artifact_command',
        ],
        fixture: 'runtime-preflight-summary-failure',
        status: FAILURE_STATUS,
      },
      null,
      2,
    ),
  );
} finally {
  rmSync(tempDir, { force: true, recursive: true });
}
