import type { LayoutLoad } from './$types';
import { error } from '@sveltejs/kit';
import { getMockReport } from '$lib/data/mock-research';
import { availableReports } from '$lib/data/mock-research';

export const load: LayoutLoad = ({ params }) => {
  const known = availableReports.find(r =>
    r.ticker.toLowerCase() === params.ticker.toLowerCase()
  );

  if (!known) {
    error(404, `No research report found for ticker "${params.ticker}". Try 600519 or 00700.`);
  }

  const report = getMockReport(params.ticker);
  return { report, ticker: params.ticker };
};
