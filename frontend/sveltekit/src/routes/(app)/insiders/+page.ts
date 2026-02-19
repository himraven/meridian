import { api } from '$lib/api';
import type { InsiderTradesResponse } from '$lib/types/api';

export async function load({ url }) {
	const days = parseInt(url.searchParams.get('days') || '30');
	const transaction_type = url.searchParams.get('transaction_type') || '';
	const cluster_only = url.searchParams.get('cluster_only') === 'true';
	const min_value = parseInt(url.searchParams.get('min_value') || '0');

	const data = await api.insiders.trades({
		days,
		transaction_type: transaction_type || undefined,
		cluster_only: cluster_only || undefined,
		min_value: min_value || undefined,
	}) as InsiderTradesResponse;

	return { data, filters: { days, transaction_type, cluster_only, min_value } };
}
