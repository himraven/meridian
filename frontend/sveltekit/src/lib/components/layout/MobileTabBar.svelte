<script lang="ts">
	import { page } from '$app/stores';

	const tabs = [
		{ label: 'Home', href: '/dashboard', icon: 'home' },
		{ label: 'Feed', href: '/feed', icon: 'feed' },
		{ label: 'Ranking', href: '/ranking', icon: 'ranking' },
		{ label: 'Search', href: '/search', icon: 'search' },
	];

	function isActive(href: string, pathname: string): boolean {
		if (href === '/dashboard') return pathname === '/' || pathname === '/dashboard';
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
				{:else if tab.icon === 'feed'}
					<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
				{:else if tab.icon === 'ranking'}
					<rect x="3" y="12" width="4" height="9" rx="1" />
					<rect x="10" y="7" width="4" height="14" rx="1" />
					<rect x="17" y="3" width="4" height="18" rx="1" />
				{:else if tab.icon === 'search'}
					<circle cx="11" cy="11" r="8" />
					<line x1="21" y1="21" x2="16.65" y2="16.65" />
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
