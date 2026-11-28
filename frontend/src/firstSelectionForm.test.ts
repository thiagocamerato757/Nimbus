import { describe, expect, it } from 'vitest';
import {
  afterRecordedWinner, closedForm, firstSelectionReducer as reduce, offeredPrefill, requestFields,
  type FirstSelectionForm,
} from './firstSelectionForm';

// BS-012 / #14 (amended 2026-11-28): only the analyst's own change or Apply
// moves the holder in an open setup or Replay form.
const open = (prefill: 'A' | 'B' | '' = 'B') =>
  reduce(closedForm, { type: 'sync', key: 'game', prefill });
const result = (form: FirstSelectionForm, prefill: 'A' | 'B' | '') =>
  reduce(form, { type: 'sync', key: form.key, prefill });
const holder = (form: FirstSelectionForm, value: 'A' | 'B' | '') =>
  reduce(form, { type: 'holder', holder: value });
const choose = (form: FirstSelectionForm) => reduce(form, { type: 'choice', choice: 'side' });

describe('opening a form', () => {
  it('takes the First Selection pre-fill once, with no choice and no offer', () => {
    expect(open()).toMatchObject({ holder: 'B', choice: '' });
    expect(offeredPrefill(open())).toBeNull();
  });

  it('starts again for another form and empties when closed', () => {
    const edited = choose(holder(open(), 'A'));
    expect(reduce(edited, { type: 'sync', key: 'next', prefill: '' })).toMatchObject({ key: 'next', holder: '', choice: '' });
    expect(reduce(edited, { type: 'sync', key: '', prefill: 'A' })).toBe(closedForm);
  });

  it('keeps the same state when nothing changed', () => {
    const form = open();
    expect(result(form, 'B')).toBe(form);
    expect(reduce(closedForm, { type: 'sync', key: '', prefill: '' })).toBe(closedForm);
  });
});

describe('holder changed by the analyst', () => {
  it('clears the choice', () => {
    expect(holder(choose(open()), 'A')).toMatchObject({ holder: 'A', choice: '' });
    expect(holder(choose(open()), '')).toMatchObject({ holder: '', choice: '' });
  });

  it('keeps the choice when the same holder is selected', () => {
    expect(holder(choose(open()), 'B')).toMatchObject({ holder: 'B', choice: 'side' });
  });

  it('allows no choice without a holder', () => {
    expect(choose(open('')).choice).toBe('');
  });
});

describe('result changes while the form is open', () => {
  it('offers the new pre-fill and changes no field', () => {
    const form = result(choose(open()), 'A');
    expect(form).toMatchObject({ holder: 'B', choice: 'side' });
    expect(offeredPrefill(form)).toBe('A');
  });

  it('offers nothing when the result no longer gives a pre-fill', () => {
    expect(offeredPrefill(result(open(), ''))).toBeNull();
  });

  it('withdraws the offer when the result returns, or the holder already matches', () => {
    expect(offeredPrefill(result(result(open(), 'A'), 'B'))).toBeNull();
    expect(offeredPrefill(holder(result(open(), 'A'), 'A'))).toBeNull();
  });
});

describe('Apply', () => {
  it('updates the holder, clears the choice and closes the offer', () => {
    const form = reduce(result(choose(open()), 'A'), { type: 'apply' });
    expect(form).toMatchObject({ holder: 'A', choice: '' });
    expect(offeredPrefill(form)).toBeNull();
  });

  it('does nothing without an offer', () => {
    const form = choose(open());
    expect(reduce(form, { type: 'apply' })).toBe(form);
  });
});

describe('Record winner and start', () => {
  it('does not start the draft when the pre-fill differs, and offers it', () => {
    const { form, startDraft } = afterRecordedWinner(choose(open()), 'A');
    expect(startDraft).toBe(false);
    expect(form).toMatchObject({ holder: 'B', choice: 'side' });
    expect(offeredPrefill(form)).toBe('A');
  });

  it('also stops after an earlier Apply', () => {
    const applied = reduce(result(open(), 'A'), { type: 'apply' });
    expect(afterRecordedWinner(applied, 'B').startDraft).toBe(false);
  });

});

