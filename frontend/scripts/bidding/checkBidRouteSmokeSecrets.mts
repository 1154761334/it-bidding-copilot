import { readFileSync } from 'node:fs';
import path from 'node:path';

const DEFAULT_TARGET_FILES = [
  'package.json',
  'scripts/bidding/bidSmokeAcceptanceManifest.json',
  'scripts/bidding/README.md',
  'scripts/bidding/captureBidRouteStorageState.mts',
  'scripts/bidding/runBidSmokeAcceptance.mts',
  'scripts/bidding/smokeBidRoute.mts',
  'scripts/bidding/testBidRouteProductionDocsDrift.mts',
  'scripts/bidding/testBidRouteProductionDocs.mts',
  'scripts/bidding/testBidRouteProductionDocsFailure.mts',
  'scripts/bidding/testBidSmokeAcceptanceManifestDrift.mts',
  'scripts/bidding/testBidSmokeAcceptanceManifest.mts',
  'scripts/bidding/testBidSmokeAcceptanceRunner.mts',
  'scripts/bidding/testBidSmokeCommandMatrix.mts',
  'scripts/bidding/testBidSmokePreflightOrder.mts',
  'scripts/bidding/testBidSmokePreflightSummaryFailure.mts',
  'scripts/bidding/testBidSmokePreflightSummary.mts',
];

interface CheckedLine {
  line: string;
  lineNumber: number;
}

interface Rule {
  name: string;
  pattern: RegExp;
}

interface Finding {
  excerpt: string;
  file: string;
  line: number;
  rule: string;
}

const longValue = String.raw`[\w.~+/-]{20,}`;
const assignmentPrefix = String.raw`(?:api[_-]?key|secret|token|password)\s*[:=]\s*['"]`;

const RULES: Rule[] = [
  {
    name: 'secret-like assignment',
    pattern: new RegExp(`${assignmentPrefix}[^'"\n]{12,}['"]`, 'i'),
  },
  {
    name: 'bearer credential literal',
    pattern: new RegExp(`Bearer\\s+${longValue}`, 'i'),
  },
  {
    name: 'service key literal',
    pattern: new RegExp('s' + 'k-' + String.raw`[\w-]{20,}`),
  },
  {
    name: 'jwt-like literal',
    pattern: /\beyJ[\w-]{10,}\.[\w-]{10,}\.[\w-]{10,}\b/,
  },
  {
    name: 'long hex literal',
    pattern: /\b[\da-f]{40,}\b/i,
  },
];

function redact(line: string) {
  return line
    .replaceAll(new RegExp(longValue, 'g'), '<redacted>')
    .replaceAll(/\b[\da-f]{20,}\b/gi, '<redacted>');
}

function readLines(file: string) {
  return readFileSync(path.resolve(file), 'utf8').split(/\r?\n/);
}

function targetFilesFromEnv() {
  const configuredTargets = process.env.BID_ROUTE_SMOKE_SECRET_CHECK_TARGETS;
  if (!configuredTargets) return DEFAULT_TARGET_FILES;

  return configuredTargets
    .split(path.delimiter)
    .map((file) => file.trim())
    .filter(Boolean);
}

function packageBidScriptLines(): CheckedLine[] {
  const file = 'package.json';
  const lines = readLines(file);
  const packageJson = JSON.parse(lines.join('\n')) as {
    scripts?: Record<string, string>;
  };

  return Object.entries(packageJson.scripts ?? {})
    .filter(([name]) => name.includes('bid') || name.includes('smoke'))
    .map(([name, value]) => ({
      line: `"${name}": "${value}"`,
      lineNumber: Math.max(1, lines.findIndex((line) => line.includes(`"${name}"`)) + 1),
    }));
}

function fileLines(file: string): CheckedLine[] {
  if (file === 'package.json') return packageBidScriptLines();

  return readLines(file).map((line, index) => ({
    line,
    lineNumber: index + 1,
  }));
}

function scanFile(file: string) {
  const findings: Finding[] = [];

  for (const { line, lineNumber } of fileLines(file)) {
    for (const rule of RULES) {
      if (!rule.pattern.test(line)) continue;
      findings.push({
        excerpt: redact(line.trim()),
        file,
        line: lineNumber,
        rule: rule.name,
      });
    }
  }

  return findings;
}

const TARGET_FILES = targetFilesFromEnv();
const findings = TARGET_FILES.flatMap(scanFile);

if (findings.length > 0) {
  console.error(
    JSON.stringify(
      {
        findings,
        status: 'BID_ROUTE_SMOKE_SECRET_CHECK_FAIL',
      },
      null,
      2,
    ),
  );
  process.exit(1);
}

console.log(
  JSON.stringify(
    {
      files: TARGET_FILES,
      status: 'BID_ROUTE_SMOKE_SECRET_CHECK_PASS',
    },
    null,
    2,
  ),
);
