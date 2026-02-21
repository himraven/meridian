<script lang="ts">
	import Card from '$lib/components/ui/Card.svelte';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	const d = $derived(data.data);

	// VIX regime color
	function vixColor(regime: string): string {
		const map: Record<string, string> = {
			calm: 'var(--green)',
			elevated: 'var(--amber)',
			fearful: '#f97316',
			crisis: 'var(--red)',
			unknown: 'var(--text-muted)',
		};
		return map[regime] ?? 'var(--text-muted)';
	}

	function vixLabel(regime: string): string {
		const map: Record<string, string> = {
			calm: 'Calm',
			elevated: 'Elevated',
			fearful: 'Fearful',
			crisis: 'Crisis',
		};
		return map[regime] ?? regime;
	}

	function sentimentColor(s: string): string {
		if (s === 'bullish') return 'var(--green)';
		if (s === 'bearish') return 'var(--red)';
		return 'var(--text-muted)';
	}

	function scoreColor(score: number): string {
		if (score >= 75) return 'var(--green)';
		if (score >= 50) return 'var(--amber)';
		if (score >= 25) return '#f97316';
		return 'var(--red)';
	}

	function fmtReturn(v: number | null): string {
		if (v === null || v === undefined) return '—';
		return `${v > 0 ? '+' : ''}${v.toFixed(1)}%`;
	}

	function returnColor(v: number | null): string {
		if (v === null || v === undefined) return 'var(--text-muted)';
		return v > 0 ? 'var(--green)' : 'var(--red)';
	}
</script>

<svelte:head>
	<title>Crisis Dashboard — Meridian</title>
</svelte:head>

