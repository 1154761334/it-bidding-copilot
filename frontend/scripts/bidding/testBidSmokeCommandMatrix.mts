import { readFileSync } from 'node:fs';

const README_PATH = 'scripts/bidding/README.md';
const packageJson = JSON.parse(readFileSync('package.json', 'utf8')) as {
  scripts?: Record<string, string>;
};
const readme = readFileSync(README_PATH, 'utf8');

const MATRIX_HEADINGS = ['## Command matrix', '## Production command matrix'];
const REQUIRED_MATRIX_COMMANDS = [
  'acceptance:bid-smoke',
  'acceptance:bid-smoke:local',
  'acceptance:bid-smoke:preflight',
  'capture:bid-storage-state:prod',
  'smoke:bid-route:prod',
];

function commandMatrixSection(heading: string) {
  const headingIndex = readme.indexOf(heading);
  if (headingIndex < 0) {
    throw new Error(`${heading} heading was not found.`);
  }

  const nextHeadingIndex = readme.indexOf('\n## ', headingIndex + 1);
  return readme.slice(headingIndex, nextHeadingIndex < 0 ? undefined : nextHeadingIndex);
}

const matrixText = MATRIX_HEADINGS.map((heading) => commandMatrixSection(heading)).join('\n');
const documentedCommands = [
  ...new Set(
    [...matrixText.matchAll(/`(?:[A-Z_]+=[^\s`]+\s+)*pnpm run ([\w:-]+)`/g)].map(
      (match) => match[1],
    ),
  ),
].sort();
const packageCommands = Object.keys(packageJson.scripts ?? {})
  .filter((name) => REQUIRED_MATRIX_COMMANDS.includes(name) || documentedCommands.includes(name))
  .sort();

const missingFromPackage = documentedCommands.filter(
  (command) => !packageCommands.includes(command),
);
const missingFromMatrix = REQUIRED_MATRIX_COMMANDS.filter(
  (command) => !documentedCommands.includes(command),
);
const missingRequiredPackage = REQUIRED_MATRIX_COMMANDS.filter(
  (command) => !packageCommands.includes(command),
);

if (documentedCommands.length === 0) {
  throw new Error('Command matrices did not document any bid smoke commands.');
}
if (
  missingFromPackage.length > 0 ||
  missingFromMatrix.length > 0 ||
  missingRequiredPackage.length > 0
) {
  throw new Error(
    JSON.stringify(
      {
        documented_commands: documentedCommands,
        missing_from_matrix: missingFromMatrix,
        missing_from_package: missingFromPackage,
        missing_required_package: missingRequiredPackage,
        package_commands: packageCommands,
        required_commands: REQUIRED_MATRIX_COMMANDS,
        status: 'BID_SMOKE_COMMAND_MATRIX_TEST_FAIL',
      },
      null,
      2,
    ),
  );
}

console.log(
  JSON.stringify(
    {
      documented_commands: documentedCommands,
      package_commands: packageCommands,
      required_commands: REQUIRED_MATRIX_COMMANDS,
      status: 'BID_SMOKE_COMMAND_MATRIX_TEST_PASS',
    },
    null,
    2,
  ),
);
