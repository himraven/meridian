<script lang="ts">
	import { onMount } from 'svelte';

	interface SourceStatus {
		name: string;
		status: string;
		icon: string;
		age_hours: number | null;
		critical: boolean;
		schedule: string;
		message: string;
	}

	interface HealthData {
		overall: {
			status: string;
			icon: string;
			fresh: number;
			stale: number;
			missing: number;
			total: number;
			critical_issues: number;
		};
		sources: SourceStatus[];
		checked_at: string;
	}

	let health = $state<HealthData | null>(null);
	let expanded = $state(false);
	let error = $state(false);

	const statusColors: Record<string, string> = {
		healthy: 'var(--green)',
		warning: 'var(--amber)',
		degraded: 'var(--red)',
	};

	function dotColor(status: string): string {
		return statusColors[status] ?? 'var(--text-dimmed)';
	}

	function sourceIcon(s: SourceStatus): string {
		if (s.status === 'fresh') return '🟢';
		if (s.status === 'stale' && s.age_hours && s.age_hours > (s as any).max_age_hours * 1.5) return '🔴';
		if (s.status === 'stale') return '🟡';
		if (s.status === 'missing' || s.status === 'empty') return '🔴';
		return '⚪';
	}

	function formatAge(hours: number | null): string {
		if (hours === null) return '—';
		if (hours < 1) return `${Math.round(hours * 60)}m`;
		if (hours < 24) return `${Math.round(hours)}h`;
		return `${Math.round(hours / 24)}d`;
	}

	async function fetchHealth() {
		try {
			const res = await fetch('/api/data-health');
			if (!res.ok) throw new Error();
			health = await res.json();
			error = false;
		} catch {
			error = true;
		}
	}

	onMount(() => {
		fetchHealth();
		// Refresh every 5 minutes
		const interval = setInterval(fetchHealth, 5 * 60 * 1000);
		return () => clearInterval(interval);
	});
</script>

<!-- Status indicator at sidebar bottom -->
<div class="health-container">
	<button
		class="health-trigger"
		onclick={() => expanded = !expanded}
		aria-label="Data health status"
		aria-expanded={expanded}
	>
		{#if error}
			<span class="health-dot" style="background: var(--text-dimmed)"></span>
			<span class="health-label">Status unavailable</span>
		{:else if health}
			<span class="health-dot" style="background: {dotColor(health.overall.status)}"></span>
			<span class="health-label">
				{health.overall.fresh}/{health.overall.total} sources
			</span>
			{#if health.overall.critical_issues > 0}
				<span class="health-alert">{health.overall.critical_issues}</span>
			{/if}
		{:else}
			<span class="health-dot" style="background: var(--text-dimmed)"></span>
			<span class="health-label">Checking...</span>
		{/if}
	</button>

	<!-- Expanded detail panel -->
	{#if expanded && health}
		<div class="health-panel">
			<div class="panel-header">
				<span class="panel-title">Data Sources</span>
				<span class="panel-summary" style="color: {dotColor(health.overall.status)}">
					{health.overall.status}
				</span>
			</div>
			
			<div class="panel-sources">
				{#each health.sources as source}
					<div class="source-row" class:source-critical={source.critical}>
						<span class="source-status">{source.icon}</span>
						<span class="source-name">{source.name}</span>
						<span class="source-age">{formatAge(source.age_hours)}</span>
					</div>
				{/each}
			</div>

			<div class="panel-footer">
				Checked {new Date(health.checked_at).toLocaleTimeString()}
			</div>
		</div>
	{/if}
</div>

<style>
	.health-container {
		position: relative;
		margin-top: auto;
		padding: 8px;
		border-top: 1px solid var(--border-default);
	}

	.health-trigger {
		display: flex;
		align-items: center;
		gap: 8px;
		width: 100%;
		padding: 6px 10px;
		background: none;
		border: none;
		border-radius: 6px;
		cursor: pointer;
		transition: background 150ms;
	}

	.health-trigger:hover {
		background: var(--bg-elevated);
	}

	.health-dot {
		width: 7px;
		height: 7px;
		border-radius: 50%;
		flex-shrink: 0;
	}

	.health-label {
		font-size: 11px;
		color: var(--text-muted);
	}

	.health-alert {
		font-size: 10px;
		font-weight: 600;
		color: var(--red);
		background: rgba(248, 113, 113, 0.12);
		border-radius: 4px;
		padding: 1px 5px;
		margin-left: auto;
	}

	/* Panel */
	.health-panel {
		position: absolute;
		bottom: calc(100% + 4px);
		left: 4px;
		right: 4px;
		background: var(--bg-surface);
		border: 1px solid var(--border-default);
		border-radius: 10px;
		overflow: hidden;
		box-shadow: 0 -4px 24px rgba(0, 0, 0, 0.4);
		z-index: 50;
	}

	.panel-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 10px 12px;
		border-bottom: 1px solid var(--border-default);
	}

	.panel-title {
		font-size: 12px;
		font-weight: 600;
		color: var(--text-primary);
	}

	.panel-summary {
		font-size: 11px;
		font-weight: 500;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.panel-sources {
		max-height: 320px;
		overflow-y: auto;
		padding: 4px 0;
	}

	.source-row {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 5px 12px;
		font-size: 11px;
	}

	.source-row:hover {
		background: var(--bg-elevated);
	}

	.source-critical {
		/* subtle left accent for critical sources */
	}

	.source-status {
		font-size: 8px;
		flex-shrink: 0;
		width: 14px;
		text-align: center;
	}

	.source-name {
		flex: 1;
		color: var(--text-secondary);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.source-age {
		color: var(--text-muted);
		font-family: 'JetBrains Mono', monospace;
		font-size: 10px;
		flex-shrink: 0;
	}

	.panel-footer {
		padding: 6px 12px;
		border-top: 1px solid var(--border-default);
		font-size: 10px;
		color: var(--text-dimmed);
	}
</style>
