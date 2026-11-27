import { useEffect, useState, type FormEvent } from 'react';
import { ApiError, request, requestSnapshot } from './api';
import { useLiveQuery } from './useLiveQuery';
import { errorText, t } from './i18n';
import type { Game, Profile, Series, TeamId, Fearless } from './types';

export default function App() {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const workspace = useLiveQuery<Series[]>('/series');
  const seriesList = workspace.snapshot?.data ?? [];
  const version = workspace.snapshot?.version ?? '';
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const series = seriesList.find(item => item.id === selectedId) ?? null;
  const [editVersion, setEditVersion] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [backupNotice, setBackupNotice] = useState('');
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
  const profile = profiles.find(p => p.id === (series?.profile_id ?? profileId));
  const current = series?.games.at(-1);
  const nextTurn = current?.state.next_turn;
  const characterName = (id: string) => profile?.catalog.find(c => c.id === id)?.name ?? id;
  const teamName = (id: TeamId) => series?.teams.find(team => team.id === id)?.name ?? id;

  const creationProfile = profiles.find(p => p.id === profileId);
  const selectedFormat = (formatIndex === '' ? creationProfile?.default_series_format : creationProfile?.series_formats[Number(formatIndex)]);
  const chosenVariant = variant || creationProfile?.default_fearless || 'hard';
  const chosenFearless = chosenVariant === 'custom' ? { lock_reach: reach, lock_sources: sources }
    : creationProfile?.fearless_presets.find(p => p.id === chosenVariant);
  const invalidCombination = chosenFearless?.lock_reach === 'picking_team' && chosenFearless?.lock_sources === 'picks_and_bans';
  const displayFormat = series?.rule_snapshot.series_format;

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

  async function save(path: string, body?: unknown) {
    setBusy(true); setError('');
    try {
      const result = await requestSnapshot<Series>(path, body, editVersion ?? version);
      const updated = result.data;
      setCharacter(''); setSearch('');
      workspace.accept({ data: [updated, ...seriesList.filter(item => item.id !== updated.id)], version: result.version });
      setSelectedId(updated.id); setEditVersion(null);
      void workspace.refresh();
    } catch (e) {
      setError(errorText(e instanceof ApiError ? e.code : 'unexpected'));
      if (e instanceof ApiError && e.code === 'stale_version') {
        setCharacter(''); setEditVersion(null);
        await workspace.refresh();
      }
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
    void save('/series', { profile_id: profileId, team_a: teamA, team_b: teamB, our_team: ourTeam || null,
      draft_order_id: draftOrder || creationProfile?.default_draft_order, series_format: selectedFormat,
      fearless: chosenFearless, patch: patch || null, record_type: recordType });
  }
  function start(event: FormEvent) {
    event.preventDefault();
    if (series) void save(`/series/${series.id}/games`, { team_a_side: side, first_pick_team: firstPick, patch: gamePatch || series.patch });
  }
  function record(event: FormEvent) {
    event.preventDefault();
    if (series && current) void save(`/series/${series.id}/games/${current.id}/actions`, { character_id: character });
  }
  function actionList(game: Game, teamId: TeamId, kind: 'ban' | 'pick') {
    const actions = game.actions.filter(action => action.team_id === teamId && action.kind === kind);
    return actions.length ? <ol className={`entries ${kind}`}>
      {actions.map(action => <li key={action.turn_index}>{characterName(action.character_id)}</li>)}
    </ol> : <p className="empty">{t('noActions')}</p>;
  }

  return <div className="app-shell">
    <aside className="sidebar">
      <a className="brand" href="/" aria-label={t('brand')}><span className="brand-mark" aria-hidden="true">N</span>{t('brand')}</a>
      <p className="sidebar-caption">{t('workspace')}</p>
      <button className="new-series" onClick={() => { setSelectedId(null); setError(''); setEditVersion(null); setCharacter(''); }} disabled={busy}>{t('newSeries')}</button>
      <h2 className="eyebrow">{t('yourSeries')}</h2>
      <nav className="series-nav">
        {seriesList.map(item => <button key={item.id} className={series?.id === item.id ? 'selected' : ''}
          disabled={busy} onClick={() => { setSelectedId(item.id); setEditVersion(null); setCharacter(''); setError(''); }}>
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
      {(error || workspace.error) && <div role="alert" className="alert">{error || errorText(workspace.error)}{!profiles.length && <button onClick={() => void load()}>{t('retry')}</button>}</div>}
      {loading || (!workspace.snapshot && !workspace.error) ? <p role="status">{t('loading')}</p> : !series ? <section className="setup panel">
        <div className="setup-intro"><div className="orbit" aria-hidden="true"><span>N</span></div>
          <h2>{t('setupTitle')}</h2><p>{t('setupDescription')}</p></div>
        <form onChangeCapture={() => setEditVersion(previous => previous ?? version)} onSubmit={create} className="series-form">
          <label>{t('titleProfile')}<select value={profileId} onChange={event => {
            setProfileId(event.target.value); setDraftOrder(''); setFormatIndex(''); setVariant(''); setSide(profiles.find(p => p.id === event.target.value)?.sides[0] ?? '');
          }}>{profiles.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
          <div className="form-pair"><label>{t('teamA')}<input value={teamA} onChange={e => setTeamA(e.target.value)} required maxLength={100} /></label>
            <label>{t('teamB')}<input value={teamB} onChange={e => setTeamB(e.target.value)} required maxLength={100} /></label></div>
          <label>{t('ourTeam')}<select value={ourTeam} onChange={e => setOurTeam(e.target.value)}>
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
        <div className="game-strip" aria-label={t('timeline')}>
          {series.games.map(game => <div className={game.id === current?.id ? 'game-step active' : 'game-step'} key={game.id}>
            <span>{t('game', { number: game.number })}</span><small>{game.state.complete ? t('drafted') : t('drafting')}</small>
          </div>)}
        </div>
        {current && <>
          <section className="entry-panel panel">
            {current.patch && <p data-testid="game-patch">{current.patch}</p>}
            <div className="entry-heading"><span className="eyebrow">{t('liveEntry')}</span><span data-testid="draft-progress" className="mono">
              {t('progress', { filled: current.actions.length, total: series.rule_snapshot.draft_order.turns.length })}</span></div>
            {nextTurn ? <><h2 data-testid="next-turn">{t('turn', { number: nextTurn.index + 1, team: teamName(nextTurn.team_id), kind: t(nextTurn.kind) })}</h2>
              <form className="entry-form" onSubmit={record}>
                <label>{t('search')}<input disabled={busy} value={search} placeholder={t('searchHint')} onChange={e => { setSearch(e.target.value); setCharacter(''); }} /></label>
                <label>{t('character')}<select disabled={busy} value={character} onChange={e => { setCharacter(e.target.value); setEditVersion(version); }} required>
                  <option value="">{t('select')}</option>
                  {profile?.catalog.filter(c => !c.retired && [c.name, ...c.aliases].some(name => name.toLowerCase().includes(search.toLowerCase())))
                    .map(c => <option key={c.id} value={c.id}>{current.state.locks[nextTurn.team_id].includes(c.id) ? t('lockedOption', { name: c.name }) : c.name}</option>)}
                </select></label>
                <button className="primary" disabled={busy || !character}>{busy ? t('saving') : t('record')}</button>
              </form></> : <><h2>{t('complete')}</h2><p className="muted">{t('draftCompleteHint')}</p></>}
          </section>
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
        {(!current || current.state.complete) && series.games.length < series.rule_snapshot.series_format.games ? <section className="next-game panel">
          <div><h2>{t('gameSetup')}</h2><p className="muted">{t('gameSetupHint')}</p></div>
          <form onChangeCapture={() => setEditVersion(previous => previous ?? version)} onSubmit={start} className="next-game-form">
            <label>{t('sideFor', { team: teamName('A') })}<select value={side} onChange={e => setSide(e.target.value)}>
              {profile?.sides.map(value => <option key={value} value={value}>{value === 'blue' || value === 'red' ? t(value) : value}</option>)}</select></label>
            <label>{t('firstPick')}<select value={firstPick} onChange={e => setFirstPick(e.target.value as TeamId)}>
              {series.teams.map(team => <option key={team.id} value={team.id}>{team.name}</option>)}</select></label>
            <label>{t('gamePatch')}<input value={gamePatch} placeholder={series.patch ?? ''} onChange={e => setGamePatch(e.target.value)} maxLength={100} /></label>
            <button className="primary" disabled={busy}>{t('startGame', { number: series.games.length + 1 })}</button>
          </form>
        </section> : <p className="muted">{series.games.length >= series.rule_snapshot.series_format.games ? t('allStarted') : t('remaining')}</p>}
        {!!series.games.length && <section className="timeline" data-testid="timeline"><div className="section-title"><h2>{t('timeline')}</h2><p>{t('timelineHint')}</p></div>
          {series.games.map(game => <details className="timeline-game panel" key={game.id} open={game.id !== current?.id}>
            <summary><strong>{t('game', { number: game.number })}</strong><span>{game.state.complete ? t('drafted') : t('drafting')}</span></summary>
            <div className="timeline-teams">{series.teams.map(team => <div key={team.id}><h3>{team.name}</h3>
              <h4>{t('picks')}</h4>{actionList(game, team.id, 'pick')}<h4>{t('bans')}</h4>{actionList(game, team.id, 'ban')}</div>)}</div>
            {game.state.complete && <p className="muted">{t('missing')}</p>}
          </details>)}
        </section>}
      </>}
    </main>
  </div>;
}
