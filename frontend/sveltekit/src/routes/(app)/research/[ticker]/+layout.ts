import type { LayoutLoad } from './$types';
import type { ResearchReport } from '$lib/types/research';
import { error } from '@sveltejs/kit';
import { fetchApi } from '$lib/api';
import { getMockReport, availableReports } from '$lib/data/mock-research';

export const load: LayoutLoad = async ({ params }) => {
  const ticker = params.ticker;

  // Try API first
  try {
    const report = await fetchApi<ResearchReport>(`/research/${ticker}`);
    return { report, ticker };
  } catch {
    // Fallback to mock data
    const known = availableReports.find(r =>
      r.ticker.toLowerCase() === ticker.toLowerCase()
    );

    if (!known) {
      error(404, `No research report found for ticker "${ticker}". Try 600519 or 00700.`);
    }

    const report = getMockReport(ticker);
    return { report, ticker };
  }
};
