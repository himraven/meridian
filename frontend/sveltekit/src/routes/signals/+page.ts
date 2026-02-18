import { api } from '$lib/api';

export async function load({ url }) {
	const min_score = parseInt(url.searchParams.get('min_score') || '0');
	const source = url.searchParams.get('source') || '';
	const days = parseInt(url.searchParams.get('days') || '30');
	
	const data = await api.signals.smartMoney({ 
		min_score, 
		source: source || undefined,
		days,
	});

	return { data, filters: { min_score, source, days } };
}
