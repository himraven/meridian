import { api } from '$lib/api';

export async function load() {
	try {
		const [data, etfFlows] = await Promise.allSettled([
			api.macro.cryptoSignals(),
			api.macro.etfFlows({ category: 'crypto' }),
		]);

		return {
			data: data.status === 'fulfilled' ? data.value : null,
			etfFlows: etfFlows.status === 'fulfilled' ? etfFlows.value : null,
			error: data.status === 'rejected'
				? (data.reason instanceof Error ? data.reason.message : 'Unknown error')
				: null,
		};
	} catch (error) {
		console.error('Crypto signals load error:', error);
		return {
			data: null,
			etfFlows: null,
			error: error instanceof Error ? error.message : 'Unknown error',
		};
	}
}
