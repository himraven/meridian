<svelte:head>
	<title>Short Interest — Meridian</title>
</svelte:head>

<div class="coming-soon-page">
	<div class="coming-soon-content">
		<span class="coming-soon-badge">Coming Soon</span>
		<h1 class="coming-soon-title">Short Interest</h1>
		<p class="coming-soon-desc">
			Track the most heavily shorted stocks across US markets. View short interest ratios, 
			days to cover, and identify potential short squeeze setups alongside smart money signals.
		</p>
		<p class="coming-soon-note">
			Short interest data is currently factored into our composite signal scores. 
			This dedicated page will provide deeper analysis and historical trends.
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
