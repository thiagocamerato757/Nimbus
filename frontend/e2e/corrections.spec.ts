import { test, expect } from '@playwright/test';

// Parent BS-010: correction controls, edit history and acknowledgement reasons on screen.
test('analyst corrects an earlier Game, acknowledges its effect and clears latest action', async ({ page, request }) => {
  const write = async (path: string, body: unknown) => {
    const state = await request.get('/api/series');
    const result = await request.post(`/api${path}`, {
      headers: { 'X-Nimbus-App': '1', 'X-Nimbus-Version': state.headers()['x-nimbus-version'] }, data: body,
    });
    expect(result.ok()).toBeTruthy();
    return result.json();
  };
  let series = await write('/series', { profile_id: 'league-of-legends', team_a: 'Correction A', team_b: 'Correction B' });
  const base = `/series/${series.id}`;
  series = await write(`${base}/games`, { team_a_side: 'blue', first_pick_team: 'A' });
  const first = series.games[0].id;
  const picks = ['Ahri', 'Ashe', 'Azir', 'Bard', 'Braum', 'Caitlyn', 'Camille', 'Cassiopeia', 'Darius', 'Diana'];
  let index = 0;
  for (const turn of series.rule_snapshot.draft_order.turns) {
    await write(`${base}/games/${first}/actions`, { character_id: turn.kind === 'ban' ? null : picks[index++] });
  }
  series = await write(`${base}/games`, { team_a_side: 'blue', first_pick_team: 'A' });
  const second = series.games[1].id;
  for (let i = 0; i < 6; i++) await write(`${base}/games/${second}/actions`, { character_id: null });
  await write(`${base}/games/${second}/actions`, { character_id: 'Annie' });
  await page.goto('/');
  await page.getByRole('button', { name: 'Correction A vs Correction B' }).click();
  const firstGame = page.getByTestId('timeline').locator('details').first();
  await firstGame.getByRole('button', { name: 'Correct turn 7', exact: true }).click();
  await firstGame.getByLabel('Replacement Character').selectOption('Annie');
  await firstGame.getByRole('button', { name: 'Save correction', exact: true }).click();
  await expect(firstGame.getByTestId('edit-history')).toContainText('Ahri → Annie');
  await expect(page.getByTestId('rule-notices')).toContainText('Open Violation');
  await page.getByTestId('rule-notices').getByLabel('Acknowledgement reason').selectOption('official_ruling');
  await page.getByTestId('rule-notices').getByLabel('Acknowledgement note').fill('Stage referee confirmed');
  await page.getByTestId('rule-notices').getByRole('button', { name: 'Acknowledge Violation' }).click();
  await expect(page.getByTestId('rule-notices')).toContainText('Acknowledged Violation');
  await expect(page.getByTestId('rule-notices')).toContainText('Stage referee confirmed');
  await page.getByRole('button', { name: 'Clear latest Draft Action', exact: true }).click();
  await expect(page.getByTestId('next-turn')).toContainText('Turn 7');
  await expect(page.getByTestId('rule-notices')).not.toContainText('Violation');
  const secondGame = page.getByTestId('timeline').locator('details').nth(1);
  await secondGame.locator('summary').click();
  await expect(secondGame.getByTestId('edit-history')).toContainText('Annie → Cleared');
  await page.reload();
  await page.getByRole('button', { name: 'Correction A vs Correction B' }).click();
  await expect(page.getByTestId('timeline').locator('details').first().getByTestId('edit-history')).toContainText('Ahri → Annie');
});
