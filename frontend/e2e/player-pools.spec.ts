import { test, expect } from '@playwright/test';

// Parent: US-012 / BS-004 and #15's profile-label acceptance criterion.
// The coach sees both counts and the Characters through the app, for both profiles.
for (const fixture of [
  { profile: 'league-of-legends', label: 'Champion Pool', pool: ['Ahri', 'Akali', 'Orianna', 'Syndra'] },
  { profile: 'synthetic-deadlock', label: 'Hero Pool', pool: ['lantern', 'clockwork', 'cobblestone', 'nightjar'] },
]) {
  test(`shows Remaining and Available Now with ${fixture.label}`, async ({ page }) => {
    await page.goto('/');
    await page.getByLabel('Title profile').selectOption(fixture.profile);
    await page.getByLabel('Team A name', { exact: true }).fill(`Pool Owls ${fixture.profile}`);
    await page.getByLabel('Team B name', { exact: true }).fill('Pool Foxes');
    await page.getByLabel(/^Our Team/).selectOption('A');
    await page.getByRole('button', { name: 'Create Series', exact: true }).click();
    const roster = page.getByTestId('roster-A');
    await roster.getByLabel('New Player name').fill('Pool Mid');
    await roster.getByRole('button', { name: 'Create Player' }).click();
    const player = roster.getByTestId('roster-player');
    await player.getByLabel('Declared Pool').selectOption(fixture.pool);
    await player.getByRole('button', { name: 'Save Declared Pool' }).click();
    await page.getByRole('button', { name: 'Start Game 1' }).click();
    const game = page.getByTestId('game-players-current');
    await game.getByTestId('lineup-A').getByRole('checkbox').check();
    await game.getByTestId('lineup-A').getByRole('button', { name: 'Save Lineup' }).click();
    const pool = game.getByTestId('player-pool');
    await expect(pool).toContainText(fixture.label);
    await expect(pool).toContainText('4 Remaining');
    await expect(pool).toContainText('4 Available Now');
    await page.getByLabel(/^Character to record/).selectOption(fixture.pool[0]);
    await page.getByRole('button', { name: 'Record entry', exact: true }).click();
    for (let index = 1; index < 6; index++) {
      await page.getByRole('button', { name: 'Skip ban', exact: true }).click();
    }
    await page.getByLabel(/^Character to record/).selectOption(fixture.pool[1]);
    await page.getByRole('button', { name: 'Record entry', exact: true }).click();
    await expect(pool).toContainText('4 Remaining');
    await expect(pool).toContainText('2 Available Now');
    await expect(pool.getByTestId('available-now')).toContainText(fixture.profile === 'league-of-legends' ? 'Orianna' : 'Cobblestone');
    await page.reload();
    await page.getByRole('button', { name: `Pool Owls ${fixture.profile} vs Pool Foxes`, exact: true }).click();
    await expect(page.getByTestId('game-players-current').getByTestId('player-pool')).toContainText('2 Available Now');
  });
}
