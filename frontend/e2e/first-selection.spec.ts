import { test, expect } from '@playwright/test';

// Parent BS-012 / US-002: optional metadata is visible, editable and independent
// of Side/Draft Position; actual results continue to determine turn ownership.
test('records optional First Selection and corrects it without changing turn ownership', async ({ page, request }) => {
  const current = await request.get('/api/series');
  const response = await request.post('/api/series', {
    headers: {'X-Nimbus-App': '1', 'X-Nimbus-Version': current.headers()['x-nimbus-version']},
    data: {profile_id: 'league-of-legends', team_a: 'Selection Owls', team_b: 'Selection Foxes'},
  });
  expect(response.ok()).toBeTruthy();
  await page.goto('/');
  await page.getByRole('button', {name: 'Selection Owls vs Selection Foxes', exact: true}).click();
  const setup = page.locator('.next-game');
  await expect(setup.getByLabel('First Selection holder')).toHaveValue('');
  await expect(setup.getByLabel('First Selection choice')).toHaveValue('');
  // #14 (amended 2026-11-27): a choice always belongs to a holder.
  await expect(setup.getByLabel('First Selection choice')).toBeDisabled();
  await setup.getByLabel('Side for Selection Owls').selectOption('blue');
  await setup.getByLabel('First-pick Team', {exact: true}).selectOption('B');
  await setup.getByLabel('First Selection holder').selectOption('A');
  await setup.getByLabel('First Selection choice').selectOption('side');
  await setup.getByRole('button', {name: 'Start Game 1', exact: true}).click();
  await expect(page.getByRole('heading', {name: 'Turn 1 · Selection Foxes · Ban'})).toBeVisible();
  const entry = page.getByTestId('timeline').locator('details').first();
  await entry.locator('summary').click();
  const selection = entry.getByRole('region', {name: 'First Selection for Game 1'});
  await expect(selection.getByLabel('First Selection holder')).toHaveValue('A');
  await expect(selection.getByLabel('First Selection choice')).toHaveValue('side');
  await selection.getByLabel('First Selection holder').selectOption('B');
  await selection.getByLabel('First Selection choice').selectOption('draft_position');
  await Promise.all([
    page.waitForResponse(response => response.url().endsWith('/first-selection') && response.request().method() === 'POST' && response.ok()),
    selection.getByRole('button', {name: 'Save First Selection'}).click(),
  ]);
  await page.reload();
  await page.getByRole('button', {name: 'Selection Owls vs Selection Foxes', exact: true}).click();
  await entry.locator('summary').click();
  await expect(selection.getByLabel('First Selection holder')).toHaveValue('B');
  await expect(selection.getByLabel('First Selection choice')).toHaveValue('draft_position');
  // #14 (amended 2026-11-27): a new holder with an untouched choice clears it,
  // because the stored choice belonged to the other Team.
  await selection.getByLabel('First Selection holder').selectOption('A');
  await expect(selection.getByLabel('First Selection choice')).toHaveValue('');
  await Promise.all([
    page.waitForResponse(response => response.url().endsWith('/first-selection') && response.request().method() === 'POST' && response.ok()),
    selection.getByRole('button', {name: 'Save First Selection'}).click(),
  ]);
  await expect(selection.getByLabel('First Selection holder')).toHaveValue('A');
  await expect(selection.getByLabel('First Selection choice')).toHaveValue('');
  // The form sends exactly what it shows: a new holder with the same choice as
  // the stored one is recorded in one save.
  await selection.getByLabel('First Selection choice').selectOption('side');
  await Promise.all([
    page.waitForResponse(response => response.url().endsWith('/first-selection') && response.request().method() === 'POST' && response.ok()),
    selection.getByRole('button', {name: 'Save First Selection'}).click(),
  ]);
  await expect(selection.getByLabel('First Selection choice')).toHaveValue('side');
  await selection.getByLabel('First Selection holder').selectOption('B');
  await selection.getByLabel('First Selection choice').selectOption('side');
  await Promise.all([
    page.waitForResponse(response => response.url().endsWith('/first-selection') && response.request().method() === 'POST' && response.ok()),
    selection.getByRole('button', {name: 'Save First Selection'}).click(),
  ]);
  await expect(selection.getByLabel('First Selection holder')).toHaveValue('B');
  await expect(selection.getByLabel('First Selection choice')).toHaveValue('side');
  await selection.getByLabel('First Selection choice').selectOption('side');
  await selection.getByLabel('First Selection holder').selectOption('');
  await expect(selection.getByLabel('First Selection choice')).toBeDisabled();
  await expect(selection.getByLabel('First Selection choice')).toHaveValue('');
  await selection.getByRole('button', {name: 'Save First Selection'}).click();
  await expect(page.getByTestId('draft-progress')).toHaveText('0 / 20 turns');
  await expect(page.getByRole('heading', {name: 'Turn 1 · Selection Foxes · Ban'})).toBeVisible();
});

