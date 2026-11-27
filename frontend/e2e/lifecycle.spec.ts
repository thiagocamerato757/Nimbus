import { test, expect } from '@playwright/test';

// Parent: BS-011 / US-004 / US-009. HTTP sets up draft; screen-only labels,
// winner prompt, correction controls and void notices are exercised in browser.
test('continues with a pending result and corrects or voids through the timeline', async ({ page, request }) => {
  async function post(path: string, data: unknown) {
    const listing = await request.get('/api/series');
    const response = await request.post(path, { headers: { 'X-Nimbus-App': '1', 'X-Nimbus-Version': listing.headers()['x-nimbus-version'] }, data });
    expect(response.ok(), await response.text()).toBeTruthy();
    return response.json();
  }
  let series = await post('/api/series', {profile_id: 'league-of-legends', team_a: 'Lifecycle Owls', team_b: 'Lifecycle Foxes'});
  series = await post(`/api/series/${series.id}/games`, {team_a_side: 'blue', first_pick_team: 'A'});
  const profiles = await (await request.get('/api/profiles')).json();
  const catalog = profiles.find((p: {id: string}) => p.id === series.profile_id).catalog;
  for (let i = 0; i < series.rule_snapshot.draft_order.turns.length; i++) {
    series = await post(`/api/series/${series.id}/games/${series.games[0].id}/actions`, {
      character_id: series.rule_snapshot.draft_order.turns[i].kind === 'pick' ? catalog[i].id : null,
    });
  }
  await page.goto('/');
  await page.getByRole('button', {name: 'Lifecycle Owls vs Lifecycle Foxes', exact: true}).click();
  await page.getByRole('button', {name: 'Start Game 2', exact: true}).click();
  const prompt = page.getByRole('dialog', {name: 'Record the previous Game’s winner'});
  await expect(prompt).toBeVisible();
  await prompt.getByRole('button', {name: 'Later', exact: true}).click();
  const first = page.getByTestId('timeline').locator('details').first();
  await expect(first).toContainText('Result pending');
  await expect(first).toContainText('Player Assignments missing');
  await expect(first).toContainText('Locked Characters');
  await first.getByLabel('Winner', {exact: true}).selectOption('A');
  await first.getByRole('button', {name: 'Save winner', exact: true}).click();
  await expect(page.getByTestId('series-score')).toContainText('Lifecycle Owls 1');
  await first.getByLabel('Winner', {exact: true}).selectOption('B');
  await first.getByRole('button', {name: 'Save winner', exact: true}).click();
  await expect(page.getByTestId('series-score')).toContainText('Lifecycle Foxes 1');
  await first.getByRole('button', {name: 'Void Game', exact: true}).click();
  await expect(first.locator('summary')).toContainText('Voided');
  await expect(page.getByTestId('locks-A')).toContainText('No locks from earlier Games.');
  const second = page.getByTestId('timeline').locator('details').nth(1);
  await second.locator('summary').click();
  await second.getByRole('button', {name: 'Void Game', exact: true}).click();
  await expect(page.getByRole('heading', {name: 'Voided', exact: true})).toBeVisible();
  await expect(page.getByRole('button', {name: 'Start Game 3', exact: true})).toBeVisible();
  await page.screenshot({path: '/tmp/nimbus-sequential/issue13-lifecycle.png', fullPage: true});
});
