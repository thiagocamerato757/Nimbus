import { test, expect } from '@playwright/test';

// Parent BS-011 confirmed setup, copy, provenance, timeline and chain.
test('requires explicit draft choice and shows prefill, carried reasons and linked attempts', async ({ page, request }) => {
  async function post(path: string, data: unknown) {
    const current = await request.get('/api/series');
    const response = await request.post(path, {headers: {'X-Nimbus-App': '1', 'X-Nimbus-Version': current.headers()['x-nimbus-version']}, data});
    expect(response.ok(), await response.text()).toBeTruthy();
    return response.json();
  }
  let series = await post('/api/series', {profile_id: 'league-of-legends', team_a: 'Replay Owls', team_b: 'Replay Foxes', patch: '26.1'});
  const player = await post('/api/players', {name: 'Replay Player', current_team_id: series.teams[0].roster_id});
  series = await post(`/api/series/${series.id}/games`, {team_a_side: 'red', first_pick_team: 'A'});
  const base = `/api/series/${series.id}/games/${series.games[0].id}`;
  await post(base + '/lineups', {team_id: 'A', player_ids: [player.id]});
  await post(base + '/actions', {character_id: 'Ahri'});
  await post(base + '/actions', {character_id: 'Ahri', override: {category: 'official_ruling', note: 'Referee retained draft'}});
  await post(base + '/actions', {character_id: 'Akali'});
  await post(base + '/actions/2/correct', {character_id: 'Ahri'});
  await post(base + '/void', {});
  await page.goto('/');
  await page.getByRole('button', {name: 'Replay Owls vs Replay Foxes', exact: true}).click();
  await page.getByRole('button', {name: 'Replay Game 1', exact: true}).click();
  const setup = page.getByRole('region', {name: 'Replay setup'});
  await expect(setup.getByLabel('Replay Patch')).toHaveValue('26.1');
  await expect(setup.getByLabel('Replay Team A Side')).toHaveValue('red');
  await expect(setup.getByLabel('Replay First-pick Team')).toHaveValue('A');
  await expect(setup.getByLabel('Replay Owls Lineup')).toHaveValues([player.id]);
  await expect(setup.getByLabel('Copy the voided Game’s draft')).not.toBeChecked();
  await expect(setup.getByLabel('New draft', {exact: true})).not.toBeChecked();
  await expect(setup.getByRole('button', {name: 'Create Replay', exact: true})).toBeDisabled();
  await setup.getByLabel('Replay Patch').fill('26.2');
  await setup.getByLabel('Copy the voided Game’s draft').check();
  await expect(setup.getByTestId('replay-preview')).toContainText('carried from voided Game 1');
  await expect(setup.getByTestId('replay-preview')).toContainText('Referee retained draft');
  await expect(setup.getByTestId('replay-preview')).toContainText('Open Violation');
  await setup.getByRole('button', {name: 'Create Replay', exact: true}).click();
  const timeline = page.getByTestId('timeline');
  await expect(timeline.locator('details')).toHaveCount(2);
  await expect(timeline.locator('details').last().locator('summary')).toContainText('Replay of voided Game 1');
  await timeline.locator('details').last().locator('summary').click();
  await expect(timeline.locator('details').last().getByRole('link', {name: 'View voided source'})).toBeVisible();
  await expect(page.getByTestId('game-patch')).toHaveText('26.2');
  await timeline.locator('details').last().getByRole('button', {name: 'Void Game', exact: true}).click();
  await page.getByRole('button', {name: 'Replay Game 1', exact: true}).click();
  // ADR-0034 (amended 2026-11-27): Draft Positions are editable, but not with a copied draft.
  await setup.getByLabel('Copy the voided Game’s draft').check();
  await setup.getByLabel('Replay First-pick Team').selectOption('B');
  await expect(setup.getByTestId('copy-blocked')).toHaveText('Copying the draft requires the same Draft Positions; keep them or choose new draft.');
  await expect(setup.getByRole('button', {name: 'Create Replay', exact: true})).toBeDisabled();
  await expect(setup.getByTestId('replay-preview')).toHaveCount(0);
  await setup.getByLabel('New draft', {exact: true}).check();
  await expect(setup.getByTestId('copy-blocked')).toHaveCount(0);
  await setup.getByRole('button', {name: 'Create Replay', exact: true}).click();
  await expect(timeline.locator('details')).toHaveCount(3);
  await expect(page.getByTestId('draft-progress')).toHaveText('0 / 20 turns');
});

// Parent BS-026 / #13: another edit while the Replay setup is open makes the
// first try stale. The panel reloads, lists what changed and the next try saves.
test('a stale Replay setup reloads, shows what changed and saves on the next try', async ({ page, request }) => {
  async function post(path: string, data: unknown) {
    const current = await request.get('/api/series');
    const response = await request.post(path, {headers: {'X-Nimbus-App': '1', 'X-Nimbus-Version': current.headers()['x-nimbus-version']}, data});
    expect(response.ok(), await response.text()).toBeTruthy();
    return response.json();
  }
  let series = await post('/api/series', {profile_id: 'league-of-legends', team_a: 'Stale Owls', team_b: 'Stale Foxes'});
  series = await post(`/api/series/${series.id}/games`, {team_a_side: 'blue', first_pick_team: 'A'});
  const base = `/api/series/${series.id}/games/${series.games[0].id}`;
  await post(base + '/actions', {character_id: 'Ahri'});
  await post(base + '/void', {});
  await page.goto('/');
  await page.getByRole('button', {name: 'Stale Owls vs Stale Foxes', exact: true}).click();
  await page.getByRole('button', {name: 'Replay Game 1', exact: true}).click();
  const setup = page.getByRole('region', {name: 'Replay setup'});
  await setup.getByLabel('New draft', {exact: true}).check();
  await expect(setup.getByTestId('replay-preview')).toBeVisible();
  await post(base + '/first-selection', {first_selection_holder: 'B'});
  // Wait until the live refresh already shows the other edit: the list of
  // changes must still come from the setup's own baseline.
  await expect(page.locator(`#game-${series.games[0].id} select[name="first_selection_holder"]`)).toHaveValue('B');
  await setup.getByRole('button', {name: 'Create Replay', exact: true}).click();
  await expect(setup.getByTestId('replay-changes')).toContainText('Game 1: First Selection holder');
  await expect(setup.getByTestId('replay-changes')).toContainText('The Series changed while this Replay setup was open.');
  await setup.getByRole('button', {name: 'Create Replay', exact: true}).click();
  await expect(page.getByTestId('timeline').locator('details')).toHaveCount(2);
  await expect(page.getByTestId('draft-progress')).toHaveText('0 / 20 turns');
});
