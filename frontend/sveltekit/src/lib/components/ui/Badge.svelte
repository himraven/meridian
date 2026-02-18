<script lang="ts">
	import type { Snippet } from 'svelte';
	
	interface Props {
		variant?: 'bullish' | 'bearish' | 'neutral' | 'warning' | 'success' | 'info';
		class?: string;
		children: Snippet;
	}
	
	let { variant = 'neutral', class: className = '', children }: Props = $props();
	
	// Only bullish/bearish get color — everything else is muted gray
	const variantClasses: Record<string, string> = {
		bullish: 'badge-bullish',
		bearish: 'badge-bearish',
		neutral: 'badge-neutral',
		warning: 'badge-neutral',  // grayscale
		success: 'badge-bullish',
		info:    'badge-neutral',  // grayscale
	};
</script>

<span class="badge {variantClasses[variant]} {className}">
	{@render children()}
</span>

<style>
	.badge {
		display: inline-flex;
		align-items: center;
		font-family: 'JetBrains Mono', 'SF Mono', 'Cascadia Code', monospace;
		font-size: 11px;
		letter-spacing: 0.05em;
		font-weight: 500;
		text-transform: uppercase;
	}

	/* Market direction — only colored variants; text only, no background */
	.badge-bullish {
		color: var(--green);
	}

	.badge-bearish {
		color: var(--red);
	}

	/* Everything else — muted, no background */
	.badge-neutral {
		color: var(--text-muted);
	}
</style>
