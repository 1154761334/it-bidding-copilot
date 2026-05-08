import { spawnSync } from 'node:child_process';
import net from 'node:net';

const TEST_NAME = 'testBidSmokeAcceptanceRunner';
const HOST = '127.0.0.1';
const PNPM_COMMAND = process.platform === 'win32' ? 'pnpm.cmd' : 'pnpm';

interface CommandResult {
  output: string;
  status: number | null;
}

function listen(host: string, port = 0) {
  return new Promise<net.Server>((resolve, reject) => {
    const server = net.createServer();
    server.once('error', reject);
    server.listen(port, host, () => {
      server.off('error', reject);
      resolve(server);
    });
  });
}

function close(server: net.Server) {
  return new Promise<void>((resolve, reject) => {
    server.close((error) => {
      if (error) reject(error);
      else resolve();
    });
  });
}

function serverPort(server: net.Server) {
  const address = server.address();
  if (!address || typeof address === 'string') {
    throw new Error('Expected TCP server address with a numeric port.');
  }
  return address.port;
}

async function reserveFreePort() {
  const server = await listen(HOST);
  const port = serverPort(server);
  await close(server);
  return port;
}

function runPreflight(backendPort: number, frontendPort: number): CommandResult {
  const result = spawnSync(
    PNPM_COMMAND,
    ['exec', 'tsx', 'scripts/bidding/runBidSmokeAcceptance.mts'],
    {
      cwd: process.cwd(),
      encoding: 'utf8',
      env: {
        ...process.env,
        BID_ACCEPTANCE_PREFLIGHT_ONLY: '1',
        BID_BACKEND_HOST: HOST,
        BID_BACKEND_PORT: String(backendPort),
        BID_FRONTEND_HOST: HOST,
        BID_FRONTEND_PORT: String(frontendPort),
      },
    },
  );

  return {
    output: `${result.stdout}\n${result.stderr}`,
    status: result.status,
  };
}

const freeBackendPort = await reserveFreePort();
const freeFrontendPort = await reserveFreePort();
const passResult = runPreflight(freeBackendPort, freeFrontendPort);

if (passResult.status !== 0) {
  throw new Error(`Expected preflight-only mode to pass on free ports.\n${passResult.output}`);
}
if (!passResult.output.includes('BID_SMOKE_ACCEPTANCE_PREFLIGHT_PASS')) {
  throw new Error('Expected preflight pass status was not emitted.');
}

const occupiedServer = await listen(HOST);
try {
  const occupiedBackendPort = serverPort(occupiedServer);
  const failureFrontendPort = await reserveFreePort();
  const failResult = runPreflight(occupiedBackendPort, failureFrontendPort);

  if (failResult.status === 0) {
    throw new Error('Expected preflight-only mode to fail when the backend port is occupied.');
  }
  if (!failResult.output.includes('Bidding API port is already in use')) {
    throw new Error('Expected occupied backend port diagnostic was not emitted.');
  }
  if (failResult.output.includes('BID_SMOKE_ACCEPTANCE_LOCAL_PASS')) {
    throw new Error('Local acceptance pass status should not be emitted during preflight failure.');
  }
  if (failResult.output.includes('BID_SMOKE_ACCEPTANCE_PREFLIGHT_PASS')) {
    throw new Error('Preflight pass status should not be emitted during preflight failure.');
  }

  console.log(
    JSON.stringify(
      {
        fixture: 'runtime-ports',
        status: 'BID_SMOKE_ACCEPTANCE_RUNNER_TEST_PASS',
        test: TEST_NAME,
      },
      null,
      2,
    ),
  );
} finally {
  await close(occupiedServer);
}
