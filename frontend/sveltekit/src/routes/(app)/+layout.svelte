<script lang="ts">
	import type { Snippet } from 'svelte';
	import '../../app.css';
	import Navbar from '$lib/components/layout/Navbar.svelte';
	import Sidebar from '$lib/components/layout/Sidebar.svelte';
	import MobileTabBar from '$lib/components/layout/MobileTabBar.svelte';
	import CommandPalette from '$lib/components/ui/CommandPalette.svelte';
	import { page } from '$app/stores';
	
	interface Props {
		children: Snippet;
	}
	
	let { children }: Props = $props();
	
	let sidebarOpen = $state(false);
	
	function toggleSidebar() {
		sidebarOpen = !sidebarOpen;
	}
	
	function closeSidebar() {
		sidebarOpen = false;
	}
	
	// Close sidebar on route change (mobile)
	$effect(() => {
		$page.url.pathname;
		if (window.innerWidth < 768) {
			sidebarOpen = false;
		}
	});
</script>

<svelte:head>
	<title>Meridian</title>
	<meta name="description" content="Smart money intelligence platform — where signals converge" />
</svelte:head>

<div class="min-h-screen flex flex-col bg-bg-base font-body">
	<!-- Floating Navbar -->
	<Navbar onMobileMenuToggle={toggleSidebar} />
	
	<div class="flex flex-1 overflow-hidden">
		<!-- Sidebar -->
		<Sidebar bind:open={sidebarOpen} onClose={closeSidebar} />
		
		<!-- Main content -->
		<main class="flex-1 overflow-y-auto scrollbar-thin pb-16 md:pb-0">
			<div class="max-w-7xl mx-auto px-4 py-6">
				{@render children()}
			</div>
		</main>
	</div>
	
	<!-- Mobile Bottom Tab Bar -->
	<MobileTabBar />
	
	<!-- Global Command Palette (⌘K) -->
	<CommandPalette />
</div>
