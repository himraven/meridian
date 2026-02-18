import type { PageLoad } from './$types';
import { fetchApi } from '$lib/api';
import { availableReports } from '$lib/data/mock-research';

interface ReportSummary {
  ticker: string;
  name: string;
  market: string;
  signal: string;
  updatedAt?: string;
}

interface ReportListResponse {
  reports: ReportSummary[];
  count: number;
}

export const load: PageLoad = async () => {
  try {
    const data = await fetchApi<ReportListResponse>('/research');
    return { reports: data.reports };
  } catch {
    // Fallback to mock data
    return { reports: availableReports.map(r => ({ ...r })) };
  }
};
