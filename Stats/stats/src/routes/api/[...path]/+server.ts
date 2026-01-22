// src/routes/api/[...path]/+server.ts
import type { RequestHandler } from '@sveltejs/kit';
import axios, { type Method } from 'axios';

// const API_BASE = 'http://localhost:4286'; // your backend
const API_BASE = `http://$localhost:${process.env.PORT_AUTH}`;

async function proxy({ request, params, url, cookies }: Parameters<RequestHandler>[0]) {
	try {
		// join path segments if `[...path]`
		const path = Array.isArray(params.path) ? params.path.join('/') : params.path;
		const target = `${API_BASE}/${path}${url.search}`;

		const response = await axios.request({
			url: target,
			method: request.method as Method,
			headers: {
				...Object.fromEntries(request.headers),
				cookie: cookies.getAll().map(c => `${c.name}=${c.value}`).join('; ')
			},
			data: request.method !== 'GET' ? await request.json().catch(() => request.text()) : undefined
		});

		// forward cookies from backend
		const headers = new Headers({ 'Content-Type': 'application/json' });
		if (response.headers['set-cookie']) {
			const cookies = Array.isArray(response.headers['set-cookie'])
				? response.headers['set-cookie']
				: [response.headers['set-cookie']];
			cookies.forEach(cookie => headers.append('set-cookie', cookie));
		}

		return new Response(JSON.stringify(response.data), {
			status: response.status,
			headers
		});
	} catch (err: unknown) {
			let message = 'Unknown error';
			let status = 500;

			// ✅ narrow error type
			if (axios.isAxiosError(err)) {
				message = err.message;
				status = err.response?.status ?? 500;
			} else if (err instanceof Error) {
				message = err.message;
			}

			return new Response(JSON.stringify({ error: message }), {
				status,
				headers: { 'Content-Type': 'application/json' }
			});
		}
}

export const GET: RequestHandler = (event) => proxy(event);
export const POST: RequestHandler = (event) => proxy(event);
export const PUT: RequestHandler = (event) => proxy(event);
export const PATCH: RequestHandler = (event) => proxy(event);
export const DELETE: RequestHandler = (event) => proxy(event);
export const OPTIONS: RequestHandler = (event) => proxy(event);
