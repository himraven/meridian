import { api } from '$lib/api';

export async function load() {
	try {
		const data = await api.macro.cryptoSignals();
		return { data };
	} catch (error) {
		console.error('Crypto signals load error:', error);
		return {
			data: null,
			error: error instanceof Error ? error.message : 'Unknown error',
		};
	}
}
