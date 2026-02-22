import { api } from '$lib/api';

export async function load() {
	const [overview, etfData, fearGreed, cryptoSignals] = await Promise.allSettled([
		api.crypto.overview(),
		api.macro.etfFlows({ category: 'crypto' }),
		api.crypto.fearGreed({ limit: 30 }),
		api.macro.cryptoSignals(),
	]);

	return {
		overview:      overview.status      === 'fulfilled' ? overview.value      : null,
		etfData:       etfData.status       === 'fulfilled' ? etfData.value       : null,
		fearGreed:     fearGreed.status     === 'fulfilled' ? fearGreed.value     : null,
		cryptoSignals: cryptoSignals.status === 'fulfilled' ? cryptoSignals.value : null,
		error: overview.status === 'rejected' ? (overview.reason?.message ?? 'Unknown error') : null,
	};
}
