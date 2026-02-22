<script lang="ts">
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	const etfData   = $derived(data.etfData as any);
	const summary   = $derived(etfData?.crypto_etf_summary ?? {});
	const btcSummary = $derived(summary?.btc ?? {});
	const ethSummary = $derived(summary?.eth ?? {});
	const btcEtfs   = $derived(btcSummary?.etfs ?? []);
	const ethEtfs   = $derived(ethSummary?.etfs ?? []);
	const meta      = $derived(etfData?.metadata ?? {});

	// ── Formatters ────────────────────────────────────────────────────

	function fmtAum(v: number | null | undefined): string {
		if (v === null || v === undefined) return '—';
		const abs = Math.abs(v);
		const prefix = v < 0 ? '-$' : '$';
		if (abs >= 1_000_000_000) return `${prefix}${(abs / 1_000_000_000).toFixed(1)}B`;
		if (abs >= 1_000_000)     return `${prefix}${(abs / 1_000_000).toFixed(0)}M`;
		if (abs >= 1_000)         return `${prefix}${(abs / 1_000).toFixed(0)}K`;
		return `${prefix}${abs.toLocaleString()}`;
	}

	function fmtFlow(v: number | null | undefined): string {
		if (v === null || v === undefined || v === 0) return '—';
		const abs = Math.abs(v);
		const prefix = v > 0 ? '+$' : '-$';
		if (abs >= 1_000_000_000) return `${prefix}${(abs / 1_000_000_000).toFixed(1)}B`;
		if (abs >= 1_000_000)     return `${prefix}${(abs / 1_000_000).toFixed(0)}M`;
		if (abs >= 1_000)         return `${prefix}${(abs / 1_000).toFixed(0)}K`;
		return `${prefix}${abs.toLocaleString()}`;
	}

	function fmtPct(v: number | null | undefined): string {
		if (v === null || v === undefined) return '—';
		return `${v > 0 ? '+' : ''}${v.toFixed(2)}%`;
	}

	function fmtPrice(v: number | null | undefined): string {
		if (v === null || v === undefined) return '—';
		return `$${v.toFixed(2)}`;
	}

	function flowColor(v: number | null | undefined): string {
		if (v === null || v === undefined || v === 0) return 'var(--text-dimmed)';
		return v > 0 ? 'var(--green)' : 'var(--red)';
	}

	function streakLabel(streak: number | null | undefined): string {
		if (streak === null || streak === undefined || streak === 0) return '';
		const days = Math.abs(streak);
		const dir  = streak > 0 ? 'inflow' : 'outflow';
		return `${days}d ${dir}`;
	}

	function streakColor(streak: number | null | undefined): string {
		if (!streak) return 'var(--text-dimmed)';
		return streak > 0 ? 'var(--green)' : 'var(--red)';
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
	<title>Crypto ETF Flows — Meridian</title>
	<meta name="description" content="Bitcoin and Ethereum ETF fund flows — daily and weekly AUM, inflow/outflow streaks" />
</svelte:head>

<div class="space-y-6">

	<!-- Header -->
	<div class="page-header">
		<div>
			<h1 class="page-title">Crypto ETF Flows</h1>
			<p class="page-subtitle">Bitcoin &amp; Ethereum spot ETF daily/weekly fund flows and AUM</p>
		</div>
		{#if meta?.collected_at}
			<span class="cache-label">
				Updated {collectedAt(meta.collected_at)}
				{#if meta.etf_count}· {meta.etf_count} ETFs{/if}
			</span>
		{/if}
	</div>

	{#if data.error}
		<!-- Error state -->
		<div class="card-base">
			<p class="error-msg">⚠ Failed to load ETF data: {data.error}</p>
		</div>

	{:else if !etfData}
		<!-- Loading state -->
		<div class="card-base">
			<div class="loading-state">
				<div class="spinner"></div>
				<span>Loading crypto ETF flows…</span>
			</div>
		</div>

	{:else}

		<!-- ── Summary Cards ────────────────────────────────────────── -->
		<div class="summary-cards">

			<!-- BTC Card -->
			<div class="summary-card btc-card">
				<div class="summary-card-header">
					<span class="asset-icon">₿</span>
					<span class="asset-label">BTC ETFs</span>
				</div>
				<div class="summary-stats">
					<div class="stat-row">
						<span class="stat-label">Total AUM</span>
						<span class="stat-val">{fmtAum(btcSummary?.total_aum)}</span>
					</div>
					<div class="stat-row">
						<span class="stat-label">Daily Flow</span>
						<span class="stat-val" style="color: {flowColor(btcSummary?.daily_flow)}">{fmtFlow(btcSummary?.daily_flow)}</span>
					</div>
					<div class="stat-row">
						<span class="stat-label">Weekly Flow</span>
						<span class="stat-val" style="color: {flowColor(btcSummary?.weekly_flow)}">{fmtFlow(btcSummary?.weekly_flow)}</span>
					</div>
					{#if btcEtfs.length}
						<div class="stat-row">
							<span class="stat-label">ETF Count</span>
							<span class="stat-val">{btcEtfs.length}</span>
						</div>
					{/if}
				</div>
			</div>

			<!-- ETH Card -->
			<div class="summary-card eth-card">
				<div class="summary-card-header">
					<span class="asset-icon eth-icon">Ξ</span>
					<span class="asset-label">ETH ETFs</span>
				</div>
				<div class="summary-stats">
					<div class="stat-row">
						<span class="stat-label">Total AUM</span>
						<span class="stat-val">{fmtAum(ethSummary?.total_aum)}</span>
					</div>
					<div class="stat-row">
						<span class="stat-label">Daily Flow</span>
						<span class="stat-val" style="color: {flowColor(ethSummary?.daily_flow)}">{fmtFlow(ethSummary?.daily_flow)}</span>
					</div>
					<div class="stat-row">
						<span class="stat-label">Weekly Flow</span>
						<span class="stat-val" style="color: {flowColor(ethSummary?.weekly_flow)}">{fmtFlow(ethSummary?.weekly_flow)}</span>
					</div>
					{#if ethEtfs.length}
						<div class="stat-row">
							<span class="stat-label">ETF Count</span>
							<span class="stat-val">{ethEtfs.length}</span>
						</div>
					{/if}
				</div>
			</div>

		</div>

		<!-- ── BTC ETF Breakdown ────────────────────────────────────── -->
		<div class="card-base">
			<div class="section-label">BTC ETF Breakdown</div>

			{#if btcEtfs.length}
				<div class="table-wrap">
					<table class="data-table">
						<thead>
							<tr>
								<th>Ticker</th>
								<th>Name</th>
								<th class="text-right">AUM</th>
								<th class="text-right">Daily Flow</th>
								<th class="text-right">Weekly Flow</th>
								<th class="text-right">Streak</th>
								<th class="text-right">Price</th>
								<th class="text-right">Chg %</th>
							</tr>
						</thead>
						<tbody>
							{#each btcEtfs as etf}
								<tr>
									<td><span class="ticker-mono">{etf.ticker}</span></td>
									<td class="dim truncate">{etf.name ?? '—'}</td>
									<td class="text-right mono">{fmtAum(etf.aum)}</td>
									<td class="text-right mono" style="color: {flowColor(etf.daily_flow)}">{fmtFlow(etf.daily_flow)}</td>
									<td class="text-right mono" style="color: {flowColor(etf.weekly_flow)}">{fmtFlow(etf.weekly_flow)}</td>
									<td class="text-right">
										{#if etf.streak}
											<span class="streak-badge" style="color: {streakColor(etf.streak)}; border-color: {streakColor(etf.streak)}40">
												{streakLabel(etf.streak)}
											</span>
										{:else}
											<span class="dim">—</span>
										{/if}
									</td>
									<td class="text-right mono dim">{fmtPrice(etf.price)}</td>
									<td class="text-right mono" style="color: {flowColor(etf.change_pct)}">{fmtPct(etf.change_pct)}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{:else}
				<p class="empty-state">No BTC ETF data available</p>
			{/if}
		</div>

		<!-- ── ETH ETF Breakdown ────────────────────────────────────── -->
		<div class="card-base">
			<div class="section-label">ETH ETF Breakdown</div>

			{#if ethEtfs.length}
				<div class="table-wrap">
					<table class="data-table">
						<thead>
							<tr>
								<th>Ticker</th>
								<th>Name</th>
								<th class="text-right">AUM</th>
								<th class="text-right">Daily Flow</th>
								<th class="text-right">Weekly Flow</th>
								<th class="text-right">Streak</th>
								<th class="text-right">Price</th>
								<th class="text-right">Chg %</th>
							</tr>
						</thead>
						<tbody>
							{#each ethEtfs as etf}
								<tr>
									<td><span class="ticker-mono">{etf.ticker}</span></td>
									<td class="dim truncate">{etf.name ?? '—'}</td>
									<td class="text-right mono">{fmtAum(etf.aum)}</td>
									<td class="text-right mono" style="color: {flowColor(etf.daily_flow)}">{fmtFlow(etf.daily_flow)}</td>
									<td class="text-right mono" style="color: {flowColor(etf.weekly_flow)}">{fmtFlow(etf.weekly_flow)}</td>
									<td class="text-right">
										{#if etf.streak}
											<span class="streak-badge" style="color: {streakColor(etf.streak)}; border-color: {streakColor(etf.streak)}40">
												{streakLabel(etf.streak)}
											</span>
										{:else}
											<span class="dim">—</span>
										{/if}
									</td>
									<td class="text-right mono dim">{fmtPrice(etf.price)}</td>
									<td class="text-right mono" style="color: {flowColor(etf.change_pct)}">{fmtPct(etf.change_pct)}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{:else}
				<p class="empty-state">No ETH ETF data available</p>
			{/if}
		</div>

		<!-- ── About ─────────────────────────────────────────────────── -->
		<div class="card-base about-card">
			<div class="section-label">About Crypto ETF Flows</div>
			<p class="about-text">
				Crypto ETF flows track daily and weekly net inflows and outflows for Bitcoin and Ethereum spot ETFs.
				Positive flows indicate institutional and retail capital entering the products; negative flows indicate
				redemptions. <strong>Streak</strong> shows how many consecutive days a product has seen inflows or
				outflows — a useful indicator of sustained momentum. AUM (Assets Under Management) reflects total
				market value of each fund's holdings.
			</p>
			<p class="about-text">
				Data is aggregated from SEC Form N-CEN filings, issuer disclosures, and market data providers.
				BTC and ETH spot ETFs began US trading in January 2024 and May 2024 respectively.
			</p>
		</div>

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

	/* ── Summary Cards ───────────────────────────────────────────────── */
	.summary-cards {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 16px;
	}

	@media (max-width: 640px) {
		.summary-cards { grid-template-columns: 1fr; }
	}

	.summary-card {
		background: var(--bg-surface);
		border: 1px solid var(--border-default);
		border-radius: 12px;
		padding: 20px;
	}

	.btc-card { border-top: 2px solid #f7931a40; }
	.eth-card  { border-top: 2px solid #627eea40; }

	.summary-card-header {
		display: flex;
		align-items: center;
		gap: 8px;
		margin-bottom: 16px;
	}

	.asset-icon {
		font-size: 20px;
		font-weight: 700;
		color: #f7931a;
		line-height: 1;
	}

	.eth-icon {
		color: #627eea;
	}

	.asset-label {
		font-family: 'SF Mono', 'Fira Code', 'JetBrains Mono', monospace;
		font-size: 13px;
		font-weight: 700;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		color: var(--text-primary);
	}

	.summary-stats {
		display: flex;
		flex-direction: column;
		gap: 10px;
	}

	.stat-row {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		gap: 8px;
	}

	.stat-label {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 11px;
		font-weight: 500;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		color: var(--text-dimmed);
	}

	.stat-val {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 16px;
		font-weight: 700;
		color: var(--text-primary);
		text-align: right;
	}

	/* ── Section label ───────────────────────────────────────────────── */
	.section-label {
		font-family: 'SF Mono', 'Fira Code', 'JetBrains Mono', monospace;
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
	}

	.data-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 13px;
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

	.truncate {
		max-width: 180px;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.ticker-mono {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 12px;
		font-weight: 700;
		color: var(--text-primary);
		letter-spacing: 0.02em;
	}

	/* ── Streak Badge ─────────────────────────────────────────────────── */
	.streak-badge {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 10px;
		font-weight: 600;
		padding: 2px 6px;
		border-radius: 4px;
		border: 1px solid;
		white-space: nowrap;
		letter-spacing: 0.02em;
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

	/* ── About ────────────────────────────────────────────────────────── */
	.about-card {
		border-color: var(--border-subtle, rgba(255,255,255,0.06));
	}

	.about-text {
		font-size: 12px;
		line-height: 1.7;
		color: var(--text-muted);
		max-width: 800px;
	}

	.about-text + .about-text {
		margin-top: 8px;
	}

	.about-text strong {
		color: var(--text-secondary);
		font-weight: 600;
	}
</style>
