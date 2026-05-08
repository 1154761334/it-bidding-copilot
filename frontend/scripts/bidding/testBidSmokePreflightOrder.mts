import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';

const MANIFEST_PATH =
  process.env.BID_SMOKE_PREFLIGHT_ORDER_MANIFEST ??
  'scripts/bidding/bidSmokeAcceptanceManifest.json';
const PACKAGE_PATH = process.env.BID_SMOKE_PREFLIGHT_ORDER_PACKAGE ?? 'package.json';
const PREFLIGHT_SCRIPT_NAME = 'acceptance:bid-smoke:preflight';
const FULL_SCRIPT_NAME = 'acceptance:bid-smoke';
const ORDER_SCRIPT_NAME = 'test:bid-smoke-preflight-order';
const ORDER_STATUS = 'BID_SMOKE_PREFLIGHT_ORDER_TEST_PASS';
const PREFLIGHT_TERMINAL_ARTIFACT_ID = 'preflight_port_guard';
const PREFLIGHT_TERMINAL_MARKER = 'BID_ACCEPTANCE_PREFLIGHT_ONLY=1';
const PREFLIGHT_TERMINAL_LABEL = 'port preflight guard';
const FULL_TERMINAL_COMMAND = 'pnpm run smoke:bid-route';
const FULL_TERMINAL_LABEL = 'route smoke command';

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

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

function splitSteps(script: string) {
  return script
    .split('&&')
    .map((step) => step.trim())
    .filter(Boolean);
}

function commandIndex(steps: string[], command: string) {
  return steps.indexOf(command);
}

function terminalIndex(steps: string[], terminalLabel: string, matcher: (step: string) => boolean) {
  const index = steps.findIndex(matcher);
  assert(index >= 0, `Package script is missing the ${terminalLabel}.`);
  return index;
}

function serviceFreeCommandsFromManifest(manifest: Manifest) {
  assert(manifest.schema_version === 1, 'Manifest schema version must be 1.');
  assert(manifest.gate === PREFLIGHT_SCRIPT_NAME, 'Manifest gate must target preflight.');
  assert(manifest.mode === 'service-free', 'Manifest mode must stay service-free.');

  const terminalArtifacts = manifest.sub_artifacts.filter(
    (artifact) => artifact.status === manifest.expected_terminal_status,
  );
  assert(terminalArtifacts.length > 0, 'Manifest terminal artifact is missing.');
  assert(terminalArtifacts.length === 1, 'Manifest terminal artifact must be unique.');

  const [terminalArtifact] = terminalArtifacts;
  const terminalArtifactIndex = manifest.sub_artifacts.indexOf(terminalArtifact);
  assert(
    terminalArtifact.id === PREFLIGHT_TERMINAL_ARTIFACT_ID,
    'Manifest terminal artifact must be the preflight port guard.',
  );
  assert(
    terminalArtifact.command.includes(PREFLIGHT_TERMINAL_MARKER),
    'Manifest terminal artifact must run the port preflight guard.',
  );
  assert(
    terminalArtifactIndex === manifest.sub_artifacts.length - 1,
    'Manifest terminal artifact must be last.',
  );

  const commands = manifest.sub_artifacts
    .slice(0, terminalArtifactIndex)
    .map((artifact) => artifact.command);
  assert(commands.length > 0, 'Manifest service-free command list is empty.');
  assert(
    commands.every((command) => command.startsWith('pnpm run ')),
    'Manifest service-free commands must be package scripts.',
  );

  return commands;
}

function assertServiceFreeOrder(
  steps: string[],
  label: string,
  terminalLabel: string,
  terminalStepIndex: number,
  orderedServiceFreeCommands: string[],
) {
  let previousIndex = -1;
  let previousCommand = '';

  for (const command of orderedServiceFreeCommands) {
    const index = commandIndex(steps, command);
    assert(index >= 0, `${label} package script does not invoke ${command}.`);
    assert(
      index < terminalStepIndex,
      `${label} order drift: ${command} must run before ${terminalLabel}.`,
    );
    assert(
      index > previousIndex,
      `${label} order drift: ${command} must run after ${previousCommand}.`,
    );

    previousIndex = index;
    previousCommand = command;
  }
}

