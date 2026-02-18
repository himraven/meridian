<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';

	interface DataPoint {
		time: string;
		value: number;
	}

	interface Props {
		data: DataPoint[];
		secondaryData?: DataPoint[];
		height?: number;
		color?: string;
		secondaryColor?: string;
		class?: string;
	}

	let {
		data,
		secondaryData,
		height = 300,
		color = '#22c55e',
		secondaryColor = '#71717a',
		class: className = ''
	}: Props = $props();

	let container: HTMLDivElement;
	let chart: any = null;
	let primarySeries: any = null;
	let secondarySeries: any = null;
	let resizeObserver: ResizeObserver | null = null;

	async function initChart() {
		if (!browser || !container || chart) return;

		const lw = await import('lightweight-charts');

		chart = lw.createChart(container, {
			height,
			layout: {
				background: { type: lw.ColorType.Solid, color: 'transparent' },
				textColor: '#71717a',
				fontFamily: "'JetBrains Mono', 'SF Mono', monospace",
				fontSize: 11,
			},
			grid: {
				vertLines: { color: '#27272a' },
				horzLines: { color: '#27272a' },
			},
			crosshair: {
				vertLine: { color: '#3f3f46', labelBackgroundColor: '#27272a' },
				horzLine: { color: '#3f3f46', labelBackgroundColor: '#27272a' },
			},
			rightPriceScale: { borderColor: '#27272a' },
			timeScale: { borderColor: '#27272a', timeVisible: false },
			handleScroll: { vertTouchDrag: false },
		});

		primarySeries = chart.addLineSeries({
			color,
			lineWidth: 2,
			priceLineVisible: false,
			lastValueVisible: true,
			crosshairMarkerRadius: 4,
		});

		if (data?.length) {
			primarySeries.setData(data);
		}

		if (secondaryData?.length) {
			secondarySeries = chart.addLineSeries({
				color: secondaryColor,
				lineWidth: 1,
				lineStyle: lw.LineStyle.Dashed,
				priceLineVisible: false,
				lastValueVisible: true,
			});
			secondarySeries.setData(secondaryData);
		}

		chart.timeScale().fitContent();

		resizeObserver = new ResizeObserver(() => {
			if (chart && container) {
				chart.applyOptions({ width: container.clientWidth });
			}
		});
		resizeObserver.observe(container);
	}

	onMount(() => {
		initChart();
		return () => {
			resizeObserver?.disconnect();
			if (chart) { chart.remove(); chart = null; }
		};
	});

	$effect(() => {
		if (primarySeries && data?.length) {
			primarySeries.setData(data);
			chart?.timeScale().fitContent();
		}
	});
</script>

<div class="{className}" bind:this={container}></div>
