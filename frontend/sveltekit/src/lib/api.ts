// ═══════════════════════════════════════════════════════════════════
// API Client — Meridian
// Unified fetch wrapper with error handling
// ═══════════════════════════════════════════════════════════════════

const API_BASE = typeof window === 'undefined' 
	? (process.env.API_URL || 'http://localhost:8502') + '/api'
	: '/api';

export class ApiError extends Error {
	constructor(
		message: string,
		public status: number,
		public endpoint: string
	) {
		super(message);
		this.name = 'ApiError';
	}
}

/**
 * Unified API fetch with error handling
 */
export async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
	const url = `${API_BASE}${endpoint}`;
	
	try {
		const response = await fetch(url, {
			headers: {
				'Content-Type': 'application/json',
				...options?.headers
			},
			...options
		});

		if (!response.ok) {
			const errorText = await response.text().catch(() => 'Unknown error');
			throw new ApiError(
				`API request failed: ${errorText}`,
				response.status,
				endpoint
			);
		}

		return await response.json();
	} catch (error) {
		if (error instanceof ApiError) {
			throw error;
		}
		throw new ApiError(
			error instanceof Error ? error.message : 'Network error',
			0,
			endpoint
		);
	}
}

/**
 * Build query string from parameters
 */
export function buildQueryString(params: Record<string, any>): string {
	const filtered = Object.entries(params)
		.filter(([_, value]) => value !== undefined && value !== null && value !== '')
		.map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`);
	
	return filtered.length > 0 ? `?${filtered.join('&')}` : '';
}

/**
 * API endpoint helpers
 */
export const api = {
	// Congress
	congress: {
		trades: (params?: { days?: number; party?: string; chamber?: string; trade_type?: string; ticker?: string }) =>
			fetchApi(`/congress/trades${buildQueryString(params || {})}`),
	},
	
	// ARK
	ark: {
		trades: (params?: { days?: number; fund?: string; direction?: string; ticker?: string }) =>
			fetchApi(`/ark/trades${buildQueryString(params || {})}`),
		holdings: (params?: { fund?: string; ticker?: string; min_weight?: number }) =>
			fetchApi(`/ark/holdings${buildQueryString(params || {})}`),
	},
	
	// Dark Pool
	darkpool: {
		analytics: (params?: { days?: number; min_zscore?: number; ticker?: string }) =>
			fetchApi(`/darkpool/analytics${buildQueryString(params || {})}`),
	},
	
	// Institutions
	institutions: {
		filings: () => fetchApi('/institutions/filings'),
	},
	
	// Insiders
	insiders: {
		trades: (params?: { days?: number; transaction_type?: string; ticker?: string; min_value?: number; cluster_only?: boolean }) =>
			fetchApi(`/us/insiders${buildQueryString(params || {})}`),
	},
	
	// Ranking
	ranking: {
		confluence: (params?: { min_score?: number; direction?: string; ticker?: string }) =>
			fetchApi(`/ranking/confluence${buildQueryString(params || {})}`),
		smartMoney: (params?: { min_score?: number; source?: string; days?: number }) =>
			fetchApi(`/ranking/smart-money${buildQueryString(params || {})}`),
		feed: (params?: { days?: number; source?: string; ticker?: string; limit?: number }) =>
			fetchApi(`/ranking/feed${buildQueryString(params || {})}`),
	},
	
	// Ticker
	ticker: {
		detail: (symbol: string) => fetchApi(`/ticker/${symbol}`),
	},
	
	// HK
	hk: {
		signals: () => fetchApi('/hk/signals'),
		history: () => fetchApi('/hk/history'),
	},
	
	// CN
	cn: {
		trend: () => fetchApi('/cn/trend'),
		strategy: {
			nav: () => fetchApi('/cn/8x30/nav'),
			portfolio: () => fetchApi('/cn/8x30/portfolio'),
			metrics: () => fetchApi('/cn/8x30/metrics'),
			sensitivity: () => fetchApi('/cn/8x30/sensitivity'),
		},
	},
	
	// Dividend
	dividend: () => fetchApi('/dividend-screener'),
	
	// Research
	research: {
		list: () => fetchApi('/research'),
		detail: (ticker: string) => fetchApi(`/research/${ticker}`),
	},
};
