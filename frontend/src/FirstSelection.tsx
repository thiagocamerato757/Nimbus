import { useReducer, type Dispatch } from 'react';
import {
  closedForm, firstSelectionReducer, offeredPrefill, requestFields,
  type Choice, type FirstSelectionAction, type FirstSelectionForm,
} from './firstSelectionForm';
import { t } from './i18n';
import type { Game, Series, TeamId } from './types';

// The setup or Replay form: it opens with the First Selection pre-fill of that
// moment, and later results only change what is offered.
export function useFirstSelectionForm(key: string, prefill: TeamId | '') {
  const [stored, dispatch] = useReducer(firstSelectionReducer, closedForm);
  const sync = { type: 'sync', key, prefill } as const;
  const form = firstSelectionReducer(stored, sync);
  if (form !== stored) dispatch(sync);
  return [form, dispatch] as const;
}

// The choice is disabled until a holder is selected (#14, amended).
export function FirstSelectionFields({ teams, form, dispatch }: {
  teams: Series['teams']; form: FirstSelectionForm; dispatch: Dispatch<FirstSelectionAction>;
}) {
  return <>
    <label>{t('selectionHolder')}<select name="first_selection_holder" value={form.holder}
      onChange={event => dispatch({ type: 'holder', holder: event.target.value as TeamId | '' })}>
      <option value="">{t('noSelectionHolder')}</option>
      {teams.map(team => <option key={team.id} value={team.id}>{team.name}</option>)}
    </select></label>
    <label>{t('selectionChoice')}<select name="first_selection_choice" value={form.choice} disabled={!form.holder}
      onChange={event => dispatch({ type: 'choice', choice: event.target.value as Choice | '' })}>
      <option value="">{t('noSelectionChoice')}</option>
      <option value="side">{t('choseSide')}</option>
      <option value="draft_position">{t('chosePosition')}</option>
    </select></label>
  </>;
}

// A later result never changes a form the analyst is filling in: the new First
// Selection pre-fill is offered, and only Apply takes it.
export function PrefillOffer({ teams, form, onApply }: {
  teams: Series['teams']; form: FirstSelectionForm; onApply: () => void;
}) {
  const offered = offeredPrefill(form);
  if (offered === null) return null;
  const team = teams.find(item => item.id === offered);
  return <p role="status" data-testid="prefill-offer">
    {team ? t('prefillOffered', { team: team.name }) : t('prefillOfferedNone')}{' '}
    <button type="button" onClick={onApply}>{t('applyPrefill')}</button>
  </p>;
}

// Editing the recorded First Selection of one Game; remount it when that changes.
export function RecordedFirstSelection({ teams, game, busy, onEdit, onSave }: {
  teams: Series['teams']; game: Game; busy: boolean;
  onEdit: () => void; onSave: (body: ReturnType<typeof requestFields>) => void;
}) {
  const holder = game.first_selection_holder ?? '';
  const [form, dispatch] = useReducer(firstSelectionReducer, {
    key: game.id, holder, choice: game.first_selection_choice ?? '', taken: holder, latest: holder,
  });
  return <form onChangeCapture={onEdit} onSubmit={event => { event.preventDefault(); onSave(requestFields(form)); }}>
    <FirstSelectionFields teams={teams} form={form} dispatch={dispatch} />
    <button disabled={busy}>{t('saveSelection')}</button>
  </form>;
}
