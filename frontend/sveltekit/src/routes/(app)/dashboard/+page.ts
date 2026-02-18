import { api } from '$lib/api';
import type { 
	HkSignalsResponse, 
	Cn8x30MetricsResponse,
} from '$lib/types/api';

export async function load() {
	try {
		const [hkSignals, cnMetrics, signals] = await Promise.all([
			api.hk.signals() as Promise<HkSignalsResponse>,
			api.cn.strategy.metrics() as Promise<Cn8x30MetricsResponse>,
			api.signals.smartMoney({ min_score: 0, days: 30 }),
		]);

		return {
			hkSignals,
			cnMetrics,
			signals,
		};
	} catch (error) {
		console.error('Dashboard load error:', error);
		return {
			hkSignals: null,
			cnMetrics: null,
			signals: null,
			error: error instanceof Error ? error.message : 'Unknown error'
		};
	}
}
