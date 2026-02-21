import { api } from '$lib/api';
import type { FeedResponse } from '$lib/types/api';

export async function load() {
	try {
		// Load "all" view with higher limit to include all sources
		const feed = await api.ranking.feed({ limit: 200, days: 30 }) as FeedResponse;
		return { feed };
	} catch (error) {
		console.error('Feed load error:', error);
		return {
			feed: null,
			error: error instanceof Error ? error.message : 'Unknown error'
		};
	}
}
