import { test, expect } from '@playwright/test';

// Parent BS-026 and issue #6 live-update acceptance: real browser + API + SQLite.
test('two tabs refresh automatically and an outdated edit shows a rejection notice', async ({ page, context }) => {
  await page.goto('/');
  await page.getByLabel('Team A name', { exact: true }).fill('Local North');
  await page.getByLabel('Team B name', { exact: true }).fill('Local South');
  await page.getByRole('button', { name: 'Create Series', exact: true }).click();
  await page.getByRole('button', { name: 'Start Game 1', exact: true }).click();
  const other = await context.newPage();
  await other.goto('/');
  await other.getByRole('button', { name: 'Local North vs Local South', exact: true }).click();
  await expect(other.getByTestId('draft-progress')).toHaveText('0 / 20 turns');
  // The second tab has prepared an edit based on the old state.
  await other.getByLabel('Character to record').selectOption('Akali');
  await page.getByLabel('Character to record').selectOption('Ahri');
  await page.getByRole('button', { name: 'Record entry', exact: true }).click();
  // No reload or navigation: both screens must show the committed entry.
  await expect(other.getByTestId('draft-progress')).toHaveText('1 / 20 turns');
  await expect(other.getByTestId('timeline')).toContainText('Ahri');
  await other.getByRole('button', { name: 'Record entry', exact: true }).click();
  await expect(other.getByRole('alert')).toContainText('outdated');
  await expect(other.getByTestId('draft-progress')).toHaveText('1 / 20 turns');
  await expect(page.getByTestId('draft-progress')).toHaveText('1 / 20 turns');
  await other.screenshot({ path: '/tmp/nimbus-6-stale-notice.png', fullPage: true });
  // Deliberately select from the new state, then both tabs show the second entry.
  await other.getByLabel('Character to record').selectOption('Akali');
  await other.getByRole('button', { name: 'Record entry', exact: true }).click();
  await expect(page.getByTestId('draft-progress')).toHaveText('2 / 20 turns');
  await expect(page.getByTestId('timeline')).toContainText('Akali');
  await page.screenshot({ path: '/tmp/nimbus-6-two-tabs.png', fullPage: true });
});
