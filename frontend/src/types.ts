export type TeamId = 'A' | 'B';
export type Kind = 'ban' | 'pick';
export interface Character { id: string; name: string; aliases: string[]; retired: boolean }
export interface SeriesFormat { kind: 'best_of' | 'fixed_length'; games: number }
export interface Fearless { id: 'off' | 'soft' | 'hard' | 'custom'; lock_reach: 'none' | 'picking_team' | 'both_teams'; lock_sources: 'picks' | 'picks_and_bans' }
export interface Profile { id: string; name: string; sides: string[]; catalog: Character[];
  draft_orders: { id: string; name: string; turns: Turn[] }[]; default_draft_order: string;
  series_formats: SeriesFormat[]; default_series_format: SeriesFormat;
  fearless_presets: Fearless[]; default_fearless: string;
}
export interface Turn { position: 'first' | 'second'; kind: Kind }
export interface Game {
  id: string; number: number; patch: string | null;
  assignments: { team_id: TeamId; side: string; position: 'first' | 'second' }[];
  actions: { turn_index: number; team_id: TeamId; kind: Kind; character_id: string }[];
  state: { locks: Record<TeamId, string[]>; available: Record<TeamId, string[]>;
    complete: boolean; next_turn: { index: number; team_id: TeamId; kind: Kind } | null };
}
export interface Series {
  id: string; profile_id: string; teams: { id: TeamId; name: string }[]; our_team: TeamId | null;
  patch: string | null; record_type: 'official' | 'scrim';
  rule_snapshot: { series_format: SeriesFormat; fearless: Fearless; draft_order: { id: string; name: string; turns: Turn[] } };
  games: Game[];
}
