<script lang="ts">
	import { page } from '$app/stores';

	const tabs = [
		{ label: 'Home', href: '/', icon: 'home' },
		{ label: 'Markets', href: '/smart-money', icon: 'markets' },
		{ label: 'Asia', href: '/hk', icon: 'asia' },
		{ label: 'Research', href: '/dividend', icon: 'research' }
	];

	function isActive(href: string, pathname: string): boolean {
		if (href === '/') return pathname === '/';
		if (href === '/hk') return pathname.startsWith('/hk') || pathname.startsWith('/cn');
		return pathname.startsWith(href);
	}
</script>

<nav class="mobile-tab-bar md:hidden">
	{#each tabs as tab}
		<a
			href={tab.href}
			class="tab-item"
			class:active={isActive(tab.href, $page.url.pathname)}
		>
			<svg class="tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
				{#if tab.icon === 'home'}
					<path d="M3 9.5L12 3l9 6.5V20a1 1 0 01-1 1H4a1 1 0 01-1-1V9.5z" />
					<polyline points="9 22 9 12 15 12 15 22" />
				{:else if tab.icon === 'markets'}
					<polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
				{:else if tab.icon === 'asia'}
					<circle cx="12" cy="12" r="10" />
					<path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20" />
					<path d="M2 12h20" />
				{:else if tab.icon === 'research'}
					<circle cx="11" cy="11" r="8" />
					<line x1="21" y1="21" x2="16.65" y2="16.65" />
					<line x1="8" y1="11" x2="14" y2="11" />
					<line x1="11" y1="8" x2="11" y2="14" />
				{/if}
			</svg>
			<span class="tab-label">{tab.label}</span>
		</a>
	{/each}
</nav>

<style>
	.mobile-tab-bar {
		position: fixed;
		bottom: 0;
		left: 0;
		right: 0;
		z-index: 50;
		display: flex;
		align-items: center;
		justify-content: space-around;
		height: calc(56px + env(safe-area-inset-bottom, 0px));
		padding-bottom: env(safe-area-inset-bottom, 0px);
		background: var(--bg-surface);
		border-top: 1px solid var(--border-default);
		backdrop-filter: blur(12px);
		-webkit-backdrop-filter: blur(12px);
	}

	.tab-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2px;
		flex: 1;
		height: 56px;
		text-decoration: none;
		color: var(--text-muted);
		transition: color 150ms ease;
		-webkit-tap-highlight-color: transparent;
	}

	.tab-item:hover {
		color: var(--text-secondary);
	}

	.tab-item.active {
		color: var(--text-primary);
	}

	.tab-icon {
		width: 22px;
		height: 22px;
	}

	.tab-label {
		font-size: 10px;
		font-weight: 500;
		line-height: 1;
		letter-spacing: 0.01em;
	}
</style>
