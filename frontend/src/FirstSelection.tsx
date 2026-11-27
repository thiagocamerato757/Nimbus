import { useState } from 'react';
import { t } from './i18n';
import type { Series, TeamId } from './types';

// A choice always belongs to a holder (#14, amended 2026-11-27): the choice is
// disabled until a holder is selected and cleared whenever the holder changes.
// With handlers the parent owns both values; without them the fields keep their
// own state inside an uncontrolled form, and a disabled choice is not submitted.
export function FirstSelectionFields({ teams, holder, choice, onHolder, onChoice }: {
  teams: Series['teams']; holder: string; choice: string;
  onHolder?: (value: TeamId | '') => void;
  onChoice?: (value: string) => void;
}) {
  const [ownHolder, setOwnHolder] = useState(holder);
  const [ownChoice, setOwnChoice] = useState(choice);
  const shownHolder = onHolder ? holder : ownHolder;
  const shownChoice = onChoice ? choice : ownChoice;
  function changeHolder(value: TeamId | '') {
    if (onHolder) onHolder(value); else setOwnHolder(value);
    if (onChoice) onChoice(''); else setOwnChoice('');
  }
  return <>
    <label>{t('selectionHolder')}<select name="first_selection_holder" value={shownHolder}
      onChange={event => changeHolder(event.target.value as TeamId | '')}>
      <option value="">{t('noSelectionHolder')}</option>
      {teams.map(team => <option key={team.id} value={team.id}>{team.name}</option>)}
    </select></label>
    <label>{t('selectionChoice')}<select name="first_selection_choice" value={shownChoice}
      disabled={!shownHolder}
      onChange={event => onChoice ? onChoice(event.target.value) : setOwnChoice(event.target.value)}>
      <option value="">{t('noSelectionChoice')}</option>
      <option value="side">{t('choseSide')}</option>
      <option value="draft_position">{t('chosePosition')}</option>
    </select></label>
  </>;
}
