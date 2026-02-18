import { api } from '$lib/api';
import type { InstitutionsFilingsResponse } from '$lib/types/api';

export async function load() {
	const data = await api.institutions.filings() as InstitutionsFilingsResponse;
	return { data };
}
