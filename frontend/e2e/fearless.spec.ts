import { test, expect } from '@playwright/test';

// Parent BS-001: only browser entry; no API seeding or mocked responses.
test('starting Game 2 shows Game 1 picks locked for both Teams', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('textbox', { name: 'Team A name', exact: true }).fill('Northwind');
  await page.getByRole('textbox', { name: 'Team B name', exact: true }).fill('Tidebreak');
  await page.getByRole('button', { name: 'Create Series' }).click();
  await page.getByLabel('Side for Northwind').selectOption('red');
  await page.getByLabel('First-pick Team').selectOption('A');
  await page.getByRole('button', { name: 'Start Game 1' }).click();
  await expect(page.getByTestId('next-turn')).toContainText('Northwind');
  const characters = ['Ahri', 'Akali', 'Alistar', 'Amumu', 'Anivia', 'Annie',
    'Orianna', 'Ashe', 'Azir', 'Bard', 'Braum', 'Caitlyn', 'Camille', 'Cassiopeia',
    'Darius', 'Diana', 'Draven', 'Ekko', 'Elise', 'Evelynn'];
  for (const [index, character] of characters.entries()) {
    await page.getByLabel('Character to record').selectOption(character);
    await page.getByRole('button', { name: 'Record entry' }).click();
    await expect(page.getByTestId('draft-progress')).toHaveText(`${index + 1} / 20 turns`);
  }
  await page.getByLabel('First-pick Team').selectOption('B');
  await page.getByRole('button', { name: 'Start Game 2' }).click();
  for (const team of ['A', 'B']) {
    await expect(page.getByTestId(`locks-${team}`)).toContainText('Orianna');
  }
  await expect(page.getByTestId('timeline')).toContainText('Orianna');
  // BS-009, additionally exercised in the UI: locked options remain selectable
  // so an attempted pick receives the actual engine rejection and its reason.
  for (const [i, character] of ['Garen', 'Gragas', 'Gwen', 'Hecarim', 'Heimerdinger', 'Hwei'].entries()) {
    await page.getByLabel('Character to record').selectOption(character);
    await page.getByRole('button', { name: 'Record entry' }).click();
    await expect(page.getByTestId('draft-progress')).toHaveText(`${i + 1} / 20 turns`);
  }
  await page.getByLabel('Character to record').selectOption('Orianna');
  await page.getByRole('button', { name: 'Record entry' }).click();
  await expect(page.getByRole('alert')).toContainText('Fearless Lock');
  await expect(page.getByTestId('draft-progress')).toHaveText('6 / 20 turns');
  await page.screenshot({ path: '/tmp/nimbus-4-board.png', fullPage: true });
  await page.reload();
  await page.getByRole('button', { name: 'Northwind vs Tidebreak' }).click();
  await expect(page.getByTestId('locks-A')).toContainText('Orianna');
});
