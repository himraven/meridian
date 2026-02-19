import { api } from '$lib/api';

export async function load() {
	const data = await api.knowledge.list() as {
		articles: KnowledgeArticleSummary[];
		count: number;
	};
	return { articles: data.articles ?? [], count: data.count ?? 0 };
}

export interface KnowledgeArticleSummary {
	slug: string;
	title: string;
	subtitle: string;
	category: string;
	signal_source: string;
	tldr: string;
	hero_stat: {
		value: string;
		label: string;
		source: string;
	} | null;
	key_takeaways: string[];
	updated_at: string;
}
