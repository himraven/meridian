<script lang="ts">
	interface Props {
		icon?: string;
		title: string;
		description?: string;
		class?: string;
	}
	
	let { 
		icon = '📭', 
		title, 
		description,
		class: className = ''
	}: Props = $props();
</script>

<div class="flex flex-col items-center justify-center py-12 px-4 text-center {className}">
	<div class="text-6xl mb-4 opacity-50">{icon}</div>
	<h3 class="text-lg font-semibold text-white mb-2">{title}</h3>
	{#if description}
		<p class="text-sm text-muted max-w-md">{description}</p>
	{/if}
</div>
