import { api } from '$lib/api';
import type { ArkTradesResponse, ArkHoldingsResponse } from '$lib/types/api';

export async function load() {
	const [trades, holdings] = await Promise.all([
		api.ark.trades({ days: 30 }) as Promise<ArkTradesResponse>,
		api.ark.holdings() as Promise<ArkHoldingsResponse>
	]);

	return { trades, holdings };
}
