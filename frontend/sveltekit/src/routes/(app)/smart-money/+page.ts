import { api } from '$lib/api';
import type { 
	SignalsConfluenceResponse,
	CongressTradesResponse,
	ArkHoldingsResponse,
	DarkpoolAnalyticsResponse,
	InstitutionsFilingsResponse
} from '$lib/types/api';

export async function load({ fetch }) {
	const [signals, congress, ark, darkpool, institutions] = await Promise.all([
		api.ranking.confluence({ min_score: 0 }) as Promise<SignalsConfluenceResponse>,
		api.congress.trades({ days: 30 }) as Promise<CongressTradesResponse>,
		api.ark.holdings() as Promise<ArkHoldingsResponse>,
		api.darkpool.analytics({ days: 7 }) as Promise<DarkpoolAnalyticsResponse>,
		api.institutions.filings() as Promise<InstitutionsFilingsResponse>
	]);

	return {
		signals,
		congress,
		ark,
		darkpool,
		institutions
	};
}
