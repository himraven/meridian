import { api } from '$lib/api';

export async function load() {
	try {
		const data = await api.crypto.derivatives();
		return { derivatives: data };
	} catch (e) {
		return { derivatives: null, error: (e as Error).message };
	}
}
