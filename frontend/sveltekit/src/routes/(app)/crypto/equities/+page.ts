import { api } from '$lib/api';

export async function load() {
	try {
		const [signals, etfFlows] = await Promise.allSettled([
			api.macro.cryptoSignals(),
			api.macro.etfFlows({ category: 'crypto' }),
		]);

		return {
			signals: signals.status === 'fulfilled' ? signals.value : null,
			etfFlows: etfFlows.status === 'fulfilled' ? etfFlows.value : null,
			error: signals.status === 'rejected'
				? (signals.reason instanceof Error ? signals.reason.message : 'Unknown error')
				: null,
		};
	} catch (error) {
		console.error('Crypto equities load error:', error);
		return {
			signals: null,
			etfFlows: null,
			error: error instanceof Error ? error.message : 'Unknown error',
		};
	}
}
