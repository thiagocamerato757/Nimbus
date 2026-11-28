// The one First Selection form logic, shared by the setup, Replay and timeline
// forms (#14, amended 2026-11-28). Only the analyst's own change or Apply moves
// the holder; a changed result is only offered. A choice belongs to its holder.
import type { TeamId } from './types';

export type Choice = 'side' | 'draft_position';

export interface FirstSelectionForm {
  // Which form is open; an empty key means no form.
  key: string;
  holder: TeamId | '';
  choice: Choice | '';
  // The First Selection pre-fill the form last took: on opening or on Apply.
  taken: TeamId | '';
  // The pre-fill the current result gives.
  latest: TeamId | '';
}

export type FirstSelectionAction =
  | { type: 'sync'; key: string; prefill: TeamId | '' }
  | { type: 'holder'; holder: TeamId | '' }
  | { type: 'choice'; choice: Choice | '' }
  | { type: 'apply' }
  // The analyst recorded the previous winner on the way to starting the draft.
  | { type: 'recorded'; prefill: TeamId | '' };

export const closedForm: FirstSelectionForm = { key: '', holder: '', choice: '', taken: '', latest: '' };

// The new pre-fill to offer ('' means there is none now), or null for no offer.
export function offeredPrefill(form: FirstSelectionForm): TeamId | '' | null {
  return form.latest !== form.taken && form.latest !== form.holder ? form.latest : null;
}

function withHolder(form: FirstSelectionForm, holder: TeamId | ''): FirstSelectionForm {
  return holder === form.holder ? form : { ...form, holder, choice: '' };
}

export function firstSelectionReducer(form: FirstSelectionForm, action: FirstSelectionAction): FirstSelectionForm {
  switch (action.type) {
    case 'sync': {
      const { key, prefill } = action;
      if (!key) return form.key ? closedForm : form;
      if (key !== form.key) return { key, holder: prefill, choice: '', taken: prefill, latest: prefill };
      return prefill === form.latest ? form : { ...form, latest: prefill };
    }
    case 'holder':
      return withHolder(form, action.holder);
    case 'choice':
      return form.holder ? { ...form, choice: action.choice } : form;
    case 'apply': {
      const offered = offeredPrefill(form);
      return offered === null ? form : { ...withHolder(form, offered), taken: offered };
    }
    case 'recorded': {
      const { prefill } = action;
      // A pre-fill the draft stops for must be offered, even if it was taken before.
      return { ...form, latest: prefill, taken: startsAfterRecording(form, prefill) ? form.taken : form.holder };
    }
  }
}

// "Different" means different from the holder shown (docs/spec/mvp.md, amended
// 2026-11-28). With no new pre-fill, nothing unseen would be recorded.
function startsAfterRecording(form: FirstSelectionForm, prefill: TeamId | '') {
  return prefill === '' || prefill === form.holder;
}

// "Record winner and start": the draft does not start when the recorded result
// names another Team than the holder shown; the analyst Applies or starts again.
export function afterRecordedWinner(form: FirstSelectionForm, prefill: TeamId | '') {
  return {
    form: firstSelectionReducer(form, { type: 'recorded', prefill }),
    startDraft: startsAfterRecording(form, prefill),
  };
}

// A request carries holder and choice exactly as displayed.
export function requestFields(form: FirstSelectionForm) {
  return { first_selection_holder: form.holder || null, first_selection_choice: form.choice || null };
}