function assertPackageOrder(packageJson: PackageJson, manifest: Manifest) {
  const orderedServiceFreeCommands = serviceFreeCommandsFromManifest(manifest);
  const scripts = packageJson.scripts ?? {};
  const preflightSteps = splitSteps(scripts[PREFLIGHT_SCRIPT_NAME] ?? '');
  const fullSteps = splitSteps(scripts[FULL_SCRIPT_NAME] ?? '');
  const orderScript = scripts[ORDER_SCRIPT_NAME] ?? '';

  assert(
    orderScript.includes('testBidSmokePreflightOrder.mts'),
    'Order package script is missing.',
  );

  const preflightTerminalIndex = terminalIndex(preflightSteps, PREFLIGHT_TERMINAL_LABEL, (step) =>
    step.includes(PREFLIGHT_TERMINAL_MARKER),
  );
  const fullTerminalIndex = terminalIndex(
    fullSteps,
    FULL_TERMINAL_LABEL,
    (step) => step === FULL_TERMINAL_COMMAND,
  );

  assertServiceFreeOrder(
    preflightSteps,
    'Preflight',
    PREFLIGHT_TERMINAL_LABEL,
    preflightTerminalIndex,
    orderedServiceFreeCommands,
  );
  assertServiceFreeOrder(
    fullSteps,
    'Full acceptance',
    FULL_TERMINAL_LABEL,
    fullTerminalIndex,
    orderedServiceFreeCommands,
  );

  return {
    ordered_commands: orderedServiceFreeCommands,
    terminal_steps: {
      full_terminal_step: fullSteps[fullTerminalIndex],
      preflight_terminal_step: preflightSteps[preflightTerminalIndex],
    },
  };
}

function cloneManifest(manifest: Manifest) {
  return structuredClone(manifest);
}

function clonePackage(packageJson: PackageJson) {
  return structuredClone(packageJson);
}

function moveStepAfter(
  script: string,
  stepToMove: string,
  targetMatcher: (step: string) => boolean,
) {
  const steps = splitSteps(script);
  const stepIndex = steps.indexOf(stepToMove);
  assert(stepIndex >= 0, `Fixture source is missing ${stepToMove}.`);
  const [step] = steps.splice(stepIndex, 1);
  const targetIndex = steps.findIndex(targetMatcher);
  assert(targetIndex >= 0, 'Fixture source is missing the target command.');
  steps.splice(targetIndex + 1, 0, step);
  return steps.join(' && ');
}

function moveArtifactAfter(manifest: Manifest, artifactId: string, targetId: string) {
  const artifacts = [...manifest.sub_artifacts];
  const artifactIndex = artifacts.findIndex((artifact) => artifact.id === artifactId);
  assert(artifactIndex >= 0, `Fixture manifest is missing ${artifactId}.`);
  const [artifact] = artifacts.splice(artifactIndex, 1);
  const targetIndex = artifacts.findIndex((item) => item.id === targetId);
  assert(targetIndex >= 0, `Fixture manifest is missing ${targetId}.`);
  artifacts.splice(targetIndex + 1, 0, artifact);
  manifest.sub_artifacts = artifacts;
}

function removeArtifact(manifest: Manifest, artifactId: string) {
  const artifacts = manifest.sub_artifacts.filter((artifact) => artifact.id !== artifactId);
  assert(
    artifacts.length === manifest.sub_artifacts.length - 1,
    `Fixture manifest is missing ${artifactId}.`,
  );
  manifest.sub_artifacts = artifacts;
}

function duplicateArtifactAfter(manifest: Manifest, artifactId: string, targetId: string) {
  const artifacts = [...manifest.sub_artifacts];
  const artifact = artifacts.find((item) => item.id === artifactId);
  assert(artifact, `Fixture manifest is missing ${artifactId}.`);
  const targetIndex = artifacts.findIndex((item) => item.id === targetId);
  assert(targetIndex >= 0, `Fixture manifest is missing ${targetId}.`);
  artifacts.splice(targetIndex + 1, 0, {
    ...artifact,
    id: `${artifact.id}_duplicate`,
  });
  manifest.sub_artifacts = artifacts;
}

function assertOrderFailure(
  packageJson: PackageJson,
  manifest: Manifest,
  expected: string,
  label: string,
) {
  try {
    assertPackageOrder(packageJson, manifest);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    if (!message.includes(expected)) {
      throw new Error(`Expected preflight order ${label} diagnostic was not emitted.`, {
        cause: error,
      });
    }
    return;
  }

  throw new Error(`Expected preflight order ${label} fixture to fail.`);
}

const tempDir = mkdtempSync(path.join(tmpdir(), 'bid-smoke-preflight-order-'));

