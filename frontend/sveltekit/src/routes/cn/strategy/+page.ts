import { api } from '$lib/api';
import type { 
	Cn8x30NavResponse,
	Cn8x30PortfolioResponse,
	Cn8x30MetricsResponse,
	Cn8x30SensitivityResponse
} from '$lib/types/api';

export async function load({ fetch }) {
	const [nav, portfolio, metrics, sensitivity] = await Promise.all([
		api.cn.strategy.nav() as Promise<Cn8x30NavResponse>,
		api.cn.strategy.portfolio() as Promise<Cn8x30PortfolioResponse>,
		api.cn.strategy.metrics() as Promise<Cn8x30MetricsResponse>,
		api.cn.strategy.sensitivity() as Promise<Cn8x30SensitivityResponse>
	]);

	return {
		nav,
		portfolio,
		metrics,
		sensitivity
	};
}
