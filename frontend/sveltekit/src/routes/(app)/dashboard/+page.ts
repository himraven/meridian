import { api } from '$lib/api';
import type { FeedResponse, SignalsConfluenceResponse } from '$lib/types/api';

export async function load() {
	try {
		const [feed, signals] = await Promise.all([
			api.ranking.feed({ days: 3, limit: 15 }) as Promise<FeedResponse>,
			api.ranking.smartMoney({ min_score: 0, days: 30 }) as Promise<SignalsConfluenceResponse>,
		]);

		return {
			feed,
			signals,
		};
	} catch (error) {
		console.error('Dashboard load error:', error);
		return {
			feed: null,
			signals: null,
			error: error instanceof Error ? error.message : 'Unknown error'
		};
	}
}
