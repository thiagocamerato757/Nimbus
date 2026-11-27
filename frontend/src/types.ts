export type TeamId = 'A' | 'B';
export type Kind = 'ban' | 'pick';
export interface Character { id: string; name: string; aliases: string[]; retired: boolean }
export interface Profile { id: string; name: string; sides: string[]; catalog: Character[] }
export interface Turn { position: 'first' | 'second'; kind: Kind }
export interface Game {
  id: string; number: number;
  assignments: { team_id: TeamId; side: string; position: 'first' | 'second' }[];
  actions: { turn_index: number; team_id: TeamId; kind: Kind; character_id: string }[];
  state: { locks: Record<TeamId, string[]>; available: Record<TeamId, string[]>;
    complete: boolean; next_turn: { index: number; team_id: TeamId; kind: Kind } | null };
}
export interface Series {
  id: string; profile_id: string; teams: { id: TeamId; name: string }[]; our_team: TeamId | null;
  rule_snapshot: { draft_order: { id: string; name: string; turns: Turn[] } };
  games: Game[];
}
