<script lang="ts">
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	const d         = $derived(data.derivatives as any);
	const coins     = $derived((d?.coins ?? []) as any[]);
	const funding   = $derived((d?.funding_rates ?? {}) as Record<string, any[]>);
	const options   = $derived((d?.options ?? {}) as Record<string, any>);
	const meta      = $derived(d?.metadata ?? {});

	// ── Pill tab state ────────────────────────────────────────────────
	type Tab = 'oi' | 'funding' | 'options';
	let activeTab   = $state<Tab>('oi');

	// ── Sub-selectors ─────────────────────────────────────────────────
	let fundingCoin  = $state<'BTC' | 'ETH'>('BTC');
	let optionsCoin  = $state<'BTC' | 'ETH'>('BTC');

	// ── KPI calculations ──────────────────────────────────────────────
	const totalOI = $derived(
		d?.total_oi ?? coins.reduce((s: number, c: any) => s + (c.openInterest ?? 0), 0)
	);
	const totalVol = $derived(
		coins.reduce((s: number, c: any) => s + (c.volUsd ?? 0), 0)
	);
	const oiVolRatio = $derived(totalVol > 0 ? totalOI / totalVol : null);

	// ── Funding rates for selected coin (sorted by |rate| desc) ───────
	const fundingRows = $derived(
		[...(funding[fundingCoin] ?? [])].sort(
			(a, b) => Math.abs(b.rate ?? 0) - Math.abs(a.rate ?? 0)
		)
	);

	// ── Options data for selected coin ────────────────────────────────
	const optionsData   = $derived(options[optionsCoin] ?? null);
	const optionsTotals = $derived(optionsData?.totals ?? null);
	const optionsRows   = $derived(
		((optionsData?.exchanges ?? []) as any[]).filter((e: any) => e.name !== 'All')
	);

	// ── Formatters ────────────────────────────────────────────────────
	function fmtUsd(v: number | null | undefined, decimals = 1): string {
		if (v === null || v === undefined) return '—';
		const abs = Math.abs(v);
		const prefix = v < 0 ? '-$' : '$';
		if (abs >= 1_000_000_000_000) return `${prefix}${(abs / 1_000_000_000_000).toFixed(decimals)}T`;
		if (abs >= 1_000_000_000)     return `${prefix}${(abs / 1_000_000_000).toFixed(decimals)}B`;
		if (abs >= 1_000_000)         return `${prefix}${(abs / 1_000_000).toFixed(decimals)}M`;
		if (abs >= 1_000)             return `${prefix}${(abs / 1_000).toFixed(decimals)}K`;
		return `${prefix}${abs.toFixed(decimals)}`;
	}

	function fmtContracts(v: number | null | undefined): string {
		if (v === null || v === undefined) return '—';
		if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(2)}M`;
		if (v >= 1_000)     return `${(v / 1_000).toFixed(2)}K`;
		return v.toFixed(2);
	}

	function fmtPct(v: number | null | undefined, decimals = 2): string {
		if (v === null || v === undefined) return '—';
		return `${v > 0 ? '+' : ''}${v.toFixed(decimals)}%`;
	}

	function fmtRate(v: number | null | undefined): string {
		if (v === null || v === undefined) return '—';
		const pct = v * 100;
		const sign = pct >= 0 ? '+' : '';
		return `${sign}${pct.toFixed(4)}%`;
	}

	function changeColor(v: number | null | undefined): string {
		if (v === null || v === undefined) return 'var(--text-dimmed)';
		if (v > 0) return 'var(--green)';
		if (v < 0) return 'var(--red)';
		return 'var(--text-dimmed)';
	}

	/** Rate gradient: > +0.01% deep green, > 0 light green, < 0 light red, < -0.01% deep red */
	function rateColor(rate: number | null | undefined): string {
		if (rate === null || rate === undefined) return 'var(--text-dimmed)';
		const pct = rate * 100;
		if (pct > 0.01)  return '#22c55e';   // deep green
		if (pct > 0)     return '#86efac';   // light green
		if (pct < -0.01) return '#ef4444';   // deep red
		if (pct < 0)     return '#fca5a5';   // light red
		return 'var(--text-dimmed)';
	}

	/** Relative time from epoch ms */
	function relTime(ms: number | null | undefined): string {
		if (!ms) return '—';
		const diff = ms - Date.now();
		if (diff <= 0) return 'passed';
		const h = Math.floor(diff / 3_600_000);
		const m = Math.floor((diff % 3_600_000) / 60_000);
		if (h === 0) return `in ${m}m`;
		if (m === 0) return `in ${h}h`;
		return `in ${h}h ${m}m`;
	}

	function collectedAt(ts: string | null | undefined): string {
		if (!ts) return '';
		try {
			return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
		} catch {
			return '';
		}
	}
</script>

<svelte:head>
	<title>Crypto Derivatives — Meridian</title>
	<meta name="description" content="Crypto derivatives: open interest, funding rates, and options data across top coins and exchanges" />
</svelte:head>

<div class="space-y-6">

	<!-- Header -->
	<div class="page-header">
		<div>
			<h1 class="page-title">Crypto Derivatives</h1>
			<p class="page-subtitle">Open interest, funding rates &amp; options across 20 coins</p>
		</div>
		{#if meta?.collected_at}
			<span class="cache-label">Updated {collectedAt(meta.collected_at)}</span>
		{/if}
	</div>

	{#if data.error}
		<div class="card-base">
			<p class="error-msg">⚠ Failed to load derivatives data: {data.error}</p>
		</div>

	{:else if !d}
		<div class="card-base">
			<div class="loading-state">
				<div class="spinner"></div>
				<span>Loading crypto derivatives…</span>
			</div>
		</div>

	{:else}

		<!-- ── KPI Row ─────────────────────────────────────────────── -->
		<div class="kpi-row">
			<div class="kpi-card">
				<span class="kpi-label">Total Open Interest</span>
				<span class="kpi-val">{fmtUsd(totalOI)}</span>
			</div>
			<div class="kpi-card">
				<span class="kpi-label">24h Volume</span>
				<span class="kpi-val">{fmtUsd(totalVol)}</span>
			</div>
			<div class="kpi-card">
				<span class="kpi-label">OI / Vol Ratio</span>
				<span class="kpi-val">{oiVolRatio != null ? oiVolRatio.toFixed(2) + 'x' : '—'}</span>
			</div>
		</div>

		<!-- ── Pill Tabs ───────────────────────────────────────────── -->
		<div class="pills-bar">
			<button
				class="pill"
				class:pill-active={activeTab === 'oi'}
				onclick={() => (activeTab = 'oi')}
			>Open Interest</button>
			<button
				class="pill"
				class:pill-active={activeTab === 'funding'}
				onclick={() => (activeTab = 'funding')}
			>Funding Rates</button>
			<button
				class="pill"
				class:pill-active={activeTab === 'options'}
				onclick={() => (activeTab = 'options')}
			>Options</button>
		</div>

		<!-- ═══════════════════════════════════════════════════════════
		     TAB: Open Interest
		═══════════════════════════════════════════════════════════ -->
		{#if activeTab === 'oi'}
			<div class="card-base">
				<div class="section-label">Open Interest — {coins.length} coins</div>
				{#if coins.length}
					<div class="table-wrap">
						<table class="data-table">
							<thead>
								<tr>
									<th class="text-right">#</th>
									<th>Coin</th>
									<th class="text-right">OI</th>
									<th class="text-right">Vol 24h</th>
									<th class="text-right">Avg Funding</th>
									<th class="text-right">ΔOI 1h</th>
									<th class="text-right">ΔOI 4h</th>
									<th class="text-right">ΔOI 7d</th>
									<th class="text-right">ΔOI 30d</th>
									<th class="text-right">OI/Vol</th>
								</tr>
							</thead>
							<tbody>
								{#each coins as coin, i}
									<tr>
										<td class="text-right dim mono">{i + 1}</td>
										<td>
											<span class="ticker-mono">{coin.symbol}</span>
										</td>
										<td class="text-right mono">{fmtUsd(coin.openInterest)}</td>
										<td class="text-right mono dim">{fmtUsd(coin.volUsd)}</td>
										<td class="text-right mono" style="color: {rateColor(coin.avgFundingRate)}">
											{fmtRate(coin.avgFundingRate)}
										</td>
										<td class="text-right mono" style="color: {changeColor(coin.h1OIChange)}">
											{#if coin.h1OIChange != null}{fmtPct(coin.h1OIChange)}{:else}<span class="dim">—</span>{/if}
										</td>
										<td class="text-right mono" style="color: {changeColor(coin.h4OIChange)}">
											{#if coin.h4OIChange != null}{fmtPct(coin.h4OIChange)}{:else}<span class="dim">—</span>{/if}
										</td>
										<td class="text-right mono" style="color: {changeColor(coin.oiChange7d)}">
											{#if coin.oiChange7d != null}{fmtPct(coin.oiChange7d)}{:else}<span class="dim">—</span>{/if}
										</td>
										<td class="text-right mono" style="color: {changeColor(coin.oiChange30d)}">
											{#if coin.oiChange30d != null}{fmtPct(coin.oiChange30d)}{:else}<span class="dim">—</span>{/if}
										</td>
										<td class="text-right mono dim">
											{coin.oiVolRatio != null ? coin.oiVolRatio.toFixed(2) : '—'}
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{:else}
					<p class="empty-state">No open interest data available</p>
				{/if}
			</div>

		<!-- ═══════════════════════════════════════════════════════════
		     TAB: Funding Rates
		═══════════════════════════════════════════════════════════ -->
		{:else if activeTab === 'funding'}
			<!-- Sub-selector -->
			<div class="sub-pills">
				<button
					class="sub-pill"
					class:sub-pill-active={fundingCoin === 'BTC'}
					onclick={() => (fundingCoin = 'BTC')}
				>BTC</button>
				<button
					class="sub-pill"
					class:sub-pill-active={fundingCoin === 'ETH'}
					onclick={() => (fundingCoin = 'ETH')}
				>ETH</button>
			</div>

			<div class="card-base">
				<div class="section-label">Funding Rates — {fundingCoin} — {fundingRows.length} exchanges</div>
				{#if fundingRows.length}
					<div class="table-wrap">
						<table class="data-table">
							<thead>
								<tr>
									<th>Exchange</th>
									<th class="text-right">Rate</th>
									<th>Margin</th>
									<th class="text-right">Next Funding</th>
								</tr>
							</thead>
							<tbody>
								{#each fundingRows as row}
									<tr>
										<td class="ex-name">{row.name}</td>
										<td class="text-right">
											<span class="rate-val" style="color: {rateColor(row.rate)}">
												{fmtRate(row.rate)}
											</span>
										</td>
										<td>
											{#if row.marginType}
												<span class="margin-badge" class:margin-u={row.marginType === 'uMargin'} class:margin-c={row.marginType === 'cMargin'}>
													{row.marginType}
												</span>
											{:else}
												<span class="dim">—</span>
											{/if}
										</td>
										<td class="text-right mono dim funding-time">
											{relTime(row.nextFundingTime)}
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{:else}
					<p class="empty-state">No funding rate data for {fundingCoin}</p>
				{/if}
			</div>

			<!-- Legend -->
			<div class="funding-legend">
				<span class="legend-item" style="color: #22c55e">● &gt;+0.01% (bullish)</span>
				<span class="legend-item" style="color: #86efac">● &gt;0% (mildly bullish)</span>
				<span class="legend-item" style="color: #fca5a5">● &lt;0% (mildly bearish)</span>
				<span class="legend-item" style="color: #ef4444">● &lt;-0.01% (bearish)</span>
			</div>

		<!-- ═══════════════════════════════════════════════════════════
		     TAB: Options
		═══════════════════════════════════════════════════════════ -->
		{:else if activeTab === 'options'}
			<!-- Sub-selector -->
			<div class="sub-pills">
				<button
					class="sub-pill"
					class:sub-pill-active={optionsCoin === 'BTC'}
					onclick={() => (optionsCoin = 'BTC')}
				>BTC</button>
				<button
					class="sub-pill"
					class:sub-pill-active={optionsCoin === 'ETH'}
					onclick={() => (optionsCoin = 'ETH')}
				>ETH</button>
			</div>

			{#if optionsData}
				<!-- Summary card -->
				{#if optionsTotals}
					<div class="options-summary">
						<div class="opt-kpi-card">
							<span class="kpi-label">Total OI (contracts)</span>
							<span class="kpi-val">{fmtContracts(optionsTotals.openInterest)}</span>
						</div>
						<div class="opt-kpi-card">
							<span class="kpi-label">Total OI (USD)</span>
							<span class="kpi-val">{fmtUsd(optionsTotals.openInterestUsd)}</span>
						</div>
						<div class="opt-kpi-card">
							<span class="kpi-label">Total Vol 24h</span>
							<span class="kpi-val">{fmtContracts(optionsTotals.vol24h)}</span>
						</div>
					</div>
				{/if}

				<!-- Exchange table -->
				<div class="card-base">
					<div class="section-label">{optionsCoin} Options — Exchange Breakdown</div>
					{#if optionsRows.length}
						<div class="table-wrap">
							<table class="data-table">
								<thead>
									<tr>
										<th>Exchange</th>
										<th class="text-right">OI (contracts)</th>
										<th class="text-right">OI ($)</th>
										<th class="text-right">Vol 24h</th>
										<th>Share %</th>
									</tr>
								</thead>
								<tbody>
									{#each optionsRows as row}
										{@const totalOiContracts = optionsTotals?.openInterest ?? 0}
										{@const share = totalOiContracts > 0 ? (row.openInterest / totalOiContracts) * 100 : 0}
										<tr>
											<td class="ex-name">{row.name}</td>
											<td class="text-right mono">{fmtContracts(row.openInterest)}</td>
											<td class="text-right mono">{fmtUsd(row.openInterestUsd)}</td>
											<td class="text-right mono dim">{fmtContracts(row.vol24h)}</td>
											<td class="share-cell">
												<div class="share-row">
													<span class="share-pct mono">{share.toFixed(1)}%</span>
													<div class="share-bar-track">
														<div class="share-bar-fill" style="width: {Math.min(share, 100)}%"></div>
													</div>
												</div>
											</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					{:else}
						<p class="empty-state">No options exchange data for {optionsCoin}</p>
					{/if}
				</div>
			{:else}
				<div class="card-base">
					<p class="empty-state">No options data available for {optionsCoin}</p>
				</div>
			{/if}
		{/if}

	{/if}

</div>

<style>
	/* ── Layout ─────────────────────────────────────────────────────── */
	.page-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 12px;
		flex-wrap: wrap;
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
		white-space: nowrap;
	}

	.card-base {
		background: var(--bg-surface);
		border: 1px solid var(--border-default);
		border-radius: 12px;
		padding: 20px;
	}

	/* ── KPI Row ─────────────────────────────────────────────────────── */
	.kpi-row {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 12px;
	}

	@media (max-width: 500px) {
		.kpi-row { grid-template-columns: 1fr; }
	}

	.kpi-card {
		background: var(--bg-surface);
		border: 1px solid var(--border-default);
		border-radius: 10px;
		padding: 16px;
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	.kpi-label {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 10px;
		font-weight: 500;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--text-dimmed);
	}

	.kpi-val {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 22px;
		font-weight: 700;
		color: var(--text-primary);
		line-height: 1;
	}

	/* ── Pill tabs ────────────────────────────────────────────────────── */
	.pills-bar {
		display: flex;
		gap: 8px;
		flex-wrap: wrap;
	}

	.pill {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 12px;
		font-weight: 600;
		letter-spacing: 0.03em;
		padding: 7px 18px;
		border-radius: 999px;
		border: 1px solid var(--border-default);
		background: transparent;
		color: var(--text-muted);
		cursor: pointer;
		transition: background 0.15s, color 0.15s, border-color 0.15s;
	}

	.pill:hover {
		border-color: var(--text-muted);
		color: var(--text-secondary);
	}

	.pill-active {
		background: var(--accent, #3b82f6);
		border-color: var(--accent, #3b82f6);
		color: #fff;
	}

	.pill-active:hover {
		background: var(--accent, #3b82f6);
		border-color: var(--accent, #3b82f6);
		color: #fff;
	}

	/* ── Sub-pills ────────────────────────────────────────────────────── */
	.sub-pills {
		display: flex;
		gap: 6px;
	}

	.sub-pill {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.04em;
		padding: 4px 14px;
		border-radius: 999px;
		border: 1px solid var(--border-default);
		background: transparent;
		color: var(--text-muted);
		cursor: pointer;
		transition: background 0.12s, color 0.12s, border-color 0.12s;
	}

	.sub-pill:hover {
		border-color: var(--text-muted);
		color: var(--text-secondary);
	}

	.sub-pill-active {
		background: rgba(59, 130, 246, 0.2);
		border-color: #3b82f6;
		color: #93c5fd;
	}

	/* ── Section label ────────────────────────────────────────────────── */
	.section-label {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 11px;
		font-weight: 500;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		color: var(--text-muted);
		margin-bottom: 14px;
	}

	/* ── Tables ───────────────────────────────────────────────────────── */
	.table-wrap {
		overflow-x: auto;
		-webkit-overflow-scrolling: touch;
	}

	.data-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 13px;
		min-width: 600px;
	}

	.data-table th {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 10px;
		font-weight: 500;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--text-dimmed);
		padding: 6px 8px;
		border-bottom: 1px solid var(--border-default);
		text-align: left;
		white-space: nowrap;
	}

	.data-table td {
		padding: 8px 8px;
		border-bottom: 1px solid var(--border-subtle, rgba(255,255,255,0.04));
		color: var(--text-secondary);
		white-space: nowrap;
	}

	.data-table tr:last-child td {
		border-bottom: none;
	}

	.data-table tr:hover td {
		background: var(--bg-elevated);
	}

	.text-right { text-align: right; }

	.mono {
		font-family: 'SF Mono', 'Fira Code', monospace;
	}

	.dim { color: var(--text-dimmed); }

	/* ── Ticker ───────────────────────────────────────────────────────── */
	.ticker-mono {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 12px;
		font-weight: 700;
		color: var(--text-primary);
		letter-spacing: 0.02em;
	}

	/* ── Rate value ───────────────────────────────────────────────────── */
	.rate-val {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 13px;
		font-weight: 600;
	}

	/* ── Exchange name ────────────────────────────────────────────────── */
	.ex-name {
		font-size: 13px;
		font-weight: 500;
		color: var(--text-primary);
	}

	/* ── Margin badge ─────────────────────────────────────────────────── */
	.margin-badge {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 10px;
		font-weight: 600;
		padding: 2px 7px;
		border-radius: 4px;
		border: 1px solid;
		white-space: nowrap;
		letter-spacing: 0.03em;
	}

	.margin-u {
		color: #93c5fd;
		border-color: #3b82f640;
		background: #3b82f610;
	}

	.margin-c {
		color: #d8b4fe;
		border-color: #a855f740;
		background: #a855f710;
	}

	/* ── Funding next time ────────────────────────────────────────────── */
	.funding-time {
		font-size: 11px;
	}

	/* ── Funding legend ───────────────────────────────────────────────── */
	.funding-legend {
		display: flex;
		gap: 16px;
		flex-wrap: wrap;
		padding: 0 2px;
	}

	.legend-item {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 11px;
		font-weight: 500;
		color: var(--text-dimmed);
		white-space: nowrap;
	}

	/* ── Options summary ──────────────────────────────────────────────── */
	.options-summary {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 12px;
	}

	@media (max-width: 500px) {
		.options-summary { grid-template-columns: 1fr; }
	}

	.opt-kpi-card {
		background: var(--bg-surface);
		border: 1px solid var(--border-default);
		border-radius: 10px;
		padding: 16px;
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	/* ── Share bar ────────────────────────────────────────────────────── */
	.share-cell {
		min-width: 140px;
		padding-right: 12px !important;
	}

	.share-row {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.share-pct {
		font-size: 12px;
		color: var(--text-secondary);
		min-width: 38px;
		text-align: right;
	}

	.share-bar-track {
		flex: 1;
		height: 5px;
		border-radius: 999px;
		background: var(--border-default);
		overflow: hidden;
		min-width: 60px;
	}

	.share-bar-fill {
		height: 100%;
		border-radius: 999px;
		background: var(--accent, #3b82f6);
		transition: width 0.3s ease;
	}

	/* ── Loading & States ─────────────────────────────────────────────── */
	.loading-state {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 12px;
		padding: 40px;
		color: var(--text-muted);
		font-size: 13px;
	}

	.spinner {
		width: 18px;
		height: 18px;
		border: 2px solid var(--border-default);
		border-top-color: var(--text-muted);
		border-radius: 50%;
		animation: spin 0.7s linear infinite;
		flex-shrink: 0;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.error-msg {
		color: var(--red);
		font-size: 13px;
		padding: 16px;
	}

	.empty-state {
		color: var(--text-dimmed);
		font-size: 12px;
		padding: 12px 0;
	}
</style>
