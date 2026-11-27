import type { FormEvent } from 'react';
import { t } from './i18n';
import type { Game, Player, Profile, Series } from './types';

const identity = (player: Player) => t('playerIdentity', { name: player.name, id: player.id.slice(0, 8) });
interface Shared { series: Series; profile: Profile; players: Player[]; busy: boolean; onEdit: () => void }
interface RostersProps extends Shared { onSave: (path: string, body: unknown) => Promise<boolean> }

export function Rosters({ series, profile, players, busy, onEdit, onSave }: RostersProps) {
  const edit = (p: Player, current_team_id: string | null) => onSave(`/players/${p.id}`, { name: p.name, usual_role: p.usual_role, current_team_id });
  return <details className="panel roster-editor" open><summary>{t('rosters')}</summary>
    <fieldset disabled={busy} className="people-fields"><div className="people-grid">{series.teams.map(team => <section key={team.id} data-testid={`roster-${team.id}`}>
      <h2>{team.name} · {t('roster')}</h2>
      {players.filter(p => p.current_team_id === team.roster_id).map(player => <article className="roster-player" data-testid="roster-player" key={player.id}>
        <h3>{identity(player)}</h3>
        <form key={`${player.name}:${player.usual_role}`} onChangeCapture={onEdit} onSubmit={event => {
          event.preventDefault(); const fields = new FormData(event.currentTarget);
          void onSave(`/players/${player.id}`, { name: fields.get('name'), usual_role: fields.get('role') || null, current_team_id: team.roster_id });
        }}>
          <label>{t('playerName')}<input name="name" defaultValue={player.name} required maxLength={100} /></label>
          <label>{t('usualRole')}<input name="role" defaultValue={player.usual_role ?? ''} maxLength={100} /></label>
          <button disabled={busy}>{t('savePlayer')}</button>
        </form>
        <button disabled={busy} onClick={() => void edit(player, null)}>{t('removePlayer')}</button>
        {series.our_team === team.id && <form key={(player.declared_pools[profile.id] ?? []).join(',')} onChangeCapture={onEdit} onSubmit={event => {
          event.preventDefault(); const fields = new FormData(event.currentTarget);
          void onSave(`/series/${series.id}/teams/${team.id}/players/${player.id}/pool`, { character_ids: fields.getAll('characters') });
        }}>
          <label>{t('declaredPool')} · {profile.character_pool_label}<select aria-label={t('declaredPool')} multiple name="characters" size={6} defaultValue={player.declared_pools[profile.id] ?? []}>
            {profile.catalog.filter(c => !c.retired).map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select></label>
          <button disabled={busy}>{t('savePool')}</button>
        </form>}
      </article>)}
      <form onChangeCapture={onEdit} onSubmit={event => {
        event.preventDefault(); const form = event.currentTarget; const fields = new FormData(form);
        void onSave('/players', { name: fields.get('name'), usual_role: fields.get('role') || null, current_team_id: team.roster_id }).then(saved => { if (saved) form.reset(); });
      }}>
        <label>{t('newPlayer')}<input name="name" required maxLength={100} /></label>
        <label>{t('usualRole')}<input name="role" maxLength={100} /></label>
        <button disabled={busy}>{t('createPlayer')}</button>
      </form>
      <form onChangeCapture={onEdit} onSubmit={event => {
        event.preventDefault(); const fields = new FormData(event.currentTarget); const player = players.find(p => p.id === fields.get('player'));
        if (player) void edit(player, team.roster_id);
      }}>
        <label>{t('existingPlayer')}<select aria-label={t('existingPlayer')} name="player" required defaultValue="">
          <option value="">{t('choosePlayer')}</option>{players.filter(p => p.current_team_id !== team.roster_id).map(p => <option key={p.id} value={p.id}>{identity(p)}</option>)}
        </select></label>
        <button disabled={busy}>{t('addPlayer')}</button>
      </form>
    </section>)}</div></fieldset>
  </details>;
}

interface GamePlayersProps extends Shared {
  game: Game; current?: boolean; onSave: (path: string, body: unknown) => Promise<void>;
}
export function GamePlayers({ series, profile, players, game, busy, current, onEdit, onSave }: GamePlayersProps) {
  const path = `/series/${series.id}/games/${game.id}`;
  return <section className="panel game-players" data-testid={current ? 'game-players-current' : `game-players-${game.number}`}>
    <h2>{t('game', { number: game.number })} · {t('lineup')}</h2><p className="muted">{t('lineupHint')}</p>
    <fieldset disabled={busy} className="people-fields"><div className="people-grid">{series.teams.map(team => {
      const ids = game.lineups[team.id];
      const eligible = players.filter(p => p.current_team_id === team.roster_id || ids.includes(p.id));
      return <section key={team.id}>
        <h3>{team.name}</h3>
        <form key={ids.join(',')} data-testid={`lineup-${team.id}`} onChangeCapture={onEdit} onSubmit={(event: FormEvent<HTMLFormElement>) => {
          event.preventDefault(); const fields = new FormData(event.currentTarget);
          void onSave(`${path}/lineups`, { team_id: team.id, player_ids: fields.getAll('players') });
        }}>
          <p>{t('lineupCount', { count: ids.length, size: profile.team_size })}</p>
          {eligible.map(p => <label className="lineup-choice" key={p.id}><input type="checkbox" name="players" value={p.id} defaultChecked={ids.includes(p.id)} />
            {identity(p)}{p.current_team_id !== team.roster_id && <small> · {t('formerMember')}</small>}</label>)}
          <button disabled={busy}>{t('saveLineup')}</button>
        </form>
        <h4>{t('playerAssignments')}</h4>
        {game.actions.filter(a => a.kind === 'pick' && a.team_id === team.id).map(action => {
          const assigned = game.player_assignments.find(a => a.turn_index === action.turn_index)?.player_id ?? '';
          return <form key={`${action.turn_index}:${assigned}`} onChangeCapture={onEdit} onSubmit={event => {
            event.preventDefault(); const fields = new FormData(event.currentTarget);
            void onSave(`${path}/player-assignments`, { turn_index: action.turn_index, player_id: fields.get('player') || null });
          }}>
            <label>{t('playerForTurn', { number: action.turn_index + 1 })} · {profile.catalog.find(c => c.id === action.character_id)?.name ?? action.character_id}
              <select aria-label={t('playerForTurn', { number: action.turn_index + 1 })} name="player" defaultValue={assigned}>
                <option value="">{t('unassigned')}</option>{ids.map(id => <option key={id} value={id}>{players.find(p => p.id === id) ? identity(players.find(p => p.id === id)!) : id}</option>)}
              </select>
            </label>
            <button disabled={busy}>{t('saveAssignment')}</button>
          </form>;
        })}
      </section>;
    })}</div></fieldset>
  </section>;
}
