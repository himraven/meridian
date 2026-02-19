import { api } from '$lib/api';
import type { SignalsConfluenceResponse } from '$lib/types/api';

export async function load() {
	try {
		const trending = await api.ranking.smartMoney({ min_score: 0, days: 30 }) as SignalsConfluenceResponse;
		return {
			trending: trending.data?.slice(0, 10) ?? [],
		};
	} catch (error) {
		console.error('Search page load error:', error);
		return {
			trending: [],
		};
	}
}
