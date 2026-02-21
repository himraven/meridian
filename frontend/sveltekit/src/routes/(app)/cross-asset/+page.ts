import { api } from '$lib/api';

export async function load() {
	try {
		const data = await api.macro.crossAsset();
		return { data };
	} catch (error) {
		console.error('Cross-asset load error:', error);
		return {
			data: null,
			error: error instanceof Error ? error.message : 'Unknown error',
		};
	}
}
