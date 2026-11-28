// The one First Selection form logic, shared by the setup, Replay and timeline
// forms (docs/spec/mvp.md, amended 2026-11-28). Only the analyst's own change or
// Apply moves the holder; a choice belongs to its holder. The offer is derived
// from the current pre-fill and the holder shown, never stored (as in ADR-0008).
import type { TeamId } from './types';

export type Choice = 'side' | 'draft_position';

export interface FirstSelectionForm {
  // Which form is open; an empty key means no form.
  key: string;
  holder: TeamId | '';
  choice: Choice | '';
  // The First Selection pre-fill the current result gives.
  latest: TeamId | '';
  // "Record winner and start" recorded the winner but started no draft.
  notStarted: boolean;
}

export type FirstSelectionAction =
  | { type: 'sync'; key: string; prefill: TeamId | '' }
  | { type: 'holder'; holder: TeamId | '' }
  | { type: 'choice'; choice: Choice | '' }
  | { type: 'apply' }
  // The analyst recorded the previous winner on the way to starting the draft.
  | { type: 'recorded'; prefill: TeamId | '' };

export const closedForm: FirstSelectionForm = { key: '', holder: '', choice: '', latest: '', notStarted: false };

// The Team to offer: the current pre-fill, when it names another Team than the
// holder shown. Null means there is no offer.
export function offeredPrefill(form: FirstSelectionForm): TeamId | null {
  return form.latest !== '' && form.latest !== form.holder ? form.latest : null;
}

function withHolder(form: FirstSelectionForm, holder: TeamId | ''): FirstSelectionForm {
  return holder === form.holder ? form : { ...form, holder, choice: '' };
}

function withPrefill(form: FirstSelectionForm, prefill: TeamId | ''): FirstSelectionForm {
  return prefill === form.latest ? form : { ...form, latest: prefill };
}

function apply(form: FirstSelectionForm, action: FirstSelectionAction): FirstSelectionForm {
  switch (action.type) {
    case 'sync': {
      const { key, prefill } = action;
      if (!key) return form.key ? closedForm : form;
      if (key !== form.key) return { key, holder: prefill, choice: '', latest: prefill, notStarted: false };
      return withPrefill(form, prefill);
    }
    case 'holder':
      return withHolder(form, action.holder);
    case 'choice':
      return form.holder ? { ...form, choice: action.choice } : form;
    case 'apply': {
      const offered = offeredPrefill(form);
      return offered === null ? form : withHolder(form, offered);
    }
    case 'recorded': {
      const next = withPrefill(form, action.prefill);
      return { ...next, notStarted: offeredPrefill(next) !== null };
    }
  }
}

export function firstSelectionReducer(form: FirstSelectionForm, action: FirstSelectionAction): FirstSelectionForm {
  const next = apply(form, action);
  // The "draft has not started" notice lasts only as long as there is an offer.
  return next.notStarted && offeredPrefill(next) === null ? { ...next, notStarted: false } : next;
}

// "Record winner and start" starts the draft unless, with the recorded result,
// there is an offer; then the analyst applies it or presses Start again.
export function afterRecordedWinner(form: FirstSelectionForm, prefill: TeamId | '') {
  const next = firstSelectionReducer(form, { type: 'recorded', prefill });
  return { form: next, startDraft: offeredPrefill(next) === null };
}

// A request carries holder and choice exactly as displayed.
export function requestFields(form: FirstSelectionForm) {
  return { first_selection_holder: form.holder || null, first_selection_choice: form.choice || null };
}
