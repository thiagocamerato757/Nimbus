import { t } from './i18n';
import type { Series, TeamId } from './types';

export function FirstSelectionFields({ teams, holder, choice, onHolder, onChoice }: {
  teams: Series['teams']; holder: string; choice: string;
  onHolder?: (value: TeamId | '') => void;
  onChoice?: (value: string) => void;
}) {
  return <>
    <label>{t('selectionHolder')}<select name="first_selection_holder"
      value={onHolder ? holder : undefined} defaultValue={onHolder ? undefined : holder}
      onChange={onHolder ? event => onHolder(event.target.value as TeamId | '') : undefined}>
      <option value="">{t('noSelectionHolder')}</option>
      {teams.map(team => <option key={team.id} value={team.id}>{team.name}</option>)}
    </select></label>
    <label>{t('selectionChoice')}<select name="first_selection_choice"
      value={onChoice ? choice : undefined} defaultValue={onChoice ? undefined : choice}
      onChange={onChoice ? event => onChoice(event.target.value) : undefined}>
      <option value="">{t('noSelectionChoice')}</option>
      <option value="side">{t('choseSide')}</option>
      <option value="draft_position">{t('chosePosition')}</option>
    </select></label>
  </>;
}
