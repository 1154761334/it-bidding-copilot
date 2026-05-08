import { type ChildProcess, spawn } from 'node:child_process';
import net from 'node:net';
import path from 'node:path';

const FRONTEND_DIR = process.cwd();
const REPO_ROOT = path.resolve(FRONTEND_DIR, '..');
const BACKEND_DIR = process.env.BID_BACKEND_DIR ?? path.join(REPO_ROOT, 'backend');

const BACKEND_HOST = process.env.BID_BACKEND_HOST ?? '127.0.0.1';
const BACKEND_PORT = Number(process.env.BID_BACKEND_PORT ?? 8000);
const FRONTEND_HOST = process.env.BID_FRONTEND_HOST ?? '127.0.0.1';
const FRONTEND_PORT = Number(process.env.BID_FRONTEND_PORT ?? 9876);
const READY_TIMEOUT_MS = Number(process.env.BID_ACCEPTANCE_READY_TIMEOUT_MS ?? 180_000);
const PREFLIGHT_ONLY = process.env.BID_ACCEPTANCE_PREFLIGHT_ONLY === '1';
const VERBOSE = process.env.BID_ACCEPTANCE_VERBOSE === '1';

const PNPM_COMMAND = process.platform === 'win32' ? 'pnpm.cmd' : 'pnpm';
const UVICORN_COMMAND =
  process.platform === 'win32'
    ? path.join(BACKEND_DIR, 'venv', 'Scripts', 'uvicorn.exe')
    : path.join(BACKEND_DIR, 'venv', 'bin', 'uvicorn');

const backendBaseUrl = `http://${BACKEND_HOST}:${BACKEND_PORT}`;
const frontendBaseUrl = `http://${FRONTEND_HOST}:${FRONTEND_PORT}`;

interface ManagedProcess {
  child: ChildProcess;
  exited: boolean;
  name: string;
  tail: string[];
}

interface HealthResponse {
  evidence_count?: number;
  status?: string;
}