// Parent BS-012 pending result + coupled profile: visible editable prefill and
// explicit coupled mapping are shown before the next draft, without guessing.
test('shows pending/known-result holder prefill and explicit coupled Draft Position', async ({ page, request }) => {
  async function post(path: string, data: unknown) {
    const current = await request.get('/api/series');
    const response = await request.post(path, {headers: {
      'X-Nimbus-App': '1', 'X-Nimbus-Version': current.headers()['x-nimbus-version'],
    }, data});
    expect(response.ok(), await response.text()).toBeTruthy();
    return response.json();
  }
  let series = await post('/api/series', {profile_id: 'selection-fixture', team_a: 'Coupled Owls', team_b: 'Coupled Foxes'});
  series = await post(`/api/series/${series.id}/games`, {team_a_side: 'blue', first_pick_team: 'B'});
  const path = `/api/series/${series.id}/games/${series.games[0].id}`;
  const profiles = await (await request.get('/api/profiles')).json();
  const profile = profiles.find((p: {id: string}) => p.id === 'selection-fixture');
  for (let i = 0; i < series.rule_snapshot.draft_order.turns.length; i++) {
    await post(path + '/actions', {character_id: profile.catalog[i].id});
  }
  await page.goto('/');
  await page.getByRole('button', {name: 'Coupled Owls vs Coupled Foxes', exact: true}).click();
  const setup = page.locator('.next-game');
  await expect(setup.getByLabel('First Selection holder')).toHaveValue('');
  await post(path + '/winner', {winner: 'A'});
  // #14 (amended 2026-11-27): the pre-fill is computed once when the form opens;
  // a later result is offered, never applied behind the analyst.
  await expect(setup.getByTestId('prefill-offer')).toContainText('the suggested holder would be Coupled Foxes. Apply?');
  await expect(setup.getByLabel('First Selection holder')).toHaveValue('');
  await setup.getByRole('button', {name: 'Apply', exact: true}).click();
  await expect(setup.getByLabel('First Selection holder')).toHaveValue('B');
  await expect(setup.getByTestId('prefill-offer')).toHaveCount(0);
  await expect(setup.getByLabel('First-pick Team', {exact: true})).toBeDisabled();
  await expect(setup.getByLabel('First-pick Team', {exact: true})).toHaveValue('B');
  await setup.getByLabel('Side for Coupled Owls').selectOption('red');
  await expect(setup.getByLabel('First-pick Team', {exact: true})).toHaveValue('A');
  await setup.getByLabel('First Selection holder').selectOption('A');
  await setup.getByRole('button', {name: 'Start Game 2', exact: true}).click();
  await expect(page.getByRole('heading', {name: 'Turn 1 · Coupled Owls · Ban'})).toBeVisible();
});

