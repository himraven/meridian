import { api } from '$lib/api';

export async function load() {
	try {
		const [overview, etfData] = await Promise.all([
			api.crypto.overview(),
			api.macro.etfFlows({ category: 'crypto' }),
		]);
		return { overview, etfData, error: null };
	} catch (e) {
		console.error('Crypto overview load error:', e);
		return { overview: null, etfData: null, error: (e as Error).message };
	}
}
