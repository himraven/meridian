<script lang="ts">
	import Card from '$lib/components/ui/Card.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import { formatDate, formatNumber, formatPercent } from '$lib/utils/format';
	import { api } from '$lib/api';
	import { goto } from '$app/navigation';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	// ── Filter state ────────────────────────────────────────────────
	let sortBy          = $state(data.filters.sort_by ?? 'short_interest');
	let minShortRatio   = $state<number | ''>(data.filters.min_short_ratio ?? '');
	let minDaysToCover  = $state<number | ''>(data.filters.min_days_to_cover ?? '');
	let tickerSearch    = $state(data.filters.ticker ?? '');

	// ── Row data (supports Load More) ───────────────────────────────
	let rows = $state<any[]>(data.data?.data ?? []);
	let metadata = $state<any>(data.data?.metadata ?? {});
	let loadingMore = $state(false);
	let currentLimit = $state(data.filters.limit ?? 50);

	// ── Helpers ─────────────────────────────────────────────────────
	function fmtShares(n: number | null | undefined): string {
		if (n === null || n === undefined || isNaN(n)) return '—';
		return formatNumber(n, 1);
	}

	function fmtPct(n: number | null | undefined): string {
		if (n === null || n === undefined || isNaN(n) || n === 0) return '—';
		return `${n.toFixed(1)}%`;
	}

	function fmtDays(n: number | null | undefined): string {
		if (n === null || n === undefined || isNaN(n) || n === 0) return '—';
		return `${n.toFixed(1)}d`;
	}

	function fmtChangePct(n: number | null | undefined): string {
		if (n === null || n === undefined || isNaN(n)) return '—';
		const sign = n > 0 ? '+' : '';
		return `${sign}${n.toFixed(2)}%`;
	}

	function changePctColor(n: number | null | undefined): string {
		if (n === null || n === undefined || isNaN(n)) return 'text-[var(--text-dimmed)]';
		// SI increase = bearish (red), decrease = bullish (green)
		if (n > 0) return 'text-[var(--red)]';
		if (n < 0) return 'text-[var(--green)]';
		return 'text-[var(--text-dimmed)]';
	}

	function isSqueeze(row: any): boolean {
		return (row.short_pct_float ?? 0) > 20 && (row.days_to_cover ?? 0) > 5;
	}

	// ── KPI derivations ─────────────────────────────────────────────
	const kpiMostShorted = $derived(() => {
		if (!rows.length) return null;
		return rows.reduce((best, r) =>
			(r.short_interest ?? 0) > (best.short_interest ?? 0) ? r : best
		, rows[0]);
	});

	const kpiBiggestIncrease = $derived(() => {
		if (!rows.length) return null;
		const filtered = rows.filter(r => (r.change_pct ?? 0) > 0);
		if (!filtered.length) return null;
		return filtered.reduce((best, r) =>
			(r.change_pct ?? 0) > (best.change_pct ?? 0) ? r : best
		, filtered[0]);
	});

	const kpiHighestDtc = $derived(() => {
		if (!rows.length) return null;
		return rows.reduce((best, r) =>
			(r.days_to_cover ?? 0) > (best.days_to_cover ?? 0) ? r : best
		, rows[0]);
	});

	const kpiHighestSiFloat = $derived(() => {
		if (!rows.length) return null;
		return rows.reduce((best, r) =>
			(r.short_pct_float ?? 0) > (best.short_pct_float ?? 0) ? r : best
		, rows[0]);
	});

	// Settlement date from first record
	const settlementDate = $derived(() => {
		if (!rows.length) return null;
		return rows[0]?.settlement_date ?? null;
	});

	const squeezeCount = $derived(() => rows.filter(isSqueeze).length);

	// ── Actions ─────────────────────────────────────────────────────
	function applyFilters() {
		const params = new URLSearchParams();
		params.set('sort_by', sortBy);
		if (minShortRatio !== '') params.set('min_short_ratio', String(minShortRatio));
		if (minDaysToCover !== '') params.set('min_days_to_cover', String(minDaysToCover));
		if (tickerSearch.trim()) params.set('ticker', tickerSearch.trim().toUpperCase());
		goto(`/short-interest?${params.toString()}`, { replaceState: true });
	}

	function resetFilters() {
		sortBy = 'short_interest';
		minShortRatio = '';
		minDaysToCover = '';
		tickerSearch = '';
		goto('/short-interest', { replaceState: true });
	}

	async function loadMore() {
		loadingMore = true;
		try {
			const nextLimit = currentLimit + 50;
			const result: any = await api.shortInterest.list({
				limit: nextLimit,
				sort_by: sortBy,
				min_short_ratio: minShortRatio !== '' ? Number(minShortRatio) : undefined,
				min_days_to_cover: minDaysToCover !== '' ? Number(minDaysToCover) : undefined,
				ticker: tickerSearch.trim() || undefined
			});
			rows = result.data ?? [];
			metadata = result.metadata ?? {};
			currentLimit = nextLimit;
		} catch (e) {
			console.error('Load more failed:', e);
		} finally {
			loadingMore = false;
		}
	}

	const hasMore = $derived(() => rows.length < (metadata.filtered ?? metadata.total ?? 0));
