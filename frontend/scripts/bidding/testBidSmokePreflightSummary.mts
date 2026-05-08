import { readFileSync } from 'node:fs';

const CANONICAL_MANIFEST_PATH = 'scripts/bidding/bidSmokeAcceptanceManifest.json';
const MANIFEST_PATH = process.env.BID_SMOKE_PREFLIGHT_SUMMARY_MANIFEST ?? CANONICAL_MANIFEST_PATH;
const README_PATH = process.env.BID_SMOKE_PREFLIGHT_SUMMARY_README ?? 'scripts/bidding/README.md';
const PACKAGE_PATH = process.env.BID_SMOKE_PREFLIGHT_SUMMARY_PACKAGE ?? 'package.json';
const SUMMARY_SCRIPT_NAME = 'test:bid-smoke-preflight-summary';
const SUMMARY_STATUS = 'BID_SMOKE_PREFLIGHT_SUMMARY_TEST_PASS';
const TERMINAL_ARTIFACT_ID = 'preflight_port_guard';
const TERMINAL_ARTIFACT_SOURCE = 'scripts/bidding/runBidSmokeAcceptance.mts';
const TERMINAL_COMMAND_MARKER = 'BID_ACCEPTANCE_PREFLIGHT_ONLY=1';

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

function preflightIncludesStep(steps: string[], command: string) {
  return steps.includes(command);
}

function preflightIncludesCommand(steps: string[], command: string) {
  return steps.some((step) => step === command || step.endsWith(command));
}

const manifest = readJson<Manifest>(MANIFEST_PATH);
const packageJson = readJson<PackageJson>(PACKAGE_PATH);
const packageScripts = packageJson.scripts ?? {};
const preflightScript = packageScripts[manifest.gate] ?? '';
const summaryScript = packageScripts[SUMMARY_SCRIPT_NAME] ?? '';
const readme = readText(README_PATH);
const preflightSteps = preflightScript
  .split('&&')
  .map((step) => step.trim())
  .filter(Boolean);
const artifacts = manifest.sub_artifacts.map((artifact) => ({
  command: artifact.command,
  id: artifact.id,
  source: artifact.source,
  status: artifact.status,
}));
const statuses = artifacts.map((artifact) => artifact.status);
const terminalArtifacts = artifacts.filter(
  (artifact) => artifact.status === manifest.expected_terminal_status,
);

assert(manifest.schema_version === 1, 'Summary requires manifest schema version 1.');
assert(manifest.gate === 'acceptance:bid-smoke:preflight', 'Summary gate must be preflight.');
assert(manifest.mode === 'service-free', 'Summary must remain service-free.');
assert(
  manifest.command === 'pnpm run acceptance:bid-smoke:preflight',
  'Summary manifest command drifted.',
);
assert(
  manifest.expected_terminal_status === 'BID_SMOKE_ACCEPTANCE_PREFLIGHT_PASS',
  'Summary terminal status drifted.',
);
assert(terminalArtifacts.length > 0, 'Summary terminal artifact is missing.');
assert(terminalArtifacts.length === 1, 'Summary terminal artifact must be unique.');
const [terminalArtifact] = terminalArtifacts;
assert(terminalArtifact.id === TERMINAL_ARTIFACT_ID, 'Summary terminal artifact id drifted.');
assert(
  terminalArtifact.source === TERMINAL_ARTIFACT_SOURCE,
  'Summary terminal artifact source drifted.',
);
assert(
  terminalArtifact.command.includes(TERMINAL_COMMAND_MARKER),
  'Summary terminal artifact command drifted.',
);
assert(
  summaryScript.includes('testBidSmokePreflightSummary.mts'),
  'Summary package script is missing.',
);
assert(
  preflightIncludesStep(preflightSteps, `pnpm run ${SUMMARY_SCRIPT_NAME}`),
  `Preflight package script does not invoke ${SUMMARY_SCRIPT_NAME}.`,
);
assert(
  preflightScript.includes('BID_ACCEPTANCE_PREFLIGHT_ONLY=1'),
  'Preflight script must stay service-free.',
);
assert(readme.includes(CANONICAL_MANIFEST_PATH), 'Runbook must link the preflight manifest.');
assert(
  readme.includes(`pnpm run ${SUMMARY_SCRIPT_NAME}`),
  'Runbook must document the preflight summary command.',
);

const missingStatuses = statuses.filter((status) => !readme.includes(status));
assert(
  missingStatuses.length === 0,
  `Runbook service-free artifact row is missing statuses: ${missingStatuses.join(', ')}`,
);

for (const artifact of artifacts) {
  const scriptName = packageScriptName(artifact.command);
  if (scriptName) {
    assert(packageScripts[scriptName], `Package script ${scriptName} is missing.`);
    assert(
      preflightIncludesStep(preflightSteps, `pnpm run ${scriptName}`),
      `Preflight package script does not invoke ${scriptName}.`,
    );
  } else {
    assert(
      preflightIncludesCommand(preflightSteps, artifact.command),
      `Preflight package script does not include ${artifact.command}.`,
    );
  }
}

console.log(
  JSON.stringify(
    {
      artifacts,
      command: manifest.command,
      gate: manifest.gate,
      mode: manifest.mode,
      schema_version: 1,
      status: SUMMARY_STATUS,
      sub_artifact_count: artifacts.length,
      terminal_artifact: {
        command: terminalArtifact.command,
        id: terminalArtifact.id,
        source: terminalArtifact.source,
        status: terminalArtifact.status,
      },
      terminal_status: manifest.expected_terminal_status,
    },
    null,
    2,
  ),
);
