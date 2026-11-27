import { test, expect } from '@playwright/test';

// US-001 / US-005: normal creation entry uses selected settings; no API fixtures.
test('creates a scrim with Custom Fearless and optional Patch', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Team A name', { exact: true }).fill('Visitors');
  await page.getByLabel('Team B name', { exact: true }).fill('Guests');
  await page.getByLabel('Series format', { exact: true }).selectOption('3');
  await page.getByLabel('Draft Order', { exact: true }).selectOption('lol-pro-2026');
  await page.getByLabel('Fearless Variant', { exact: true }).selectOption('custom');
  await page.getByLabel('Lock Reach', { exact: true }).selectOption('both_teams');
  await page.getByLabel('Lock Sources', { exact: true }).selectOption('picks_and_bans');
  await page.getByLabel('Record type', { exact: true }).selectOption('scrim');
  await page.getByLabel('Series Patch', { exact: true }).fill('26.23');
  await page.getByRole('button', { name: 'Create Series', exact: true }).click();
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Visitors vs Guests');
  await expect(page.getByTestId('series-settings')).toContainText('Fixed-length · 4');
  await expect(page.getByTestId('series-settings')).toContainText('Custom');
  await expect(page.getByTestId('series-settings')).toContainText('Scrim');
  await expect(page.getByTestId('series-settings')).toContainText('26.23');
  await page.getByLabel('Game Patch', { exact: true }).fill('26.24');
  await page.getByRole('button', { name: 'Start Game 1' }).click();
  await expect(page.getByTestId('game-patch')).toHaveText('26.24');
  await page.reload();
  await page.getByRole('button', { name: 'Visitors vs Guests', exact: true }).click();
  await expect(page.getByTestId('series-settings')).toContainText('Fixed-length · 4');
  await expect(page.getByTestId('game-patch')).toHaveText('26.24');
  await page.screenshot({ path: '/tmp/nimbus-9-board.png', fullPage: true });
});
