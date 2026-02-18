import { api } from '$lib/api';
import type { CongressTradesResponse } from '$lib/types/api';

export async function load({ url }) {
	const days = parseInt(url.searchParams.get('days') || '30');
	const party = url.searchParams.get('party') || '';
	const chamber = url.searchParams.get('chamber') || '';
	const trade_type = url.searchParams.get('trade_type') || '';
	
	const data = await api.congress.trades({ 
		days, 
		party, 
		chamber, 
		trade_type 
	}) as CongressTradesResponse;

	return { data, filters: { days, party, chamber, trade_type } };
}
