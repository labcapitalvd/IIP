// src/lib/api/Fetcher.ts
type FetcherArgs<TBody> = {
	url: string;
	method?: string;
	data?: TBody;
	headers?: Record<string, string>;
	svelteEvent?: { fetch: typeof fetch }; // inject event.fetch for SSR
};

export async function Fetcher<TResponse, TBody = unknown>({
	url,
	method = 'GET',
	data,
	headers = {},
	svelteEvent
}: FetcherArgs<TBody>): Promise<TResponse> {
	const f = svelteEvent?.fetch ?? fetch;

	const response = await f(`/api${url}`, {
		method,
		headers: {
			'Content-Type': 'application/json',
			...headers
		},
		body: method !== 'GET' && data !== undefined ? JSON.stringify(data) : undefined
	});

	if (!response.ok) {
		throw new Error(`Fetcher failed: ${response.status}`);
	}
	return (await response.json()) as TResponse;
}
