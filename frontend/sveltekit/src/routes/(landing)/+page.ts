import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
	try {
		const res = await fetch('/api/signals/smart-money?limit=5&min_score=60');
		if (!res.ok) throw new Error(`HTTP ${res.status}`);
		const signals = await res.json();
		return { signals: signals.data ?? [] };
	} catch {
		return { signals: [] };
	}
};
