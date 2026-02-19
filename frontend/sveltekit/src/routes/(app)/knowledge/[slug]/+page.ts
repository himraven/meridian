import { api } from '$lib/api';
import { error } from '@sveltejs/kit';

export async function load({ params }) {
	try {
		const article = await api.knowledge.article(params.slug) as KnowledgeArticle;
		return { article };
	} catch (e: any) {
		if (e?.status === 404) {
			throw error(404, `Article not found: ${params.slug}`);
		}
		throw error(500, 'Failed to load article');
	}
}

export interface KnowledgeArticle {
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
	content_md: string;
	key_takeaways: string[];
	related_articles: string[];
	related_masters: string[];
	academic_references: {
		title: string;
		journal: string;
		year: number;
		key_finding: string;
	}[];
	seo: {
		keywords: string[];
		description: string;
	};
	social: {
		hook_zh: string;
		hook_en: string;
		hashtags: string[];
	};
	updated_at: string;
}
