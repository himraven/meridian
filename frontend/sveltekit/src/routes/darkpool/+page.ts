import { api } from '$lib/api';
import type { DarkpoolAnalyticsResponse } from '$lib/types/api';

export async function load({ url }) {
	const days = parseInt(url.searchParams.get('days') || '7');
	const min_zscore = url.searchParams.get('min_zscore') || '';
	
	const data = await api.darkpool.analytics({ 
		days, 
		min_zscore: min_zscore ? parseFloat(min_zscore) : undefined 
	}) as DarkpoolAnalyticsResponse;

	return { data, filters: { days, min_zscore } };
}
