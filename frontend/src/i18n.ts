// All interface copy is keyed here; profile and user-entered names are data.
const en = {
  brand: 'Nimbus', workspace: 'Draft workspace', subtitle: 'The next pick starts here.',
  local: 'Local workspace', newSeries: 'New Series', yourSeries: 'Your Series',
  noSeries: 'Create a Series to begin recording the draft.', titleProfile: 'Title profile',
  teamA: 'Team A name', teamB: 'Team B name', ourTeam: 'Our Team', neither: 'Neither Team',
  create: 'Create Series', hard: 'Hard Fearless', bestOf: 'Best-of-5',
  setupTitle: 'Set the stage', setupDescription: 'Name the Teams, then choose their Side and Draft Position for each Game.',
  format: 'Series format', variant: 'Fearless Variant', vs: '{a} vs {b}',
  startGame: 'Start Game {number}', game: 'Game {number}', sideFor: 'Side for {team}',
  firstPick: 'First-pick Team', first: 'First pick', second: 'Second pick',
  blue: 'Blue', red: 'Red', gameSetup: 'Next Game',
  gameSetupHint: 'Side and Draft Position are independent. Choose both before starting.',
  turn: 'Turn {number} · {team} · {kind}', ban: 'Ban', pick: 'Pick',
  progress: '{filled} / {total} turns', search: 'Find a Character',
  searchHint: 'Search names or aliases', character: 'Character to record', select: 'Choose a Character',
  record: 'Record entry', saving: 'Saving…', lockedOption: '{name} · Locked',
  liveEntry: 'Live entry', complete: 'Draft complete', draftCompleteHint: 'The next Game is ready to start.',
  drafting: 'Drafting', drafted: 'Drafted · Result pending',
  locks: 'Fearless Locks', noLocks: 'No locks from earlier Games.',
  lockHint: 'Picks from earlier Games are locked for both Teams.', available: '{count} available now',
  picks: 'Picks', bans: 'Bans', noActions: 'No entries yet.',
  timeline: 'Series timeline', timelineHint: 'Every entry, Game by Game.',
  missing: 'Player Assignments and winner pending',
  remaining: 'Complete the current draft to start the next Game.', allStarted: 'All five Games have been started.',
  loading: 'Loading your workspace…', retry: 'Try again', refresh: 'Refresh',
  network: 'Could not reach Nimbus. Check that the backend is running, then try again.',
  unexpected: 'The request could not be saved. Please try again.',
  fearless_lock: 'Fearless Lock: this Character was picked in an earlier Game.',
  draft_incomplete: 'Complete the current draft before starting the next Game.',
  series_full: 'All Games in this Best-of-5 Series have been started.',
  unknown_side: 'Choose a Side from the Title profile.',
  not_current_game: 'Enter Draft Actions in the current Game.',
  draft_complete: 'This draft is already complete.',
  unknown_character: 'Choose an active Character from the Character Catalog.',
  series_not_found: 'This Series could not be found.', profile_not_found: 'The Title profile could not be found.',
  formInvalid: 'Check the form values and try again.', active: 'Current Game',
} as const;
export type TranslationKey = keyof typeof en;
export function t(key: TranslationKey, values: Record<string, string | number> = {}): string {
  return Object.entries(values).reduce((text, [name, value]) => text.replaceAll(`{${name}}`, String(value)), en[key] as string);
}
export function errorText(code: string): string {
  return Object.hasOwn(en, code) ? t(code as TranslationKey) : t('unexpected');
}