<div class="space-y-6">

	<!-- Header -->
	<div class="page-header">
		<div>
			<h1 class="page-title">Crisis Dashboard</h1>
			<p class="page-subtitle">Real-time market stress indicators + smart money crisis behavior</p>
		</div>
		{#if d?.cached_at}
			<span class="cache-label">Updated {new Date(d.cached_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
		{/if}
	</div>

	{#if data.error}
		<Card>
			{#snippet children()}
				<p class="error-msg">Failed to load crisis data: {data.error}</p>
			{/snippet}
		</Card>
	{:else if d}

		<!-- VIX Regime + Conviction Score row -->
		<div class="top-row">

			<!-- VIX Panel -->
			<div class="vix-panel card-base">
				<div class="section-label">VIX REGIME</div>
				{#if d.vix}
					<div class="vix-hero">
						<span class="vix-number" style="color: {vixColor(d.vix.regime)}">
							{d.vix.current?.toFixed(1) ?? '—'}
						</span>
						<span class="vix-regime-badge" style="color: {vixColor(d.vix.regime)}">
							{vixLabel(d.vix.regime)}
						</span>
					</div>
					<div class="vix-stats">
						<div class="vix-stat">
							<span class="vix-stat-label">1Y Avg</span>
							<span class="vix-stat-val">{d.vix.avg_1y?.toFixed(1) ?? '—'}</span>
						</div>
						<div class="vix-divider"></div>
						<div class="vix-stat">
							<span class="vix-stat-label">5Y Avg</span>
							<span class="vix-stat-val">{d.vix.avg_5y?.toFixed(1) ?? '—'}</span>
						</div>
					</div>
					{#if d.vix.is_elevated}
						<div class="vix-alert">
							⚡ VIX elevated — Smart Money behavior below
						</div>
					{/if}
				{:else}
					<p class="no-data">VIX data unavailable</p>
				{/if}
			</div>

			<!-- Conviction Score -->
			<div class="conviction-panel card-base">
				<div class="section-label">CRISIS CONVICTION SCORE</div>
				{#if d.conviction_score !== undefined}
					<div class="score-hero">
						<div class="score-ring" style="--score-color: {scoreColor(d.conviction_score)}">
							<span class="score-number" style="color: {scoreColor(d.conviction_score)}">
								{d.conviction_score}
							</span>
							<span class="score-max">/100</span>
						</div>
						<div class="score-info">
							<span class="score-label" style="color: {scoreColor(d.conviction_score)}">
								{d.conviction_label ?? '—'}
							</span>
							<p class="score-desc">
								{#if d.conviction_score >= 75}
									Multiple smart money sources buying — strong crisis opportunity signal.
								{:else if d.conviction_score >= 50}
									Majority of smart money sources net buying during stress.
								{:else if d.conviction_score >= 25}
									Mixed signals — partial smart money participation.
								{:else}
									Smart money predominantly defensive — watch for reversal signals.
								{/if}
							</p>
							<div class="score-weights">
								<span>Weights: GOV 25 · INS 25 · 13F 20 · ARK 15 · DP 15</span>
							</div>
						</div>
					</div>
					<!-- Score bar -->
					<div class="score-bar-track">
						<div class="score-bar-fill" style="width: {d.conviction_score}%; background: {scoreColor(d.conviction_score)}"></div>
					</div>
				{/if}
			</div>

		</div>

		<!-- Smart Money Signals -->
		{#if d.smart_money_signals && d.smart_money_signals.length > 0}
			<div>
				<div class="section-label mb-3">SMART MONEY CRISIS BEHAVIOR</div>
				<div class="signals-grid">
					{#each d.smart_money_signals as signal}
						<div class="signal-card card-base {signal.net_buying ? 'signal-buy' : 'signal-sell'}">
							<div class="signal-top">
								<span class="signal-source">{signal.label}</span>
								<span class="signal-sentiment" style="color: {sentimentColor(signal.sentiment)}">
									{signal.net_buying ? '▲ NET BUYING' : '▼ NET SELLING'}
								</span>
							</div>
							<div class="signal-counts">
								<span class="signal-buy-count">↑ {signal.buy_count} buys</span>
								<span class="signal-sell-count">↓ {signal.sell_count} sells</span>
							</div>
							<div class="signal-weight-bar">
								<div
									class="signal-weight-fill"
									style="width: {signal.weight}%; background: {sentimentColor(signal.sentiment)}"
								></div>
							</div>
							<span class="signal-weight-label">Weight: {signal.weight}pts</span>
						</div>
					{/each}
				</div>
			</div>
		{/if}

		<!-- Historical Playbook -->
		{#if d.historical_playbook && d.historical_playbook.length > 0}
			<div>
				<div class="section-label mb-3">HISTORICAL CRISIS PLAYBOOK</div>
				<div class="card-base overflow-x-auto">
					<table class="playbook-table">
						<thead>
							<tr>
								<th>Event</th>
								<th>Date</th>
								<th>VIX Peak</th>
								<th>SPY Drawdown</th>
								<th>+6M Return</th>
								<th>+12M Return</th>
								<th class="lesson-col">Lesson</th>
							</tr>
						</thead>
						<tbody>
							{#each d.historical_playbook as row}
								<tr>
									<td class="event-name">{row.event}</td>
									<td class="mono">{row.date}</td>
									<td class="mono" style="color: var(--red)">{row.vix_peak?.toFixed(1)}</td>
									<td class="mono" style="color: var(--red)">{fmtReturn(row.spy_drawdown)}</td>
									<td class="mono" style="color: {returnColor(row.return_6m)}">{fmtReturn(row.return_6m)}</td>
									<td class="mono" style="color: {returnColor(row.return_12m)}">{fmtReturn(row.return_12m)}</td>
									<td class="lesson-text">{row.lesson}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
				<p class="table-footnote">
					* Returns measured from VIX peak date. Past performance does not guarantee future results.
				</p>
			</div>
		{/if}

	{:else}
		<Card>
			{#snippet children()}
				<div class="loading-state">Loading crisis data…</div>
			{/snippet}
		</Card>
	{/if}
</div>

<style>
	.page-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 12px;
	}

	.page-title {
		font-size: 18px;
		font-weight: 600;
		color: var(--text-primary);
	}

	.page-subtitle {
		font-size: 12px;
		color: var(--text-muted);
		margin-top: 2px;
	}

	.cache-label {
		font-size: 11px;
		color: var(--text-dimmed);
		flex-shrink: 0;
	}

	.error-msg {
		color: var(--red);
		font-size: 13px;
		padding: 16px;
	}

	.loading-state {
		text-align: center;
		padding: 32px;
		color: var(--text-muted);
		font-size: 13px;
	}

	.no-data {
		color: var(--text-muted);
		font-size: 13px;
		margin-top: 12px;
	}

	.section-label {
		font-family: 'SF Mono', 'Fira Code', 'JetBrains Mono', monospace;
		font-size: 11px;
		font-weight: 500;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		color: var(--text-muted);
		margin-bottom: 8px;
	}

	.mb-3 { margin-bottom: 12px; }

	.card-base {
		background: var(--bg-surface);
		border: 1px solid var(--border-default);
		border-radius: 12px;
		padding: 20px;
	}

	/* Top row */
	.top-row {
		display: grid;
		grid-template-columns: 1fr 2fr;
		gap: 16px;
	}

	@media (max-width: 768px) {
		.top-row { grid-template-columns: 1fr; }
	}

	/* VIX Panel */
	.vix-panel {}

	.vix-hero {
		display: flex;
		align-items: baseline;
		gap: 12px;
		margin: 12px 0;
	}

	.vix-number {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 48px;
		font-weight: 700;
		line-height: 1;
	}

	.vix-regime-badge {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 14px;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	.vix-stats {
		display: flex;
		gap: 16px;
		align-items: center;
		margin-bottom: 12px;
	}

	.vix-stat {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.vix-stat-label {
		font-size: 10px;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--text-dimmed);
		font-family: 'SF Mono', 'Fira Code', monospace;
	}

	.vix-stat-val {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 14px;
		font-weight: 600;
		color: var(--text-secondary);
	}

	.vix-divider {
		width: 1px;
		height: 28px;
		background: var(--border-default);
	}

	.vix-alert {
		font-size: 12px;
		color: var(--amber);
		background: rgba(245, 158, 11, 0.1);
		border: 1px solid rgba(245, 158, 11, 0.2);
		border-radius: 6px;
		padding: 8px 12px;
		margin-top: 4px;
	}

	/* Conviction Score */
	.conviction-panel {}

	.score-hero {
		display: flex;
		align-items: center;
		gap: 20px;
		margin: 12px 0;
	}

	.score-ring {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		width: 80px;
		height: 80px;
		border-radius: 50%;
		border: 3px solid var(--score-color, var(--text-muted));
		flex-shrink: 0;
	}

	.score-number {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 26px;
		font-weight: 700;
		line-height: 1;
	}

	.score-max {
		font-size: 10px;
		color: var(--text-dimmed);
	}

	.score-info {
		flex: 1;
	}

	.score-label {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 14px;
		font-weight: 700;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		display: block;
		margin-bottom: 6px;
	}

	.score-desc {
		font-size: 12px;
		color: var(--text-muted);
		line-height: 1.5;
		margin-bottom: 6px;
	}

	.score-weights {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 10px;
		color: var(--text-dimmed);
	}

	.score-bar-track {
		width: 100%;
		height: 4px;
		background: var(--bg-elevated);
		border-radius: 2px;
		overflow: hidden;
		margin-top: 8px;
	}

	.score-bar-fill {
		height: 100%;
		border-radius: 2px;
		transition: width 0.5s ease;
	}

	/* Smart money signals */
	.signals-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
		gap: 12px;
	}

	.signal-card {
		padding: 14px 16px;
	}

	.signal-buy {
		border-color: rgba(34, 197, 94, 0.25);
	}

	.signal-sell {
		border-color: rgba(248, 113, 113, 0.25);
	}

	.signal-top {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 8px;
		flex-wrap: wrap;
		gap: 4px;
	}

	.signal-source {
		font-size: 13px;
		font-weight: 600;
		color: var(--text-primary);
	}

	.signal-sentiment {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 10px;
		font-weight: 700;
		letter-spacing: 0.04em;
	}

	.signal-counts {
		display: flex;
		flex-wrap: wrap;
		gap: 4px 12px;
		margin-bottom: 8px;
	}

	.signal-buy-count {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 12px;
		color: var(--green);
		white-space: nowrap;
	}

	.signal-sell-count {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 12px;
		color: var(--red);
		white-space: nowrap;
	}

	.signal-weight-bar {
		width: 100%;
		height: 3px;
		background: var(--bg-elevated);
		border-radius: 2px;
		overflow: hidden;
		margin-bottom: 4px;
	}

	.signal-weight-fill {
		height: 100%;
		border-radius: 2px;
	}

	.signal-weight-label {
		font-size: 10px;
		color: var(--text-dimmed);
		font-family: 'SF Mono', 'Fira Code', monospace;
	}

	/* Playbook table */
	.overflow-x-auto {
		overflow-x: auto;
	}

	.playbook-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 13px;
	}

	.playbook-table th {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 10px;
		font-weight: 500;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--text-dimmed);
		text-align: left;
		padding: 8px 12px;
		border-bottom: 1px solid var(--border-default);
	}

	.playbook-table td {
		padding: 12px;
		border-bottom: 1px solid var(--border-default);
		vertical-align: top;
	}

	.playbook-table tr:last-child td {
		border-bottom: none;
	}

	.playbook-table tr:hover td {
		background: var(--bg-elevated);
	}

	.event-name {
		font-weight: 600;
		color: var(--text-primary);
		white-space: nowrap;
	}

	.mono {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-weight: 600;
	}

	.lesson-col {
		min-width: 200px;
	}

	.lesson-text {
		font-size: 12px;
		color: var(--text-muted);
		line-height: 1.5;
		max-width: 300px;
	}

	.table-footnote {
		font-size: 11px;
		color: var(--text-dimmed);
		margin-top: 10px;
		padding-left: 4px;
	}
</style>