try {
  const sourceManifest = JSON.parse(await readFile(MANIFEST_PATH, 'utf8')) as Manifest;
  const sourcePackage = JSON.parse(await readFile(PACKAGE_PATH, 'utf8')) as PackageJson;
  const orderReport = assertPackageOrder(sourcePackage, sourceManifest);

  const summaryAfterPortPackage = clonePackage(sourcePackage);
  summaryAfterPortPackage.scripts ??= {};
  summaryAfterPortPackage.scripts[PREFLIGHT_SCRIPT_NAME] = moveStepAfter(
    summaryAfterPortPackage.scripts[PREFLIGHT_SCRIPT_NAME] ?? '',
    'pnpm run test:bid-smoke-preflight-summary',
    (step) => step.includes(PREFLIGHT_TERMINAL_MARKER),
  );
  assertOrderFailure(
    summaryAfterPortPackage,
    sourceManifest,
    'Preflight order drift: pnpm run test:bid-smoke-preflight-summary must run before port preflight guard.',
    'summary_after_port_preflight',
  );

  const manifestAfterSmokePackage = clonePackage(sourcePackage);
  manifestAfterSmokePackage.scripts ??= {};
  manifestAfterSmokePackage.scripts[FULL_SCRIPT_NAME] = moveStepAfter(
    manifestAfterSmokePackage.scripts[FULL_SCRIPT_NAME] ?? '',
    'pnpm run test:bid-smoke-acceptance-manifest',
    (step) => step === FULL_TERMINAL_COMMAND,
  );
  assertOrderFailure(
    manifestAfterSmokePackage,
    sourceManifest,
    'Full acceptance order drift: pnpm run test:bid-smoke-acceptance-manifest must run before route smoke command.',
    'manifest_after_route_smoke',
  );

  const manifestOrderDrift = cloneManifest(sourceManifest);
  moveArtifactAfter(manifestOrderDrift, 'command_matrix_guard', 'acceptance_manifest_guard');
  assertOrderFailure(
    sourcePackage,
    manifestOrderDrift,
    'Preflight order drift: pnpm run test:bid-smoke-command-matrix must run after pnpm run test:bid-smoke-acceptance-manifest.',
    'manifest_order_drift',
  );

  const terminalArtifactOmitted = cloneManifest(sourceManifest);
  removeArtifact(terminalArtifactOmitted, PREFLIGHT_TERMINAL_ARTIFACT_ID);
  assertOrderFailure(
    sourcePackage,
    terminalArtifactOmitted,
    'Manifest terminal artifact is missing.',
    'terminal_artifact_omitted',
  );

  const terminalArtifactDuplicated = cloneManifest(sourceManifest);
  duplicateArtifactAfter(
    terminalArtifactDuplicated,
    PREFLIGHT_TERMINAL_ARTIFACT_ID,
    'acceptance_manifest_guard',
  );
  assertOrderFailure(
    sourcePackage,
    terminalArtifactDuplicated,
    'Manifest terminal artifact must be unique.',
    'terminal_artifact_duplicated',
  );

  const terminalArtifactMoved = cloneManifest(sourceManifest);
  moveArtifactAfter(
    terminalArtifactMoved,
    PREFLIGHT_TERMINAL_ARTIFACT_ID,
    'acceptance_manifest_guard',
  );
  assertOrderFailure(
    sourcePackage,
    terminalArtifactMoved,
    'Manifest terminal artifact must be last.',
    'terminal_artifact_moved',
  );

  writeFileSync(
    path.join(tempDir, 'preflight-order-package.json'),
    `${JSON.stringify(sourcePackage, null, 2)}\n`,
    'utf8',
  );
  writeFileSync(
    path.join(tempDir, 'preflight-order-manifest.json'),
    `${JSON.stringify(sourceManifest, null, 2)}\n`,
    'utf8',
  );

  console.log(
    JSON.stringify(
      {
        drift_cases: [
          'summary_after_port_preflight',
          'manifest_after_route_smoke',
          'manifest_order_drift',
        ],
        fixture: 'runtime-preflight-order',
        ordered_commands: orderReport.ordered_commands,
        status: ORDER_STATUS,
        terminal_artifact_cases: [
          'terminal_artifact_omitted',
          'terminal_artifact_duplicated',
          'terminal_artifact_moved',
        ],
        terminal_steps: orderReport.terminal_steps,
      },
      null,
      2,
    ),
  );
} finally {
  rmSync(tempDir, { force: true, recursive: true });
}
