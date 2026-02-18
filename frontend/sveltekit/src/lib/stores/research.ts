import { writable } from 'svelte/store';
import type { ResearchReport } from '$lib/types/research';

export const currentTicker = writable<string>('');
export const currentReport = writable<ResearchReport | null>(null);
export const activeTab = writable<string>('overview');
