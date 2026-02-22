import { api } from '$lib/api';

export async function load() {
	try {
		const regime = await api.macro.regime();
		return { regime };
	} catch {
		return { regime: null };
	}
}
