import { defineConfig } from '@playwright/test';
import { cpSync, readFileSync, writeFileSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const data = mkdtempSync(join(tmpdir(), 'nimbus-browser-'));
const profiles = join(data, 'profiles');
cpSync('../profiles', profiles, { recursive: true });
cpSync('../tests/fixtures/profiles', profiles, { recursive: true });
const normal = readFileSync(join(profiles, 'league-of-legends.rules.yaml'), 'utf8');
writeFileSync(join(profiles, 'warning.rules.yaml'), normal
  .replace('id: league-of-legends', 'id: warning')
  .replace('name: League of Legends', 'name: Warning test profile')
  .replace('banning_locked: reject', 'banning_locked: warn'));
writeFileSync(join(profiles, 'selection.rules.yaml'), normal
  .replace('id: league-of-legends', 'id: selection-fixture')
  .replace('name: League of Legends', 'name: Coupled selection fixture')
  .replace('sides_coupled: false', 'sides_coupled: true\nfirst_pick_side: red')
  .replace('default_first_selection_holder: none', 'default_first_selection_holder: loser'));
export default defineConfig({
  testDir: './e2e', workers: 1, fullyParallel: false,
  use: { baseURL: 'http://127.0.0.1:5173', trace: 'retain-on-failure' },
  reporter: [['list']],
  webServer: [
    { command: `../.venv/bin/python -c 'import os; from pathlib import Path; import uvicorn; from nimbus.api import create_app; uvicorn.run(create_app(profile_dir=Path(os.environ["NIMBUS_TEST_PROFILES"])), host="127.0.0.1", port=8000)'`, url: 'http://127.0.0.1:8000/api/profiles',
      env: { NIMBUS_DATA_DIR: data, NIMBUS_TEST_PROFILES: profiles }, reuseExistingServer: false },
    { command: 'npm run dev -- --port 5173 --strictPort', url: 'http://127.0.0.1:5173',
      reuseExistingServer: false },
  ],
});
