import { api } from '$lib/api';
import { error } from '@sveltejs/kit';
import type { TickerDetailResponse } from '$lib/types/api';

export async function load({ params }) {
	try {
		const data = await api.ticker.detail(params.symbol.toUpperCase()) as TickerDetailResponse;
		return { data };
	} catch (err) {
		throw error(404, `Ticker ${params.symbol.toUpperCase()} not found`);
	}
}
