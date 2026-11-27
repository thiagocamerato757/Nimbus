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
  // ADR-0034 (amended 2026-11-27): only the current Game can be voided.
  await expect(first.getByRole('button', {name: 'Void Game', exact: true})).toHaveCount(0);
  const second = page.getByTestId('timeline').locator('details').nth(1);
  await second.locator('summary').click();
  // #13 (Q11): a winner is recorded only for a Drafted or Closed Game.
  await expect(second.getByLabel('Winner', {exact: true})).toHaveCount(0);
  await second.getByRole('button', {name: 'Void Game', exact: true}).click();
  await expect(page.getByRole('heading', {name: 'Voided', exact: true})).toBeVisible();
  // ADR-0034 (amended 2026-11-27): after a void, the next Game is its Replay.
  await expect(page.getByRole('button', {name: 'Replay Game 2', exact: true})).toBeVisible();
  await expect(page.getByText('After a Voided Game, replay it: copy its draft or choose new draft.')).toBeVisible();
  await expect(page.getByRole('button', {name: /^Start Game/})).toHaveCount(0);
  await page.screenshot({path: '/tmp/nimbus-sequential/issue13-lifecycle.png', fullPage: true});
});

// Parent #13 (amended 2026-11-27): a Game sent back to Drafting keeps a stored
// winner that does not count; clearing a winner is allowed in any status.
test('clears the stored winner of a Game returned to Drafting', async ({ page, request }) => {
  async function post(path: string, data: unknown) {
    const listing = await request.get('/api/series');
    const response = await request.post(path, { headers: { 'X-Nimbus-App': '1', 'X-Nimbus-Version': listing.headers()['x-nimbus-version'] }, data });
    expect(response.ok(), await response.text()).toBeTruthy();
    return response.json();
  }
  let series = await post('/api/series', {profile_id: 'league-of-legends', team_a: 'Stored Owls', team_b: 'Stored Foxes'});
  series = await post(`/api/series/${series.id}/games`, {team_a_side: 'blue', first_pick_team: 'A'});
  const path = `/api/series/${series.id}/games/${series.games[0].id}`;
  const turns = series.rule_snapshot.draft_order.turns;
  const catalog = (await (await request.get('/api/profiles')).json()).find((p: {id: string}) => p.id === series.profile_id).catalog;
  for (let i = 0; i < turns.length; i++) {
    await post(path + '/actions', {character_id: turns[i].kind === 'pick' ? catalog[i].id : null});
  }
  await post(path + '/winner', {winner: 'A'});
  await post(path + `/actions/${turns.length - 1}/clear`, {});
  await page.goto('/');
  await page.getByRole('button', {name: 'Stored Owls vs Stored Foxes', exact: true}).click();
  await expect(page.getByTestId('series-score')).toContainText('Stored Owls 0');
  const game = page.getByTestId('timeline').locator('details').first();
  await game.locator('summary').click();
  await expect(game.getByLabel('Winner', {exact: true})).toHaveCount(0);
  await expect(game).toContainText('Stored winner Stored Owls does not count until the draft is complete.');
  await game.getByRole('button', {name: 'Clear stored winner', exact: true}).click();
  await expect(game.getByRole('button', {name: 'Clear stored winner', exact: true})).toHaveCount(0);
  const saved = await (await request.get(`/api/series/${series.id}`)).json();
  expect(saved.games[0].winner).toBeNull();
});

async function client(request: import('@playwright/test').APIRequestContext) {
  return async function post(path: string, data: unknown) {
    const listing = await request.get('/api/series');
    const response = await request.post(path, { headers: { 'X-Nimbus-App': '1', 'X-Nimbus-Version': listing.headers()['x-nimbus-version'] }, data });
    expect(response.ok(), await response.text()).toBeTruthy();
    return response.json();
  };
}

