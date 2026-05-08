import { readFileSync } from 'node:fs';

const CANONICAL_MANIFEST_PATH = 'scripts/bidding/bidSmokeAcceptanceManifest.json';
const MANIFEST_PATH = process.env.BID_SMOKE_ACCEPTANCE_MANIFEST_PATH ?? CANONICAL_MANIFEST_PATH;
const README_PATH = process.env.BID_SMOKE_ACCEPTANCE_MANIFEST_README ?? 'scripts/bidding/README.md';
const PACKAGE_PATH = process.env.BID_SMOKE_ACCEPTANCE_MANIFEST_PACKAGE ?? 'package.json';

interface PackageJson {
  scripts?: Record<string, string>;
}

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

function readText(path: string) {
  return readFileSync(path, 'utf8');
}

function readJson<T>(path: string) {
  return JSON.parse(readText(path)) as T;
}

function packageScriptName(command: string) {
  const match = command.match(/^pnpm run ([\w:-]+)$/);
  return match?.[1];
}

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

const manifest = readJson<Manifest>(MANIFEST_PATH);
const packageJson = readJson<PackageJson>(PACKAGE_PATH);
const packageScripts = packageJson.scripts ?? {};
const preflightScript = packageScripts[manifest.gate] ?? '';
const readme = readText(README_PATH);

assert(manifest.schema_version === 1, 'Manifest schema version must be 1.');
assert(manifest.gate === 'acceptance:bid-smoke:preflight', 'Manifest gate must target preflight.');
assert(manifest.mode === 'service-free', 'Manifest mode must stay service-free.');
assert(manifest.command === 'pnpm run acceptance:bid-smoke:preflight', 'Manifest command drifted.');
assert(preflightScript.length > 0, 'Preflight package script is missing.');
assert(
  preflightScript.includes('BID_ACCEPTANCE_PREFLIGHT_ONLY=1'),
  'Preflight package script must stay service-free.',
);
assert(
  manifest.expected_terminal_status === 'BID_SMOKE_ACCEPTANCE_PREFLIGHT_PASS',
  'Unexpected preflight terminal status.',
);
assert(
  readme.includes(CANONICAL_MANIFEST_PATH) &&
    readme.includes('pnpm run test:bid-smoke-acceptance-manifest'),
  'Runbook must point to the compact acceptance manifest and its self-test.',
);

const seenIds = new Set<string>();
const seenStatuses = new Set<string>();
for (const artifact of manifest.sub_artifacts) {
  assert(artifact.id, 'Manifest artifact id is missing.');
  assert(!seenIds.has(artifact.id), `Duplicate manifest artifact id: ${artifact.id}`);
  seenIds.add(artifact.id);

  assert(artifact.command, `Manifest command is missing for ${artifact.id}.`);
  assert(artifact.source, `Manifest source is missing for ${artifact.id}.`);
  assert(artifact.status, `Manifest status is missing for ${artifact.id}.`);
  assert(!seenStatuses.has(artifact.status), `Duplicate manifest status: ${artifact.status}`);
  seenStatuses.add(artifact.status);

  const sourceText = readText(artifact.source);
  assert(
    sourceText.includes(artifact.status),
    `${artifact.source} does not emit ${artifact.status}.`,
  );

  const scriptName = packageScriptName(artifact.command);
  if (scriptName) {
    assert(packageScripts[scriptName], `Package script ${scriptName} is missing.`);
    assert(
      preflightScript.includes(`pnpm run ${scriptName}`),
      `Preflight package script does not invoke ${scriptName}.`,
    );
  } else {
    assert(
      preflightScript.includes(artifact.command),
      `Preflight package script does not include ${artifact.command}.`,
    );
  }
}

for (const expectedStatus of [
  'BID_ROUTE_SMOKE_SECRET_CHECK_PASS',
  'BID_ROUTE_SMOKE_SECRET_TEST_PASS',
  'BID_SMOKE_ACCEPTANCE_RUNNER_TEST_PASS',
  'BID_SMOKE_COMMAND_MATRIX_TEST_PASS',
  'BID_SMOKE_ACCEPTANCE_MANIFEST_TEST_PASS',
  'BID_SMOKE_ACCEPTANCE_MANIFEST_DRIFT_TEST_PASS',
  'BID_SMOKE_PREFLIGHT_SUMMARY_TEST_PASS',
  'BID_SMOKE_PREFLIGHT_SUMMARY_FAILURE_TEST_PASS',
  'BID_SMOKE_PREFLIGHT_ORDER_TEST_PASS',
  'BID_ROUTE_PRODUCTION_DOCS_TEST_PASS',
  'BID_ROUTE_PRODUCTION_DOCS_FAILURE_TEST_PASS',
  'BID_ROUTE_PRODUCTION_DOCS_DRIFT_TEST_PASS',
  'BID_SMOKE_ACCEPTANCE_PREFLIGHT_PASS',
]) {
  assert(seenStatuses.has(expectedStatus), `Manifest is missing ${expectedStatus}.`);
}

console.log(
  JSON.stringify(
    {
      artifact_count: manifest.sub_artifacts.length,
      gate: manifest.gate,
      mode: manifest.mode,
      status: 'BID_SMOKE_ACCEPTANCE_MANIFEST_TEST_PASS',
      statuses: [...seenStatuses].sort(),
    },
    null,
    2,
  ),
);
