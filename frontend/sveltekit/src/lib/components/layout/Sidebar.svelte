<script lang="ts">
	import { page } from '$app/stores';
	import DataHealthIndicator from './DataHealthIndicator.svelte';
	
	interface Props {
		open: boolean;
		onClose: () => void;
	}
	
	let { open = $bindable(), onClose }: Props = $props();
	
	// Nav sections — no emoji, clean text labels only
	const navSections = [
		{
			title: 'Sources',
			items: [
				{ href: '/smart-money', label: 'Overview' },
				{ href: '/congress', label: 'Congress' },
				{ href: '/ark', label: 'ARK Invest' },
				{ href: '/darkpool', label: 'Dark Pool' },
				{ href: '/institutions', label: 'Institutions' },
				{ href: '/insiders', label: 'Insiders' },
			]
		},
		{
			title: 'Asia Markets',
			items: [
				{ href: '/hk', label: 'HK Signals' },
				{ href: '/cn', label: 'CN Trend' },
				{ href: '/cn/strategy', label: 'CN Strategy' }
			]
		},
		{
			title: 'Research',
			items: [
				{ href: '/research', label: 'Reports' },
				{ href: '/dividend', label: 'Dividend' },
				{ href: '/knowledge', label: 'Knowledge Hub' }
			]
		}
	];
	
	let expandedSections = $state<Record<string, boolean>>({
		'Sources': true,
		'Asia Markets': true,
		'Research': true
	});
	
	function toggleSection(title: string) {
		expandedSections[title] = !expandedSections[title];
	}
	
	function isActive(href: string): boolean {
		return $page.url.pathname === href || 
			($page.url.pathname !== '/' && $page.url.pathname.startsWith(href));
	}
</script>

<!-- Mobile backdrop -->
{#if open}
	<button 
		class="fixed inset-0 bg-black/60 z-30 md:hidden"
		onclick={onClose}
		aria-label="Close menu"
	></button>
{/if}

<!-- Sidebar -->
<aside 
	class="sidebar {open ? 'sidebar-open' : ''}"
>
	<!-- Mobile close button -->
	<div class="sidebar-close-row md:hidden">
		<span class="sidebar-brand">Menu</span>
		<button onclick={onClose} class="sidebar-close-btn" aria-label="Close sidebar">
			<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M6 18L18 6M6 6l12 12" />
			</svg>
		</button>
	</div>
	
	<!-- Navigation + Health Indicator wrapper -->
	<nav class="sidebar-nav">
		<!-- Core navigation -->
		<a 
			href="/dashboard" 
			class="sidebar-link {$page.url.pathname === '/dashboard' || $page.url.pathname === '/' ? 'sidebar-link-active' : ''}"
			onclick={() => { if (window.innerWidth < 768) onClose(); }}
		>
			Dashboard
		</a>
		<a 
			href="/feed" 
			class="sidebar-link {$page.url.pathname === '/feed' ? 'sidebar-link-active' : ''}"
			onclick={() => { if (window.innerWidth < 768) onClose(); }}
		>
			Feed
		</a>
		<a 
			href="/ranking" 
			class="sidebar-link {$page.url.pathname.startsWith('/ranking') ? 'sidebar-link-active' : ''}"
			onclick={() => { if (window.innerWidth < 768) onClose(); }}
		>
			Ranking
		</a>
		<a 
			href="/search" 
			class="sidebar-link {$page.url.pathname === '/search' ? 'sidebar-link-active' : ''}"
			onclick={() => { if (window.innerWidth < 768) onClose(); }}
		>
			Search
		</a>
		
		<!-- Navigation sections -->
		{#each navSections as section}
			<div class="sidebar-section">
				<button 
					class="sidebar-section-header"
					onclick={() => toggleSection(section.title)}
				>
					<span class="text-label">{section.title}</span>
					<svg 
						class="sidebar-chevron {expandedSections[section.title] ? 'expanded' : ''}"
						fill="none" 
						stroke="currentColor" 
						viewBox="0 0 24 24"
					>
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 9l-7 7-7-7" />
					</svg>
				</button>
				
				{#if expandedSections[section.title]}
					<div class="sidebar-items">
						{#each section.items as item}
							<a 
								href={item.href}
								class="sidebar-link {isActive(item.href) ? 'sidebar-link-active' : ''}"
								onclick={() => { if (window.innerWidth < 768) onClose(); }}
							>
								{item.label}
							</a>
						{/each}
					</div>
				{/if}
			</div>
		{/each}
	</nav>

	<!-- Data health indicator — pinned to bottom -->
	<DataHealthIndicator />
</aside>

<style>
	.sidebar {
		position: fixed;
		top: 0;
		left: 0;
		height: 100vh;
		width: 220px;
		background: var(--bg-surface);
		border-right: 1px solid var(--border-default);
		z-index: 40;
		display: flex;
		flex-direction: column;
		transform: translateX(-100%);
		transition: transform 150ms ease;
	}

	@media (min-width: 768px) {
		.sidebar {
			position: sticky;
			transform: translateX(0);
			flex-shrink: 0;
		}
	}

	.sidebar-open {
		transform: translateX(0) !important;
	}

	.sidebar-close-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 14px 16px;
		border-bottom: 1px solid var(--border-default);
	}

	.sidebar-brand {
		font-size: 14px;
		font-weight: 600;
		color: var(--text-primary);
	}

	.sidebar-close-btn {
		color: var(--text-muted);
		background: none;
		border: none;
		cursor: pointer;
		padding: 4px;
		border-radius: 6px;
		display: flex;
		align-items: center;
		transition: color 150ms;
	}

	.sidebar-close-btn:hover {
		color: var(--text-primary);
	}

	.sidebar-nav {
		padding: 16px 10px;
		display: flex;
		flex-direction: column;
		gap: 2px;
		flex: 1;
		overflow-y: auto;
	}

	.sidebar-section {
		margin-top: 16px;
	}

	.sidebar-section:first-of-type {
		margin-top: 12px;
	}

	.sidebar-section-header {
		width: 100%;
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0 8px 6px;
		background: none;
		border: none;
		cursor: pointer;
		border-radius: 0;
	}

	/* Override the .text-label from global — make headers smaller, uppercase, distinct */
	.sidebar-section-header :global(.text-label) {
		font-size: 10px !important;
		font-weight: 600 !important;
		letter-spacing: 0.08em !important;
		text-transform: uppercase !important;
		color: var(--text-dimmed) !important;
	}

	.sidebar-section-header:hover :global(.text-label) {
		color: var(--text-muted) !important;
	}

	.sidebar-chevron {
		width: 10px;
		height: 10px;
		color: var(--text-dimmed);
		transition: transform 150ms;
		transform: rotate(-90deg);
		opacity: 0;
	}

	.sidebar-section-header:hover .sidebar-chevron {
		opacity: 1;
	}

	.sidebar-chevron.expanded {
		transform: rotate(0deg);
	}

	.sidebar-items {
		margin-top: 1px;
		display: flex;
		flex-direction: column;
		gap: 0;
		padding-left: 4px;
		border-left: 1px solid var(--border-default);
		margin-left: 10px;
	}

	.sidebar-link {
		display: block;
		padding: 6px 12px;
		font-size: 13px;
		color: var(--text-muted);
		text-decoration: none;
		border-radius: 5px;
		transition: color 120ms, background 120ms;
	}

	.sidebar-link:hover {
		color: var(--text-secondary);
		background: var(--bg-elevated);
	}

	.sidebar-link-active {
		color: var(--text-primary) !important;
		font-weight: 500;
		background: var(--bg-elevated);
	}
</style>
