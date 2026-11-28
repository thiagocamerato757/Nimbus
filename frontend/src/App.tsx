import { useEffect, useState, type FormEvent } from 'react';
import { ApiError, request, requestSnapshot } from './api';
import { useLiveQuery } from './useLiveQuery';
import { errorText, t } from './i18n';
import { Rosters, GamePlayers } from './Players';
import { FirstSelectionFields, PrefillOffer, RecordedFirstSelection, useFirstSelectionForm } from './FirstSelection';
import { afterRecordedWinner, requestFields } from './firstSelectionForm';
import type { Player, RosterTeam, Game, Profile, Series, TeamId, Fearless } from './types';

export default function App() {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const workspace = useLiveQuery<Series[]>('/series');
  const people = useLiveQuery<Player[]>('/players');
  const teams = useLiveQuery<RosterTeam[]>('/teams');
  const players = people.snapshot?.data ?? [];
  const rosterTeams = teams.snapshot?.data ?? [];
  const [teamAId, setTeamAId] = useState('');
  const [teamBId, setTeamBId] = useState('');
  const seriesList = workspace.snapshot?.data ?? [];
  const version = workspace.snapshot?.version ?? '';
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const series = seriesList.find(item => item.id === selectedId) ?? null;
  const [editVersion, setEditVersion] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [backupNotice, setBackupNotice] = useState('');
  const [correctionImpact, setCorrectionImpact] = useState<string[]>([]);
  const [teamA, setTeamA] = useState('');
  const [teamB, setTeamB] = useState('');
  const [ourTeam, setOurTeam] = useState('');
  const [profileId, setProfileId] = useState('');
  const [draftOrder, setDraftOrder] = useState('');
  const [formatIndex, setFormatIndex] = useState('');
  const [variant, setVariant] = useState('');
  const [reach, setReach] = useState<Fearless['lock_reach']>('both_teams');
  const [sources, setSources] = useState<Fearless['lock_sources']>('picks');
  const [patch, setPatch] = useState('');
  const [gamePatch, setGamePatch] = useState('');
  const [recordType, setRecordType] = useState('official');
  const [side, setSide] = useState('');
  const [firstPick, setFirstPick] = useState<TeamId>('A');
  const [character, setCharacter] = useState('');
  const [search, setSearch] = useState('');
  const [rejectedRule, setRejectedRule] = useState('');
  const [overrideCategory, setOverrideCategory] = useState('official_ruling');
  const [overrideNote, setOverrideNote] = useState('');
  const [correction, setCorrection] = useState<{ game: string; turn: number; character: string } | null>(null);
  const [winnerPrompt, setWinnerPrompt] = useState(false);
  const [replay, setReplay] = useState<{ source: string; choice: '' | 'copy_draft' | 'new_draft'; side: string; first: TeamId; patch: string; lineups: Record<TeamId, string[]>; version: string; baseline: Series } | null>(null);
  const [replayPreview, setReplayPreview] = useState<Game | null>(null);
  const [replayChanges, setReplayChanges] = useState<string[]>([]);
  const [promptWinner, setPromptWinner] = useState<TeamId>('A');
  const profile = profiles.find(p => p.id === (series?.profile_id ?? profileId));
  const current = series?.games.at(-1);
  const nextTurn = current?.state.next_turn;
  const characterName = (id: string) => profile?.catalog.find(c => c.id === id)?.name ?? id;
  const teamName = (id: TeamId) => series?.teams.find(team => team.id === id)?.name ?? id;
  // The one "has a result" rule: a winner can be set only on a Drafted or Closed Game.
  const isDraftedOrClosed = (game: Game) => game.state.status === 'Drafted' || game.state.status === 'Closed';

  const creationProfile = profiles.find(p => p.id === profileId);
  const selectedFormat = (formatIndex === '' ? creationProfile?.default_series_format : creationProfile?.series_formats[Number(formatIndex)]);
  const chosenVariant = variant || creationProfile?.default_fearless || 'hard';
  const chosenFearless = chosenVariant === 'custom' ? { lock_reach: reach, lock_sources: sources }
    : creationProfile?.fearless_presets.find(p => p.id === chosenVariant);
  const invalidCombination = chosenFearless?.lock_reach === 'picking_team' && chosenFearless?.lock_sources === 'picks_and_bans';
  const displayFormat = series?.rule_snapshot.series_format;
  const seriesSides = series?.rule_snapshot.sides ?? profile?.sides ?? [];
  const setupFirst = series?.rule_snapshot.sides_coupled
    ? (side === series.rule_snapshot.first_pick_side ? 'A' : 'B') : firstPick;
  const nextNumber = Math.max(0, ...(series?.games ?? []).map(game => game.number)) + 1;
  // The server never applies a First Selection pre-fill: requests carry what is
  // shown. Both forms share one reducer, so only the analyst moves a holder.
  const [setupForm, dispatchSetup] = useFirstSelectionForm(
    series?.progress.can_start_next ? `${series.id}:${current?.id ?? ''}` : '', series?.next_first_selection_holder ?? '');
  const replaySource = series?.games.find(game => game.id === replay?.source);
  const [replayForm, dispatchReplay] = useFirstSelectionForm(replay?.source ?? '', replaySource?.first_selection_prefill ?? '');
  const copyBlocked = replay?.choice === 'copy_draft'
    && replay.first !== replaySource?.assignments.find(a => a.position === 'first')?.team_id;
  useEffect(() => { setSide(seriesSides[0] ?? ''); }, [series?.id]);

  async function load() {
    setLoading(true); setError('');
    try {
      const loadedProfiles = await request<Profile[]>('/profiles');
      setProfiles(loadedProfiles);
      setProfileId(loadedProfiles[0]?.id ?? ''); setSide(loadedProfiles[0]?.sides[0] ?? '');
    } catch (e) { setError(errorText(e instanceof ApiError ? e.code : 'unexpected')); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, []);

  useEffect(() => {
    setReplayPreview(null);
    if (!replay?.choice || !series || copyBlocked) return;
    let active = true;
    requestSnapshot<Game>(`/series/${series.id}/games/${replay.source}/replay-preview`, {
      draft_choice: replay.choice, team_a_side: replay.side, first_pick_team: replay.first,
      patch: replay.patch || null, lineups: replay.lineups,
      ...requestFields(replayForm),
    }, replay.version).then(result => { if (active) { setReplayPreview(result.data); setError(''); } })
      .catch(e => {
        if (!active) return;
        setError(errorText(e instanceof ApiError ? e.code : 'unexpected'));
        if (e instanceof ApiError && e.code === 'stale_version') void rebaseReplay();
      });
    return () => { active = false; };
  }, [replay, series?.id, replayForm.holder, replayForm.choice, copyBlocked]);

  // What another edit changed in the Series while a form was open.
  function describeChanges(before: Series, after: Series): string[] {
    const fields: [keyof Game, Parameters<typeof t>[0]][] = [
      ['winner', 'fieldWinner'], ['voided', 'fieldVoided'], ['actions', 'fieldActions'],
      ['lineups', 'fieldLineups'], ['player_assignments', 'fieldAssignments'],
      ['first_selection_holder', 'fieldHolder'], ['first_selection_choice', 'fieldChoice'], ['patch', 'fieldPatch'],
    ];
    return after.games.flatMap(game => {
      const old = before.games.find(g => g.id === game.id);
      if (!old) return [t('changeGameAdded', {number: game.number})];
      const changed = fields.filter(([key]) => JSON.stringify(old[key]) !== JSON.stringify(game[key]));
      return changed.length ? [t('changeGame', {number: game.number, fields: changed.map(([, label]) => t(label)).join(', ')})] : [];
    });
  }

  // A stale Replay setup reloads the current state, keeps the analyst's entries,
  // takes the latest version and lists what changed since the setup's baseline,
  // the Series as it was when the setup opened or last rebased. The live poll
  // may already show the change, so the screen's Series is not the baseline.
  async function rebaseReplay() {
    if (!replay) return;
    const before = replay.baseline;
    const latest = await workspace.refresh();
    const after = latest?.data.find(item => item.id === before.id);
    if (!latest || !after) return;
    setReplay(open => open && {...open, version: latest.version, baseline: after});
    setReplayChanges(describeChanges(before, after));
  }

  function setupReplay() {
    if (!current || !series) return;
    setReplayChanges([]);
    setReplay({source: current.id, choice: '', patch: current.patch ?? '', lineups: {...current.lineups},
      side: current.assignments.find(a => a.team_id === 'A')!.side,
      first: current.assignments.find(a => a.position === 'first')!.team_id, version, baseline: series});
  }

  async function save(path: string, body?: unknown, expectedVersion?: string, correctedAction?: { game: string; turn: number }, onStale?: () => Promise<void>) {
    setBusy(true); setError(''); setRejectedRule(''); setCorrectionImpact([]);
    try {
      const result = await requestSnapshot<Series>(path, body, expectedVersion ?? editVersion ?? version);
      const updated = result.data;
      if (correctedAction && series) {
        setCorrectionImpact(updated.games.flatMap(game => {
          const previous = series.games.find(g => g.id === game.id);
          return game.state.violations.filter(violation =>
            !(game.id === correctedAction.game && violation.turn_index === correctedAction.turn)
            && !previous?.state.violations.some(v => v.turn_index === violation.turn_index && v.rule === violation.rule)
          ).map(violation => {
            const action = game.id === correctedAction.game
              ? t('correctionTurn', { number: violation.turn_index + 1 })
              : t('correctionGameTurn', { game: game.number, number: violation.turn_index + 1 });
            if (violation.rule === 'duplicate_character') return t('correctionDuplicate', { action });
            if (violation.rule === 'fearless_lock') return t('correctionFearless', { action });
            if (violation.rule === 'wasted_ban') return t('correctionWastedBan', { action });
            return t('correctionViolation', { action, rule: errorText(violation.rule) });
          });
        }));
      }
      setCharacter(''); setSearch(''); setOverrideNote('');
      workspace.accept({ data: [updated, ...seriesList.filter(item => item.id !== updated.id)], version: result.version });
      setSelectedId(updated.id); setEditVersion(null); setCorrection(null);
      await Promise.all([workspace.refresh(), people.refresh(), teams.refresh()]);
      return result;
    } catch (e) {
      setError(errorText(e instanceof ApiError ? e.code : 'unexpected'));
      if (e instanceof ApiError && ['fearless_lock', 'wasted_ban', 'duplicate_character'].includes(e.code)) setRejectedRule(e.code);
      if (e instanceof ApiError && e.code === 'stale_version') {
        setCharacter(''); setEditVersion(null); setCorrection(null);
        await (onStale ? onStale() : workspace.refresh());
      }
    } finally { setBusy(false); }
  }
  async function savePlayer(path: string, body: unknown): Promise<boolean> {
    setBusy(true); setError('');
    try {
      const result = await requestSnapshot<Player>(path, body, editVersion ?? people.snapshot?.version ?? version);
      people.accept({ data: players.some(p => p.id === result.data.id)
        ? players.map(p => p.id === result.data.id ? result.data : p) : [...players, result.data], version: result.version });
      setEditVersion(null);
      await workspace.refresh();
      await people.refresh();
      return true;
    } catch (e) {
      setError(errorText(e instanceof ApiError ? e.code : 'unexpected'));
      if (e instanceof ApiError && e.code === 'stale_version') {
        setEditVersion(null); await workspace.refresh(); await people.refresh();
      }
      return false;
    } finally { setBusy(false); }
  }
  async function backup() {
    setBusy(true); setError(''); setBackupNotice('');
    try {
      const result = await requestSnapshot<{ name: string }>('/backups', {}, version);
      setBackupNotice(t('backupCreated', { name: result.data.name }));
      await workspace.refresh();
    } catch (e) {
      setError(errorText(e instanceof ApiError ? e.code : 'unexpected'));
      if (e instanceof ApiError && e.code === 'stale_version') await workspace.refresh();
    } finally { setBusy(false); }
  }
  function create(event: FormEvent) {
    event.preventDefault();
    void save('/series', { profile_id: profileId, team_a: teamA, team_b: teamB, team_a_id: teamAId || null, team_b_id: teamBId || null, our_team: ourTeam || null,
      draft_order_id: draftOrder || creationProfile?.default_draft_order, series_format: selectedFormat,
      fearless: chosenFearless, patch: patch || null, record_type: recordType });
  }
  function start(event: FormEvent) {
    event.preventDefault();
    if (current && !current.voided && current.winner === null) setWinnerPrompt(true);
    else void launchGame();
  }
  async function launchGame(winner?: TeamId) {
    if (!series) return;
    let expectedVersion = editVersion ?? version;
    if (winner && current) {
      const result = await save(`/series/${series.id}/games/${current.id}/winner`, { winner });
      if (!result) return;
      expectedVersion = result.version;
      if (!result.data.progress.can_start_next) { setWinnerPrompt(false); return; }
      const prefill = result.data.next_first_selection_holder ?? '';
      dispatchSetup({ type: 'recorded', prefill });
      if (!afterRecordedWinner(setupForm, prefill).startDraft) {
        setWinnerPrompt(false);
        return;
      }
    }
    const result = await save(`/series/${series.id}/games`, { team_a_side: side, first_pick_team: setupFirst, patch: gamePatch || series.patch,
      ...requestFields(setupForm) }, expectedVersion);
    if (result) setWinnerPrompt(false);
  }
  function record(event: FormEvent) {
    event.preventDefault();
    if (series && current) void save(`/series/${series.id}/games/${current.id}/actions`, { character_id: character });
  }
  function actionList(game: Game, teamId: TeamId, kind: 'ban' | 'pick') {
    const actions = game.actions.filter(action => action.team_id === teamId && action.kind === kind);
    return actions.length ? <ol className={`entries ${kind}`}>
      {actions.map(action => <li key={action.turn_index}>{action.character_id === null ? t('skippedBan') : characterName(action.character_id)}</li>)}
    </ol> : <p className="empty">{t('noActions')}</p>;
  }

  function violationList(game: Game, preview = false) {
    return game.state.violations.map(violation => <div key={`${violation.turn_index}-${violation.rule}`}>
      <p>{t(violation.status === 'acknowledged' ? 'acknowledgedViolation' : 'openViolation')} · {t('turn', { number: violation.turn_index + 1, team: teamName(game.actions.find(a => a.turn_index === violation.turn_index)!.team_id), kind: '' })} · {errorText(violation.rule)}
        {violation.carried_from?.map((source, index) => <span key={`${source.game_id}-${index}`}> · <a href={`#game-${source.game_id}`}>{t('carriedFrom', {number: source.game_number})}</a></span>)}
        {violation.reason && <> · {t(violation.reason.category)}{violation.reason.note && <> · {violation.reason.note}</>}</>}
      </p>
      {violation.status === 'open' && !preview && <form onChangeCapture={() => setEditVersion(previous => previous ?? version)} onSubmit={event => {
        event.preventDefault();
        const fields = new FormData(event.currentTarget);
        void save(`/series/${series!.id}/games/${game.id}/actions/${violation.turn_index}/acknowledge`, {
          rule: violation.rule, reason: { category: fields.get('category'), note: fields.get('note') || null },
        });
      }}>
        <label>{t('acknowledgementReason')}<select name="category" required onChange={event => {
          const note = event.currentTarget.form?.elements.namedItem('note') as HTMLInputElement | null;
          if (note) note.required = event.target.value === 'other';
        }}>
          {(['official_ruling', 'profile_mismatch', 'earlier_entry_wrong', 'other'] as const).map(category => <option key={category} value={category}>{t(category)}</option>)}
        </select></label>
        <label>{t('acknowledgementNote')}<input name="note" maxLength={2000} /></label>
        <button disabled={busy}>{t('acknowledgeViolation')}</button>
      </form>}
    </div>);
  }

  return <div className="app-shell">
    <aside className="sidebar">
      <a className="brand" href="/" aria-label={t('brand')}><span className="brand-mark" aria-hidden="true">N</span>{t('brand')}</a>
      <p className="sidebar-caption">{t('workspace')}</p>
      <button className="new-series" onClick={() => { setSelectedId(null); setReplay(null); setCorrectionImpact([]); setWinnerPrompt(false); setError(''); setEditVersion(null); setCharacter(''); setRejectedRule(''); }} disabled={busy}>{t('newSeries')}</button>
      <h2 className="eyebrow">{t('yourSeries')}</h2>
      <nav className="series-nav">
        {seriesList.map(item => <button key={item.id} className={series?.id === item.id ? 'selected' : ''}
          disabled={busy} onClick={() => { setSelectedId(item.id); setReplay(null); setCorrectionImpact([]); setWinnerPrompt(false); setEditVersion(null); setCharacter(''); setError(''); }}>
          {t('vs', { a: item.teams[0].name, b: item.teams[1].name })}
        </button>)}
        {!seriesList.length && <p className="muted">{t('noSeries')}</p>}
      </nav>
      <button disabled={busy || !version} onClick={() => void backup()}>{t('createBackup')}</button>
      {backupNotice && <p role="status" className="backup-notice">{backupNotice}</p>}
      <p className="local-label">{t('local')}</p>
    </aside>
    <main>
      <header className="page-header">
        <div><p className="eyebrow">{profile?.name ?? t('workspace')}</p>
          <h1>{series ? t('vs', { a: teamName('A'), b: teamName('B') }) : t('subtitle')}</h1>
        </div>
        {series && <div className="badges" data-testid="series-settings"><span>{displayFormat && `${t(displayFormat.kind)} · ${displayFormat.games}`}</span><span className="fearless-badge">{t(series.rule_snapshot.fearless.id)}</span><span>{t(series.record_type)}</span>{series.patch && <span>{series.patch}</span>}</div>}
      </header>
      {(error || workspace.error || people.error || teams.error) && <div role="alert" className="alert">{error || errorText(workspace.error || people.error || teams.error)}{!profiles.length && <button onClick={() => void load()}>{t('retry')}</button>}</div>}
      {!!correctionImpact.length && <div role="status" data-testid="correction-impact">{correctionImpact.map(message => <p key={message}>{message}</p>)}</div>}
      {loading || (!workspace.snapshot && !workspace.error) ? <p role="status">{t('loading')}</p> : !series ? <section className="setup panel">
        <div className="setup-intro"><div className="orbit" aria-hidden="true"><span>N</span></div>
          <h2>{t('setupTitle')}</h2><p>{t('setupDescription')}</p></div>
        <form onChangeCapture={() => setEditVersion(previous => previous ?? version)} onSubmit={create} className="series-form">
          <label>{t('titleProfile')}<select value={profileId} onChange={event => {
            setProfileId(event.target.value); setDraftOrder(''); setFormatIndex(''); setVariant(''); setSide(profiles.find(p => p.id === event.target.value)?.sides[0] ?? '');
          }}>{profiles.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
          <div className="form-pair"><label>{t('teamA')}<input disabled={!!teamAId} value={teamA} onChange={e => setTeamA(e.target.value)} required maxLength={100} /></label>
            <label>{t('teamB')}<input disabled={!!teamBId} value={teamB} onChange={e => setTeamB(e.target.value)} required maxLength={100} /></label></div>
          <div className="form-pair">{(['A', 'B'] as const).map(team => <label key={team}>{t(team === 'A' ? 'existingTeamA' : 'existingTeamB')}<select aria-label={t(team === 'A' ? 'existingTeamA' : 'existingTeamB')} value={team === 'A' ? teamAId : teamBId} onChange={e => {
            const name = rosterTeams.find(t => t.id === e.target.value)?.name ?? '';
            if (team === 'A') { setTeamAId(e.target.value); setTeamA(name); }
            else { setTeamBId(e.target.value); setTeamB(name); }
          }}><option value="">{t('newTeam')}</option>{rosterTeams.map(team => <option value={team.id} key={team.id}>{team.name} · {team.id.slice(-8)}</option>)}</select></label>)}</div>
          <label>{t('ourTeam')}<select aria-label={t('ourTeam')} value={ourTeam} onChange={e => setOurTeam(e.target.value)}>
            <option value="">{t('neither')}</option><option value="A">{teamA || t('teamA')}</option><option value="B">{teamB || t('teamB')}</option>
          </select></label>
          <label>{t('format')}<select aria-label={t('format')} value={formatIndex || String(creationProfile?.series_formats.findIndex(f => f.kind === creationProfile.default_series_format.kind && f.games === creationProfile.default_series_format.games))} onChange={e => setFormatIndex(e.target.value)}>
            {creationProfile?.series_formats.map((f, i) => <option key={i} value={i}>{t(f.kind)} · {f.games}</option>)}
          </select></label>
          <label>{t('draftOrder')}<select aria-label={t('draftOrder')} value={draftOrder || creationProfile?.default_draft_order} onChange={e => setDraftOrder(e.target.value)}>
            {creationProfile?.draft_orders.map(o => <option key={o.id} value={o.id}>{o.name}</option>)}
          </select></label>
          <label>{t('variant')}<select aria-label={t('variant')} value={chosenVariant} onChange={e => setVariant(e.target.value)}>
            {creationProfile?.fearless_presets.map(v => <option key={v.id} value={v.id}>{t(v.id)}</option>)}<option value="custom">{t('custom')}</option>
          </select></label>
          {chosenVariant === 'custom' && <>
            <label>{t('lockReach')}<select aria-label={t('lockReach')} value={reach} onChange={e => setReach(e.target.value as Fearless['lock_reach'])}>
              {(['none', 'picking_team', 'both_teams'] as const).map(v => <option key={v} value={v}>{t(v)}</option>)}
            </select></label>
            <label>{t('lockSources')}<select aria-label={t('lockSources')} value={sources} onChange={e => setSources(e.target.value as Fearless['lock_sources'])}>
              <option value="picks">{t('sourcesPicks')}</option><option value="picks_and_bans">{t('sourcesBans')}</option>
            </select></label>
            {invalidCombination && <p role="alert">{t('invalidCombination')}</p>}
          </>}
          <label>{t('recordType')}<select aria-label={t('recordType')} value={recordType} onChange={e => setRecordType(e.target.value)}><option value="official">{t('official')}</option><option value="scrim">{t('scrim')}</option></select></label>
          <label>{t('seriesPatch')}<input value={patch} onChange={e => setPatch(e.target.value)} maxLength={100} /></label>
          <button className="primary" disabled={busy || !profile || invalidCombination}>{busy ? t('saving') : t('create')}</button>
        </form>
      </section> : <>
        <p data-testid="series-score">{series.teams.map(team => `${team.name} ${series.progress.score[team.id]}`).join(' · ')}{series.progress.ended && <> · {t('seriesEnded')}</>}</p>
        {!!series.progress.games_past_decision.length && <p role="alert">{t('pastDecision', { number: series.progress.deciding_game! })}</p>}
        {current?.voided && !replay && !series.progress.ended && <button disabled={busy} onClick={setupReplay}>{t('replayGame', {number: current.number})}</button>}
        {replay && current?.id === replay.source && <section className="panel" role="region" aria-label={t('replaySetup')}>
          <h2>{t('replaySetup')}</h2>
          <form onSubmit={async event => {
            event.preventDefault(); if (!replay.choice || copyBlocked) return;
            const result = await save(`/series/${series.id}/games/${replay.source}/replay`, {
              draft_choice: replay.choice, team_a_side: replay.side, first_pick_team: replay.first,
              patch: replay.patch || null, lineups: replay.lineups,
              ...requestFields(replayForm),
            }, replay.version, undefined, rebaseReplay);
            if (result) { setReplay(null); setReplayChanges([]); }
          }}>
            <label>{t('replayPatch')}<input maxLength={100} value={replay.patch} onChange={e => setReplay({...replay, patch: e.target.value})} /></label>
            <label>{t('replaySide')}<select value={replay.side} onChange={e => setReplay({...replay, side: e.target.value, first: series.rule_snapshot.sides_coupled ? (e.target.value === series.rule_snapshot.first_pick_side ? 'A' : 'B') : replay.first})}>{seriesSides.map(side => <option key={side} value={side}>{side}</option>)}</select></label>
            <label>{t('replayFirst')}<select value={replay.first} disabled={series.rule_snapshot.sides_coupled} onChange={e => setReplay({...replay, first: e.target.value as TeamId})}>{series.teams.map(team => <option key={team.id} value={team.id}>{team.name}</option>)}</select></label>
            <FirstSelectionFields teams={series.teams} form={replayForm} dispatch={dispatchReplay} />
            <PrefillOffer teams={series.teams} form={replayForm} onApply={() => dispatchReplay({ type: 'apply' })} />
            {series.teams.map(team => <label key={team.id}>{t('replayLineup', {team: team.name})}<select multiple value={replay.lineups[team.id]} onChange={e => setReplay({...replay, lineups: {...replay.lineups, [team.id]: [...e.target.selectedOptions].map(option => option.value)}})}>
              {players.filter(player => player.current_team_id === team.roster_id || current.lineups[team.id].includes(player.id)).map(player => <option key={player.id} value={player.id}>{player.name}</option>)}
            </select></label>)}
            <fieldset><legend>{t('replayChoice')}</legend>
              <label><input type="radio" name="replay-choice" checked={replay.choice === 'copy_draft'} onChange={() => setReplay({...replay, choice: 'copy_draft'})} />{t('copyDraft')}</label>
              <label><input type="radio" name="replay-choice" checked={replay.choice === 'new_draft'} onChange={() => setReplay({...replay, choice: 'new_draft'})} />{t('newDraft')}</label>
            </fieldset>
            {!!replayChanges.length && <div role="status" data-testid="replay-changes"><p>{t('replayRebased')}</p>
              <ul>{replayChanges.map(change => <li key={change}>{change}</li>)}</ul></div>}
            {copyBlocked && <p role="alert" data-testid="copy-blocked">{t('copy_requires_same_draft_positions')}</p>}
            <button disabled={busy || !replay.choice || copyBlocked}>{t('createReplay')}</button>
            <button type="button" onClick={() => { setReplay(null); setReplayChanges([]); }}>{t('cancelReplay')}</button>
          </form>
          {replayPreview && <div data-testid="replay-preview"><h3>{t('replayPreview')}</h3>{series.teams.map(team => <div key={team.id}>{actionList(replayPreview, team.id, 'pick')}{actionList(replayPreview, team.id, 'ban')}</div>)}{violationList(replayPreview, true)}</div>}
        </section>}
        {winnerPrompt && <section role="dialog" aria-modal="true" aria-label={t('winnerPrompt')} className="panel">
          <h2>{t('winnerPrompt')}</h2>
          <label>{t('winner')}<select value={promptWinner} onChange={e => setPromptWinner(e.target.value as TeamId)}>{series.teams.map(team => <option key={team.id} value={team.id}>{team.name}</option>)}</select></label>
          <button disabled={busy} onClick={() => void launchGame(promptWinner)}>{t('recordAndStart')}</button>
          <button disabled={busy} onClick={() => void launchGame()}>{t('later')}</button>
          <button disabled={busy} onClick={() => setWinnerPrompt(false)}>{t('cancelCorrection')}</button>
        </section>}
        {profile && <Rosters series={series} profile={profile} players={players} busy={busy || Number(people.snapshot?.version ?? -1) < Number(version)}
          onEdit={() => setEditVersion(previous => previous ?? people.snapshot?.version ?? version)} onSave={savePlayer} />}
        {current && profile && <GamePlayers game={current} series={series} profile={profile} players={players} busy={busy}
          current onEdit={() => setEditVersion(previous => previous ?? version)} onSave={async (path, body) => { await save(path, body); }} />}
        <div className="game-strip" aria-label={t('timeline')}>
          {series.games.map(game => <div className={game.id === current?.id ? 'game-step active' : 'game-step'} key={game.id}>
            <span>{t('game', { number: game.number })}</span><small>{t(game.state.status)}{game.state.result_pending && <> · {t('resultPending')}</>}</small>
          </div>)}
        </div>
        {current && <>
          <section className="entry-panel panel">
            {current.patch && <p data-testid="game-patch">{current.patch}</p>}
            <div className="entry-heading"><span className="eyebrow">{t('liveEntry')}</span><span data-testid="draft-progress" className="mono">
              {t('progress', { filled: current.actions.length, total: series.rule_snapshot.draft_order.turns.length })}</span></div>
            {nextTurn ? <><h2 data-testid="next-turn">{t('turn', { number: nextTurn.index + 1, team: teamName(nextTurn.team_id), kind: t(nextTurn.kind) })}</h2>
              <form className="entry-form" onSubmit={record}>
                <label>{t('search')}<input disabled={busy} value={search} placeholder={t('searchHint')} onChange={e => { setSearch(e.target.value); setCharacter(''); setRejectedRule(''); }} /></label>
                <label>{t('character')}<select disabled={busy} value={character} onChange={e => { setCharacter(e.target.value); setRejectedRule(''); setEditVersion(version); }} required>
                  <option value="">{t('select')}</option>
                  {profile?.catalog.filter(c => !c.retired && [c.name, ...c.aliases].some(name => name.toLowerCase().includes(search.toLowerCase())))
                    .map(c => <option key={c.id} value={c.id}>{current.state.locks[nextTurn.team_id].includes(c.id) ? t('lockedOption', { name: c.name }) : c.name}</option>)}
                </select></label>
                <button className="primary" disabled={busy || !character}>{busy ? t('saving') : t('record')}</button>
              </form>
              {nextTurn.kind === 'ban' && <button disabled={busy} onClick={() => void save(`/series/${series.id}/games/${current.id}/actions`, { character_id: null })}>{t('skipBan')}</button>}
              {rejectedRule && character && <form onSubmit={event => {
                event.preventDefault();
                void save(`/series/${series.id}/games/${current.id}/actions`, { character_id: character, override: { category: overrideCategory, note: overrideNote || null } });
              }}>
                <label>{t('overrideReason')}<select value={overrideCategory} onChange={e => setOverrideCategory(e.target.value)}>
                  {(['official_ruling', 'profile_mismatch', 'earlier_entry_wrong', 'other'] as const).map(category => <option key={category} value={category}>{t(category)}</option>)}
                </select></label>
                <label>{t('overrideNote')}<input value={overrideNote} maxLength={2000} required={overrideCategory === 'other'} onChange={e => setOverrideNote(e.target.value)} /></label>
                <button disabled={busy || (overrideCategory === 'other' && !overrideNote.trim())}>{t('recordOverride')}</button>
              </form>}
              </> : <><h2>{current.voided ? t('Voided') : t('complete')}</h2>{series.progress.can_start_next && <p className="muted">{t('draftCompleteHint')}</p>}</>}
          </section>
          {!!current.actions.length && !current.voided && <button disabled={busy} onClick={() => void save(`/series/${series.id}/games/${current.id}/actions/${current.actions.at(-1)!.turn_index}/clear`, {})}>{t('clearLatest')}</button>}
          <div data-testid="rule-notices" role="status">
            {current.state.notices.map(notice => <p key={`notice-${notice.turn_index}`}>{errorText(notice.rule)}</p>)}
            {violationList(current)}
          </div>
          {!!current.state.profile_update_hints.length && <p data-testid="profile-update-hint">{t('profileUpdateHint')}</p>}
          <div className="team-grid">{series.teams.map(team => {
            const assignment = current.assignments.find(a => a.team_id === team.id)!;
            return <section className={`team-panel panel team-${team.id}`} key={team.id}>
              <div className="team-header"><div><p className="eyebrow">{assignment.side === 'blue' || assignment.side === 'red' ? t(assignment.side) : assignment.side} · {t(assignment.position)}</p>
                <h2>{team.name}{series.our_team === team.id && <small className="our-team">{t('ourTeam')}</small>}</h2></div>
                <span className="available">{t('available', { count: current.state.available[team.id].length })}</span></div>
              <h3>{t('picks')}</h3>{actionList(current, team.id, 'pick')}
              <h3>{t('bans')}</h3>{actionList(current, team.id, 'ban')}
              <div className="locks" data-testid={`locks-${team.id}`}><h3>{t('locks')} <span className="mono">{current.state.locks[team.id].length}</span></h3>
                {current.state.locks[team.id].length ? <ul>{current.state.locks[team.id].map(id => <li key={id}>{characterName(id)}</li>)}</ul> : <p className="muted">{t('noLocks')}</p>}
              </div>
            </section>;
          })}</div>
          <p className="lock-footnote">{t('lockHint')}</p>
        </>}
        {series.progress.can_start_next ? <section className="next-game panel">
          <div><h2>{t('gameSetup')}</h2><p className="muted">{t(series.rule_snapshot.sides_coupled ? 'coupledSetupHint' : 'gameSetupHint')}</p></div>
          <form onChangeCapture={() => setEditVersion(previous => previous ?? version)} onSubmit={start} className="next-game-form">
            <label>{t('sideFor', { team: teamName('A') })}<select value={side} onChange={e => setSide(e.target.value)}>
              {seriesSides.map(value => <option key={value} value={value}>{value === 'blue' || value === 'red' ? t(value) : value}</option>)}</select></label>
            <label>{t('firstPick')}<select aria-label={t('firstPick')} value={setupFirst} disabled={series.rule_snapshot.sides_coupled} onChange={e => setFirstPick(e.target.value as TeamId)}>
              {series.teams.map(team => <option key={team.id} value={team.id}>{team.name}</option>)}</select></label>
            <FirstSelectionFields teams={series.teams} form={setupForm} dispatch={dispatchSetup} />
            <PrefillOffer teams={series.teams} form={setupForm} onApply={() => dispatchSetup({ type: 'apply' })} />
            {setupForm.notStarted && <p role="status" data-testid="prefill-notice">{t('draftNotStarted', { number: nextNumber })}</p>}
            <p className="muted">{t('selectionHint')}</p>
            <label>{t('gamePatch')}<input value={gamePatch} placeholder={series.patch ?? ''} onChange={e => setGamePatch(e.target.value)} maxLength={100} /></label>
            <button className="primary" disabled={busy}>{t('startGame', { number: nextNumber })}</button>
          </form>
        </section> : <p className="muted">{series.progress.ended ? t('seriesEnded') : current?.voided ? t('replay_required') : series.games.filter(g => !g.voided).length >= series.rule_snapshot.series_format.games ? t('allStarted') : t('remaining')}</p>}
        {!!series.games.length && <section className="timeline" data-testid="timeline"><div className="section-title"><h2>{t('timeline')}</h2><p>{t('timelineHint')}</p></div>
          {series.games.map(game => <details id={`game-${game.id}`} className="timeline-game panel" key={game.id} open={game.id !== current?.id}>
            <summary><strong>{t('game', { number: game.number })}{game.replay_of && <> · {t('replayOf', {number: game.number})}</>}</strong><span>{t(game.state.status)}{game.state.result_pending && <> · {t('resultPending')}</>}</span></summary>
            {game.replay_of && <a href={`#game-${game.replay_of}`}>{t('viewSource')}</a>}
            {isDraftedOrClosed(game) && <form key={game.winner ?? 'pending'} onChangeCapture={() => setEditVersion(previous => previous ?? version)} onSubmit={event => {
              event.preventDefault(); const fields = new FormData(event.currentTarget);
              void save(`/series/${series.id}/games/${game.id}/winner`, { winner: fields.get('winner') || null });
            }}>
              <label>{t('winner')}<select aria-label={t('winner')} name="winner" defaultValue={game.winner ?? ''}><option value="">{t('resultPending')}</option>{series.teams.map(team => <option key={team.id} value={team.id}>{team.name}</option>)}</select></label>
              <button disabled={busy}>{t('saveWinner')}</button>
            </form>}
            {!isDraftedOrClosed(game) && game.winner !== null && <p>{t(game.voided ? 'storedWinnerVoided' : 'storedWinner', { team: teamName(game.winner) })}
              <button disabled={busy} onClick={() => void save(`/series/${series.id}/games/${game.id}/winner`, { winner: null })}>{t('clearWinner')}</button></p>}
            <section aria-label={t('selectionForGame', {number: game.number})}>
              <RecordedFirstSelection key={`${game.id}-${game.first_selection_holder}-${game.first_selection_choice}`}
                teams={series.teams} game={game} busy={busy} onEdit={() => setEditVersion(previous => previous ?? version)}
                onSave={body => void save(`/series/${series.id}/games/${game.id}/first-selection`, body)} />
            </section>
            {!game.voided && game.id === current?.id && <button disabled={busy} onClick={() => void save(`/series/${series.id}/games/${game.id}/void`, {})}>{t('voidGame')}</button>}
            {game.id !== current?.id && profile && <GamePlayers game={game} series={series} profile={profile} players={players} busy={busy}
              onEdit={() => setEditVersion(previous => previous ?? version)} onSave={async (path, body) => { await save(path, body); }} />}
            <div className="timeline-teams">{series.teams.map(team => <div key={team.id}><h3>{team.name}</h3>
              <h4>{t('picks')}</h4>{actionList(game, team.id, 'pick')}<h4>{t('bans')}</h4>{actionList(game, team.id, 'ban')}
              <h4>{t('timelineLocks')}</h4><p>{game.state.locks[team.id].map(characterName).join(', ') || t('noLocks')}</p></div>)}</div>
            {game.id !== current?.id && violationList(game)}
            <ol className="correction-actions">{game.actions.map(action => <li key={action.turn_index}>
              <span>{action.turn_index + 1} · {teamName(action.team_id)} · {t(action.kind)} · {action.character_id === null ? t('skippedBan') : characterName(action.character_id)}</span>
              <button disabled={busy} onClick={() => { setCorrection({ game: game.id, turn: action.turn_index, character: action.character_id ?? '' }); setEditVersion(version); }}>{t('correctTurn', { number: action.turn_index + 1 })}</button>
              {correction?.game === game.id && correction.turn === action.turn_index && <form onSubmit={event => {
                event.preventDefault();
                void save(`/series/${series.id}/games/${game.id}/actions/${action.turn_index}/correct`, { character_id: correction.character || null }, undefined, { game: game.id, turn: action.turn_index });
              }}>
                <label>{t('replacementCharacter')}<select value={correction.character} onChange={event => setCorrection({ ...correction, character: event.target.value })}>
                  {action.kind === 'ban' && <option value="">{t('skippedBan')}</option>}
                  {profile?.catalog.map(c => <option key={c.id} value={c.id}>{c.retired ? t('retiredCharacter', { name: c.name }) : c.name}</option>)}
                </select></label>
                <button disabled={busy}>{t('saveCorrection')}</button>
                <button type="button" disabled={busy} onClick={() => { setCorrection(null); setEditVersion(null); }}>{t('cancelCorrection')}</button>
              </form>}
            </li>)}</ol>
            {!!game.edit_history.length && <section data-testid="edit-history"><h3>{t('editHistory')}</h3><ol>{game.edit_history.map((edit, index) => <li key={index}>
              <time dateTime={edit.recorded_at}>{new Date(edit.recorded_at).toLocaleString()}</time> · {edit.before.turn_index + 1} · {edit.before.character_id === null ? t('skippedBan') : characterName(edit.before.character_id)} → {edit.after === null ? t('cleared') : edit.after.character_id === null ? t('skippedBan') : characterName(edit.after.character_id)}
            </li>)}</ol></section>}
            {!game.voided && <p className="muted">{game.state.missing.map(field => field === 'winner' ? t('winnerMissing') : field === 'draft' ? t('draftMissing') : t('assignmentsMissing')).join(' · ') || t('recordComplete')}</p>}
          </details>)}
        </section>}
      </>}
    </main>
  </div>;
}
