<script lang="ts">
	import Card from '$lib/components/ui/Card.svelte';
	import Badge from '$lib/components/ui/Badge.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import { formatDate, formatPercent } from '$lib/utils/format';
	import type { PageData } from './$types';
	
	let { data }: { data: PageData } = $props();
	
	let activeTab = $state('signals');
	let expandedPick = $state<string | null>(null);
	
	function toggleExpand(ticker: string) {
		expandedPick = expandedPick === ticker ? null : ticker;
	}
	
	const getEntryColor = (label: string) => {
		const l = (label || '').toLowerCase();
		if (l.includes('有利') || l.includes('buy')) return { bg: 'bg-[var(--green)]/15', border: 'border-[var(--green)]/40', text: 'text-[var(--green)]', dot: 'bg-[var(--green)]' };
		if (l.includes('中性') || l.includes('hold')) return { bg: 'bg-[var(--amber)]/15', border: 'border-[var(--amber)]/40', text: 'text-[var(--amber)]', dot: 'bg-[var(--amber)]' };
		if (l.includes('不利') || l.includes('sell')) return { bg: 'bg-[var(--red)]/15', border: 'border-[var(--red)]/40', text: 'text-[var(--red)]', dot: 'bg-[var(--red)]' };
		return { bg: 'bg-[var(--bg-elevated)]', border: 'border-[var(--border-default)]', text: 'text-[var(--text-muted)]', dot: 'bg-[var(--text-muted)]' };
	};
	
	const getRsiColor = (rsi: number) => {
		if (rsi >= 70) return 'text-[var(--red)]';
		if (rsi >= 60) return 'text-[var(--amber)]';
		if (rsi <= 30) return 'text-[var(--green)]';
		if (rsi <= 40) return 'text-[var(--blue)]';
		return 'text-[var(--text-primary)]';
	};
	
	const getBbColor = (pos: number) => {
		if (pos >= 0.8) return 'text-[var(--red)]';
		if (pos >= 0.6) return 'text-[var(--amber)]';
		if (pos <= 0.2) return 'text-[var(--green)]';
		return 'text-[var(--text-primary)]';
	};
</script>

