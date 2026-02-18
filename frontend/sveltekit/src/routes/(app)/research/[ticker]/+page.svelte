<script lang="ts">
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();

  const report = $derived(data.report);
  const overview = $derived(report.overview);
  const latest = $derived(report.financials[report.financials.length - 1]);

  function formatLargeNumber(n: number, market: string): string {
    const symbol = market === 'CN' ? '¥' : market === 'HK' ? 'HK$' : '$';
    if (n >= 1e12) return `${symbol}${(n / 1e12).toFixed(2)}T`;
    if (n >= 1e9)  return `${symbol}${(n / 1e9).toFixed(1)}B`;
    if (n >= 1e6)  return `${symbol}${(n / 1e6).toFixed(1)}M`;
    return `${symbol}${n.toFixed(0)}`;
  }

  const metrics = $derived([
    {
      label: 'Market Cap',
      value: formatLargeNumber(overview.marketCap, overview.market),
      sub: overview.market
    },
    {
      label: 'P/E Ratio',
      value: overview.pe != null ? overview.pe.toFixed(1) + 'x' : 'N/A',
      sub: 'trailing'
    },
    {
      label: 'P/B Ratio',
      value: overview.pb != null ? overview.pb.toFixed(1) + 'x' : 'N/A',
      sub: 'price to book'
    },
    {
      label: 'ROE',
      value: latest.roe.toFixed(1) + '%',
      sub: `FY${latest.year}`
    },
    {
      label: 'Revenue',
      value: formatLargeNumber(latest.revenue, overview.market),
      sub: `FY${latest.year}`
    },
    {
      label: 'Net Income',
      value: formatLargeNumber(latest.netIncome, overview.market),
      sub: `FY${latest.year}`
    },
    {
      label: 'Free Cash Flow',
      value: formatLargeNumber(latest.freeCashFlow, overview.market),
      sub: `FY${latest.year}`
    },
    {
      label: 'Debt / Equity',
      value: latest.debtToEquity.toFixed(2) + 'x',
      sub: 'leverage ratio'
    }
  ]);
</script>

<div class="space-y-5">
  <!-- Key Metrics Grid -->
  <section aria-labelledby="metrics-heading">
    <h2 id="metrics-heading" class="text-[11px] font-mono uppercase tracking-wider text-[var(--text-muted)] mb-3">
      Key Metrics
    </h2>
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {#each metrics as metric}
        <div class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-4 hover:border-[var(--border-hover)] transition-colors">
          <p class="text-[11px] font-mono uppercase tracking-wider text-[var(--text-muted)] mb-1">{metric.label}</p>
          <p class="text-xl font-mono font-semibold text-[var(--text-primary)] tabular-nums">{metric.value}</p>
          <p class="text-xs text-[var(--text-dimmed)] mt-0.5">{metric.sub}</p>
        </div>
      {/each}
    </div>
  </section>

  <!-- About -->
  <section aria-labelledby="about-heading">
    <h2 id="about-heading" class="text-[11px] font-mono uppercase tracking-wider text-[var(--text-muted)] mb-3">
      About
    </h2>
    <div class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-5">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
        <div class="space-y-3">
          <div>
            <p class="text-xs text-[var(--text-muted)] mb-0.5">Company</p>
            <p class="text-sm font-medium text-[var(--text-primary)]">{overview.name}</p>
          </div>
          <div>
            <p class="text-xs text-[var(--text-muted)] mb-0.5">Ticker</p>
            <p class="text-sm font-mono text-[var(--text-primary)]">{overview.ticker}</p>
          </div>
          <div>
            <p class="text-xs text-[var(--text-muted)] mb-0.5">Market</p>
            <p class="text-sm font-mono text-[var(--text-secondary)]">{overview.market}</p>
          </div>
        </div>
        <div class="space-y-3">
          <div>
            <p class="text-xs text-[var(--text-muted)] mb-0.5">Sector</p>
            <p class="text-sm text-[var(--text-secondary)]">{overview.sector}</p>
          </div>
          <div>
            <p class="text-xs text-[var(--text-muted)] mb-0.5">Industry</p>
            <p class="text-sm text-[var(--text-secondary)]">{overview.industry}</p>
          </div>
          <div>
            <p class="text-xs text-[var(--text-muted)] mb-0.5">Investment Thesis</p>
            <p class="text-sm text-[var(--text-secondary)] leading-relaxed">{data.report.rating.thesis}</p>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- Rating Summary -->
  <section aria-labelledby="rating-heading">
    <h2 id="rating-heading" class="text-[11px] font-mono uppercase tracking-wider text-[var(--text-muted)] mb-3">
      Research Rating
    </h2>
    <div class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-5">
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div>
          <p class="text-xs text-[var(--text-muted)] mb-1">Signal</p>
          <p class="text-sm font-mono font-semibold uppercase text-[var(--green)]">{data.report.rating.signal.replace('-', ' ')}</p>
        </div>
        <div>
          <p class="text-xs text-[var(--text-muted)] mb-1">Target Price</p>
          <p class="text-sm font-mono font-semibold text-[var(--text-primary)] tabular-nums">
            {overview.market === 'CN' ? '¥' : overview.market === 'HK' ? 'HK$' : '$'}{data.report.rating.targetPrice.toLocaleString()}
          </p>
        </div>
        <div>
          <p class="text-xs text-[var(--text-muted)] mb-1">Moat Score</p>
          <p class="text-sm font-mono font-semibold text-[var(--text-primary)] tabular-nums">{data.report.rating.moatScore.toFixed(1)}/10</p>
        </div>
        <div>
          <p class="text-xs text-[var(--text-muted)] mb-1">Risk Level</p>
          <p class="text-sm font-mono font-semibold capitalize
            {data.report.rating.riskLevel === 'low' ? 'text-[var(--green)]' :
             data.report.rating.riskLevel === 'medium' ? 'text-[var(--amber)]' :
             'text-[var(--red)]'}">
            {data.report.rating.riskLevel}
          </p>
        </div>
      </div>
    </div>
  </section>
</div>
