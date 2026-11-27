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

// Parent BS-010 confirmed extension: immediately connect the correction to the untouched duplicate.
test('saving an earlier correction immediately explains the later duplicate', async ({ page, request }) => {
  const write = async (path: string, body: unknown) => {
    const state = await request.get('/api/series');
    const result = await request.post(`/api${path}`, {
      headers: { 'X-Nimbus-App': '1', 'X-Nimbus-Version': state.headers()['x-nimbus-version'] }, data: body,
    });
    expect(result.ok()).toBeTruthy();
    return result.json();
  };
  let series = await write('/series', { profile_id: 'league-of-legends', team_a: 'Duplicate A', team_b: 'Duplicate B' });
  const base = `/series/${series.id}`;
  series = await write(`${base}/games`, { team_a_side: 'blue', first_pick_team: 'A' });
  const actions = `${base}/games/${series.games[0].id}/actions`;
  for (let i = 0; i < 6; i++) await write(actions, { character_id: null });
  for (const character of ['Ahri', 'Akali', 'Annie', 'Ashe']) {
    series = await write(actions, { character_id: character });
  }
  const untouched = series.games[0].actions.slice(7);
  await page.goto('/');
  await page.getByRole('button', { name: 'Duplicate A vs Duplicate B' }).click();
  const game = page.getByTestId('timeline').locator('details').first();
  await game.locator('summary').click();
  await game.getByRole('button', { name: 'Correct turn 7', exact: true }).click();
  await game.getByLabel('Replacement Character').selectOption('Ashe');
  await game.getByRole('button', { name: 'Save correction', exact: true }).click();
  await expect(page.getByTestId('correction-impact')).toHaveText('This correction makes turn 10 a duplicate');
  await expect(page.getByTestId('rule-notices')).toContainText('Turn 10');
  await expect(page.getByTestId('rule-notices')).not.toContainText('Turn 7');
  const saved = await (await request.get(`/api${base}`)).json();
  expect(saved.games[0].actions.slice(7)).toEqual(untouched);
});

// Parent BS-010: any newly affected action is explained, including multiple later Games.
for (const affectedKind of ['pick', 'ban'] as const) {
  test(`saving an earlier Game correction explains later ${affectedKind} impacts`, async ({ page, request }) => {
    const write = async (path: string, body: unknown) => {
      const state = await request.get('/api/series');
      const result = await request.post(`/api${path}`, {
        headers: { 'X-Nimbus-App': '1', 'X-Nimbus-Version': state.headers()['x-nimbus-version'] }, data: body,
      });
      expect(result.ok()).toBeTruthy();
      return result.json();
    };
    const name = `Impact ${affectedKind}`;
    let series = await write('/series', { profile_id: 'league-of-legends', team_a: name, team_b: 'Opponent' });
    const base = `/series/${series.id}`;
    const catalog = (await (await request.get('/api/profiles')).json()).find((p: { id: string }) => p.id === 'league-of-legends').catalog;
    const characters: string[] = catalog.filter((c: { id: string; retired: boolean }) => !c.retired && c.id !== 'Annie').map((c: { id: string }) => c.id);
    let offset = 0;
    const affectedGames = affectedKind === 'ban' ? 3 : 2;
    for (let number = 1; number <= affectedGames; number++) {
      series = await write(`${base}/games`, { team_a_side: 'blue', first_pick_team: 'A' });
      const actions = `${base}/games/${series.games.at(-1).id}/actions`;
      for (const [index, turn] of series.rule_snapshot.draft_order.turns.entries()) {
        const affected = number > 1 && index === (affectedKind === 'ban' ? 0 : 6);
        series = await write(actions, { character_id: affected ? 'Annie' : turn.kind === 'ban' ? null : characters[offset++] });
        if (number === affectedGames && affected) break;
      }
    }
    const untouched = series.games.slice(1).map((game: { actions: unknown; edit_history: unknown }) => ({ actions: game.actions, edit_history: game.edit_history }));
    await page.goto('/');
    await page.getByRole('button', { name: `${name} vs Opponent` }).click();
    const firstGame = page.getByTestId('timeline').locator('details').first();
    await firstGame.getByRole('button', { name: 'Correct turn 7', exact: true }).click();
    await firstGame.getByLabel('Replacement Character').selectOption('Annie');
    await firstGame.getByRole('button', { name: 'Save correction', exact: true }).click();
    const messages = page.getByTestId('correction-impact').locator('p');
    const expected = affectedKind === 'ban'
      ? ['This correction makes Game 2 turn 1 a wasted ban', 'This correction makes Game 3 turn 1 a wasted ban']
      : ['This correction makes Game 2 turn 7 break a Fearless Lock'];
    await expect(messages).toHaveText(expected);
    const saved = await (await request.get(`/api${base}`)).json();
    expect(saved.games.slice(1).map((game: { actions: unknown; edit_history: unknown }) => ({ actions: game.actions, edit_history: game.edit_history }))).toEqual(untouched);
    await page.getByRole('button', { name: 'New Series', exact: true }).click();
    await expect(page.getByTestId('correction-impact')).toHaveCount(0);
    await page.getByRole('button', { name: `${name} vs Opponent` }).click();
    await expect(page.getByTestId('correction-impact')).toHaveCount(0);
  });
}
