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

  it('offers that there is no pre-fill any more', () => {
    expect(offeredPrefill(result(open(), ''))).toBe('');
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

  it('starts the draft when the recorded result offers nothing new', () => {
    expect(afterRecordedWinner(open(), 'B').startDraft).toBe(true);
    expect(afterRecordedWinner(open(''), '').startDraft).toBe(true);
    expect(afterRecordedWinner(holder(open(''), 'A'), 'A').startDraft).toBe(true);
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
