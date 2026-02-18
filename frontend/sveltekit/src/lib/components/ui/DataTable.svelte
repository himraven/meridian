<script lang="ts">
	import { writable } from 'svelte/store';
	import Skeleton from './Skeleton.svelte';
	import EmptyState from './EmptyState.svelte';
	
	interface Column {
		key: string;
		label: string;
		sortable?: boolean;
		class?: string;
		render?: (value: any, row: any) => string;
	}
	
	interface Props {
		columns: Column[];
		data: any[];
		loading?: boolean;
		emptyMessage?: string;
		class?: string;
	}
	
	let { 
		columns, 
		data = [], 
		loading = false,
		emptyMessage = 'No data available',
		class: className = ''
	}: Props = $props();
	
	let sortKey = $state<string | null>(null);
	let sortDirection = $state<'asc' | 'desc'>('asc');
	
	function handleSort(key: string) {
		if (sortKey === key) {
			sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
		} else {
			sortKey = key;
			sortDirection = 'asc';
		}
	}
	
	let sortedData = $derived(() => {
		if (!sortKey || !data) return data;
		
		return [...data].sort((a, b) => {
			const aVal = a[sortKey];
			const bVal = b[sortKey];
			
			if (aVal === null || aVal === undefined) return 1;
			if (bVal === null || bVal === undefined) return -1;
			
			let comparison = 0;
			if (typeof aVal === 'number' && typeof bVal === 'number') {
				comparison = aVal - bVal;
			} else {
				comparison = String(aVal).localeCompare(String(bVal));
			}
			
			return sortDirection === 'asc' ? comparison : -comparison;
		});
	});
</script>

<div class="overflow-x-auto scrollbar-thin {className}">
	{#if loading}
		<Skeleton type="table" />
	{:else if data.length === 0}
		<EmptyState title={emptyMessage} />
	{:else}
		<table class="rn-table">
			<thead>
				<tr>
					{#each columns as column}
						<th class="{column.class || ''}">
							{#if column.sortable}
								<button
									class="sort-btn"
									onclick={() => handleSort(column.key)}
								>
									{column.label}
									{#if sortKey === column.key}
										<span class="sort-indicator">
											{sortDirection === 'asc' ? '▲' : '▼'}
										</span>
									{/if}
								</button>
							{:else}
								{column.label}
							{/if}
						</th>
					{/each}
				</tr>
			</thead>
			<tbody>
				{#each sortedData() as row}
					<tr>
						{#each columns as column}
							<td class="{column.class || ''}">
								{#if column.render}
									{@html column.render(row[column.key], row)}
								{:else}
									{row[column.key] ?? 'N/A'}
								{/if}
							</td>
						{/each}
					</tr>
				{/each}
			</tbody>
		</table>
	{/if}
</div>

<style>
	/* Sort button inherits th monospace style from app.css .rn-table */
	.sort-btn {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		background: none;
		border: none;
		cursor: pointer;
		font-family: inherit;
		font-size: inherit;
		font-weight: inherit;
		letter-spacing: inherit;
		text-transform: inherit;
		color: var(--text-muted);
		padding: 0;
		transition: color 150ms;
	}

	.sort-btn:hover {
		color: var(--text-secondary);
	}

	.sort-indicator {
		font-size: 9px;
		opacity: 0.7;
	}
</style>
