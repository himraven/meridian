<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		children: Snippet;
	}

	let { children }: Props = $props();
</script>

<svelte:head>
	<title>Meridian — Where Smart Money Converges</title>
	<meta name="description" content="Institutional-grade signal intelligence. Track Congress trades, dark pool activity, 13F filings, and ARK fund moves before they hit the news." />
</svelte:head>

<div class="landing-root">
	{@render children()}
</div>

<style>
	.landing-root {
		min-height: 100vh;
		background: #09090b;
		color: #a1a1aa;
		font-family: 'Inter', -apple-system, system-ui, sans-serif;
		-webkit-font-smoothing: antialiased;
		-moz-osx-font-smoothing: grayscale;
	}
</style>
