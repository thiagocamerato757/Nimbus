export class ApiError extends Error {
  constructor(public code: string) { super(code); }
}
export async function request<T>(path: string, body?: unknown): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, body === undefined ? undefined : {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
    });
  } catch { throw new ApiError('network'); }
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new ApiError(data.detail?.code ?? (response.status === 422 ? 'formInvalid' : 'unexpected'));
  }
  return response.json() as Promise<T>;
}