// Parent BS-011 "A Voided Game creates no Fearless Locks by default": Given a
// Game with recorded picks, When the analyst voids it, Then its picks lock nothing
// in later Games; its Replay's picks lock Game 2 (ADR-0034, amended 2026-11-27).
test('a voided Game locks nothing in later Games while its Replay does', async ({ page, request }) => {
  const post = await client(request);
  let series = await post('/api/series', {profile_id: 'league-of-legends', team_a: 'Void Owls', team_b: 'Void Foxes'});
  const turns = series.rule_snapshot.draft_order.turns;
  const catalog = (await (await request.get('/api/profiles')).json()).find((p: {id: string}) => p.id === series.profile_id).catalog;
  async function fill(gameId: string, offset: number) {
    let pick = offset;
    for (const turn of turns) {
      await post(`/api/series/${series.id}/games/${gameId}/actions`, {character_id: turn.kind === 'pick' ? catalog[pick++].id : null});
    }
  }
  series = await post(`/api/series/${series.id}/games`, {team_a_side: 'blue', first_pick_team: 'A'});
  await fill(series.games[0].id, 0);
  await page.goto('/');
  await page.getByRole('button', {name: 'Void Owls vs Void Foxes', exact: true}).click();
  const first = page.getByTestId('timeline').locator('details').first();
  await first.locator('summary').click();
  await first.getByRole('button', {name: 'Void Game', exact: true}).click();
  await page.getByRole('button', {name: 'Replay Game 1', exact: true}).click();
  const setup = page.getByRole('region', {name: 'Replay setup'});
  await setup.getByLabel('New draft', {exact: true}).check();
  await setup.getByRole('button', {name: 'Create Replay', exact: true}).click();
  await expect(page.getByTestId('locks-A')).toContainText('No locks from earlier Games.');
  const replay = (await (await request.get(`/api/series/${series.id}`)).json()).games[1];
  await fill(replay.id, 10);
  await page.getByRole('button', {name: 'Start Game 2', exact: true}).click();
  await page.getByRole('dialog').getByRole('button', {name: 'Later', exact: true}).click();
  await expect(page.getByTestId('draft-progress')).toHaveText('0 / 20 turns');
  const locks = page.getByTestId('locks-A');
  await expect(locks).toContainText(catalog[10].name);
  for (const voided of catalog.slice(0, 10)) await expect(locks.getByText(voided.name, {exact: true})).toHaveCount(0);
});

// Parent ADR-0034 (amended 2026-11-27): a Replay follows the same series_ended
// gate as an ordinary next Game; un-deciding the Series makes it available again.
test('a voided Game past the decision is replayed only while the Series is undecided', async ({ page, request }) => {
  const post = await client(request);
  let series = await post('/api/series', {profile_id: 'league-of-legends', team_a: 'Gate Owls', team_b: 'Gate Foxes',
    series_format: {kind: 'best_of', games: 3}, fearless: {lock_reach: 'none', lock_sources: 'picks'}});
  const turns = series.rule_snapshot.draft_order.turns;
  const catalog = (await (await request.get('/api/profiles')).json()).find((p: {id: string}) => p.id === series.profile_id).catalog;
  for (let game = 0; game < 2; game++) {
    series = await post(`/api/series/${series.id}/games`, {team_a_side: 'blue', first_pick_team: 'A'});
    for (let i = 0; i < turns.length; i++) {
      await post(`/api/series/${series.id}/games/${series.games[game].id}/actions`, {character_id: turns[i].kind === 'pick' ? catalog[i].id : null});
    }
  }
  series = await post(`/api/series/${series.id}/games`, {team_a_side: 'blue', first_pick_team: 'A'});
  await post(`/api/series/${series.id}/games/${series.games[0].id}/winner`, {winner: 'A'});
  await post(`/api/series/${series.id}/games/${series.games[1].id}/winner`, {winner: 'A'});
  await post(`/api/series/${series.id}/games/${series.games[2].id}/void`, {});
  await page.goto('/');
  await page.getByRole('button', {name: 'Gate Owls vs Gate Foxes', exact: true}).click();
  await expect(page.getByText('Series ended', {exact: true})).toBeVisible();
  await expect(page.getByRole('button', {name: 'Replay Game 3', exact: true})).toHaveCount(0);
  const second = page.getByTestId('timeline').locator('details').nth(1);
  await second.getByLabel('Winner', {exact: true}).selectOption('B');
  await second.getByRole('button', {name: 'Save winner', exact: true}).click();
  await expect(page.getByRole('button', {name: 'Replay Game 3', exact: true})).toBeVisible();
  await expect(page.getByText('After a Voided Game, replay it: copy its draft or choose new draft.')).toBeVisible();
});
