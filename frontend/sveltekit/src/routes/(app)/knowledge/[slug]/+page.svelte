<script lang="ts">
	import { marked } from 'marked';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	const article = $derived(data.article);

	// Render markdown
	const htmlContent = $derived(() => {
		if (!article?.content_md) return '';
		const result = marked(article.content_md, { breaks: true, gfm: true });
		return typeof result === 'string' ? result : '';
	});

	// Auto-generate table of contents from h2 headings in content_md
	const toc = $derived(() => {
		if (!article?.content_md) return [];
		const headings: { id: string; label: string }[] = [];
		const lines = article.content_md.split('\n');
		for (const line of lines) {
			const match = line.match(/^## (.+)$/);
			if (match) {
				const label = match[1].trim();
				const id = label.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
				headings.push({ id, label });
			}
		}
		return headings;
	});

	// Inject anchor ids into rendered HTML
	const htmlWithAnchors = $derived(() => {
		let html = htmlContent();
		// Add ids to h2 elements
		html = html.replace(/<h2>(.*?)<\/h2>/g, (_, content) => {
			const id = content.toLowerCase().replace(/<[^>]+>/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
			return `<h2 id="${id}">${content}</h2>`;
		});
		return html;
	});

	// Category display
	const categoryLabels: Record<string, string> = {
		'signal-guide': 'Signal Guide',
		'deep-dive': 'Deep Dive',
		'masters': 'Masters',
	};

	const categoryColors: Record<string, string> = {
		'signal-guide': 'bg-[var(--blue)]/15 text-[var(--blue)] border-[var(--blue)]/20',
		'deep-dive': 'bg-purple-500/15 text-purple-400 border-purple-500/20',
		'masters': 'bg-[var(--amber)]/15 text-[var(--amber)] border-[var(--amber)]/20',
	};
</script>

<svelte:head>
	{#if article}
		<title>{article.title} — Meridian Knowledge Hub</title>
		<meta name="description" content={article.seo?.description ?? article.tldr} />
		{#if article.seo?.keywords?.length}
			<meta name="keywords" content={article.seo.keywords.join(', ')} />
		{/if}
		<!-- Open Graph -->
		<meta property="og:title" content={article.title} />
		<meta property="og:description" content={article.seo?.description ?? article.tldr} />
		<meta property="og:type" content="article" />
	{/if}
</svelte:head>

{#if article}
<div class="max-w-5xl mx-auto">
	<!-- ── Breadcrumb ── -->
	<div class="flex items-center gap-2 text-sm text-[var(--text-muted)] mb-6">
		<a href="/knowledge" class="hover:text-[var(--text-secondary)] transition-colors">Knowledge Hub</a>
		<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
		</svg>
		<span class="text-[var(--text-dimmed)] truncate">{article.title}</span>
	</div>

	<div class="lg:grid lg:grid-cols-[1fr_260px] lg:gap-10">
		<!-- ── Main column ── -->
		<div>
			<!-- Article hero -->
			<div class="mb-8">
				<!-- Category badge -->
				<div class="flex items-center gap-3 mb-4">
					<span class="px-2.5 py-1 rounded-full text-[10px] font-semibold uppercase tracking-wide border
						{categoryColors[article.category] ?? 'bg-[var(--bg-elevated)] text-[var(--text-muted)] border-[var(--border-default)]'}">
						{categoryLabels[article.category] ?? article.category}
					</span>
					<span class="text-xs text-[var(--text-dimmed)]">Updated {article.updated_at}</span>
				</div>

				<!-- Title + subtitle -->
				<h1 class="text-[28px] font-bold text-[var(--text-primary)] leading-tight tracking-tight mb-3">
					{article.title}
				</h1>
				<p class="text-lg text-[var(--text-secondary)] leading-relaxed mb-6">
					{article.subtitle}
				</p>

				<!-- Hero stat (big feature number) -->
				{#if article.hero_stat}
					<div class="flex items-start gap-4 p-5 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-default)]">
						<div>
							<div class="text-5xl font-black text-[var(--text-primary)] tracking-tighter leading-none mb-1">
								{article.hero_stat.value}
							</div>
							<div class="text-sm text-[var(--text-secondary)] font-medium mb-1">
								{article.hero_stat.label}
							</div>
							<div class="text-[11px] text-[var(--text-dimmed)]">
								Source: {article.hero_stat.source}
							</div>
						</div>
					</div>
				{/if}
			</div>

			<!-- TLDR -->
			<div class="mb-8 p-4 rounded-xl border-l-2 border-[var(--blue)] bg-[var(--blue)]/5">
				<p class="text-[11px] font-semibold uppercase tracking-wider text-[var(--blue)] mb-2">TL;DR</p>
				<p class="text-sm text-[var(--text-secondary)] leading-relaxed">{article.tldr}</p>
			</div>

			<!-- Table of contents (mobile) — only on smaller screens -->
			{#if toc().length > 0}
				<div class="lg:hidden mb-8 p-4 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-default)]">
					<p class="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-3">
						Contents
					</p>
					<nav class="space-y-1.5">
						{#each toc() as item}
							<a
								href="#{item.id}"
								class="block text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors py-0.5"
							>
								{item.label}
							</a>
						{/each}
					</nav>
				</div>
			{/if}

			<!-- ── Article Content ── -->
			<div class="article-prose">
				{@html htmlWithAnchors()}
			</div>

			<!-- ── How Meridian Uses This Signal ── -->
			{#if article.signal_source}
				<div class="mt-10 p-5 rounded-xl bg-[var(--green)]/5 border border-[var(--green)]/20">
					<div class="flex items-center gap-2 mb-3">
						<span class="text-lg">📡</span>
						<h3 class="text-base font-semibold text-[var(--text-primary)]">
							How Meridian Tracks <span class="text-[var(--green)]">{article.signal_source}</span>
						</h3>
					</div>
					<p class="text-sm text-[var(--text-secondary)] mb-3">
						This signal is live in Meridian's multi-source conviction engine.
					</p>
					<a
						href="/{article.signal_source === 'insiders' ? 'insiders' : article.signal_source === 'congress' ? 'congress' : article.signal_source === 'ark' ? 'ark' : article.signal_source === 'institutions' ? 'institutions' : article.signal_source === 'darkpool' ? 'darkpool' : article.signal_source}"
						class="inline-flex items-center gap-1.5 text-sm font-medium text-[var(--green)] hover:underline"
					>
						View live {article.signal_source} signals
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M9 5l7 7-7 7" />
						</svg>
					</a>
				</div>
			{/if}

			<!-- ── Academic References ── -->
			{#if article.academic_references?.length}
				<div class="mt-10">
					<h3 class="text-base font-semibold text-[var(--text-primary)] mb-4">
						Academic References
					</h3>
					<div class="space-y-3">
						{#each article.academic_references as ref}
							<div class="p-4 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-default)]">
								<p class="text-sm font-medium text-[var(--text-primary)] mb-1">
									{ref.title}
								</p>
								<p class="text-xs text-[var(--text-muted)] mb-2">
									<span class="italic">{ref.journal}</span>, {ref.year}
								</p>
								<p class="text-xs text-[var(--text-secondary)] flex items-start gap-1.5">
									<span class="text-[var(--green)] flex-shrink-0 mt-0.5">→</span>
									{ref.key_finding}
								</p>
							</div>
						{/each}
					</div>
				</div>
			{/if}

			<!-- ── Related Articles ── -->
			{#if article.related_articles?.length}
				<div class="mt-10">
					<h3 class="text-base font-semibold text-[var(--text-primary)] mb-4">
						Related Articles
					</h3>
					<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
						{#each article.related_articles as relatedSlug}
							<a
								href="/knowledge/{relatedSlug}"
								class="flex items-center gap-3 p-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-default)]
									hover:border-[var(--border-hover)] transition-colors group"
							>
								<span class="text-xl">📄</span>
								<div class="flex-1 min-w-0">
									<p class="text-sm font-medium text-[var(--text-secondary)] group-hover:text-[var(--text-primary)] transition-colors truncate">
										{relatedSlug.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
									</p>
								</div>
								<svg class="w-4 h-4 text-[var(--text-dimmed)] group-hover:text-[var(--text-muted)] flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M9 5l7 7-7 7" />
								</svg>
							</a>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Back link -->
			<div class="mt-12 pt-6 border-t border-[var(--border-default)]">
				<a
					href="/knowledge"
					class="inline-flex items-center gap-2 text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M15 19l-7-7 7-7" />
					</svg>
					Back to Knowledge Hub
				</a>
			</div>
		</div>

		<!-- ── Sidebar (desktop) ── -->
		<aside class="hidden lg:block">
			<div class="sticky top-24 space-y-6">

				<!-- Table of contents -->
				{#if toc().length > 0}
					<div class="p-4 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-default)]">
						<p class="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-3">
							Contents
						</p>
						<nav class="space-y-1">
							{#each toc() as item}
								<a
									href="#{item.id}"
									class="block text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors py-1 leading-tight"
								>
									{item.label}
								</a>
							{/each}
						</nav>
					</div>
				{/if}

				<!-- Key takeaways -->
				{#if article.key_takeaways?.length}
					<div class="p-4 rounded-xl bg-[var(--amber)]/5 border border-[var(--amber)]/20">
						<p class="text-[11px] font-semibold uppercase tracking-wider text-[var(--amber)] mb-3">
							Key Takeaways
						</p>
						<ul class="space-y-2">
							{#each article.key_takeaways as point}
								<li class="flex items-start gap-2 text-sm text-[var(--text-secondary)]">
									<span class="text-[var(--amber)] flex-shrink-0 mt-0.5 font-bold">·</span>
									{point}
								</li>
							{/each}
						</ul>
					</div>
				{/if}

				<!-- CTA to live signal -->
				{#if article.signal_source}
					<div class="p-4 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-default)]">
						<p class="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-3">
							Live Signals
						</p>
						<p class="text-xs text-[var(--text-dimmed)] mb-3">
							See this signal in action in the Meridian dashboard.
						</p>
						<a
							href="/ranking"
							class="block text-center px-3 py-2 bg-[var(--bg-elevated)] hover:bg-[var(--border-default)]
								border border-[var(--border-default)] rounded-lg text-sm text-[var(--text-secondary)]
								hover:text-[var(--text-primary)] transition-colors"
						>
							View Ranking →
						</a>
					</div>
				{/if}
			</div>
		</aside>
	</div>
</div>
{/if}

<style>
	/* Article body prose styles */
	:global(.article-prose) {
		color: var(--text-secondary);
		font-size: 15px;
		line-height: 1.75;
		max-width: 72ch;
	}

	:global(.article-prose h2) {
		font-size: 20px;
		font-weight: 700;
		color: var(--text-primary);
		letter-spacing: -0.01em;
		margin: 2rem 0 1rem;
		padding-bottom: 0.5rem;
		border-bottom: 1px solid var(--border-default);
		scroll-margin-top: 80px;
	}

	:global(.article-prose h3) {
		font-size: 16px;
		font-weight: 600;
		color: var(--text-primary);
		margin: 1.5rem 0 0.75rem;
	}

	:global(.article-prose p) {
		margin: 0 0 1rem;
	}

	:global(.article-prose ul),
	:global(.article-prose ol) {
		padding-left: 1.5rem;
		margin: 0 0 1rem;
	}

	:global(.article-prose li) {
		margin-bottom: 0.4rem;
	}

	:global(.article-prose strong) {
		font-weight: 600;
		color: var(--text-primary);
	}

	:global(.article-prose em) {
		color: var(--text-muted);
		font-style: italic;
	}

	:global(.article-prose blockquote) {
		border-left: 3px solid var(--border-hover);
		padding: 0.5rem 1rem;
		margin: 1.25rem 0;
		color: var(--text-muted);
		background: var(--bg-elevated);
		border-radius: 0 6px 6px 0;
	}

	:global(.article-prose code) {
		font-family: 'JetBrains Mono', monospace;
		font-size: 13px;
		background: var(--bg-elevated);
		border: 1px solid var(--border-default);
		padding: 1px 6px;
		border-radius: 4px;
		color: var(--text-primary);
	}

	:global(.article-prose hr) {
		border: none;
		border-top: 1px solid var(--border-default);
		margin: 2rem 0;
	}

	:global(.article-prose a) {
		color: var(--blue);
		text-decoration: none;
	}

	:global(.article-prose a:hover) {
		text-decoration: underline;
	}
</style>
