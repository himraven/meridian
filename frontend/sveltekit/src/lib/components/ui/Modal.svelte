<script lang="ts">
	import type { Snippet } from 'svelte';
	
	interface Props {
		open: boolean;
		title?: string;
		onClose: () => void;
		children: Snippet;
	}
	
	let { open = $bindable(), title, onClose, children }: Props = $props();
	
	function handleBackdropClick(e: MouseEvent) {
		if (e.target === e.currentTarget) {
			onClose();
		}
	}
	
	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape' && open) {
			onClose();
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

{#if open}
	<div 
		class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
		onclick={handleBackdropClick}
	>
		<div class="bg-card rounded-lg border border-accent/30 shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden fade-in">
			{#if title}
				<div class="px-6 py-4 border-b border-accent/20 flex items-center justify-between">
					<h2 class="text-xl font-semibold text-white">{title}</h2>
					<button 
						onclick={onClose}
						class="text-muted hover:text-white transition-colors"
					>
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				</div>
			{/if}
			<div class="p-6 overflow-y-auto scrollbar-thin max-h-[calc(90vh-6rem)]">
				{@render children()}
			</div>
		</div>
	</div>
{/if}
