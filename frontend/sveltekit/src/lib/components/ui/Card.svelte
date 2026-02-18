<script lang="ts">
	import type { Snippet } from 'svelte';
	
	interface Props {
		title?: string;
		badge?: string;
		badgeClass?: string;
		hover?: boolean;
		class?: string;
		children: Snippet;
	}
	
	let { 
		title, 
		badge, 
		badgeClass = '',
		hover = false,
		class: className = '',
		children
	}: Props = $props();
</script>

<div class="card {hover ? 'card-hover' : ''} {className}">
	{#if title || badge}
		<div class="card-header">
			<span class="text-label">{title ?? ''}</span>
			{#if badge}
				<span class="card-badge {badgeClass}">
					{badge}
				</span>
			{/if}
		</div>
	{/if}
	<div class="card-body">
		{@render children()}
	</div>
</div>

<style>
	.card {
		background: var(--bg-surface);
		border: 1px solid var(--border-default);
		border-radius: 12px;
		overflow: hidden;
		transition: border-color 150ms;
	}

	.card-hover:hover {
		border-color: var(--border-hover);
	}

	.card-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 14px 20px;
		border-bottom: 1px solid var(--border-default);
	}

	/* .text-label is defined globally in app.css */

	.card-badge {
		font-family: 'JetBrains Mono', 'SF Mono', 'Cascadia Code', monospace;
		font-size: 11px;
		letter-spacing: 0.05em;
		color: var(--text-muted);
	}

	.card-body {
		padding: 20px;
	}
</style>
