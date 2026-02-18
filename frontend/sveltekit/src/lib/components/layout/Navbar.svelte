<script lang="ts">
	import { page } from '$app/stores';
	import { openPalette } from '$lib/stores/commandPalette';
	
	interface Props {
		onMobileMenuToggle: () => void;
	}
	
	let { onMobileMenuToggle }: Props = $props();

	let mobileMenuOpen = $state(false);

	function handleSearchClick() {
		openPalette();
	}

	function handleSearchKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' || e.key === ' ') {
			e.preventDefault();
			openPalette();
		}
	}

	function toggleMobileMenu() {
		mobileMenuOpen = !mobileMenuOpen;
		onMobileMenuToggle();
	}
</script>

<!-- Floating pill navbar — backdrop-blur only here -->
<nav class="navbar-floating z-40 sticky top-0">
	<div class="navbar-inner">
		<!-- Logo & Mobile Hamburger -->
		<div class="flex items-center gap-3">
			<button 
				class="md:hidden navbar-icon-btn"
				onclick={toggleMobileMenu}
				aria-label="Toggle menu"
			>
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 6h16M4 12h16M4 18h16"/>
				</svg>
			</button>
			
			<a href="/" class="navbar-logo">
				Meridian
			</a>
		</div>
		
		<!-- Search / Command Palette Trigger -->
		<div class="flex-1 max-w-sm">
			<!-- svelte-ignore a11y_interactive_supports_focus -->
			<div
				class="navbar-search"
				onclick={handleSearchClick}
				onkeydown={handleSearchKeydown}
				role="searchbox"
				aria-label="Open command palette"
				aria-haspopup="dialog"
				tabindex="0"
			>
				<svg 
					class="search-icon"
					fill="none" 
					stroke="currentColor" 
					viewBox="0 0 24 24"
				>
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
				</svg>
				<span class="search-placeholder">Search or navigate...</span>
				<kbd class="hidden sm:inline-flex search-kbd">⌘K</kbd>
			</div>
		</div>
		
		<!-- Desktop Nav Links -->
		<div class="hidden lg:flex items-center gap-1">
			<a 
				href="/" 
				class="nav-link {$page.url.pathname === '/' ? 'nav-link-active' : ''}"
			>
				Home
			</a>
			<a 
				href="/smart-money" 
				class="nav-link {$page.url.pathname.startsWith('/smart-money') || 
					 $page.url.pathname.startsWith('/congress') || 
					 $page.url.pathname.startsWith('/ark') ||
					 $page.url.pathname.startsWith('/darkpool') ||
					 $page.url.pathname.startsWith('/institutions') ||
					 $page.url.pathname.startsWith('/signals') ? 'nav-link-active' : ''}"
			>
				Markets
			</a>
			<a 
				href="/hk" 
				class="nav-link {$page.url.pathname.startsWith('/hk') || 
					 $page.url.pathname.startsWith('/cn') ? 'nav-link-active' : ''}"
			>
				Asia
			</a>
			<a 
				href="/research" 
				class="nav-link {$page.url.pathname.startsWith('/research') || 
					 $page.url.pathname.startsWith('/dividend') ? 'nav-link-active' : ''}"
			>
				Research
			</a>
		</div>
	</div>
</nav>

<style>
	/* Floating pill — ONLY element with backdrop-blur */
	.navbar-floating {
		margin: 12px 16px 0;
		background: rgba(24, 24, 27, 0.80); /* --bg-surface at 80% */
		backdrop-filter: blur(12px);
		-webkit-backdrop-filter: blur(12px);
		border: 1px solid var(--border-default);
		border-radius: 16px;
		height: 48px;
	}

	.navbar-inner {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 16px;
		padding: 0 16px;
		height: 100%;
	}

	.navbar-logo {
		font-family: 'Inter', -apple-system, system-ui, sans-serif;
		font-size: 15px;
		font-weight: 600;
		color: var(--text-primary);
		text-decoration: none;
		letter-spacing: -0.01em;
		flex-shrink: 0;
	}

	.navbar-icon-btn {
		color: var(--text-muted);
		background: none;
		border: none;
		cursor: pointer;
		padding: 4px;
		border-radius: 6px;
		transition: color 150ms;
		display: flex;
		align-items: center;
	}

	.navbar-icon-btn:hover {
		color: var(--text-primary);
	}

	/* Search trigger */
	.navbar-search {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 7px 12px;
		background: transparent;
		border: 1px solid var(--border-default);
		border-radius: 10px;
		cursor: pointer;
		transition: border-color 150ms;
	}

	.navbar-search:hover {
		border-color: var(--border-hover);
	}

	.search-icon {
		width: 15px;
		height: 15px;
		color: var(--text-muted);
		flex-shrink: 0;
	}

	.search-placeholder {
		flex: 1;
		font-size: 13px;
		color: var(--text-muted);
		user-select: none;
	}

	.search-kbd {
		font-family: 'JetBrains Mono', monospace;
		font-size: 11px;
		color: var(--text-dimmed);
		background: transparent;
		border: 1px solid var(--border-default);
		border-radius: 4px;
		padding: 1px 6px;
	}

	/* Nav links — text-only, no background pill */
	.nav-link {
		padding: 6px 10px;
		font-size: 13px;
		font-weight: 400;
		color: var(--text-muted);
		text-decoration: none;
		transition: color 150ms;
	}

	.nav-link:hover {
		color: var(--text-primary);
	}

	.nav-link-active {
		color: var(--text-primary) !important;
		font-weight: 500;
	}
</style>
