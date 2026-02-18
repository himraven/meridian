<script lang="ts">
  import { page } from '$app/stores';
  import type { LayoutData } from './$types';
  import type { Snippet } from 'svelte';

  interface Props {
    data: LayoutData;
    children: Snippet;
  }

  let { data, children }: Props = $props();

  const report = $derived(data.report);
  const overview = $derived(report.overview);
  const rating = $derived(report.rating);

  const tabs = $derived([
    { label: 'Overview', href: `/research/${data.ticker}` },
    { label: 'Financials', href: `/research/${data.ticker}/financials` },
    { label: 'Valuation', href: `/research/${data.ticker}/valuation` },
    { label: 'Moat', href: `/research/${data.ticker}/moat` },
    { label: 'Risks', href: `/research/${data.ticker}/risks` },
    { label: 'Catalysts', href: `/research/${data.ticker}/catalysts` },
    { label: 'Meridian AI', href: `/research/${data.ticker}/analysis` }
  ]);

  function isActiveTab(href: string): boolean {
    const path = $page.url.pathname;
    if (href === `/research/${data.ticker}`) {
      return path === href;
    }
    return path.startsWith(href);
  }

  const signalConfig = $derived((() => {
    switch (rating.signal) {
      case 'strong-buy': return { label: 'Strong Buy', color: 'text-[var(--green)]', dotColor: 'bg-[var(--green)]', bars: 4 };
      case 'buy':        return { label: 'Buy',         color: 'text-[var(--green)]', dotColor: 'bg-[var(--green)]', bars: 3 };
      case 'hold':       return { label: 'Hold',        color: 'text-[var(--amber)]', dotColor: 'bg-[var(--amber)]', bars: 2 };
      case 'caution':    return { label: 'Caution',     color: 'text-[var(--amber)]', dotColor: 'bg-[var(--amber)]', bars: 2 };
      case 'avoid':      return { label: 'Avoid',       color: 'text-[var(--red)]',   dotColor: 'bg-[var(--red)]',   bars: 1 };
    }
  })());

  const riskConfig = $derived((() => {
    switch (rating.riskLevel) {
      case 'low':    return { label: 'Low Risk',    color: 'text-[var(--green)]' };
      case 'medium': return { label: 'Medium Risk', color: 'text-[var(--amber)]' };
      case 'high':   return { label: 'High Risk',   color: 'text-[var(--red)]' };
    }
  })());

  const marketLabel = $derived(
    overview.market === 'CN' ? 'A股' :
    overview.market === 'HK' ? '港股' : 'US'
  );

  function formatPrice(price: number, market: string): string {
    if (market === 'CN') return `¥${price.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    if (market === 'HK') return `HK$${price.toLocaleString('en-HK', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    return `$${price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }

  const priceStr = $derived(formatPrice(overview.price, overview.market));
  const targetStr = $derived(formatPrice(rating.targetPrice, overview.market));

  const changePositive = $derived(overview.change >= 0);
  const changeColor = $derived(changePositive ? 'text-[var(--green)]' : 'text-[var(--red)]');
  const changeSign = $derived(changePositive ? '+' : '');
</script>

<svelte:head>
  <title>{overview.ticker} {overview.name} — Research — Meridian</title>
</svelte:head>

<div class="space-y-4">
  <!-- Breadcrumb -->
  <nav class="flex items-center gap-2 text-xs text-[var(--text-muted)]" aria-label="Breadcrumb">
    <a href="/research" class="hover:text-[var(--text-secondary)] transition-colors">Research</a>
    <span class="text-[var(--text-dimmed)]">/</span>
    <span class="text-[var(--text-secondary)] font-mono">{overview.ticker}</span>
    <span class="text-[var(--text-dimmed)]">/</span>
    <span class="text-[var(--text-secondary)]">{overview.name}</span>
  </nav>

  <!-- Hero Card -->
  <div class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-5 hover:border-[var(--border-hover)] transition-colors">
    <!-- Top row: Signal + Market Badge -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-3">
        <!-- Signal rating -->
        <div class="flex items-center gap-1.5">
          <div class="flex items-center gap-0.5">
            {#each Array(4) as _, i}
              <div
                class="w-1.5 h-4 rounded-sm {i < signalConfig.bars ? signalConfig.dotColor : 'bg-[var(--bg-elevated)]'}"
                style="height: {10 + i * 3}px"
              ></div>
            {/each}
          </div>
          <span class="text-xs font-medium font-mono uppercase tracking-wide {signalConfig.color}">
            {signalConfig.label}
          </span>
        </div>
        <!-- Risk badge -->
        <span class="text-xs font-mono {riskConfig.color} opacity-70">
          {riskConfig.label}
        </span>
      </div>
      <!-- Market badge -->
      <span class="px-2 py-0.5 rounded text-xs font-mono font-medium bg-[var(--bg-elevated)] text-[var(--text-muted)] border border-[var(--border-default)]">
        {marketLabel}
      </span>
    </div>

    <!-- Main info grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- Left: Name + Price -->
      <div>
        <div class="flex items-baseline gap-2 mb-1">
          <h1 class="text-xl font-semibold text-[var(--text-primary)]">{overview.name}</h1>
          <span class="text-sm font-mono text-[var(--text-muted)]">{overview.ticker}</span>
        </div>
        <p class="text-xs text-[var(--text-muted)] mb-3">{overview.sector} · {overview.industry}</p>

        <!-- Price -->
        <div class="flex items-baseline gap-3">
          <span class="text-3xl font-mono font-semibold text-[var(--text-primary)] tabular-nums">
            {priceStr}
          </span>
          <span class="text-sm font-mono {changeColor} tabular-nums">
            {changeSign}{formatPrice(overview.change, overview.market)}
            ({changeSign}{overview.changePercent.toFixed(2)}%)
          </span>
        </div>
      </div>

      <!-- Right: Target + Moat + Margin -->
      <div class="grid grid-cols-3 gap-3">
        <!-- Target Price -->
        <div class="space-y-0.5">
          <p class="text-[11px] font-mono uppercase tracking-wider text-[var(--text-muted)]">Target</p>
          <p class="text-base font-mono font-semibold text-[var(--text-primary)] tabular-nums">{targetStr}</p>
          <p class="text-xs text-[var(--green)] font-mono">+{rating.safetyMargin.toFixed(1)}% upside</p>
        </div>

        <!-- Moat Score -->
        <div class="space-y-0.5">
          <p class="text-[11px] font-mono uppercase tracking-wider text-[var(--text-muted)]">Moat</p>
          <div class="flex items-baseline gap-1">
            <span class="text-base font-mono font-semibold text-[var(--text-primary)] tabular-nums">{rating.moatScore.toFixed(1)}</span>
            <span class="text-xs text-[var(--text-muted)] font-mono">/10</span>
          </div>
          <!-- Moat bar -->
          <div class="w-full h-1.5 bg-[var(--bg-elevated)] rounded-full overflow-hidden">
            <div
              class="h-full bg-[var(--green)] rounded-full transition-all"
              style="width: {rating.moatScore * 10}%"
            ></div>
          </div>
        </div>

        <!-- Safety Margin -->
        <div class="space-y-0.5">
          <p class="text-[11px] font-mono uppercase tracking-wider text-[var(--text-muted)]">Margin of Safety</p>
          <p class="text-base font-mono font-semibold text-[var(--green)] tabular-nums">{rating.safetyMargin.toFixed(1)}%</p>
          <p class="text-xs text-[var(--text-muted)]">vs target</p>
        </div>
      </div>
    </div>

    <!-- Thesis -->
    <div class="mt-4 pt-4 border-t border-[var(--border-default)]">
      <p class="text-xs font-mono uppercase tracking-wider text-[var(--text-muted)] mb-1.5">Investment Thesis</p>
      <p class="text-sm text-[var(--text-secondary)] leading-relaxed">{rating.thesis}</p>
    </div>

    <!-- Updated -->
    <div class="mt-3 flex items-center justify-end">
      <span class="text-xs text-[var(--text-dimmed)] font-mono">Updated {rating.updatedAt}</span>
    </div>
  </div>

  <!-- Tab Navigation -->
  <nav class="flex gap-1 overflow-x-auto scrollbar-none pb-0.5" aria-label="Research sections">
    {#each tabs as tab}
      {@const active = isActiveTab(tab.href)}
      <a
        href={tab.href}
        class="shrink-0 px-3.5 py-1.5 rounded-full text-sm font-medium transition-colors whitespace-nowrap
          {active
            ? 'bg-[var(--bg-elevated)] text-[var(--text-primary)] border border-[var(--border-hover)]'
            : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:bg-[var(--bg-surface)]'
          }"
        aria-current={active ? 'page' : undefined}
      >
        {tab.label}
      </a>
    {/each}
  </nav>

  <!-- Tab Content -->
  <div>
    {@render children()}
  </div>
</div>
