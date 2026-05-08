import { spawnSync } from 'node:child_process';
import { randomBytes } from 'node:crypto';

const env = { ...process.env };

env.APP_URL ||= 'http://app.com';
env.DATABASE_DRIVER ||= 'node';
env.DATABASE_URL ||= 'postgres://postgres:password@localhost:5432/postgres';
env.KEY_VAULTS_SECRET ||= randomBytes(32).toString('base64');
env.AUTH_SECRET ||= randomBytes(32).toString('base64');

const result = spawnSync('pnpm', ['run', 'build:next:raw'], {
  env,
  stdio: 'inherit',
});

process.exit(result.status ?? 1);
