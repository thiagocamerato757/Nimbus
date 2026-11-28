import { defineConfig } from 'vitest/config';

// Unit tests live beside the source; browser journeys in e2e/ belong to Playwright.
export default defineConfig({ test: { include: ['src/**/*.test.ts'] } });