</script>

<svelte:head>
	<title>Short Interest — Meridian</title>
</svelte:head>

<div class="space-y-6">

	<!-- ── Header ─────────────────────────────────────────────── -->
	<div class="flex flex-wrap items-start justify-between gap-3">
		<div>
			<h1 class="text-heading mb-1">Short Interest</h1>
			<p class="text-[var(--text-secondary)]">
				Track heavily shorted stocks across US markets. Identify potential short squeeze setups.
			</p>
		</div>
		{#if settlementDate()}
			<div class="settlement-badge">
				<span class="text-[var(--text-dimmed)] text-xs">Settlement</span>
				<span class="font-mono text-xs text-[var(--text-muted)] ml-1">{formatDate(settlementDate())}</span>
			</div>
		{/if}
	</div>

	{#if data.error}
		<!-- Error state -->
		<Card>
			{#snippet children()}
				<div class="text-center py-8">
					<p class="text-[var(--red)] mb-2">Failed to load data</p>
					<p class="text-sm text-[var(--text-muted)]">{data.error}</p>
				</div>
			{/snippet}
		</Card>
	{:else if !rows.length}
		<EmptyState title="No Data Available" message="Short interest data is not yet loaded. Check back soon." />
	{:else}

		<!-- ── KPI Cards ───────────────────────────────────────── -->
		<div class="grid grid-cols-2 lg:grid-cols-4 gap-4">

			<!-- Most Shorted -->
			<Card hover>
				{#snippet children()}
					<div class="kpi-card">
						<p class="kpi-label">Most Shorted</p>
						{#if kpiMostShorted()}
							<a href="/ticker/{kpiMostShorted().ticker}" class="kpi-ticker">
								{kpiMostShorted().ticker}
							</a>
							<p class="kpi-value">{fmtShares(kpiMostShorted().short_interest)}</p>
							<p class="kpi-sub">shares short</p>
						{:else}
							<p class="kpi-value">—</p>
						{/if}
					</div>
				{/snippet}
			</Card>

			<!-- Biggest SI Increase -->
			<Card hover>
				{#snippet children()}
					<div class="kpi-card">
						<p class="kpi-label">Biggest SI Increase</p>
						{#if kpiBiggestIncrease()}
							<a href="/ticker/{kpiBiggestIncrease().ticker}" class="kpi-ticker">
								{kpiBiggestIncrease().ticker}
							</a>
							<p class="kpi-value text-[var(--red)]">+{kpiBiggestIncrease().change_pct?.toFixed(2)}%</p>
							<p class="kpi-sub">vs prior period</p>
						{:else}
							<p class="kpi-value">—</p>
						{/if}
					</div>
				{/snippet}
			</Card>

			<!-- Highest Days to Cover -->
			<Card hover>
				{#snippet children()}
					<div class="kpi-card">
						<p class="kpi-label">Highest Days to Cover</p>
						{#if kpiHighestDtc()}
							<a href="/ticker/{kpiHighestDtc().ticker}" class="kpi-ticker">
								{kpiHighestDtc().ticker}
							</a>
							<p class="kpi-value text-[var(--amber)]">{fmtDays(kpiHighestDtc().days_to_cover)}</p>
							<p class="kpi-sub">to cover short</p>
						{:else}
							<p class="kpi-value">—</p>
						{/if}
					</div>
				{/snippet}
			</Card>

			<!-- Highest Short % Float -->
			<Card hover>
				{#snippet children()}
					<div class="kpi-card">
						<p class="kpi-label">Highest Short % Float</p>
						{#if kpiHighestSiFloat()}
							<a href="/ticker/{kpiHighestSiFloat().ticker}" class="kpi-ticker">
								{kpiHighestSiFloat().ticker}
							</a>
							<p class="kpi-value text-[var(--red)]">{fmtPct(kpiHighestSiFloat().short_pct_float)}</p>
							<p class="kpi-sub">of float shorted</p>
						{:else}
							<p class="kpi-value">—</p>
						{/if}
					</div>
				{/snippet}
			</Card>

		</div>

		<!-- ── Filters ────────────────────────────────────────── -->
		<Card title="Filters">
			{#snippet children()}
				<div class="flex flex-wrap gap-4 items-end">

					<div class="filter-group">
						<label class="text-label mb-1 block" for="sort-by">Sort By</label>
						<select
							id="sort-by"
							bind:value={sortBy}
							class="filter-input"
						>
							<option value="short_interest">Short Interest</option>
							<option value="short_ratio">Short % Float</option>
							<option value="days_to_cover">Days to Cover</option>
							<option value="change_pct">Change %</option>
						</select>
					</div>

					<div class="filter-group">
						<label class="text-label mb-1 block" for="min-si-float">Min Short % Float</label>
						<input
							id="min-si-float"
							type="number"
							bind:value={minShortRatio}
							min="0"
							max="100"
							step="1"
							placeholder="e.g. 10"
							class="filter-input filter-input-sm"
						/>
					</div>

					<div class="filter-group">
						<label class="text-label mb-1 block" for="min-dtc">Min Days to Cover</label>
						<input
							id="min-dtc"
							type="number"
							bind:value={minDaysToCover}
							min="0"
							step="0.5"
							placeholder="e.g. 3"
							class="filter-input filter-input-sm"
						/>
					</div>

					<div class="filter-group">
						<label class="text-label mb-1 block" for="ticker-search">Ticker</label>
						<input
							id="ticker-search"
							type="text"
							bind:value={tickerSearch}
							placeholder="e.g. TSLA"
							class="filter-input filter-input-sm uppercase"
							onkeydown={(e) => e.key === 'Enter' && applyFilters()}
						/>
					</div>

					<div class="flex gap-2 items-end">
						<button onclick={applyFilters} class="btn-primary">
							Apply
						</button>
						<button onclick={resetFilters} class="btn-secondary">
							Reset
						</button>
					</div>

				</div>
			{/snippet}
		</Card>

		<!-- ── Data Table ─────────────────────────────────────── -->
		<Card>
			{#snippet children()}
				<!-- Table header row with meta info -->
				<div class="flex flex-wrap items-center justify-between gap-2 mb-4">
					<div class="flex items-center gap-3">
						<span class="text-label">Short Interest Data</span>
						<span class="meta-badge">{metadata.filtered ?? rows.length} stocks</span>
						{#if squeezeCount() > 0}
							<span class="squeeze-meta-badge">
								🔥 {squeezeCount()} squeeze setups
							</span>
						{/if}
					</div>
					{#if settlementDate()}
						<span class="text-xs text-[var(--text-dimmed)]">
							As of {formatDate(settlementDate())}
						</span>
					{/if}
				</div>

				<div class="overflow-x-auto -mx-5 px-5">
					<table class="w-full text-sm min-w-[900px]">
						<thead>
							<tr class="border-b border-[var(--border-default)]">
								<th class="th-cell text-left">Ticker</th>
								<th class="th-cell text-left hidden md:table-cell">Company</th>
								<th class="th-cell text-right">Short Interest</th>
								<th class="th-cell text-right hidden lg:table-cell">Prior SI</th>
								<th class="th-cell text-right">Change %</th>
								<th class="th-cell text-right">Days to Cover</th>
								<th class="th-cell text-right">SI % Float</th>
								<th class="th-cell text-right hidden lg:table-cell">Avg Volume</th>
								<th class="th-cell text-right hidden xl:table-cell">Settlement</th>
							</tr>
						</thead>
						<tbody>
							{#each rows as row (row.ticker + (row.settlement_date ?? ''))}
								{@const squeeze = isSqueeze(row)}
								<tr class="data-row {squeeze ? 'squeeze-row' : ''}">
									<!-- Ticker -->
									<td class="td-cell">
										<div class="flex items-center gap-2">
											{#if squeeze}
												<span class="squeeze-badge" title="Squeeze potential: SI Float &gt;20% and Days to Cover &gt;5">🔥</span>
											{/if}
											<a href="/ticker/{row.ticker}" class="ticker-link">
												{row.ticker}
											</a>
										</div>
									</td>

									<!-- Company -->
									<td class="td-cell hidden md:table-cell">
										<span class="company-name">{row.company || '—'}</span>
									</td>

									<!-- Short Interest -->
									<td class="td-cell text-right">
										<span class="data-num">{fmtShares(row.short_interest)}</span>
									</td>

									<!-- Prior SI -->
									<td class="td-cell text-right hidden lg:table-cell">
										<span class="data-num text-[var(--text-dimmed)]">{fmtShares(row.prior_short_interest)}</span>
									</td>

									<!-- Change % -->
									<td class="td-cell text-right">
										<span class="data-num {changePctColor(row.change_pct)}">
											{fmtChangePct(row.change_pct)}
										</span>
									</td>

									<!-- Days to Cover -->
									<td class="td-cell text-right">
										<span class="data-num {(row.days_to_cover ?? 0) > 5 ? 'text-[var(--amber)]' : ''}">
											{fmtDays(row.days_to_cover)}
										</span>
									</td>

									<!-- SI % Float -->
									<td class="td-cell text-right">
										<span class="data-num {(row.short_pct_float ?? 0) > 20 ? 'text-[var(--red)]' : ''}">
											{fmtPct(row.short_pct_float)}
										</span>
									</td>

									<!-- Avg Volume -->
									<td class="td-cell text-right hidden lg:table-cell">
										<span class="data-num text-[var(--text-muted)]">{fmtShares(row.avg_daily_volume)}</span>
									</td>

									<!-- Settlement Date -->
									<td class="td-cell text-right hidden xl:table-cell">
										<span class="text-[var(--text-dimmed)] text-xs tabular-nums">{row.settlement_date ?? '—'}</span>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>

				<!-- Load More -->
				{#if hasMore()}
					<div class="mt-6 flex justify-center">
						<button
							onclick={loadMore}
							disabled={loadingMore}
							class="load-more-btn"
						>
							{#if loadingMore}
								<span class="spinner"></span>
								Loading…
							{:else}
								Load More
								<span class="text-[var(--text-dimmed)] ml-1 text-xs">
									({rows.length} / {metadata.filtered ?? metadata.total})
								</span>
							{/if}
						</button>
					</div>
				{:else}
					<p class="text-center text-xs text-[var(--text-dimmed)] mt-4">
						Showing all {rows.length} results
					</p>
				{/if}

			{/snippet}
		</Card>

	{/if}

</div>

<style>
	/* ── Settlement badge ──────────────────────────────────────── */
	.settlement-badge {
		display: flex;
		align-items: center;
		background: var(--bg-surface);
		border: 1px solid var(--border-default);
		border-radius: 8px;
		padding: 6px 12px;
		flex-shrink: 0;
	}

	/* ── KPI Cards ─────────────────────────────────────────────── */
	.kpi-card {
		text-align: center;
		padding: 4px 0;
	}

	.kpi-label {
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--text-dimmed);
		margin-bottom: 10px;
	}

	.kpi-ticker {
		display: inline-block;
		font-family: 'JetBrains Mono', 'SF Mono', 'Cascadia Code', monospace;
		font-size: 15px;
		font-weight: 700;
		letter-spacing: 0.04em;
		color: var(--blue);
		text-decoration: none;
		margin-bottom: 4px;
		transition: color 120ms;
	}

	.kpi-ticker:hover {
		color: var(--text-primary);
	}

	.kpi-value {
		font-family: 'JetBrains Mono', 'SF Mono', 'Cascadia Code', monospace;
		font-size: 22px;
		font-weight: 700;
		letter-spacing: -0.02em;
		color: var(--text-primary);
		line-height: 1.2;
		margin-bottom: 4px;
	}

	.kpi-sub {
		font-size: 11px;
		color: var(--text-dimmed);
	}

	/* ── Filters ───────────────────────────────────────────────── */
	.filter-group {
		display: flex;
		flex-direction: column;
	}

	.filter-input {
		background: var(--bg-elevated);
		border: 1px solid var(--border-default);
		border-radius: 7px;
		padding: 7px 10px;
		font-size: 13px;
		color: var(--text-primary);
		outline: none;
		transition: border-color 150ms;
	}

	.filter-input:focus {
		border-color: var(--border-focus);
	}

	.filter-input-sm {
		width: 110px;
	}

	.btn-primary {
		padding: 7px 18px;
		background: var(--blue);
		color: #fff;
		font-size: 13px;
		font-weight: 500;
		border: none;
		border-radius: 7px;
		cursor: pointer;
		transition: opacity 150ms;
	}

	.btn-primary:hover {
		opacity: 0.85;
	}

	.btn-secondary {
		padding: 7px 14px;
		background: var(--bg-elevated);
		color: var(--text-primary);
		font-size: 13px;
		border: 1px solid var(--border-default);
		border-radius: 7px;
		cursor: pointer;
		transition: border-color 150ms, background 150ms;
	}

	.btn-secondary:hover {
		border-color: var(--border-hover);
		background: var(--border-default);
	}

	/* ── Table ─────────────────────────────────────────────────── */
	.meta-badge {
		font-size: 11px;
		font-weight: 500;
		color: var(--text-dimmed);
		background: var(--bg-elevated);
		border: 1px solid var(--border-default);
		border-radius: 20px;
		padding: 2px 8px;
	}

	.squeeze-meta-badge {
		font-size: 11px;
		font-weight: 600;
		color: var(--amber);
		background: color-mix(in srgb, var(--amber) 12%, transparent);
		border: 1px solid color-mix(in srgb, var(--amber) 25%, transparent);
		border-radius: 20px;
		padding: 2px 8px;
	}

	.th-cell {
		padding: 10px 12px;
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		color: var(--text-dimmed);
		white-space: nowrap;
	}

	.data-row {
		border-bottom: 1px solid color-mix(in srgb, var(--border-default) 50%, transparent);
		transition: background 120ms;
	}

	.data-row:hover {
		background: color-mix(in srgb, var(--bg-elevated) 60%, transparent);
	}

	.data-row:last-child {
		border-bottom: none;
	}

	/* Squeeze row: amber left border accent */
	.squeeze-row {
		border-left: 3px solid color-mix(in srgb, var(--amber) 70%, transparent);
		background: color-mix(in srgb, var(--amber) 4%, transparent);
	}

	.squeeze-row:hover {
		background: color-mix(in srgb, var(--amber) 7%, transparent);
	}

	.td-cell {
		padding: 10px 12px;
		vertical-align: middle;
	}

	.ticker-link {
		font-family: 'JetBrains Mono', 'SF Mono', 'Cascadia Code', monospace;
		font-size: 13px;
		font-weight: 700;
		letter-spacing: 0.04em;
		color: var(--blue);
		text-decoration: none;
		transition: color 120ms;
	}

	.ticker-link:hover {
		color: var(--text-primary);
	}

	.company-name {
		display: block;
		max-width: 180px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		color: var(--text-muted);
		font-size: 12px;
	}

	.data-num {
		font-family: 'JetBrains Mono', 'SF Mono', 'Cascadia Code', monospace;
		font-size: 12px;
		letter-spacing: 0.02em;
		color: var(--text-primary);
		white-space: nowrap;
		tabular-nums: all;
	}

	.squeeze-badge {
		font-size: 13px;
		flex-shrink: 0;
		line-height: 1;
	}

	/* ── Load More ─────────────────────────────────────────────── */
	.load-more-btn {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 8px 24px;
		background: var(--bg-elevated);
		border: 1px solid var(--border-default);
		border-radius: 8px;
		font-size: 13px;
		font-weight: 500;
		color: var(--text-primary);
		cursor: pointer;
		transition: border-color 150ms, background 150ms;
	}

	.load-more-btn:hover:not(:disabled) {
		border-color: var(--border-hover);
		background: var(--border-default);
	}

	.load-more-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.spinner {
		display: inline-block;
		width: 12px;
		height: 12px;
		border: 2px solid var(--border-default);
		border-top-color: var(--text-muted);
		border-radius: 50%;
		animation: spin 0.7s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	/* ── Responsive overrides ───────────────────────────────────── */
	@media (max-width: 640px) {
		.kpi-value {
			font-size: 18px;
		}

		.kpi-ticker {
			font-size: 13px;
		}
	}
</style>
