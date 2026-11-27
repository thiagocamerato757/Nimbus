export type TeamId = 'A' | 'B';
export type Kind = 'ban' | 'pick';
export interface Character { id: string; name: string; aliases: string[]; retired: boolean }
export interface SeriesFormat { kind: 'best_of' | 'fixed_length'; games: number }
export interface Fearless { id: 'off' | 'soft' | 'hard' | 'custom'; lock_reach: 'none' | 'picking_team' | 'both_teams'; lock_sources: 'picks' | 'picks_and_bans' }
export interface RosterTeam { id: string; name: string }
export interface Player { id: string; name: string; usual_role: string | null; current_team_id: string | null; declared_pools: Record<string, string[]> }
export interface Profile { team_size: number; character_pool_label: string; id: string; name: string; sides: string[]; catalog: Character[];
  draft_orders: { id: string; name: string; turns: Turn[] }[]; default_draft_order: string;
  series_formats: SeriesFormat[]; default_series_format: SeriesFormat;
  fearless_presets: Fearless[]; default_fearless: string;
}
export interface Turn { position: 'first' | 'second'; kind: Kind }
export interface DraftAction { turn_index: number; team_id: TeamId; kind: Kind; character_id: string | null }
export interface Game {
  winner: TeamId | null; voided: boolean;
  id: string; number: number; patch: string | null;
  assignments: { team_id: TeamId; side: string; position: 'first' | 'second' }[];
  lineups: Record<TeamId, string[]>;
  player_assignments: { turn_index: number; player_id: string }[];
  actions: DraftAction[];
  edit_history: { recorded_at: string; before: DraftAction; after: DraftAction | null }[];
  state: { locks: Record<TeamId, string[]>; available: Record<TeamId, string[]>;
    status: 'Drafting' | 'Drafted' | 'Closed' | 'Voided'; result_pending: boolean; missing: string[];
    notices: { turn_index: number; rule: string }[];
    violations: { turn_index: number; rule: string; status: 'open' | 'acknowledged'; reason: { category: 'official_ruling' | 'profile_mismatch' | 'earlier_entry_wrong' | 'other'; note: string | null } | null }[];
    profile_update_hints: string[];
    complete: boolean; next_turn: { index: number; team_id: TeamId; kind: Kind } | null };
}
export interface Series {
  progress: { score: Record<TeamId, number>; pending_results: number[]; ended: boolean; can_start_next: boolean; deciding_game: number | null; games_past_decision: number[] };
  id: string; profile_id: string; teams: { id: TeamId; name: string; roster_id: string }[]; our_team: TeamId | null;
  patch: string | null; record_type: 'official' | 'scrim';
  rule_snapshot: { series_format: SeriesFormat; fearless: Fearless; draft_order: { id: string; name: string; turns: Turn[] } };
  games: Game[];
}
