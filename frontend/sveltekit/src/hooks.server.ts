// ===================================================================
// Server Hooks — Meridian
// Proxies /api/* requests to FastAPI backend
// Security headers on all responses
// ===================================================================

import type { Handle } from '@sveltejs/kit';

const API_BACKEND = process.env.API_URL || 'http://localhost:8501';

export const handle: Handle = async ({ event, resolve }) => {
	if (event.url.pathname.startsWith('/api/')) {
		const apiUrl = `${API_BACKEND}${event.url.pathname}${event.url.search}`;
		
		try {
			const proxyHeaders = new Headers();
			proxyHeaders.set('Accept', 'application/json');
			if (event.request.method !== 'GET') {
				proxyHeaders.set('Content-Type', event.request.headers.get('Content-Type') || 'application/json');
			}

			const fetchOptions: RequestInit = {
				method: event.request.method,
				headers: proxyHeaders,
			};

			if (event.request.method !== 'GET' && event.request.method !== 'HEAD') {
				fetchOptions.body = await event.request.text();
			}

			const response = await fetch(apiUrl, fetchOptions);

			const body = await response.arrayBuffer();
			
			return new Response(body, {
				status: response.status,
				headers: {
					'Content-Type': response.headers.get('Content-Type') || 'application/json',
					'Cache-Control': response.headers.get('Cache-Control') || 'no-cache',
				},
			});
		} catch (err) {
			console.error(`API proxy error: ${apiUrl}`, err);
			return new Response(JSON.stringify({ error: 'API unavailable' }), {
				status: 502,
				headers: { 'Content-Type': 'application/json' },
			});
		}
	}

	const response = await resolve(event);
	
	if (response.headers.get('Content-Type')?.includes('text/html')) {
		response.headers.set('Cache-Control', 'no-cache, no-store, must-revalidate');
		response.headers.set('Pragma', 'no-cache');
	}

	// Security headers
	response.headers.set('X-Content-Type-Options', 'nosniff');
	response.headers.set('X-Frame-Options', 'DENY');
	response.headers.set('X-XSS-Protection', '1; mode=block');
	response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
	response.headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');
	response.headers.set('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
	
	return response;
};
