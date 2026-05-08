import { mkdirSync } from 'node:fs';
import path from 'node:path';

import { chromium, expect } from '@playwright/test';

const DEFAULT_FRONTEND_BASE_URL = 'http://127.0.0.1:3210';
const DEFAULT_BID_ROUTE = '/bid';
const DEFAULT_STORAGE_STATE_PATH = '.auth/bid-route-storage-state.json';
const DEFAULT_TIMEOUT_MS = 300_000;

const frontendBaseUrl = normalizeBaseUrl(
  process.env.BID_FRONTEND_BASE_URL ?? DEFAULT_FRONTEND_BASE_URL,
);
const bidRoute = process.env.BID_ROUTE_PATH ?? DEFAULT_BID_ROUTE;
const storageStatePath = process.env.BID_ROUTE_STORAGE_STATE ?? DEFAULT_STORAGE_STATE_PATH;
const timeout = Number(process.env.BID_ROUTE_CAPTURE_TIMEOUT_MS ?? DEFAULT_TIMEOUT_MS);
const headless = process.env.HEADLESS === 'true';

const SAFE_BOOTSTRAP_ENV_NAMES = [
  'APP_URL',
  'DATABASE_DRIVER',
  'DATABASE_URL',
  'AUTH_SECRET',
  'KEY_VAULTS_SECRET',
  'NEXT_PUBLIC_BIDDING_API_BASE_URL',
  'BID_FRONTEND_BASE_URL',
  'BID_ROUTE_PATH',
  'BID_ROUTE_STORAGE_STATE',
  'BID_ROUTE_CAPTURE_TIMEOUT_MS',
];

function normalizeBaseUrl(value: string) {
  return value.replace(/\/+$/, '');
}

function isAuthRoute(url: string) {
  const pathname = new URL(url).pathname;
  return pathname.endsWith('/signin') || pathname.endsWith('/signup') || pathname.includes('/signin/');
}

async function main() {
  const routeUrl = `${frontendBaseUrl}${bidRoute}`;
  const absoluteStorageStatePath = path.resolve(storageStatePath);
  const browser = await chromium.launch({ headless });
  const page = await browser.newPage();

  try {
    await page.goto(routeUrl, { timeout, waitUntil: 'domcontentloaded' });

    if (isAuthRoute(page.url())) {
      console.log(
        JSON.stringify(
          {
            current_path: new URL(page.url()).pathname,
            required_env_names: SAFE_BOOTSTRAP_ENV_NAMES,
            route: routeUrl,
            status: 'BID_ROUTE_LOGIN_REQUIRED',
            storage_state_path: storageStatePath,
          },
          null,
          2,
        ),
      );
    }

    await expect(page.getByText('Bidding Assistant')).toBeVisible({ timeout });

    if (isAuthRoute(page.url())) {
      throw new Error('Login did not complete before capture timeout.');
    }

    mkdirSync(path.dirname(absoluteStorageStatePath), { recursive: true });
    await page.context().storageState({ path: absoluteStorageStatePath });

    console.log(
      JSON.stringify(
        {
          route: routeUrl,
          status: 'BID_ROUTE_STORAGE_STATE_READY',
          storage_state_env: 'BID_ROUTE_STORAGE_STATE',
          storage_state_path: storageStatePath,
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
