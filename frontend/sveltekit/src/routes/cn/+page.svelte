<script lang="ts">
	import Card from '$lib/components/ui/Card.svelte';
	import { formatDate, formatPercent } from '$lib/utils/format';
	import type { PageData } from './$types';
	
	let { data }: { data: PageData } = $props();
	
	const isBull = $derived(data.trend.signal === 'bull');
</script>

<svelte:head>
	<title>CN Trend — Smart Money Platform</title>
</svelte:head>

<div class="space-y-6" data-market-style="cn">
	<!-- Header -->
	<div>
		<div class="flex items-center gap-3 mb-2">
			<h1 class="text-heading">CN Market Trend</h1>
		</div>
		<p class="text-[var(--text-muted)]">A-Share CSI 300 Trend Signal</p>
		<p class="text-xs text-[var(--text-dimmed)] mt-2">
			Updated: {formatDate(data.trend.updated_at)}
		</p>
	</div>
	
	<!-- Big Signal Indicator -->
	<div class="flex justify-center">
		<Card hover class="max-w-md w-full">
			{#snippet children()}
				<div class="text-center py-8 px-4" class:pulse-bull={isBull} class:pulse-bear={!isBull}>
					<div class="text-5xl font-black tracking-wider mb-3" class:color-up={isBull} class:color-down={!isBull}>
						{data.trend.signal.toUpperCase()}
					</div>
					<div class="text-sm text-[var(--text-muted)]">
						CSI 300 · {formatDate(data.trend.date)}
					</div>
				</div>
			{/snippet}
		</Card>
	</div>
	
	<!-- Key Metrics -->
	<div class="grid grid-cols-2 md:grid-cols-5 gap-4">
		<Card hover>
			{#snippet children()}
				<div class="text-center">
					<p class="text-label mb-2">Price</p>
					<p class="text-data-lg">{data.trend.price.toFixed(1)}</p>
				</div>
			{/snippet}
		</Card>
		<Card hover>
			{#snippet children()}
				<div class="text-center">
					<p class="text-label mb-2">MA200</p>
					<p class="text-data-lg">{data.trend.ma200.toFixed(1)}</p>
				</div>
			{/snippet}
		</Card>
		<Card hover>
			{#snippet children()}
				<div class="text-center">
					<p class="text-label mb-2">MA Distance</p>
					<p class="text-data-lg" class:color-up={data.trend.ma_distance_pct >= 0} class:color-down={data.trend.ma_distance_pct < 0}>
						{formatPercent(data.trend.ma_distance_pct, 1, true)}
					</p>
				</div>
			{/snippet}
		</Card>
		<Card hover>
			{#snippet children()}
				<div class="text-center">
					<p class="text-label mb-2">RSI14</p>
					<p class="text-data-lg">{data.trend.rsi14.toFixed(1)}</p>
				</div>
			{/snippet}
		</Card>
		<Card hover>
			{#snippet children()}
				<div class="text-center">
					<p class="text-label mb-2">Volume Ratio</p>
					<p class="text-data-lg">{data.trend.volume_ratio.toFixed(2)}x</p>
				</div>
			{/snippet}
		</Card>
	</div>
	
	<!-- Signal Change History -->
	{#if data.trend.last_signal_change}
		<Card title="Signal History">
			{#snippet children()}
				<div class="space-y-2">
					<div class="flex items-center justify-between p-3 bg-[var(--bg-surface)] rounded-lg border border-[var(--border-default)]">
						<div>
							<div class="text-sm text-[var(--text-primary)] font-semibold">Current Signal</div>
							<div class="text-xs text-[var(--text-muted)] mt-1">{formatDate(data.trend.last_signal_change)}</div>
						</div>
						<div class="text-lg font-bold" class:color-up={isBull} class:color-down={!isBull}>
							{data.trend.signal.toUpperCase()}
						</div>
					</div>
					{#if data.trend.previous_signal}
						<div class="flex items-center justify-between p-3 bg-[var(--bg-base)] rounded-lg border border-[var(--border-default)]">
							<div>
								<div class="text-sm text-[var(--text-muted)]">Previous Signal</div>
							</div>
							<div class="text-sm text-[var(--text-muted)]">
								{data.trend.previous_signal.toUpperCase()}
							</div>
						</div>
					{/if}
				</div>
			{/snippet}
		</Card>
	{/if}
</div>

<style>
	@keyframes pulse-bull {
		0%, 100% {
			box-shadow: 0 0 0 0 rgba(0, 184, 148, 0.5);
		}
		50% {
			box-shadow: 0 0 30px 10px rgba(0, 184, 148, 0.15);
		}
	}
	@keyframes pulse-bear {
		0%, 100% {
			box-shadow: 0 0 0 0 rgba(231, 76, 60, 0.5);
		}
		50% {
			box-shadow: 0 0 30px 10px rgba(231, 76, 60, 0.15);
		}
	}
	.pulse-bull {
		animation: pulse-bull 2s infinite;
	}
	.pulse-bear {
		animation: pulse-bear 2s infinite;
	}
</style>