// The whole start rule (docs/spec/mvp.md, amended 2026-11-28): "different" means
// different from the holder shown, not from the pre-fill the form last took.
describe('Record winner and start: the start rule', () => {
  it('starts when the new pre-fill matches the holder shown', () => {
    expect(afterRecordedWinner(open('B'), 'B').startDraft).toBe(true);
    expect(afterRecordedWinner(holder(open(''), 'A'), 'A').startDraft).toBe(true);
    expect(afterRecordedWinner(holder(open('B'), 'A'), 'A').startDraft).toBe(true);
  });

  it('stops and offers whenever it names another Team than the holder shown', () => {
    for (const form of [open(''), holder(open(''), 'A'), holder(open('B'), 'A'), holder(open('B'), '')]) {
      const after = afterRecordedWinner(form, 'B');
      expect(after.startDraft).toBe(false);
      expect(after.form).toMatchObject({ holder: form.holder, choice: form.choice });
      expect(offeredPrefill(after.form)).toBe('B');
    }
  });

  it('keeps that offer when the live refresh had already delivered the result', () => {
    const refreshed = result(choose(holder(open('B'), 'A')), 'B');
    const after = afterRecordedWinner(refreshed, 'B');
    expect(after.startDraft).toBe(false);
    expect(offeredPrefill(after.form)).toBe('B');
    expect(reduce(after.form, { type: 'apply' })).toMatchObject({ holder: 'B', choice: '' });
  });

  it('starts when the result gives no pre-fill, whatever is shown', () => {
    expect(afterRecordedWinner(holder(open('B'), 'A'), '').startDraft).toBe(true);
    expect(afterRecordedWinner(open('B'), '').startDraft).toBe(true);
    expect(afterRecordedWinner(open(''), '').startDraft).toBe(true);
  });
});

describe('request fields', () => {
  it('always carry holder and choice exactly as displayed', () => {
    expect(requestFields(open(''))).toEqual({ first_selection_holder: null, first_selection_choice: null });
    expect(requestFields(open())).toEqual({ first_selection_holder: 'B', first_selection_choice: null });
    expect(requestFields(choose(open()))).toEqual({ first_selection_holder: 'B', first_selection_choice: 'side' });
    expect(requestFields(result(choose(open()), 'A'))).toEqual({ first_selection_holder: 'B', first_selection_choice: 'side' });
  });
});

// docs/spec/mvp.md (amended 2026-11-28): the offer is derived from the current
// pre-fill and the holder shown; nothing remembers what was "already taken".
describe('derived offer', () => {
  it('offers a corrected pre-fill after the offered Team was picked by hand', () => {
    const stopped = afterRecordedWinner(holder(open(''), 'A'), 'B').form;
    expect(offeredPrefill(stopped)).toBe('B');
    const picked = holder(stopped, 'B');
    expect(offeredPrefill(picked)).toBeNull();
    const corrected = result(picked, 'A');
    expect(corrected.holder).toBe('B');
    expect(offeredPrefill(corrected)).toBe('A');
    expect(afterRecordedWinner(corrected, 'A').startDraft).toBe(false);
  });

  it('clears the offer and the notice when the offered Team is selected by hand', () => {
    const stopped = afterRecordedWinner(open(''), 'B').form;
    expect(stopped.notStarted).toBe(true);
    const picked = holder(stopped, 'B');
    expect(offeredPrefill(picked)).toBeNull();
    expect(picked.notStarted).toBe(false);
    // The offer is derived again; the old notice does not come back with it.
    const away = holder(picked, 'A');
    expect(offeredPrefill(away)).toBe('B');
    expect(away.notStarted).toBe(false);
  });

  it('is shown exactly when the current pre-fill names another Team', () => {
    for (const prefill of ['A', 'B', ''] as const) {
      for (const shown of ['A', 'B', ''] as const) {
        const form = holder(result(open(''), prefill), shown);
        expect(offeredPrefill(form)).toBe(prefill !== '' && prefill !== shown ? prefill : null);
      }
    }
  });
});
