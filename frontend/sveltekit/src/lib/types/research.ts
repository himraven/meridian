export interface StockOverview {
  ticker: string;
  name: string;
  market: 'CN' | 'HK' | 'US';
  price: number;
  change: number;
  changePercent: number;
  marketCap: number;
  pe: number | null;
  pb: number | null;
  sector: string;
  industry: string;
}

export interface ResearchRating {
  signal: 'strong-buy' | 'buy' | 'hold' | 'caution' | 'avoid';
  targetPrice: number;
  safetyMargin: number; // percentage
  moatScore: number; // 0-10
  riskLevel: 'low' | 'medium' | 'high';
  thesis: string; // one-line investment thesis
  updatedAt: string;
}

export interface FinancialData {
  year: number;
  quarter?: number;
  revenue: number;
  netIncome: number;
  operatingCashFlow: number;
  freeCashFlow: number;
  eps: number;
  roe: number;
  debtToEquity: number;
  currentRatio: number;
}

export interface ValuationData {
  metric: string;
  current: number;
  fiveYearAvg: number;
  industryAvg: number;
  percentile: number; // 0-100
}

export interface MoatFactor {
  name: string;
  score: number; // 0-10
  description: string;
  evidence: string[];
}

export interface RiskItem {
  category: string;
  severity: 'high' | 'medium' | 'low';
  description: string;
  monitorTrigger: string;
  bearishArgument: string;
}

export interface CatalystEvent {
  date: string;
  event: string;
  impact: 'positive' | 'negative' | 'neutral';
  probability: number; // 0-100
  description: string;
}

export interface ResearchReport {
  overview: StockOverview;
  rating: ResearchRating;
  financials: FinancialData[];
  valuation: ValuationData[];
  moat: MoatFactor[];
  risks: RiskItem[];
  catalysts: CatalystEvent[];
  novaAnalysis: string; // markdown
  generatedAt: string;
}