<svelte:head>
	<title>HK Signals — Smart Money Platform</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div>
		<div class="flex items-center gap-3 mb-2">
			<h1 class="text-heading">HK VMQ Signals</h1>
		</div>
		<p class="text-[var(--text-muted)]">Value-Momentum-Quality Strategy · Top 7 Picks with Entry/Exit Analysis</p>
		{#if data.signals.date}
			<p class="text-xs text-[var(--text-dimmed)] mt-2">
				Date: {data.signals.date} · Updated: {formatDate(data.signals.updated_at)}
			</p>
		{/if}
	</div>
	
	<!-- Tabs -->
	<div class="flex border-b border-[var(--border-default)] gap-2">
		<button
			class="px-4 py-3 text-sm font-medium relative transition-colors
				{activeTab === 'signals' ? 'text-[var(--text-primary)]' : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'}"
			onclick={() => activeTab = 'signals'}
		>
			Daily Top 7
			<span class="ml-2 px-2 py-0.5 bg-[var(--bg-elevated)] text-[var(--blue)] rounded-full text-xs">
				{data.signals.picks?.length || 0}
			</span>
			{#if activeTab === 'signals'}
				<div class="absolute bottom-0 left-0 right-0 h-0.5 bg-[var(--blue)]"></div>
			{/if}
		</button>
		<button
			class="px-4 py-3 text-sm font-medium relative transition-colors
				{activeTab === 'universe' ? 'text-[var(--text-primary)]' : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'}"
			onclick={() => activeTab = 'universe'}
		>
			Full Universe
			<span class="ml-2 px-2 py-0.5 bg-[var(--bg-elevated)] text-[var(--blue)] rounded-full text-xs">
				{data.history.picks?.length || 0}
			</span>
			{#if activeTab === 'universe'}
				<div class="absolute bottom-0 left-0 right-0 h-0.5 bg-[var(--blue)]"></div>
			{/if}
		</button>
	</div>
	
	<!-- Tab Content -->
	{#if activeTab === 'signals'}
		<!-- Signal Cards -->
		{#if data.signals.picks && data.signals.picks.length > 0}
			<div class="space-y-4">
				{#each data.signals.picks as pick}
					{@const colors = getEntryColor(pick.entry_label || pick.score_label || '')}
					{@const isExpanded = expandedPick === pick.ticker}
					
					<Card hover>
						{#snippet children()}
							<div class="space-y-0">
								<!-- Main Row - Always Visible -->
								<button class="w-full text-left" onclick={() => toggleExpand(pick.ticker)}>
									<div class="flex items-start gap-4">
										<!-- Rank -->
										<div class="flex-shrink-0 w-10 h-10 bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-lg flex items-center justify-center">
											<span class="text-[var(--blue)] font-bold text-lg">#{pick.rank}</span>
										</div>
										
										<!-- Ticker + Name -->
										<div class="flex-1 min-w-0">
											<div class="flex items-center gap-2 mb-1">
												<span class="ticker-code text-lg">{pick.ticker}</span>
												<span class="text-xs text-[var(--text-dimmed)] truncate">{pick.name}</span>
											</div>
											<div class="flex items-center gap-3 flex-wrap">
												<!-- VMQ Score -->
												<span class="text-sm font-semibold text-[var(--text-primary)]">VMQ {pick.vmq_score?.toFixed(1)}</span>
												
												<!-- VMQ Breakdown mini -->
												<div class="flex items-center gap-1 text-xs text-[var(--text-muted)]">
													<span>Q:{pick.quality?.toFixed(0)}</span>
													<span>M:{pick.momentum?.toFixed(0)}</span>
													<span>V:{pick.value?.toFixed(0)}</span>
												</div>
												
												<!-- Entry Label -->
												{#if pick.entry_label || pick.score_label}
													<span class="px-2 py-0.5 rounded-full text-xs font-medium {colors.bg} {colors.text} border {colors.border}">
														{pick.entry_label || pick.score_label}
														{#if pick.entry_score !== undefined}
															<span class="ml-1 opacity-75">{pick.entry_score}</span>
														{/if}
													</span>
												{/if}
												
												<!-- Sector -->
												<span class="text-xs text-[var(--text-dimmed)]">{pick.sector}</span>
											</div>
										</div>
										
										<!-- Price + Expand -->
										<div class="flex-shrink-0 text-right">
											<div class="text-lg font-semibold text-[var(--text-primary)]">
												HK${pick.current_price?.toFixed(2) || pick.entry_zone?.current_price?.toFixed(2) || 'N/A'}
											</div>
											<div class="text-xs text-[var(--text-dimmed)] mt-1">
												{isExpanded ? '▲ Less' : '▼ More'}
											</div>
										</div>
									</div>
								</button>
								
								<!-- Expanded Details -->
								{#if isExpanded}
									<div class="mt-4 pt-4 border-t border-[var(--border-default)] space-y-4 fade-in">
										
										<!-- Entry Zone + Fundamentals Row -->
										<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
											
											<!-- Entry Zone -->
											{#if pick.entry_zone}
												<div class="bg-[var(--bg-surface)] rounded-lg p-4 border border-[var(--border-default)]">
													<h4 class="text-label mb-3 flex items-center gap-2">
														<span class="w-2 h-2 rounded-full {colors.dot}"></span>
														Entry Zone
													</h4>
													<div class="space-y-2">
														<div class="flex justify-between text-sm">
															<span class="text-[var(--text-muted)]">Low</span>
															<span class="text-[var(--text-primary)] font-mono">HK${pick.entry_zone.entry_low?.toFixed(2)}</span>
														</div>
														<div class="flex justify-between text-sm">
															<span class="text-[var(--text-muted)]">Mid</span>
															<span class="text-[var(--text-primary)] font-mono font-bold">HK${pick.entry_zone.entry_mid?.toFixed(2)}</span>
														</div>
														<div class="flex justify-between text-sm">
															<span class="text-[var(--text-muted)]">High</span>
															<span class="text-[var(--text-primary)] font-mono">HK${pick.entry_zone.entry_high?.toFixed(2)}</span>
														</div>
														<!-- Price position bar -->
														{#if pick.entry_zone.entry_low && pick.entry_zone.entry_high}
															{@const low = pick.entry_zone.entry_low}
															{@const high = pick.entry_zone.entry_high}
															{@const current = pick.entry_zone.current_price || 0}
															{@const pct = Math.min(Math.max((current - low) / (high - low) * 100, 0), 100)}
															<div class="mt-3">
																<div class="relative h-2 bg-[var(--bg-elevated)] rounded-full overflow-hidden">
																	<div class="absolute h-full bg-[var(--blue)]/40 rounded-full" style="left: 0; width: 100%"></div>
																	<div class="absolute h-full w-1.5 bg-[var(--text-primary)] rounded-full" style="left: {pct}%"></div>
																</div>
																<div class="flex justify-between text-xs text-[var(--text-dimmed)] mt-1">
																	<span>Low</span>
																	<span class="font-medium {pick.entry_zone.in_zone === 'True' ? 'text-[var(--green)]' : 'text-[var(--amber)]'}">
																		{pick.entry_zone.in_zone === 'True' ? '✓ In Zone' : '✗ Outside'}
																	</span>
																	<span>High</span>
																</div>
															</div>
														{/if}
														{#if pick.score_description || pick.entry_description}
															<div class="text-xs text-[var(--text-muted)] mt-2 italic border-l-2 border-[var(--blue)]/30 pl-2">
																{pick.score_description || pick.entry_description}
															</div>
														{/if}
													</div>
												</div>
											{/if}
											
											<!-- Exit Strategy -->
											{#if pick.exit_levels}
												<div class="bg-[var(--bg-surface)] rounded-lg p-4 border border-[var(--border-default)]">
													<h4 class="text-label mb-3 flex items-center gap-2">
														<span class="w-2 h-2 rounded-full bg-[var(--amber)]"></span>
														Exit Strategy
													</h4>
													<div class="space-y-3">
														<!-- Stop Loss -->
														{#if pick.exit_levels.stop_loss}
															<div>
																<div class="text-xs text-[var(--red)] font-medium mb-1">止损 Stop Loss</div>
																<div class="flex justify-between text-sm">
																	<span class="text-[var(--text-muted)]">Initial (8%)</span>
																	<span class="text-[var(--red)] font-mono">HK${pick.exit_levels.stop_loss.initial_8pct?.toFixed(2)}</span>
																</div>
																<div class="flex justify-between text-sm">
																	<span class="text-[var(--text-muted)]">Trailing (15%)</span>
																	<span class="text-[var(--red)] font-mono">HK${pick.exit_levels.stop_loss.trailing_15pct?.toFixed(2)}</span>
																</div>
															</div>
														{/if}
														
														<!-- Take Profit -->
														{#if pick.exit_levels.take_profit}
															<div class="pt-2 border-t border-[var(--border-default)]">
																<div class="text-xs text-[var(--green)] font-medium mb-1">止盈 Take Profit</div>
																<div class="flex justify-between text-sm">
																	<span class="text-[var(--text-muted)]">T1 (+{pick.exit_levels.take_profit.t1_pct}%)</span>
																	<span class="text-[var(--green)] font-mono">HK${pick.exit_levels.take_profit.t1_price?.toFixed(2)}</span>
																</div>
																<div class="text-xs text-[var(--text-dimmed)] ml-2">{pick.exit_levels.take_profit.t1_action}</div>
																<div class="flex justify-between text-sm mt-1">
																	<span class="text-[var(--text-muted)]">T2 (+{pick.exit_levels.take_profit.t2_pct}%)</span>
																	<span class="text-[var(--green)] font-mono">HK${pick.exit_levels.take_profit.t2_price?.toFixed(2)}</span>
																</div>
																<div class="text-xs text-[var(--text-dimmed)] ml-2">{pick.exit_levels.take_profit.t2_action}</div>
																{#if pick.exit_levels.take_profit.t3_estimate}
																	<div class="flex justify-between text-sm mt-1">
																		<span class="text-[var(--text-muted)]">T3 (trailing)</span>
																		<span class="text-[var(--green)] font-mono">~HK${pick.exit_levels.take_profit.t3_estimate?.toFixed(2)}</span>
																	</div>
																	<div class="text-xs text-[var(--text-dimmed)] ml-2">{pick.exit_levels.take_profit.t3_description}</div>
																{/if}
															</div>
														{/if}
														
														<!-- Time Stop -->
														{#if pick.exit_levels.time_stop}
															<div class="pt-2 border-t border-[var(--border-default)]">
																<div class="text-xs text-[var(--amber)] font-medium mb-1">⏱ Time Stop</div>
																<div class="text-xs text-[var(--text-muted)]">{pick.exit_levels.time_stop.description}</div>
															</div>
														{/if}
													</div>
												</div>
											{/if}
										</div>
										
										<!-- Technical Indicators -->
										{#if pick.indicators}
											<div class="bg-[var(--bg-surface)] rounded-lg p-4 border border-[var(--border-default)]">
												<h4 class="text-label mb-3 flex items-center gap-2">
													<span class="w-2 h-2 rounded-full bg-[var(--blue)]"></span>
													Technical Indicators
												</h4>
												<div class="grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-3">
													<!-- RSI -->
													<div>
														<div class="text-xs text-[var(--text-dimmed)]">RSI(14)</div>
														<div class="text-sm font-semibold {getRsiColor(pick.indicators.rsi_14)}">{pick.indicators.rsi_14?.toFixed(1)}</div>
													</div>
													
													<!-- BB Position -->
													<div>
														<div class="text-xs text-[var(--text-dimmed)]">BB Position</div>
														<div class="text-sm font-semibold {getBbColor(pick.indicators.bb_position)}">{(pick.indicators.bb_position * 100)?.toFixed(0)}%</div>
													</div>
													
													<!-- Distance from SMA20 -->
													<div>
														<div class="text-xs text-[var(--text-dimmed)]">vs SMA(20)</div>
														<div class="text-sm font-semibold" class:color-up={pick.indicators.dist_20d_pct > 0} class:color-down={pick.indicators.dist_20d_pct < 0}>
															{pick.indicators.dist_20d_pct > 0 ? '+' : ''}{pick.indicators.dist_20d_pct?.toFixed(1)}%
														</div>
													</div>
													
													<!-- Distance from SMA50 -->
													<div>
														<div class="text-xs text-[var(--text-dimmed)]">vs SMA(50)</div>
														<div class="text-sm font-semibold" class:color-up={pick.indicators.dist_50d_pct > 0} class:color-down={pick.indicators.dist_50d_pct < 0}>
															{pick.indicators.dist_50d_pct > 0 ? '+' : ''}{pick.indicators.dist_50d_pct?.toFixed(1)}%
														</div>
													</div>
													
													<!-- Volatility -->
													<div>
														<div class="text-xs text-[var(--text-dimmed)]">Vol(10d)</div>
														<div class="text-sm font-semibold text-[var(--text-primary)]">{pick.indicators.recent_volatility_10d?.toFixed(1)}%</div>
													</div>
													
													<!-- Vol 30d -->
													<div>
														<div class="text-xs text-[var(--text-dimmed)]">Vol(30d)</div>
														<div class="text-sm font-semibold text-[var(--text-primary)]">{pick.indicators.volatility_30d?.toFixed(1)}%</div>
													</div>
													
													<!-- Drawdown 20d -->
													<div>
														<div class="text-xs text-[var(--text-dimmed)]">DD(20d)</div>
														<div class="text-sm font-semibold text-[var(--red)]">{pick.indicators.drawdown_20d_pct?.toFixed(1)}%</div>
													</div>
													
													<!-- 52w range -->
													<div>
														<div class="text-xs text-[var(--text-dimmed)]">52W Range</div>
														<div class="text-sm font-semibold text-[var(--text-primary)]">{pick.indicators.low_52w?.toFixed(1)} - {pick.indicators.high_52w?.toFixed(1)}</div>
													</div>
												</div>
												
												<!-- SMA levels compact -->
												<div class="mt-3 pt-3 border-t border-[var(--border-default)] flex flex-wrap gap-4 text-xs text-[var(--text-muted)]">
													<span>SMA20: <span class="font-mono text-[var(--text-primary)]">{pick.indicators.sma_20?.toFixed(2)}</span></span>
													<span>SMA50: <span class="font-mono text-[var(--text-primary)]">{pick.indicators.sma_50?.toFixed(2)}</span></span>
													<span>SMA200: <span class="font-mono text-[var(--text-primary)]">{pick.indicators.sma_200?.toFixed(2)}</span></span>
													<span>BB: <span class="font-mono text-[var(--text-primary)]">{pick.indicators.bb_lower?.toFixed(2)} - {pick.indicators.bb_upper?.toFixed(2)}</span></span>
												</div>
											</div>
										{/if}
										
										<!-- Fundamentals -->
										<div class="grid grid-cols-3 md:grid-cols-6 gap-3">
											<div class="bg-[var(--bg-surface)] rounded-lg p-3 border border-[var(--border-default)] text-center">
												<div class="text-label">PE</div>
												<div class="text-data">{pick.pe?.toFixed(1) || 'N/A'}</div>
											</div>
											<div class="bg-[var(--bg-surface)] rounded-lg p-3 border border-[var(--border-default)] text-center">
												<div class="text-label">PB</div>
												<div class="text-data">{pick.pb?.toFixed(2) || 'N/A'}</div>
											</div>
											<div class="bg-[var(--bg-surface)] rounded-lg p-3 border border-[var(--border-default)] text-center">
												<div class="text-label">ROE</div>
												<div class="text-data">{pick.roe ? (pick.roe * 100).toFixed(1) + '%' : 'N/A'}</div>
											</div>
											<div class="bg-[var(--bg-surface)] rounded-lg p-3 border border-[var(--border-default)] text-center">
												<div class="text-label">Quality</div>
												<div class="text-data color-blue">{pick.quality?.toFixed(1)}</div>
											</div>
											<div class="bg-[var(--bg-surface)] rounded-lg p-3 border border-[var(--border-default)] text-center">
												<div class="text-label">Momentum</div>
												<div class="text-data color-up">{pick.momentum?.toFixed(1)}</div>
											</div>
											<div class="bg-[var(--bg-surface)] rounded-lg p-3 border border-[var(--border-default)] text-center">
												<div class="text-label">Value</div>
												<div class="text-data color-amber">{pick.value?.toFixed(1)}</div>
											</div>
										</div>
										
										<!-- Reason -->
										{#if pick.reason}
											<div class="text-sm text-[var(--text-muted)] italic border-l-2 border-[var(--blue)]/30 pl-3">
												{pick.reason}
											</div>
										{/if}
									</div>
								{/if}
							</div>
						{/snippet}
					</Card>
				{/each}
			</div>
		{:else}
			<EmptyState 
				title="No HK Signals Available" 
				message="Check back later for updated VMQ signals"
			/>
		{/if}
		
	{:else}
		<!-- Universe / Monthly Rankings -->
		<div class="space-y-4 fade-in">
			{#if data.history.strategy}
				<Card>
					{#snippet children()}
						<div class="flex items-center justify-between">
							<div>
								<h3 class="text-subhead">{data.history.strategy}</h3>
								<p class="text-sm text-[var(--text-muted)]">{data.history.universe} · Top {data.history.top_n}</p>
							</div>
							<p class="text-xs text-[var(--text-dimmed)]">Updated: {formatDate(data.history.updated_at)}</p>
						</div>
						{#if data.history.warnings?.length}
							<div class="mt-3 p-2 bg-[var(--amber)]/10 rounded text-xs text-[var(--amber)]">
								{#each data.history.warnings as warn}
									<div>⚠ {warn}</div>
								{/each}
							</div>
						{/if}
					{/snippet}
				</Card>
			{/if}
			
			{#if data.history.picks?.length > 0}
				<!-- Top picks as compact table -->
				<Card title="Universe Rankings">
					{#snippet children()}
						<div class="overflow-x-auto">
							<table class="w-full text-sm">
								<thead>
									<tr class="border-b border-[var(--border-default)]">
										<th class="text-left text-label py-2 px-2">#</th>
										<th class="text-left text-label py-2 px-2">Ticker</th>
										<th class="text-left text-label py-2 px-2">Name</th>
										<th class="text-right text-label py-2 px-2">VMQ</th>
										<th class="text-right text-label py-2 px-2">Q</th>
										<th class="text-right text-label py-2 px-2">M</th>
										<th class="text-right text-label py-2 px-2">V</th>
										<th class="text-left text-label py-2 px-2">Sector</th>
										<th class="text-right text-label py-2 px-2">PE</th>
										<th class="text-right text-label py-2 px-2">PB</th>
										<th class="text-right text-label py-2 px-2">ROE</th>
									</tr>
								</thead>
								<tbody>
									{#each data.history.picks as pick, i}
										<tr class="border-b border-[var(--border-default)]/50 hover:bg-[var(--bg-surface)] transition-colors
											{i < 7 ? 'bg-[var(--blue)]/5' : ''}">
											<td class="py-2 px-2 text-[var(--text-muted)]">{pick.rank || i + 1}</td>
											<td class="py-2 px-2 font-mono font-bold text-[var(--blue)]">{pick.ticker}</td>
											<td class="py-2 px-2 text-[var(--text-primary)] truncate max-w-[200px]">{pick.name}</td>
											<td class="py-2 px-2 text-right font-bold text-[var(--text-primary)]">{pick.vmq_score?.toFixed(1)}</td>
											<td class="py-2 px-2 text-right text-[var(--blue)]">{pick.quality?.toFixed(0)}</td>
											<td class="py-2 px-2 text-right text-[var(--green)]">{pick.momentum?.toFixed(0)}</td>
											<td class="py-2 px-2 text-right text-[var(--amber)]">{pick.value?.toFixed(0)}</td>
											<td class="py-2 px-2 text-[var(--text-muted)] text-xs">{pick.sector || ''}</td>
											<td class="py-2 px-2 text-right text-[var(--text-primary)]">{pick.pe?.toFixed(1) || '—'}</td>
											<td class="py-2 px-2 text-right text-[var(--text-primary)]">{pick.pb?.toFixed(2) || '—'}</td>
											<td class="py-2 px-2 text-right text-[var(--text-primary)]">{pick.roe ? (pick.roe * 100).toFixed(1) + '%' : '—'}</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
						<p class="text-xs text-[var(--text-dimmed)] mt-3">Top 7 highlighted in blue. Full universe ranked by composite VMQ score.</p>
					{/snippet}
				</Card>
			{:else}
				<EmptyState title="No Universe Data" message="Monthly rankings not yet available" />
			{/if}
		</div>
	{/if}
</div>

<style>
	.fade-in {
		animation: fadeIn 0.3s ease-in;
	}
	@keyframes fadeIn {
		from { opacity: 0; transform: translateY(8px); }
		to { opacity: 1; transform: translateY(0); }
	}
</style>
