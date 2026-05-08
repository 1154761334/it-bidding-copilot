import { readFileSync } from 'node:fs';

const README_PATH = process.env.BID_ROUTE_PRODUCTION_DOCS_README ?? 'scripts/bidding/README.md';
const CAPTURE_SCRIPT_PATH =
  process.env.BID_ROUTE_PRODUCTION_DOCS_CAPTURE_SCRIPT ??
  'scripts/bidding/captureBidRouteStorageState.mts';
const SMOKE_SCRIPT_PATH =
  process.env.BID_ROUTE_PRODUCTION_DOCS_SMOKE_SCRIPT ?? 'scripts/bidding/smokeBidRoute.mts';
const GITIGNORE_PATH = process.env.BID_ROUTE_PRODUCTION_DOCS_GITIGNORE ?? '.gitignore';

const STORAGE_STATE_DIR = '.auth/';
const STORAGE_STATE_PATH = '.auth/bid-route-storage-state.json';
const ALLOWED_COMMAND_ASSIGNMENTS = new Map([['BID_ROUTE_STORAGE_STATE', STORAGE_STATE_PATH]]);
const REQUIRED_PRODUCTION_ENV_NAMES = [
  'APP_URL',
  'DATABASE_DRIVER',
  'DATABASE_URL',
  'AUTH_SECRET',
  'KEY_VAULTS_SECRET',
  'NEXT_PUBLIC_BIDDING_API_BASE_URL',
  'BID_ROUTE_STORAGE_STATE',
];

function readText(path: string) {
  return readFileSync(path, 'utf8');
}

function assertIncludes(source: string, token: string, label: string) {
  if (!source.includes(token)) {
    throw new Error(`${label} is missing ${token}`);
  }
}

function markdownSection(markdown: string, heading: string) {
  const headingIndex = markdown.indexOf(heading);
  if (headingIndex < 0) {
    throw new Error(`${heading} heading was not found.`);
  }

  const nextHeadingIndex = markdown.indexOf('\n## ', headingIndex + 1);
  return markdown.slice(headingIndex, nextHeadingIndex < 0 ? undefined : nextHeadingIndex);
}

function commandExamples(section: string) {
  const inlineCommands = [...section.matchAll(/`([^`\n]*pnpm run [^`\n]*)`/g)].map(
    (match) => match[1],
  );
  const fencedCommands = [...section.matchAll(/```bash\n([\s\S]*?)```/g)].flatMap((match) =>
    match[1]
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter((line) => line.includes('pnpm run')),
  );

  return [...new Set([...inlineCommands, ...fencedCommands])].sort();
}

function commandAssignments(command: string) {
  return [...command.matchAll(/(?:^|\s)([A-Z][A-Z0-9_]*)=([^\s`]+)/g)].map((match) => ({
    name: match[1],
    value: match[2],
  }));
}

const readme = readText(README_PATH);
const captureScript = readText(CAPTURE_SCRIPT_PATH);
const smokeScript = readText(SMOKE_SCRIPT_PATH);
const gitignoreLines = readText(GITIGNORE_PATH).split(/\r?\n/);

const localProductionSection = markdownSection(readme, '## Local production route');
const productionMatrixSection = markdownSection(readme, '## Production command matrix');
const productionDocs = `${localProductionSection}\n${productionMatrixSection}`;
const examples = commandExamples(productionDocs).filter(
  (command) =>
    command.includes('capture:bid-storage-state:prod') ||
    command.includes('smoke:bid-route:prod') ||
    command.includes('test:bid-route-production-docs'),
);

if (!gitignoreLines.some((line) => line.trim() === STORAGE_STATE_DIR)) {
  throw new Error(
    `${STORAGE_STATE_DIR} must stay ignored before storage state capture is documented.`,
  );
}

for (const envName of REQUIRED_PRODUCTION_ENV_NAMES) {
  assertIncludes(localProductionSection, `- \`${envName}\``, 'production environment name list');
}

for (const line of localProductionSection.split(/\r?\n/)) {
  if (!line.trim().startsWith('- `')) continue;
  if (line.includes('=')) {
    throw new Error(`Production environment list must contain names only: ${line.trim()}`);
  }
}

if (examples.length === 0) {
  throw new Error('Production runbook did not document any production route commands.');
}

for (const command of examples) {
  for (const assignment of commandAssignments(command)) {
    const expectedValue = ALLOWED_COMMAND_ASSIGNMENTS.get(assignment.name);
    if (!expectedValue) {
      throw new Error(`Production command example assigns ${assignment.name}; list its name only.`);
    }
    if (assignment.value !== expectedValue) {
      throw new Error(
        `Production command example assigns ${assignment.name} to an unexpected artifact path.`,
      );
    }
  }
}

assertIncludes(
  productionDocs,
  'lists environment variable names only',
  'production login diagnostic',
);
assertIncludes(productionDocs, 'and `.auth/` is ignored', 'storage-state gitignore note');
assertIncludes(
  productionMatrixSection,
  STORAGE_STATE_PATH,
  'production command matrix storage-state artifact',
);
assertIncludes(
  captureScript,
  `DEFAULT_STORAGE_STATE_PATH = '${STORAGE_STATE_PATH}'`,
  'capture script default storage-state path',
);
assertIncludes(
  smokeScript,
  "auth: storageStatePath ? 'storage_state' : 'not_required'",
  'smoke script storage-state auth artifact',
);

console.log(
  JSON.stringify(
    {
      allowed_command_assignments: [...ALLOWED_COMMAND_ASSIGNMENTS.keys()],
      ignored_path: STORAGE_STATE_DIR,
      production_commands: examples,
      required_env_names: REQUIRED_PRODUCTION_ENV_NAMES,
      status: 'BID_ROUTE_PRODUCTION_DOCS_TEST_PASS',
      storage_state_path: STORAGE_STATE_PATH,
    },
    null,
    2,
  ),
);
