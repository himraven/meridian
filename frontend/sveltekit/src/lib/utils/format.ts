// ═══════════════════════════════════════════════════════════════════
// Format Utilities — Smart Money Platform
// Currency, percentage, date, number formatting
// ═══════════════════════════════════════════════════════════════════

/**
 * Format currency (USD)
 */
export function formatCurrency(value: number | null | undefined, decimals = 2): string {
	if (value === null || value === undefined || isNaN(value)) return 'N/A';
	
	// For large numbers, use abbreviated format
	if (Math.abs(value) >= 1_000_000_000) {
		return `$${(value / 1_000_000_000).toFixed(2)}B`;
	}
	if (Math.abs(value) >= 1_000_000) {
		return `$${(value / 1_000_000).toFixed(2)}M`;
	}
	if (Math.abs(value) >= 1_000) {
		return `$${(value / 1_000).toFixed(2)}K`;
	}
	
	return `$${value.toFixed(decimals)}`;
}

/**
 * Format percentage
 */
export function formatPercent(value: number | null | undefined, decimals = 2, showSign = false): string {
	if (value === null || value === undefined || isNaN(value)) return 'N/A';
	
	const sign = showSign && value > 0 ? '+' : '';
	return `${sign}${value.toFixed(decimals)}%`;
}

/**
 * Format large numbers with K/M/B suffix
 */
export function formatNumber(value: number | null | undefined, decimals = 2): string {
	if (value === null || value === undefined || isNaN(value)) return 'N/A';
	
	if (Math.abs(value) >= 1_000_000_000) {
		return `${(value / 1_000_000_000).toFixed(decimals)}B`;
	}
	if (Math.abs(value) >= 1_000_000) {
		return `${(value / 1_000_000).toFixed(decimals)}M`;
	}
	if (Math.abs(value) >= 1_000) {
		return `${(value / 1_000).toFixed(decimals)}K`;
	}
	
	return value.toFixed(decimals);
}

/**
 * Format number with commas (e.g., 1,234,567)
 */
export function formatNumberWithCommas(value: number | null | undefined): string {
	if (value === null || value === undefined || isNaN(value)) return 'N/A';
	return value.toLocaleString('en-US');
}

/**
 * Format date (YYYY-MM-DD → readable)
 */
export function formatDate(dateStr: string | null | undefined, format: 'short' | 'long' = 'short'): string {
	if (!dateStr) return 'N/A';
	
	try {
		const date = new Date(dateStr);
		if (isNaN(date.getTime())) return dateStr;
		
		if (format === 'short') {
			return date.toLocaleDateString('en-US', { 
				month: 'short', 
				day: 'numeric', 
				year: 'numeric' 
			});
		} else {
			return date.toLocaleDateString('en-US', { 
				month: 'long', 
				day: 'numeric', 
				year: 'numeric' 
			});
		}
	} catch {
		return dateStr;
	}
}

/**
 * Format relative time (e.g., "3 hours ago")
 */
export function formatRelativeTime(dateStr: string | null | undefined): string {
	if (!dateStr) return 'N/A';
	
	try {
		const date = new Date(dateStr);
		const now = new Date();
		const diffMs = now.getTime() - date.getTime();
		const diffSecs = Math.floor(diffMs / 1000);
		const diffMins = Math.floor(diffSecs / 60);
		const diffHours = Math.floor(diffMins / 60);
		const diffDays = Math.floor(diffHours / 24);
		
		if (diffDays > 0) return `${diffDays}d ago`;
		if (diffHours > 0) return `${diffHours}h ago`;
		if (diffMins > 0) return `${diffMins}m ago`;
		return 'just now';
	} catch {
		return dateStr;
	}
}

/**
 * Get color class for positive/negative values
 */
export function getChangeColor(value: number | null | undefined): string {
	if (value === null || value === undefined || isNaN(value)) return 'text-muted';
	if (value > 0) return 'text-green';
	if (value < 0) return 'text-red';
	return 'text-muted';
}

/**
 * Get badge color for direction
 */
export function getDirectionColor(direction: string | null | undefined): string {
	if (!direction) return 'bg-muted/20 text-muted';
	
	const lower = direction.toLowerCase();
	if (lower.includes('bull') || lower.includes('buy') || lower.includes('purchase')) {
		return 'bg-green/20 text-green';
	}
	if (lower.includes('bear') || lower.includes('sell') || lower.includes('sale')) {
		return 'bg-red/20 text-red';
	}
	return 'bg-yellow/20 text-yellow';
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string | null | undefined, maxLength: number): string {
	if (!text) return '';
	if (text.length <= maxLength) return text;
	return text.slice(0, maxLength - 3) + '...';
}
