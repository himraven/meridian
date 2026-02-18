<script lang="ts">
	import { page } from '$app/stores';
	
	interface Props {
		open: boolean;
		onClose: () => void;
	}
	
	let { open = $bindable(), onClose }: Props = $props();
	
	// Nav sections — no emoji, clean text labels only
	const navSections = [
		{
			title: 'US Markets',
			items: [
				{ href: '/smart-money', label: 'Overview' },
				{ href: '/congress', label: 'Congress' },
				{ href: '/ark', label: 'ARK Invest' },
				{ href: '/darkpool', label: 'Dark Pool' },
				{ href: '/institutions', label: 'Institutions' },
				{ href: '/signals', label: 'Signals' }
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
				{ href: '/dividend', label: 'Dividend' }
			]
		}
	];
	
	let expandedSections = $state<Record<string, boolean>>({
		'US Markets': true,
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
	
	<!-- Navigation -->
	<nav class="sidebar-nav">
		<!-- Dashboard top link -->
		<a 
			href="/" 
			class="sidebar-link {$page.url.pathname === '/' ? 'sidebar-link-active' : ''}"
			onclick={() => { if (window.innerWidth < 768) onClose(); }}
		>
			Home
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
		overflow-y: auto;
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
		padding: 12px 8px;
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.sidebar-section {
		margin-top: 8px;
	}

	.sidebar-section-header {
		width: 100%;
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 6px 10px;
		background: none;
		border: none;
		cursor: pointer;
		border-radius: 6px;
	}

	.sidebar-section-header:hover {
		background: var(--bg-elevated);
	}

	.sidebar-chevron {
		width: 12px;
		height: 12px;
		color: var(--text-dimmed);
		transition: transform 150ms;
		transform: rotate(-90deg);
	}

	.sidebar-chevron.expanded {
		transform: rotate(0deg);
	}

	.sidebar-items {
		margin-top: 2px;
		display: flex;
		flex-direction: column;
		gap: 1px;
	}

	.sidebar-link {
		display: block;
		padding: 7px 10px;
		font-size: 13px;
		color: var(--text-muted);
		text-decoration: none;
		border-radius: 6px;
		transition: color 150ms;
	}

	.sidebar-link:hover {
		color: var(--text-secondary);
		background: var(--bg-elevated);
	}

	.sidebar-link-active {
		color: var(--text-primary) !important;
		font-weight: 500;
	}
</style>
