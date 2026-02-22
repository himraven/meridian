<svelte:head>
	<title>Market Regime — Meridian</title>
</svelte:head>

<script lang="ts">
	let { data }: { data: any } = $props();

	const regimeColors: Record<string, string> = {
		green: 'var(--green)',
		yellow: 'var(--amber)',
		red: 'var(--red, #ef4444)',
		unknown: 'var(--text-muted)',
	};
	const regimeLabels: Record<string, string> = {
		green: 'NORMAL',
		yellow: 'CAUTION',
		red: 'CRISIS',
		unknown: 'N/A',
	};
	const regimeDescriptions: Record<string, string> = {
		green: 'All indicators suggest a risk-on environment. Conditions favor growth-oriented positioning.',
		yellow: 'Some indicators showing stress. Consider reducing risk exposure and monitoring closely.',
		red: 'Multiple indicators in crisis territory. Defensive positioning recommended.',
		unknown: 'Unable to determine current regime. Data may be temporarily unavailable.',
	};
</script>

<div class="page-container">
	<header class="page-header">
		<h1 class="page-title">Market Regime</h1>
		<p class="page-subtitle">Real-time market environment assessment via VIX, trend, and credit signals</p>
	</header>

	{#if data.regime}
		{@const r = data.regime}
		{@const color = regimeColors[r.regime] ?? 'var(--text-muted)'}

		<!-- Main Regime Card -->
		<div class="regime-hero" style="border-color: {color}">
			<div class="regime-hero-top">
				<div class="regime-dot" style="background: {color}; box-shadow: 0 0 12px {color}"></div>
				<span class="regime-label" style="color: {color}">
					{regimeLabels[r.regime] ?? r.regime.toUpperCase()}
				</span>
			</div>
			<p class="regime-summary">{r.summary}</p>
			<p class="regime-description">{regimeDescriptions[r.regime] ?? ''}</p>
		</div>

		<!-- Components Grid -->
		<div class="components-grid">
			<!-- VIX -->
			{#if r.components?.vix}
				{@const vix = r.components.vix}
				<div class="comp-card">
					<div class="comp-header">
						<span class="comp-title">VIX (Fear Index)</span>
						<span class="comp-badge" style="color: {regimeColors[vix.status] ?? 'var(--text-muted)'}">
							{vix.label}
						</span>
					</div>
					<div class="comp-value" style="color: {regimeColors[vix.status] ?? 'var(--text-muted)'}">
						{vix.value?.toFixed(1)}
					</div>
					<div class="comp-thresholds">
						<span class="threshold green">Normal: {vix.thresholds?.green}</span>
						<span class="threshold yellow">Elevated: {vix.thresholds?.yellow}</span>
						<span class="threshold red">Crisis: {vix.thresholds?.red}</span>
					</div>
					<p class="comp-explain">CBOE Volatility Index — measures expected 30-day market volatility. Higher = more fear.</p>
				</div>
			{/if}

			<!-- SPY vs MA200 -->
			{#if r.components?.spy_ma200}
				{@const spy = r.components.spy_ma200}
				{@const spyColor = spy.status === 'bullish' ? 'var(--green)' : spy.status === 'bearish' ? 'var(--red, #ef4444)' : 'var(--text-muted)'}
				<div class="comp-card">
					<div class="comp-header">
						<span class="comp-title">SPY vs 200-Day MA</span>
						<span class="comp-badge" style="color: {spyColor}">
							{spy.label}
						</span>
					</div>
					<div class="comp-value" style="color: {spyColor}">
						{spy.pct_above > 0 ? '+' : ''}{spy.pct_above?.toFixed(1)}%
					</div>
					<div class="comp-detail">
						<span>SPY: ${spy.spy_price?.toFixed(2)}</span>
						<span>MA200: ${spy.ma200?.toFixed(2)}</span>
					</div>
					<p class="comp-explain">Price relative to 200-day moving average. Above = bullish trend. Below = bearish trend.</p>
				</div>
			{/if}

			<!-- Credit Spread -->
			{#if r.components?.credit_spread}
				{@const cs = r.components.credit_spread}
				<div class="comp-card">
					<div class="comp-header">
						<span class="comp-title">HY Credit Spread</span>
						<span class="comp-badge" style="color: {regimeColors[cs.status] ?? 'var(--text-muted)'}">
							{cs.label}
						</span>
					</div>
					<div class="comp-value" style="color: {regimeColors[cs.status] ?? 'var(--text-muted)'}">
						{cs.value?.toFixed(2)}%
					</div>
					<div class="comp-thresholds">
						<span class="threshold green">Normal: {cs.thresholds?.green}</span>
						<span class="threshold yellow">Stress: {cs.thresholds?.yellow}</span>
						<span class="threshold red">Crisis: {cs.thresholds?.red}</span>
					</div>
					<p class="comp-explain">{cs.description} — wider spread = more credit stress, risk-off.</p>
				</div>
			{/if}
		</div>

		<!-- How to Read -->
		<div class="how-to-read">
			<h2 class="section-title">How to Read</h2>
			<div class="reading-grid">
				<div class="reading-item">
					<span class="reading-dot" style="background: var(--green)"></span>
					<div>
						<strong>Normal (Green)</strong>
						<p>All indicators healthy. VIX &lt;20, SPY above MA200, spreads tight. Risk-on favored.</p>
					</div>
				</div>
				<div class="reading-item">
					<span class="reading-dot" style="background: var(--amber)"></span>
					<div>
						<strong>Caution (Yellow)</strong>
						<p>One or more indicators showing stress. Reduce leverage, tighten stops, monitor daily.</p>
					</div>
				</div>
				<div class="reading-item">
					<span class="reading-dot" style="background: var(--red, #ef4444)"></span>
					<div>
						<strong>Crisis (Red)</strong>
						<p>Multiple indicators in danger zone. Capital preservation mode. Consider hedges.</p>
					</div>
				</div>
			</div>
		</div>

		{#if r.cached_at}
			<p class="cache-time">Last updated: {new Date(r.cached_at).toLocaleString()}</p>
		{/if}
	{:else}
		<div class="error-state">
			<p>Unable to load market regime data. Please try again later.</p>
		</div>
	{/if}
</div>

<style>
	.page-container {
		max-width: 800px;
		margin: 0 auto;
		padding: 24px 16px;
	}
	.page-header {
		margin-bottom: 24px;
	}
	.page-title {
		font-size: 20px;
		font-weight: 600;
		color: var(--text-primary);
		margin-bottom: 4px;
	}
	.page-subtitle {
		font-size: 13px;
		color: var(--text-muted);
	}

	/* Hero Card */
	.regime-hero {
		background: var(--bg-elevated);
		border: 1px solid var(--border-default);
		border-left: 3px solid;
		border-radius: 10px;
		padding: 20px 24px;
		margin-bottom: 24px;
	}
	.regime-hero-top {
		display: flex;
		align-items: center;
		gap: 10px;
		margin-bottom: 8px;
	}
	.regime-dot {
		width: 12px;
		height: 12px;
		border-radius: 50%;
		flex-shrink: 0;
	}
	.regime-label {
		font-size: 13px;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}
	.regime-summary {
		font-size: 15px;
		color: var(--text-secondary);
		margin-bottom: 6px;
	}
	.regime-description {
		font-size: 13px;
		color: var(--text-muted);
		line-height: 1.5;
	}

	/* Components Grid */
	.components-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
		gap: 16px;
		margin-bottom: 24px;
	}
	.comp-card {
		background: var(--bg-surface);
		border: 1px solid var(--border-default);
		border-radius: 10px;
		padding: 16px;
	}
	.comp-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 12px;
	}
	.comp-title {
		font-size: 12px;
		font-weight: 600;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		color: var(--text-dimmed);
	}
	.comp-badge {
		font-size: 11px;
		font-weight: 600;
	}
	.comp-value {
		font-size: 28px;
		font-weight: 700;
		font-family: 'JetBrains Mono', monospace;
		margin-bottom: 10px;
	}
	.comp-thresholds {
		display: flex;
		flex-direction: column;
		gap: 2px;
		margin-bottom: 10px;
	}
	.threshold {
		font-size: 11px;
		font-family: 'JetBrains Mono', monospace;
		color: var(--text-dimmed);
	}
	.threshold.green::before { content: '🟢 '; }
	.threshold.yellow::before { content: '🟡 '; }
	.threshold.red::before { content: '🔴 '; }
	.comp-detail {
		display: flex;
		justify-content: space-between;
		font-size: 12px;
		font-family: 'JetBrains Mono', monospace;
		color: var(--text-muted);
		margin-bottom: 10px;
	}
	.comp-explain {
		font-size: 11px;
		color: var(--text-dimmed);
		line-height: 1.4;
	}

	/* How to Read */
	.how-to-read {
		background: var(--bg-surface);
		border: 1px solid var(--border-default);
		border-radius: 10px;
		padding: 16px;
		margin-bottom: 16px;
	}
	.section-title {
		font-size: 12px;
		font-weight: 600;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--text-dimmed);
		margin-bottom: 12px;
	}
	.reading-grid {
		display: flex;
		flex-direction: column;
		gap: 12px;
	}
	.reading-item {
		display: flex;
		align-items: flex-start;
		gap: 10px;
	}
	.reading-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		margin-top: 5px;
		flex-shrink: 0;
	}
	.reading-item strong {
		font-size: 13px;
		color: var(--text-primary);
	}
	.reading-item p {
		font-size: 12px;
		color: var(--text-muted);
		line-height: 1.4;
		margin-top: 2px;
	}
	.cache-time {
		font-size: 11px;
		color: var(--text-dimmed);
		text-align: right;
	}
	.error-state {
		text-align: center;
		padding: 3rem;
		color: var(--text-muted);
	}
</style>
