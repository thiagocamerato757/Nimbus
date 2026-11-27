export class ApiError extends Error {
  constructor(public code: string) { super(code); }
}
export type Snapshot<T> = { data: T; version: string };
export async function requestSnapshot<T>(path: string, body?: unknown, version?: string): Promise<Snapshot<T>> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, {
      cache: 'no-store',
      ...(body === undefined ? {} : {
        method: 'POST', headers: {
          'Content-Type': 'application/json', 'X-Nimbus-App': '1',
          'X-Nimbus-Version': version ?? '',
        }, body: JSON.stringify(body),
      }),
    });
  } catch { throw new ApiError('network'); }
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new ApiError(data.detail?.code ?? (response.status === 422 ? 'formInvalid' : 'unexpected'));
  }
  return { data: await response.json() as T, version: response.headers.get('x-nimbus-version') ?? '' };
}
export async function request<T>(path: string): Promise<T> {
  return (await requestSnapshot<T>(path)).data;
}
