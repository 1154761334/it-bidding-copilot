import { existsSync } from 'node:fs';
import path from 'node:path';

import { type BrowserContextOptions, chromium, expect } from '@playwright/test';

const DEFAULT_FRONTEND_BASE_URL = 'http://127.0.0.1:9876';
const DEFAULT_BIDDING_API_BASE_URL = 'http://127.0.0.1:8000';
const DEFAULT_BID_ROUTE = '/bid';
const DEFAULT_TIMEOUT_MS = 180_000;

const frontendBaseUrl = normalizeBaseUrl(
  process.env.BID_FRONTEND_BASE_URL ?? DEFAULT_FRONTEND_BASE_URL,
);
const biddingApiBaseUrl = normalizeBaseUrl(
  process.env.NEXT_PUBLIC_BIDDING_API_BASE_URL ?? DEFAULT_BIDDING_API_BASE_URL,
);
const bidRoute = process.env.BID_ROUTE_PATH ?? DEFAULT_BID_ROUTE;
const timeout = Number(process.env.BID_ROUTE_SMOKE_TIMEOUT_MS ?? DEFAULT_TIMEOUT_MS);
const storageStatePath = process.env.BID_ROUTE_STORAGE_STATE;
const allowAuthRequired = process.env.BID_ROUTE_ALLOW_AUTH_REQUIRED === '1';

const AUTH_BOOTSTRAP_ENV_NAMES = [
  'APP_URL',
  'DATABASE_DRIVER',
  'DATABASE_URL',
  'AUTH_SECRET',
  'KEY_VAULTS_SECRET',
  'NEXT_PUBLIC_BIDDING_API_BASE_URL',
  'BID_FRONTEND_BASE_URL',
  'BID_ROUTE_PATH',
  'BID_ROUTE_STORAGE_STATE',
];

interface HealthResponse {
  evidence_count?: number;
  status?: string;
}

function normalizeBaseUrl(value: string) {
  return value.replace(/\/+$/, '');
}

function isAuthRoute(url: string) {
  const pathname = new URL(url).pathname;
  return (
    pathname.endsWith('/signin') || pathname.endsWith('/signup') || pathname.includes('/signin/')
  );
}

function contextOptions(): BrowserContextOptions {
  if (!storageStatePath) return {};

  const absoluteStorageStatePath = path.resolve(storageStatePath);
  if (!existsSync(absoluteStorageStatePath)) {
    throw new Error(`BID_ROUTE_STORAGE_STATE file does not exist: ${absoluteStorageStatePath}`);
  }

  return { storageState: absoluteStorageStatePath };
}

async function assertBiddingApiHealthy() {
  const response = await fetch(`${biddingApiBaseUrl}/health`);
  if (!response.ok) {
    throw new Error(`Bidding API health check failed: ${response.status}`);
  }

  const health = (await response.json()) as HealthResponse;
  if (health.status !== 'ok')
    throw new Error(`Bidding API status is ${health.status ?? 'unknown'}`);
  if (!health.evidence_count || health.evidence_count <= 0) {
    throw new Error('Bidding API has no evidence records');
  }

  return health;
}

async function main() {
  const health = await assertBiddingApiHealthy();
  const browser = await chromium.launch({ headless: process.env.HEADLESS !== 'false' });
  const page = await browser.newPage(contextOptions());
  const apiRequestFailures: string[] = [];
  const pageErrors: string[] = [];
  const routeUrl = `${frontendBaseUrl}${bidRoute}`;

  page.on('pageerror', (error) => pageErrors.push(error.message));
  page.on('requestfailed', (request) => {
    if (!request.url().startsWith(biddingApiBaseUrl)) return;
    apiRequestFailures.push(
      `${request.method()} ${request.url()} ${request.failure()?.errorText ?? 'failed'}`,
    );
  });

  try {
    await page.goto(routeUrl, {
      timeout,
      waitUntil: 'domcontentloaded',
    });

    if (isAuthRoute(page.url())) {
      const authPayload = {
        current_path: new URL(page.url()).pathname,
        required_env_names: AUTH_BOOTSTRAP_ENV_NAMES,
        route: routeUrl,
        status: 'BID_ROUTE_AUTH_REQUIRED',
        storage_state_env: 'BID_ROUTE_STORAGE_STATE',
      };

      if (allowAuthRequired) {
        console.log(JSON.stringify(authPayload, null, 2));
        return;
      }

      throw new Error(
        [
          `Bid route redirected to auth: ${authPayload.current_path}`,
          `Provide ${authPayload.storage_state_env} for an authenticated production-route smoke,`,
          `or set BID_ROUTE_ALLOW_AUTH_REQUIRED=1 to record the bootstrap diagnostic.`,
          `Required env var names: ${AUTH_BOOTSTRAP_ENV_NAMES.join(', ')}`,
        ].join('\n'),
      );
    }

    await expect(page.getByText('Bidding Assistant')).toBeVisible({ timeout });
    await expect(page.getByText('Select or create a project to begin')).toBeVisible({ timeout });

    const demoButton = page.getByRole('button', { name: 'Demo Real Case' });
    await expect(demoButton).toBeVisible({ timeout });
    await expect(demoButton).toBeEnabled({ timeout });
    await demoButton.dispatchEvent('click');

    await expect(page.getByText('Draft & Artifacts')).toBeVisible({ timeout });
    await expect(page.getByText('Artifact Material Packages')).toBeVisible({ timeout });

    const contractPackage = page.getByRole('button', { name: /合同履约材料/ }).first();
    await expect(contractPackage).toBeVisible({ timeout });
    await expect(contractPackage).toContainText('Rows');
    await expect(contractPackage).toContainText('Evidence');
    await expect(contractPackage).toContainText('Trace');
    await contractPackage.dispatchEvent('click');

    await expect(page.getByText('Selected Evidence')).toBeVisible({ timeout: 30_000 });
    await expect(page.getByText('Material group', { exact: true }).first()).toBeVisible();
    await expect(page.getByText('合同履约材料').first()).toBeVisible();

    if (apiRequestFailures.length > 0) {
      throw new Error(`Bidding API request failures:\n${apiRequestFailures.join('\n')}`);
    }
    if (pageErrors.length > 0) {
      throw new Error(`Page errors:\n${pageErrors.join('\n')}`);
    }

    console.log(
      JSON.stringify(
        {
          api_evidence_count: health.evidence_count,
          api_status: health.status,
          auth: storageStatePath ? 'storage_state' : 'not_required',
          route: routeUrl,
          status: 'BID_ROUTE_SMOKE_PASS',
        },
        null,
        2,
      ),
    );
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
