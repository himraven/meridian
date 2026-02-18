import { api } from '$lib/api';
import type { CnTrendResponse } from '$lib/types/api';

export async function load() {
	const trend = await api.cn.trend() as CnTrendResponse;

	return {
		trend
	};
}
