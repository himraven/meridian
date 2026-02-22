import { api } from '$lib/api';

export async function load({ fetch }: { fetch: typeof globalThis.fetch }) {
	try {
		const data = await api.macro.etfFlows({ category: 'crypto' });
		return { etfData: data, error: null };
	} catch (e) {
		console.error('Crypto ETF load error:', e);
		return { etfData: null, error: (e as Error).message };
	}
}