// Parent BS-012 / #14 (amended 2026-11-28): "Record winner and start" with a
// different pre-fill starts no draft and changes no field. The offer is shown,
// and the analyst Applies or presses Start again.
test('offers the new pre-fill after recording the winner before the draft begins', async ({ page, request }) => {
  async function post(path: string, data: unknown) {
    const current = await request.get('/api/series');
    const response = await request.post(path, {headers: {
      'X-Nimbus-App': '1', 'X-Nimbus-Version': current.headers()['x-nimbus-version'],
    }, data});
    expect(response.ok(), await response.text()).toBeTruthy();
    return response.json();
  }
  let series = await post('/api/series', {profile_id: 'selection-fixture', team_a: 'Prefill Owls', team_b: 'Prefill Foxes'});
  series = await post(`/api/series/${series.id}/games`, {team_a_side: 'blue', first_pick_team: 'B'});
  const path = `/api/series/${series.id}/games/${series.games[0].id}`;
  const profiles = await (await request.get('/api/profiles')).json();
  const profile = profiles.find((p: {id: string}) => p.id === 'selection-fixture');
  for (let i = 0; i < series.rule_snapshot.draft_order.turns.length; i++) {
    await post(path + '/actions', {character_id: profile.catalog[i].id});
  }
  await page.goto('/');
  await page.getByRole('button', {name: 'Prefill Owls vs Prefill Foxes', exact: true}).click();
  const setup = page.locator('.next-game');
  await expect(setup.getByLabel('First Selection holder')).toHaveValue('');
  await setup.getByRole('button', {name: 'Start Game 2', exact: true}).click();
  const prompt = page.getByRole('dialog', {name: 'Record the previous Game’s winner'});
  await prompt.getByLabel('Winner').selectOption('A');
  await prompt.getByRole('button', {name: 'Record winner and start', exact: true}).click();
  await expect(prompt).toHaveCount(0);
  await expect(page.getByTestId('prefill-notice')).toHaveText('The winner is recorded and the draft has not started. Apply the offer or press Start Game 2 again.');
  await expect(setup.getByTestId('prefill-offer')).toContainText('the suggested holder would be Prefill Foxes. Apply?');
  await expect(setup.getByLabel('First Selection holder')).toHaveValue('');
  const before = await (await request.get(`/api/series/${series.id}`)).json();
  expect(before.games).toHaveLength(1);
  expect(before.games[0].winner).toBe('A');
  await setup.getByRole('button', {name: 'Apply', exact: true}).click();
  await expect(setup.getByLabel('First Selection holder')).toHaveValue('B');
  await setup.getByRole('button', {name: 'Start Game 2', exact: true}).click();
  await expect(page.getByTestId('draft-progress')).toHaveText('0 / 20 turns');
  const after = await (await request.get(`/api/series/${series.id}`)).json();
  expect(after.games).toHaveLength(2);
  expect(after.games[1].first_selection_holder).toBe('B');
});

async function client(request: import('@playwright/test').APIRequestContext) {
  return async function post(path: string, data: unknown) {
    const current = await request.get('/api/series');
    const response = await request.post(path, {headers: {
      'X-Nimbus-App': '1', 'X-Nimbus-Version': current.headers()['x-nimbus-version'],
    }, data});
    expect(response.ok(), await response.text()).toBeTruthy();
    return response.json();
  };
}

async function draftedSeries(request: import('@playwright/test').APIRequestContext, teamA: string, teamB: string) {
  const post = await client(request);
  let series = await post('/api/series', {profile_id: 'selection-fixture', team_a: teamA, team_b: teamB});
  series = await post(`/api/series/${series.id}/games`, {team_a_side: 'blue', first_pick_team: 'B'});
  const path = `/api/series/${series.id}/games/${series.games[0].id}`;
  const profiles = await (await request.get('/api/profiles')).json();
  const profile = profiles.find((p: {id: string}) => p.id === 'selection-fixture');
  for (let i = 0; i < series.rule_snapshot.draft_order.turns.length; i++) {
    await post(path + '/actions', {character_id: profile.catalog[i].id});
  }
  await post(path + '/winner', {winner: 'A'});
  return {post, series, path, profile};
}

