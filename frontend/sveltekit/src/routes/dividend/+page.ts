import { api } from '$lib/api';
import type { DividendScreenerResponse } from '$lib/types/api';

export async function load({ fetch }) {
	const dividend = await api.dividend() as DividendScreenerResponse;

	return {
		dividend
	};
}
