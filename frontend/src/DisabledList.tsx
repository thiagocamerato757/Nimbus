import { useState } from 'react';
import { ApiError, requestSnapshot } from './api';
import { useLiveQuery } from './useLiveQuery';
import { errorText, t } from './i18n';
import type { Profile } from './types';

export function DisabledList({ profile, seriesId, onSaved }: {
  profile: Profile; seriesId?: string; onSaved: () => void;
}) {
  const path = seriesId ? `/series/${seriesId}/disabled` : `/workspace/disabled/${profile.id}`;
  const query = useLiveQuery<string[]>(path);
  const [edit, setEdit] = useState<{ ids: string[]; version: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const selected = edit?.ids ?? query.snapshot?.data ?? [];
  return <section className="panel" aria-label={t(seriesId ? 'seriesDisabled' : 'workspaceDisabled')}>
    <h2>{t(seriesId ? 'seriesDisabled' : 'workspaceDisabled')}</h2>
    {!seriesId && <p>{t('workspaceDisabledHint')}</p>}
    {(error || query.error) && <p role="alert">{errorText(error || query.error)}</p>}
    <form onSubmit={async event => {
      event.preventDefault();
      if (!edit) return;
      setBusy(true); setError('');
      try {
        await requestSnapshot(path, { character_ids: edit.ids }, edit.version);
        setEdit(null); await query.refresh(); onSaved();
      } catch (e) {
        setError(e instanceof ApiError ? e.code : 'unexpected');
        if (e instanceof ApiError && e.code === 'stale_version') {
          setEdit(null); await query.refresh();
        }
      } finally { setBusy(false); }
    }}>
      <label>{t('disabledCharacters')}<select multiple size={6} disabled={busy || !query.snapshot}
        value={selected} onChange={event => setEdit({
          ids: Array.from(event.target.selectedOptions, option => option.value),
          version: edit?.version ?? query.snapshot!.version,
        })}>
        {profile.catalog.filter(c => !c.retired || selected.includes(c.id)).map(c =>
          <option key={c.id} value={c.id}>{c.name}</option>)}
      </select></label>
      <button disabled={busy || !edit}>{t('saveDisabled')}</button>
      {edit && <button type="button" disabled={busy} onClick={() => setEdit(null)}>{t('cancelCorrection')}</button>}
    </form>
  </section>;
}