// Parent BS-012 / #14 (amended 2026-11-27): a winner correction while the setup
// form is open changes nothing on screen. The new pre-fill is offered; only
// applying it changes the holder and clears the choice.
test('a winner correction while the setup is open offers the new holder without changing fields', async ({ page, request }) => {
  const {post, series, path} = await draftedSeries(request, 'Offer Owls', 'Offer Foxes');
  await page.goto('/');
  await page.getByRole('button', {name: 'Offer Owls vs Offer Foxes', exact: true}).click();
  const setup = page.locator('.next-game');
  await expect(setup.getByLabel('First Selection holder')).toHaveValue('B');
  await setup.getByLabel('First Selection choice').selectOption('side');
  await post(path + '/winner', {winner: 'B'});
  await expect(setup.getByTestId('prefill-offer')).toContainText('With the current result, the suggested holder would be Offer Owls. Apply?');
  await expect(setup.getByLabel('First Selection holder')).toHaveValue('B');
  await expect(setup.getByLabel('First Selection choice')).toHaveValue('side');
  await setup.getByRole('button', {name: 'Apply', exact: true}).click();
  await expect(setup.getByLabel('First Selection holder')).toHaveValue('A');
  await expect(setup.getByLabel('First Selection choice')).toHaveValue('');
  await expect(setup.getByTestId('prefill-offer')).toHaveCount(0);
  // Ignoring a later offer changes nothing; Start records what is shown.
  await setup.getByLabel('First Selection choice').selectOption('draft_position');
  await post(path + '/winner', {winner: 'A'});
  await expect(setup.getByTestId('prefill-offer')).toContainText('Offer Foxes');
  await setup.getByRole('button', {name: 'Start Game 2', exact: true}).click();
  await expect(page.getByText('This edit is outdated. The latest state is shown. Review it and try again.')).toBeVisible();
  await expect(setup.getByLabel('First Selection holder')).toHaveValue('A');
  await expect(setup.getByLabel('First Selection choice')).toHaveValue('draft_position');
  await setup.getByRole('button', {name: 'Start Game 2', exact: true}).click();
  await expect(page.getByTestId('draft-progress')).toHaveText('0 / 20 turns');
  const saved = await (await request.get(`/api/series/${series.id}`)).json();
  expect(saved.games[1].first_selection_holder).toBe('A');
  expect(saved.games[1].first_selection_choice).toBe('draft_position');
});

// Same rule for the Replay setup: its pre-fill is taken when the setup opens.
test('a winner correction while the Replay setup is open offers the new holder', async ({ page, request }) => {
  const {post, series, path} = await draftedSeries(request, 'Redo Owls', 'Redo Foxes');
  const next = await post(`/api/series/${series.id}/games`, {team_a_side: 'blue', first_pick_team: 'B'});
  await post(`/api/series/${series.id}/games/${next.games[1].id}/void`, {});
  await page.goto('/');
  await page.getByRole('button', {name: 'Redo Owls vs Redo Foxes', exact: true}).click();
  await page.getByRole('button', {name: 'Replay Game 2', exact: true}).click();
  const setup = page.getByRole('region', {name: 'Replay setup'});
  await setup.getByLabel('New draft', {exact: true}).check();
  await expect(setup.getByLabel('First Selection holder')).toHaveValue('B');
  await setup.getByLabel('First Selection choice').selectOption('side');
  await post(path + '/winner', {winner: 'B'});
  await expect(setup.getByTestId('prefill-offer')).toContainText('the suggested holder would be Redo Owls. Apply?');
  await expect(setup.getByLabel('First Selection holder')).toHaveValue('B');
  await expect(setup.getByLabel('First Selection choice')).toHaveValue('side');
  await setup.getByRole('button', {name: 'Apply', exact: true}).click();
  await expect(setup.getByLabel('First Selection holder')).toHaveValue('A');
  await expect(setup.getByLabel('First Selection choice')).toHaveValue('');
  await expect(setup.getByTestId('replay-changes')).toContainText('Game 1: winner');
  await setup.getByRole('button', {name: 'Create Replay', exact: true}).click();
  await expect(page.getByTestId('timeline').locator('details')).toHaveCount(3);
  const saved = await (await request.get(`/api/series/${series.id}`)).json();
  expect(saved.games[2].first_selection_holder).toBe('A');
  expect(saved.games[2].first_selection_choice).toBeNull();
});

