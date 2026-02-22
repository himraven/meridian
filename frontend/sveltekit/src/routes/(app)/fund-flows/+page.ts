import { api } from '$lib/api';

export async function load() {
	try {
		const flows = await api.macro.etfFlows();
		return { flows, error: null };
	} catch (error) {
		console.error('Fund flows load error:', error);
		return {
			flows: null,
			error: error instanceof Error ? error.message : 'Unknown error',
		};
	}
}
