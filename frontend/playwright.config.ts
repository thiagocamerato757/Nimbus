import { defineConfig } from '@playwright/test';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const data = mkdtempSync(join(tmpdir(), 'nimbus-4-browser-'));
export default defineConfig({
  testDir: './e2e', workers: 1, fullyParallel: false,
  use: { baseURL: 'http://127.0.0.1:5173', trace: 'retain-on-failure' },
  reporter: [['list']],
  webServer: [
    { command: '../.venv/bin/python -m nimbus', url: 'http://127.0.0.1:8000/api/profiles',
      env: { NIMBUS_DATA_DIR: data }, reuseExistingServer: false },
    { command: 'npm run dev -- --port 5173 --strictPort', url: 'http://127.0.0.1:5173',
      reuseExistingServer: false },
  ],
});
