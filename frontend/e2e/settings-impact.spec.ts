import { test, expect } from '@playwright/test';

// BS-013 / US-005 / US-010: normal UI entry, impact before explicit save, cancel preserves.
test('previews Disabled List changes, cancels, then explicitly saves', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Team A name', { exact: true }).fill('Preview North');
  await page.getByLabel('Team B name', { exact: true }).fill('Preview South');
  await page.getByRole('button', { name: 'Create Series', exact: true }).click();
  await page.getByRole('button', { name: 'Start Game 1', exact: true }).click();
  await page.getByLabel('Character to record').selectOption('Ahri');
  await page.getByRole('button', { name: 'Record entry', exact: true }).click();
  await expect(page.getByTestId('draft-progress')).toHaveText('1 / 20 turns');
  const settings = page.getByRole('region', { name: 'Series rule settings', exact: true });
  await settings.getByRole('listbox', { name: 'Disabled Characters', exact: true }).selectOption(['Ahri']);
  await expect(settings.getByRole('button', { name: 'Save rule settings', exact: true })).toHaveCount(0);
  await settings.getByRole('button', { name: 'Preview changes', exact: true }).click();
  await expect(page.getByTestId('settings-impact')).toContainText('Violation created');
  await expect(page.getByTestId('settings-impact')).toContainText('Ahri');
  await settings.getByRole('button', { name: 'Cancel', exact: true }).click();
  await expect(page.getByTestId('settings-impact')).toHaveCount(0);
  await expect(settings.getByRole('listbox', { name: 'Disabled Characters', exact: true })).toHaveValues([]);
  await settings.getByRole('listbox', { name: 'Disabled Characters', exact: true }).selectOption(['Ahri']);
  await settings.getByRole('button', { name: 'Preview changes', exact: true }).click();
  await settings.getByRole('button', { name: 'Save rule settings', exact: true }).click();
  await expect(page.getByTestId('settings-impact')).toHaveCount(0);
  await expect(settings.getByRole('listbox', { name: 'Disabled Characters', exact: true })).toHaveValues(['Ahri']);
  await settings.getByRole('listbox', { name: 'Disabled Characters', exact: true }).selectOption([]);
  await settings.getByRole('button', { name: 'Preview changes', exact: true }).click();
  await expect(page.getByTestId('settings-impact')).toContainText('Violation cleared');
  await settings.getByRole('button', { name: 'Save rule settings', exact: true }).click();
  await expect(settings.getByRole('listbox', { name: 'Disabled Characters', exact: true })).toHaveValues([]);
  await page.reload();
  await page.getByRole('button', { name: 'Preview North vs Preview South', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Series rule settings', exact: true }).getByRole('listbox', { name: 'Disabled Characters', exact: true })).toHaveValues([]);
});