function wait(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function isPortOpen(host: string, port: number) {
  return new Promise<boolean>((resolve) => {
    const socket = net.createConnection({ host, port });
    const done = (open: boolean) => {
      socket.removeAllListeners();
      socket.destroy();
      resolve(open);
    };

    socket.once('connect', () => done(true));
    socket.once('error', () => done(false));
    socket.setTimeout(1_000, () => done(false));
  });
}

async function assertPortFree(label: string, host: string, port: number) {
  if (!(await isPortOpen(host, port))) return;
  throw new Error(`${label} port is already in use at ${host}:${port}.`);
}

function tailOutput(processInfo: ManagedProcess, chunk: Buffer) {
  const text = chunk.toString();
  processInfo.tail.push(text);
  processInfo.tail = processInfo.tail.slice(-20);

  if (VERBOSE) {
    process.stdout.write(`[${processInfo.name}] ${text}`);
  }
}

function spawnManaged(
  name: string,
  command: string,
  args: string[],
  cwd: string,
  env = process.env,
) {
  const child = spawn(command, args, {
    cwd,
    detached: process.platform !== 'win32',
    env,
    shell: process.platform === 'win32',
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  const processInfo: ManagedProcess = { child, exited: false, name, tail: [] };

  child.stdout.on('data', (chunk: Buffer) => tailOutput(processInfo, chunk));
  child.stderr.on('data', (chunk: Buffer) => tailOutput(processInfo, chunk));
  child.once('exit', () => {
    processInfo.exited = true;
  });

  return processInfo;
}

function formatProcessTail(processInfo: ManagedProcess) {
  return processInfo.tail.join('').trim();
}

async function assertProcessRunning(processInfo: ManagedProcess) {
  if (!processInfo.exited) return;
  throw new Error(
    `${processInfo.name} exited before it became ready.\n${formatProcessTail(processInfo)}`,
  );
}

async function waitForJsonHealth(backendProcess: ManagedProcess) {
  const startedAt = Date.now();

  while (Date.now() - startedAt < READY_TIMEOUT_MS) {
    await assertProcessRunning(backendProcess);

    try {
      const response = await fetch(`${backendBaseUrl}/health`, {
        signal: AbortSignal.timeout(1_500),
      });
      if (response.ok) {
        const health = (await response.json()) as HealthResponse;
        if (health.status === 'ok' && health.evidence_count && health.evidence_count > 0) return;
      }
    } catch {
      // Retry until the backend startup deadline expires.
    }

    await wait(500);
  }

  throw new Error(`Bidding API was not ready within ${READY_TIMEOUT_MS}ms at ${backendBaseUrl}.`);
}

async function waitForFrontend(viteProcess: ManagedProcess) {
  const startedAt = Date.now();

  while (Date.now() - startedAt < READY_TIMEOUT_MS) {
    await assertProcessRunning(viteProcess);

    try {
      const response = await fetch(`${frontendBaseUrl}/bid`, {
        signal: AbortSignal.timeout(2_000),
      });
      if (response.status < 500) return;
    } catch {
      // Retry until Vite responds.
    }

    await wait(500);
  }

  throw new Error(
    `Vite /bid route was not ready within ${READY_TIMEOUT_MS}ms at ${frontendBaseUrl}.`,
  );
}

function waitForExit(child: ChildProcess) {
  return new Promise<{ code: number | null; signal: NodeJS.Signals | null }>((resolve) => {
    child.once('exit', (code, signal) => resolve({ code, signal }));
  });
}

async function terminateProcess(processInfo?: ManagedProcess) {
  if (!processInfo || processInfo.exited) return;

  const { child } = processInfo;
  const exitPromise = waitForExit(child);

  if (process.platform === 'win32') {
    child.kill('SIGTERM');
  } else if (child.pid) {
    process.kill(-child.pid, 'SIGTERM');
  }

  const result = await Promise.race([exitPromise, wait(5_000).then(() => undefined)]);
  if (result) return;

  if (process.platform === 'win32') {
    child.kill('SIGKILL');
  } else if (child.pid) {
    process.kill(-child.pid, 'SIGKILL');
  }
}

async function runAcceptance() {
  const child = spawn(PNPM_COMMAND, ['run', 'acceptance:bid-smoke'], {
    cwd: FRONTEND_DIR,
    env: {
      ...process.env,
      BID_FRONTEND_BASE_URL: frontendBaseUrl,
      BID_ROUTE_PATH: '/bid',
      NEXT_PUBLIC_BIDDING_API_BASE_URL: backendBaseUrl,
    },
    shell: process.platform === 'win32',
    stdio: 'inherit',
  });
  const { code, signal } = await waitForExit(child);

  if (code === 0) return;
  throw new Error(
    `acceptance:bid-smoke failed with code ${code ?? 'null'} signal ${signal ?? 'null'}.`,
  );
}

async function main() {
  await assertPortFree('Bidding API', BACKEND_HOST, BACKEND_PORT);
  await assertPortFree('Vite', FRONTEND_HOST, FRONTEND_PORT);

  if (PREFLIGHT_ONLY) {
    console.log(
      JSON.stringify(
        {
          backend_url: backendBaseUrl,
          frontend_url: frontendBaseUrl,
          status: 'BID_SMOKE_ACCEPTANCE_PREFLIGHT_PASS',
        },
        null,
        2,
      ),
    );
    return;
  }

  let backendProcess: ManagedProcess | undefined;
  let viteProcess: ManagedProcess | undefined;

  try {
    backendProcess = spawnManaged(
      'bidding-api',
      UVICORN_COMMAND,
      ['src.main:app', '--host', BACKEND_HOST, '--port', String(BACKEND_PORT)],
      BACKEND_DIR,
    );
    await waitForJsonHealth(backendProcess);

    viteProcess = spawnManaged(
      'vite',
      PNPM_COMMAND,
      ['dev:spa', '--host', FRONTEND_HOST],
      FRONTEND_DIR,
      {
        ...process.env,
        NEXT_PUBLIC_BIDDING_API_BASE_URL: backendBaseUrl,
      },
    );
    await waitForFrontend(viteProcess);

    await runAcceptance();

    console.log(
      JSON.stringify(
        {
          backend_url: backendBaseUrl,
          frontend_url: frontendBaseUrl,
          status: 'BID_SMOKE_ACCEPTANCE_LOCAL_PASS',
        },
        null,
        2,
      ),
    );
  } finally {
    await terminateProcess(viteProcess);
    await terminateProcess(backendProcess);
  }
}

void main().catch((error) => {
  console.error(error);
  process.exit(1);
});