// Regression from the sixth PR #34 review: recording a different winner must not
// move the holder under a choice; pressing Start again records what is shown.
test('recording another winner never moves a choice to the other Team', async ({ page, request }) => {
  const {post, series, path} = await draftedSeries(request, 'Keep Owls', 'Keep Foxes');
  await page.goto('/');
  await page.getByRole('button', {name: 'Keep Owls vs Keep Foxes', exact: true}).click();
  const setup = page.locator('.next-game');
  await expect(setup.getByLabel('First Selection holder')).toHaveValue('B');
  await post(path + '/winner', {winner: null});
  await expect(setup.getByTestId('prefill-offer')).toContainText('there is no suggested holder');
  await setup.getByLabel('First Selection choice').selectOption('side');
  await setup.getByRole('button', {name: 'Start Game 2', exact: true}).click();
  const prompt = page.getByRole('dialog', {name: 'Record the previous Game’s winner'});
  await prompt.getByLabel('Winner').selectOption('B');
  await prompt.getByRole('button', {name: 'Record winner and start', exact: true}).click();
  await expect(setup.getByTestId('prefill-offer')).toContainText('Keep Owls');
  await expect(setup.getByLabel('First Selection holder')).toHaveValue('B');
  await expect(setup.getByLabel('First Selection choice')).toHaveValue('side');
  expect((await (await request.get(`/api/series/${series.id}`)).json()).games).toHaveLength(1);
  await setup.getByRole('button', {name: 'Start Game 2', exact: true}).click();
  await expect(page.getByTestId('draft-progress')).toHaveText('0 / 20 turns');
  const saved = await (await request.get(`/api/series/${series.id}`)).json();
  expect(saved.games[1].first_selection_holder).toBe('B');
  expect(saved.games[1].first_selection_choice).toBe('side');
});

// Regression from the sixth PR #34 review: an applied pre-fill is not a reason to
// start unseen; a later "Record winner and start" still stops and offers.
test('after Apply, a different recorded result still stops before the draft', async ({ page, request }) => {
  const {post, series, path} = await draftedSeries(request, 'Again Owls', 'Again Foxes');
  await page.goto('/');
  await page.getByRole('button', {name: 'Again Owls vs Again Foxes', exact: true}).click();
  const setup = page.locator('.next-game');
  await expect(setup.getByLabel('First Selection holder')).toHaveValue('B');
  await post(path + '/winner', {winner: 'B'});
  await setup.getByRole('button', {name: 'Apply', exact: true}).click();
  await expect(setup.getByLabel('First Selection holder')).toHaveValue('A');
  await post(path + '/winner', {winner: null});
  await expect(setup.getByTestId('prefill-offer')).toContainText('there is no suggested holder');
  await setup.getByRole('button', {name: 'Start Game 2', exact: true}).click();
  const prompt = page.getByRole('dialog', {name: 'Record the previous Game’s winner'});
  await prompt.getByLabel('Winner').selectOption('A');
  await prompt.getByRole('button', {name: 'Record winner and start', exact: true}).click();
  await expect(setup.getByTestId('prefill-offer')).toContainText('Again Foxes');
  await expect(setup.getByLabel('First Selection holder')).toHaveValue('A');
  expect((await (await request.get(`/api/series/${series.id}`)).json()).games).toHaveLength(1);
});

// docs/spec/mvp.md (amended 2026-11-28): "different" means different from the
// holder shown, even when the result gives the pre-fill the form opened with.
test('stops and offers when the recorded result differs from the holder shown', async ({ page, request }) => {
  const {post, series, path} = await draftedSeries(request, 'Shown Owls', 'Shown Foxes');
  await page.goto('/');
  await page.getByRole('button', {name: 'Shown Owls vs Shown Foxes', exact: true}).click();
  const setup = page.locator('.next-game');
  await expect(setup.getByLabel('First Selection holder')).toHaveValue('B');
  await post(path + '/winner', {winner: null});
  await expect(setup.getByTestId('prefill-offer')).toContainText('there is no suggested holder');
  await setup.getByLabel('First Selection holder').selectOption('A');
  await setup.getByRole('button', {name: 'Start Game 2', exact: true}).click();
  const prompt = page.getByRole('dialog', {name: 'Record the previous Game’s winner'});
  await prompt.getByLabel('Winner').selectOption('A');
  await prompt.getByRole('button', {name: 'Record winner and start', exact: true}).click();
  await expect(setup.getByTestId('prefill-offer')).toContainText('Shown Foxes');
  await expect(setup.getByLabel('First Selection holder')).toHaveValue('A');
  expect((await (await request.get(`/api/series/${series.id}`)).json()).games).toHaveLength(1);
  await setup.getByRole('button', {name: 'Start Game 2', exact: true}).click();
  await expect(page.getByTestId('draft-progress')).toHaveText('0 / 20 turns');
  const saved = await (await request.get(`/api/series/${series.id}`)).json();
  expect(saved.games[1].first_selection_holder).toBe('A');
});
