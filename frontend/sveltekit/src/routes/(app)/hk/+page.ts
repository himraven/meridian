import { api } from '$lib/api';
import type { HkSignalsResponse } from '$lib/types/api';

export async function load() {
	const [signals, history] = await Promise.all([
		api.hk.signals() as Promise<HkSignalsResponse>,
		api.hk.history()
	]);

	return {
		signals,
		history
	};
}
