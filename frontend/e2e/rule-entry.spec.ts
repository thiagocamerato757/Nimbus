import { test, expect } from '@playwright/test';

// Parent BS-009 / US-003 / US-006: reasons and notices are visible on the board.
test('skipped bans and overrides display reasons and profile advice', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Team A name', { exact: true }).fill('Rules A');
  await page.getByLabel('Team B name', { exact: true }).fill('Rules B');
  await page.getByRole('button', { name: 'Create Series' }).click();
  await page.getByRole('button', { name: 'Start Game 1' }).click();
  await page.getByRole('button', { name: 'Skip ban', exact: true }).click();
  await expect(page.locator('.team-grid')).toContainText('Skipped Ban');
  await page.getByLabel('Character to record').selectOption('Ahri');
  await page.getByRole('button', { name: 'Record entry' }).click();
  for (let i = 0; i < 2; i++) {
    await page.getByLabel('Character to record').selectOption('Ahri');
    await page.getByRole('button', { name: 'Record entry' }).click();
    await expect(page.getByRole('alert')).toContainText('already appears');
    await page.getByLabel('Override reason').selectOption('profile_mismatch');
    await page.getByLabel('Override note').fill('Tournament permits repeated bans');
    await page.getByRole('button', { name: 'Record with Override' }).click();
    await expect(page.getByTestId('draft-progress')).toHaveText(`${3 + i} / 20 turns`);
  }
  await expect(page.getByTestId('profile-update-hint')).toContainText('update the Title profile');
  await expect(page.getByTestId('rule-notices')).toContainText('Acknowledged Violation');
  await expect(page.getByTestId('rule-notices')).toContainText('Profile mismatch');
  await expect(page.getByTestId('rule-notices')).toContainText('Tournament permits repeated bans');
  await page.reload();
  await page.getByRole('button', { name: 'Rules A vs Rules B' }).click();
  await expect(page.getByTestId('profile-update-hint')).toBeVisible();
});

test('a warn rule shows a notice after accepting a locked ban', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Title profile').selectOption('warning');
  await page.getByLabel('Team A name', { exact: true }).fill('Warn A');
  await page.getByLabel('Team B name', { exact: true }).fill('Warn B');
  await page.getByRole('button', { name: 'Create Series' }).click();
  await page.getByRole('button', { name: 'Start Game 1' }).click();
  const picks = ['Orianna', 'Ashe', 'Azir', 'Bard', 'Braum', 'Caitlyn', 'Camille', 'Cassiopeia', 'Darius', 'Diana'];
  let picked = 0;
  for (let i = 0; i < 20; i++) {
    if (i < 6 || (i >= 12 && i < 16)) {
      await page.getByRole('button', { name: 'Skip ban', exact: true }).click();
    } else {
      await page.getByLabel('Character to record').selectOption(picks[picked++]);
      await page.getByRole('button', { name: 'Record entry' }).click();
    }
    await expect(page.getByTestId('draft-progress')).toHaveText(`${i + 1} / 20 turns`);
  }
  await page.getByRole('button', { name: 'Start Game 2' }).click();
  await page.getByLabel('Character to record').selectOption('Orianna');
  await page.getByRole('button', { name: 'Record entry' }).click();
  await expect(page.getByTestId('draft-progress')).toHaveText('1 / 20 turns');
  await expect(page.getByTestId('rule-notices')).toContainText('Wasted ban');
  await expect(page.getByTestId('rule-notices')).not.toContainText('Violation');
});
