<script lang="ts">
	import type { PageData } from './$types';
	import type { KnowledgeArticleSummary } from './+page.ts';

	let { data }: { data: PageData } = $props();

	// Category filter state
	let activeCategory = $state('all');

	const categories = [
		{ id: 'all', label: 'All' },
		{ id: 'signal-guide', label: 'Signal Guides' },
		{ id: 'deep-dive', label: 'Deep Dives' },
		{ id: 'masters', label: 'Masters' },
	];

	// Filter articles by category
	const filtered = $derived(
		activeCategory === 'all'
			? data.articles
			: data.articles.filter((a) => a.category === activeCategory)
	);

	// Category labels (display)
	const categoryLabels: Record<string, string> = {
		'signal-guide': 'Signal Guide',
		'deep-dive': 'Deep Dive',
		'masters': 'Masters',
	};

	// Category badge colors
	const categoryColors: Record<string, string> = {
		'signal-guide': 'bg-[var(--blue)]/15 text-[var(--blue)] border-[var(--blue)]/20',
		'deep-dive': 'bg-purple-500/15 text-purple-400 border-purple-500/20',
		'masters': 'bg-[var(--amber)]/15 text-[var(--amber)] border-[var(--amber)]/20',
	};

	// Signal source colors (matching ranking page)
	const signalColors: Record<string, string> = {
		congress: 'text-[var(--amber)]',
		insiders: 'text-orange-400',
		ark: 'text-[var(--blue)]',
		institutions: 'text-[var(--green)]',
		darkpool: 'text-purple-400',
		short_interest: 'text-[var(--red)]',
		superinvestors: 'text-[var(--text-secondary)]',
	};
</script>

<svelte:head>
	<title>Knowledge Hub — Meridian</title>
	<meta name="description" content="Understand the signals behind smart money. Educational guides on congressional trading, insider buying, dark pools, and institutional flows." />
</svelte:head>

<div class="space-y-10">
	<!-- ── Hero ── -->
	<div class="pt-2 pb-2">
		<p class="text-[11px] font-mono uppercase tracking-wider text-[var(--text-muted)] mb-3">
			Research Library
		</p>
		<h1 class="text-[32px] font-bold tracking-tight text-[var(--text-primary)] leading-tight mb-3">
			Meridian Knowledge Hub
		</h1>
		<p class="text-lg text-[var(--text-secondary)] max-w-2xl leading-relaxed">
			Understand the signals behind smart money. Research-backed guides explaining
			why each data source has predictive power — and how Meridian uses it.
		</p>
	</div>

	<!-- ── Category Filter ── -->
	<div class="flex flex-wrap gap-2">
		{#each categories as cat}
			<button
				onclick={() => (activeCategory = cat.id)}
				class="px-4 py-1.5 rounded-full text-sm font-medium transition-all
					{activeCategory === cat.id
						? 'bg-[var(--text-primary)] text-[var(--bg-base)]'
						: 'bg-[var(--bg-surface)] border border-[var(--border-default)] text-[var(--text-muted)] hover:border-[var(--border-hover)] hover:text-[var(--text-secondary)]'}"
			>
				{cat.label}
			</button>
		{/each}
		<span class="ml-auto self-center text-sm text-[var(--text-dimmed)]">
			{filtered.length} article{filtered.length !== 1 ? 's' : ''}
		</span>
	</div>

	<!-- ── Article Grid ── -->
	{#if filtered.length > 0}
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
			{#each filtered as article}
				<a
					href="/knowledge/{article.slug}"
					class="group flex flex-col bg-[var(--bg-surface)] border border-[var(--border-default)]
						rounded-xl p-5 hover:border-[var(--border-hover)] transition-all duration-150"
				>
					<!-- Category badge -->
					<div class="flex items-center justify-between mb-4">
						<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wide border
							{categoryColors[article.category] ?? 'bg-[var(--bg-elevated)] text-[var(--text-muted)] border-[var(--border-default)]'}">
							{categoryLabels[article.category] ?? article.category}
						</span>
						{#if article.signal_source}
							<span class="text-[11px] font-mono font-semibold {signalColors[article.signal_source] ?? 'text-[var(--text-dimmed)]'}">
								{article.signal_source.toUpperCase()}
							</span>
						{/if}
					</div>

					<!-- Title -->
					<h2 class="text-[15px] font-semibold text-[var(--text-primary)] leading-snug mb-2
						group-hover:text-white transition-colors">
						{article.title}
					</h2>

					<!-- TLDR -->
					<p class="text-sm text-[var(--text-muted)] leading-relaxed flex-1 line-clamp-3 mb-4">
						{article.tldr}
					</p>

					<!-- Hero stat -->
					{#if article.hero_stat}
						<div class="mb-4 p-3 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-default)]">
							<div class="text-2xl font-black text-[var(--text-primary)] tracking-tight">
								{article.hero_stat.value}
							</div>
							<div class="text-[11px] text-[var(--text-muted)] mt-0.5 leading-tight">
								{article.hero_stat.label}
							</div>
						</div>
					{/if}

					<!-- Read link -->
					<div class="flex items-center justify-between pt-3 border-t border-[var(--border-default)]">
						<span class="text-xs text-[var(--text-dimmed)]">
							{article.updated_at}
						</span>
						<span class="flex items-center gap-1 text-sm font-medium text-[var(--text-muted)]
							group-hover:text-[var(--text-primary)] transition-colors">
							Read
							<svg class="w-4 h-4 group-hover:translate-x-0.5 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M9 5l7 7-7 7" />
							</svg>
						</span>
					</div>
				</a>
			{/each}
		</div>
	{:else}
		<div class="text-center py-20">
			<div class="text-4xl mb-4">📚</div>
			<h3 class="text-base font-medium text-[var(--text-primary)] mb-2">No articles yet</h3>
			<p class="text-sm text-[var(--text-muted)]">
				{activeCategory === 'all'
					? 'Knowledge Hub articles are being written.'
					: `No articles in the "${categories.find(c => c.id === activeCategory)?.label}" category yet.`}
			</p>
		</div>
	{/if}

	<!-- ── Footer note ── -->
	<div class="border-t border-[var(--border-default)] pt-6">
		<p class="text-xs text-[var(--text-dimmed)] text-center">
			All articles cite primary academic sources. Content is educational, not investment advice.
		</p>
	</div>
</div>

<style>
	.line-clamp-3 {
		display: -webkit-box;
		-webkit-line-clamp: 3;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
</style>
