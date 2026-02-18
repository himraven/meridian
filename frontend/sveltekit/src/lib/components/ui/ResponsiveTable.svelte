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

	// Determine the "header" column — first column with key 'ticker' or 'name', else first column
	function getHeaderKey(): string {
		const tickerCol = columns.find(c => c.key === 'ticker');
		if (tickerCol) return 'ticker';
		const nameCol = columns.find(c => c.key === 'name');
		if (nameCol) return 'name';
		return columns[0]?.key ?? '';
	}

	function getSecondaryKey(): string | null {
		const hk = getHeaderKey();
		if (hk === 'ticker') {
			const nameCol = columns.find(c => c.key === 'name');
			if (nameCol) return 'name';
		}
		return null;
	}
</script>

<!-- Desktop: normal table -->
<div class="hidden md:block overflow-x-auto scrollbar-thin {className}">
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

<!-- Mobile: card view -->
<div class="md:hidden {className}">
	{#if loading}
		<Skeleton type="table" />
	{:else if data.length === 0}
		<EmptyState title={emptyMessage} />
	{:else}
		<!-- Mobile sort control -->
		<div class="flex items-center gap-2 mb-3 px-1">
			<span class="text-xs text-[var(--text-muted)]">Sort:</span>
			<select
				class="mobile-sort-select"
				onchange={(e) => {
					const val = e.currentTarget.value;
					if (val) handleSort(val);
				}}
			>
				<option value="">Default</option>
				{#each columns.filter(c => c.sortable) as col}
					<option value={col.key} selected={sortKey === col.key}>{col.label}</option>
				{/each}
			</select>
			{#if sortKey}
				<button
					class="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
					onclick={() => sortDirection = sortDirection === 'asc' ? 'desc' : 'asc'}
				>
					{sortDirection === 'asc' ? '▲' : '▼'}
				</button>
			{/if}
		</div>

		<div class="space-y-2">
			{#each sortedData() as row, i}
				{@const headerKey = getHeaderKey()}
				{@const secondaryKey = getSecondaryKey()}
				{@const headerCol = columns.find(c => c.key === headerKey)}
				<div class="mobile-card">
					<!-- Card header -->
					<div class="card-header">
						<div class="card-header-title">
							{#if headerCol?.render}
								{@html headerCol.render(row[headerKey], row)}
							{:else}
								<span class="font-mono font-bold text-[var(--text-primary)]">{row[headerKey] ?? 'N/A'}</span>
							{/if}
							{#if secondaryKey}
								<span class="text-xs text-[var(--text-muted)] ml-2 truncate">{row[secondaryKey] ?? ''}</span>
							{/if}
						</div>
					</div>

					<!-- Card body: key-value pairs -->
					<div class="card-body">
						{#each columns.filter(c => c.key !== headerKey && (secondaryKey ? c.key !== secondaryKey : true)) as column}
							<div class="card-row">
								<span class="card-label">{column.label}</span>
								<span class="card-value">
									{#if column.render}
										{@html column.render(row[column.key], row)}
									{:else}
										{row[column.key] ?? 'N/A'}
									{/if}
								</span>
							</div>
						{/each}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	/* Sort button */
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

	/* Mobile sort dropdown */
	.mobile-sort-select {
		background: var(--bg-elevated);
		border: 1px solid var(--border-default);
		border-radius: 6px;
		padding: 4px 8px;
		font-size: 12px;
		color: var(--text-primary);
		outline: none;
	}

	.mobile-sort-select:focus {
		border-color: var(--text-muted);
	}

	/* Mobile cards */
	.mobile-card {
		background: var(--bg-surface);
		border: 1px solid var(--border-default);
		border-radius: 8px;
		overflow: hidden;
	}

	.card-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 10px 12px;
		border-bottom: 1px solid var(--border-default);
		background: var(--bg-elevated);
	}

	.card-header-title {
		display: flex;
		align-items: center;
		min-width: 0;
	}

	.card-body {
		padding: 6px 0;
	}

	.card-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 5px 12px;
		gap: 8px;
	}

	.card-row:not(:last-child) {
		border-bottom: 1px solid color-mix(in srgb, var(--border-default) 40%, transparent);
	}

	.card-label {
		font-size: 11px;
		color: var(--text-muted);
		white-space: nowrap;
		flex-shrink: 0;
	}

	.card-value {
		font-size: 13px;
		color: var(--text-primary);
		text-align: right;
		font-family: 'JetBrains Mono', monospace;
		font-size: 12px;
	}
</style>
