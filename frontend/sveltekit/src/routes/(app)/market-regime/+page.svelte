<svelte:head>
	<title>Market Regime — Meridian</title>
</svelte:head>

<div class="coming-soon-page">
	<div class="coming-soon-content">
		<span class="coming-soon-badge">Coming Soon</span>
		<h1 class="coming-soon-title">Market Regime</h1>
		<p class="coming-soon-desc">
			Identify the current market regime — risk-on, risk-off, or transition — using 
			cross-asset signals, volatility structure, and macro indicators. 
			Understand whether conditions favor aggressive or defensive positioning.
		</p>
		<p class="coming-soon-note">
			This indicator will synthesize VIX term structure, credit spreads, 
			yield curve dynamics, and sector rotation patterns.
		</p>
	</div>
</div>

<style>
	.coming-soon-page {
		display: flex;
		align-items: center;
		justify-content: center;
		min-height: 60vh;
		padding: 2rem;
	}
	.coming-soon-content {
		text-align: center;
		max-width: 480px;
	}
	.coming-soon-badge {
		display: inline-block;
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--text-dimmed);
		background: var(--bg-elevated);
		border: 1px solid var(--border-default);
		padding: 4px 12px;
		border-radius: 12px;
		margin-bottom: 16px;
	}
	.coming-soon-title {
		font-size: 24px;
		font-weight: 600;
		color: var(--text-primary);
		margin-bottom: 12px;
	}
	.coming-soon-desc {
		font-size: 14px;
		line-height: 1.6;
		color: var(--text-secondary);
		margin-bottom: 12px;
	}
	.coming-soon-note {
		font-size: 13px;
		color: var(--text-dimmed);
		font-style: italic;
	}
</style>
