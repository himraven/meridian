import { api } from '$lib/api';

export async function load({ url }: { url: URL }) {
	const sort_by = url.searchParams.get('sort_by') || 'short_interest';
	const limit = Number(url.searchParams.get('limit')) || 50;
	const min_short_ratio = url.searchParams.get('min_short_ratio')
		? Number(url.searchParams.get('min_short_ratio'))
		: undefined;
	const min_days_to_cover = url.searchParams.get('min_days_to_cover')
		? Number(url.searchParams.get('min_days_to_cover'))
		: undefined;
	const ticker = url.searchParams.get('ticker') || undefined;

	try {
		const result = await api.shortInterest.list({ limit, sort_by, min_short_ratio, min_days_to_cover, ticker });
		return {
			data: result,
			filters: { sort_by, limit, min_short_ratio, min_days_to_cover, ticker },
			error: null
		};
	} catch (e) {
		return {
			data: null,
			filters: { sort_by, limit, min_short_ratio, min_days_to_cover, ticker },
			error: (e as Error).message
		};
	}
}
