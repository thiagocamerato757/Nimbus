import { useState } from 'react';
import { ApiError, requestSnapshot } from './api';
import { errorText, t } from './i18n';
import type { Profile, Series, Player, Fearless } from './types';

type Impact = { before: Series; after: Series };
type Proposal = {
  draft_order_id?: string; series_format?: Series['rule_snapshot']['series_format'];
  fearless?: Omit<Fearless, 'id'>; disabled_characters?: string[];
  rule_settings?: Series['rule_snapshot']['rule_settings'];
};

export function SeriesSettings({ series, profile, players, version, onSaved }: {
  series: Series; profile: Profile; players: Player[]; version: string; onSaved: () => void;
}) {
  const [edit, setEdit] = useState<{ proposal: Proposal; version: string } | null>(null);
  const [impact, setImpact] = useState<Impact | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const settings = { ...series.rule_snapshot, ...edit?.proposal };
  const change = (proposal: Proposal) => {
    setEdit({ proposal: { ...edit?.proposal, ...proposal }, version: edit?.version ?? version });
    setImpact(null); setError('');
  };
  const characterName = (id: string) => profile.catalog.find(c => c.id === id)?.name ?? id;
  const playerName = (id: string) => players.find(p => p.id === id)?.name ?? id;
  const cancel = () => { setEdit(null); setImpact(null); setError(''); };
  async function submit(save: boolean) {
    if (!edit) return;
    setBusy(true); setError('');
    try {
      const response = await requestSnapshot<Impact>(`/series/${series.id}/${save ? 'settings' : 'settings-preview'}`, edit.proposal, edit.version);
      if (save) { cancel(); onSaved(); }
      else setImpact(response.data);
    } catch (e) {
      setError(e instanceof ApiError ? e.code : 'unexpected');
      if (e instanceof ApiError && e.code === 'stale_version') { setImpact(null); setEdit(null); onSaved(); }
    } finally { setBusy(false); }
  }
  const changes: string[] = [];
  if (impact) {
    for (const after of impact.after.games) {
      const before = impact.before.games.find(g => g.id === after.id)!;
      for (const [label, from, to] of [
        ['violationsCreated', before.state.violations, after.state.violations],
        ['violationsCleared', after.state.violations, before.state.violations],
      ] as const) {
        for (const v of to.filter(v => !from.some(old => old.rule === v.rule && old.turn_index === v.turn_index))) {
          changes.push(`${t(label)} · ${t('game')} ${after.number} · ${v.turn_index + 1}: ${errorText(v.rule)} · ${characterName(after.actions.find(a => a.turn_index === v.turn_index)?.character_id ?? '')}`);
        }
      }
      for (const [id, pool] of Object.entries(after.player_pools)) {
        const previous = before.player_pools[id]?.remaining ?? [];
        if (JSON.stringify(previous) !== JSON.stringify(pool.remaining)) {
          const teamId = (['A', 'B'] as const).find(team => after.lineups[team].includes(id));
          const teamName = series.teams.find(team => team.id === teamId)?.name ?? '';
          changes.push(`${teamName} · ${playerName(id)} · ${t('game')} ${after.number} · ${t('remainingPool')}: ${previous.map(characterName).join(', ') || '∅'} → ${pool.remaining.map(characterName).join(', ') || '∅'}`);
        }
      }
    }
  }
  return <section className="panel" aria-label={t('amendSettings')}>
    <h2>{t('amendSettings')}</h2>
    {error && <p role="alert">{errorText(error)}</p>}
    <fieldset disabled={busy}>
      <label>{t('draftOrder')}<select value={edit?.proposal.draft_order_id ?? '__snapshot__'} onChange={e => change({ draft_order_id: e.target.value === '__snapshot__' ? undefined : e.target.value })}>
        <option value="__snapshot__">{series.rule_snapshot.draft_order.name} · {t('currentSnapshot')}</option>
        {profile.draft_orders.map(o => <option key={o.id} value={o.id}>{o.name}</option>)}
      </select></label>
      <label>{t('format')}<select value={JSON.stringify(settings.series_format)} onChange={e => change({ series_format: JSON.parse(e.target.value) })}>
        {profile.series_formats.map(f => <option key={JSON.stringify(f)} value={JSON.stringify(f)}>{t(f.kind)} · {f.games}</option>)}
      </select></label>
      <label>{t('lockReach')}<select value={settings.fearless.lock_reach} onChange={e => change({ fearless: { ...settings.fearless, lock_reach: e.target.value as Fearless['lock_reach'] } })}>
        {(['none', 'picking_team', 'both_teams'] as const).map(r => <option key={r} value={r}>{t(r)}</option>)}
      </select></label>
      <label>{t('lockSources')}<select value={settings.fearless.lock_sources} onChange={e => change({ fearless: { ...settings.fearless, lock_sources: e.target.value as Fearless['lock_sources'] } })}>
        {(['picks', 'picks_and_bans'] as const).map(r => <option key={r} value={r}>{t(r === 'picks_and_bans' ? 'sourcesBans' : 'picks')}</option>)}
      </select></label>
      <label>{t('banningLocked')}<select value={settings.rule_settings.banning_locked} onChange={e => change({ rule_settings: { ...settings.rule_settings, banning_locked: e.target.value as 'allow' | 'warn' | 'reject' } })}>
        {(['allow', 'warn', 'reject'] as const).map(r => <option key={r} value={r}>{t(r)}</option>)}
      </select></label>
      <label>{t('mirroring')}<input type="checkbox" checked={settings.rule_settings.same_character_twice === 'allow'} onChange={e => change({ rule_settings: { ...settings.rule_settings, same_character_twice: e.target.checked ? 'allow' : 'reject' } })} /></label>
      <label>{t('countVoided')}<input type="checkbox" checked={settings.rule_settings.voided_games_count} onChange={e => change({ rule_settings: { ...settings.rule_settings, voided_games_count: e.target.checked } })} /></label>
      <label>{t('disabledCharacters')}<select multiple size={6} value={settings.disabled_characters} onChange={e => change({ disabled_characters: Array.from(e.target.selectedOptions, o => o.value) })}>
        {profile.catalog.filter(c => !c.retired || settings.disabled_characters.includes(c.id)).map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
      </select></label>
      <button disabled={!edit} onClick={() => void submit(false)}>{t('previewSettings')}</button>
      {edit && <button onClick={cancel}>{t('cancelSettings')}</button>}
    </fieldset>
    {impact && <div role="status" data-testid="settings-impact">
      <h3>{t('settingsImpact')}</h3>
      <p>{t('endedChange')}: {t(impact.before.progress.ended ? 'yes' : 'no')} → {t(impact.after.progress.ended ? 'yes' : 'no')}</p>
      {changes.length ? changes.map((text, i) => <p key={i}>{text}</p>) : <p>{t('noRuleImpact')}</p>}
      {!!impact.after.progress.games_past_decision.length && <p role="alert">{t('pastDecision', { number: impact.after.progress.deciding_game! })}</p>}
      <button disabled={busy} onClick={() => void submit(true)}>{t('saveSettings')}</button>
    </div>}
  </section>;
}
