<script lang="ts">
	import type { Snippet } from 'svelte';
	
	interface Tab {
		id: string;
		label: string;
		icon?: string;
		badge?: string | number;
		content: Snippet;
	}
	
	interface Props {
		tabs: Tab[];
		defaultTab?: string;
		class?: string;
	}
	
	let { 
		tabs, 
		defaultTab = tabs[0]?.id,
		class: className = ''
	}: Props = $props();
	
	let activeTab = $state(defaultTab);
</script>

<div class="{className}">
	<!-- Tab buttons -->
	<div class="flex border-b border-accent/30 overflow-x-auto scrollbar-thin">
		{#each tabs as tab}
			<button
				class="px-4 py-3 text-sm font-medium whitespace-nowrap transition-colors relative
					{activeTab === tab.id 
						? 'text-white' 
						: 'text-muted hover:text-white'}"
				onclick={() => activeTab = tab.id}
			>
				{#if tab.icon}
					<span class="mr-1.5">{tab.icon}</span>
				{/if}
				{tab.label}
				{#if tab.badge !== undefined}
					<span class="ml-2 px-2 py-0.5 bg-accent/40 text-blue rounded-full text-xs">
						{tab.badge}
					</span>
				{/if}
				{#if activeTab === tab.id}
					<div class="absolute bottom-0 left-0 right-0 h-0.5 bg-blue"></div>
				{/if}
			</button>
		{/each}
	</div>
	
	<!-- Tab content -->
	<div class="mt-4">
		{#each tabs as tab}
			{#if activeTab === tab.id}
				<div class="fade-in">
					{@render tab.content()}
				</div>
			{/if}
		{/each}
	</div>
</div>
