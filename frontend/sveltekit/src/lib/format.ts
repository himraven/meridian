/**
 * Shared formatters for Meridian frontend.
 * Used across crypto, fund-flows, and ETF pages.
 */

/** Format large USD values with appropriate suffix (B/M/K) */
export function fmtUsd(v: number | null | undefined, decimals = 1): string {
	if (v === null || v === undefined) return '—';
	const abs = Math.abs(v);
	const prefix = v < 0 ? '-$' : '$';
	if (abs >= 1_000_000_000_000) return `${prefix}${(abs / 1_000_000_000_000).toFixed(decimals)}T`;
	if (abs >= 1_000_000_000)     return `${prefix}${(abs / 1_000_000_000).toFixed(decimals)}B`;
	if (abs >= 1_000_000)         return `${prefix}${(abs / 1_000_000).toFixed(decimals)}M`;
	if (abs >= 1_000)             return `${prefix}${(abs / 1_000).toFixed(decimals)}K`;
	return `${prefix}${abs.toFixed(decimals)}`;
}

/** Format fund flow values with +/- prefix */
export function fmtFlow(v: number | null | undefined): string {
	if (v === null || v === undefined || v === 0) return '—';
	const abs = Math.abs(v);
	const prefix = v > 0 ? '+$' : '-$';
	if (abs >= 1_000_000_000) return `${prefix}${(abs / 1_000_000_000).toFixed(1)}B`;
	if (abs >= 1_000_000)     return `${prefix}${(abs / 1_000_000).toFixed(0)}M`;
	if (abs >= 1_000)         return `${prefix}${(abs / 1_000).toFixed(0)}K`;
	return `${prefix}${abs.toLocaleString()}`;
}

/** Format percentage with sign */
export function fmtPct(v: number | null | undefined, decimals = 2): string {
	if (v === null || v === undefined) return '—';
	return `${v > 0 ? '+' : ''}${v.toFixed(decimals)}%`;
}

/** Format funding rate (stored as decimal, display as %) */
export function fmtFunding(v: number | null | undefined): string {
	if (v === null || v === undefined) return '—';
	const pct = v * 100;
	return `${pct > 0 ? '+' : ''}${pct.toFixed(4)}%`;
}

/** Format price */
export function fmtPrice(v: number | null | undefined): string {
	if (v === null || v === undefined) return '—';
	return `$${v.toFixed(2)}`;
}

/** Format contract counts with K/M suffix */
export function fmtContracts(v: number | null | undefined): string {
	if (v === null || v === undefined) return '—';
	if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(2)}M`;
	if (v >= 1_000)     return `${(v / 1_000).toFixed(2)}K`;
	return v.toFixed(2);
}

/** Color for positive/negative/null values */
export function changeColor(v: number | null | undefined): string {
	if (v === null || v === undefined) return 'var(--text-dimmed)';
	return v > 0 ? 'var(--green)' : v < 0 ? 'var(--red)' : 'var(--text-muted)';
}

/**
 * Fear & Greed Index color.
 * Thresholds align with backend _fg_label: 20/40/60/80.
 */
export function fearGreedColor(v: number): string {
	if (v <= 20)  return 'var(--red)';         // Extreme Fear
	if (v <= 40)  return '#f97316';             // Fear (orange)
	if (v <= 60)  return '#eab308';             // Neutral (yellow)
	if (v <= 80)  return 'var(--green)';        // Greed
	return '#22c55e';                           // Extreme Greed
}

/** Funding rate color gradient */
export function rateColor(rate: number | null | undefined): string {
	if (rate === null || rate === undefined) return 'var(--text-dimmed)';
	const pct = rate * 100;
	if (pct > 0.01)  return '#22c55e';   // deep green
	if (pct > 0)     return '#86efac';   // light green
	if (pct < -0.01) return '#ef4444';   // deep red
	if (pct < 0)     return '#fca5a5';   // light red
	return 'var(--text-dimmed)';
}

/** Relative time from ISO timestamp string */
export function relativeTime(ts: string | null | undefined): string {
	if (!ts) return '';
	try {
		const d = new Date(ts);
		const now = Date.now();
		const diffMin = Math.round((now - d.getTime()) / 60000);
		if (diffMin < 1)   return 'just now';
		if (diffMin < 60)  return `${diffMin}m ago`;
		const h = Math.floor(diffMin / 60);
		return `${h}h ago`;
	} catch {
		return '';
	}
}
