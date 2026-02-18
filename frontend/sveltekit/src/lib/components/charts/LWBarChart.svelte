<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';

	interface DataPoint {
		time: string;
		value: number;
		color?: string;
	}

	interface Props {
		data: DataPoint[];
		height?: number;
		upColor?: string;
		downColor?: string;
		class?: string;
	}

	let {
		data,
		height = 150,
		upColor = '#22c55e',
		downColor = '#f87171',
		class: className = ''
	}: Props = $props();

	let container: HTMLDivElement;
	let chart: any = null;
	let series: any = null;
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
				vertLines: { visible: false },
				horzLines: { color: '#27272a' },
			},
			rightPriceScale: { borderColor: '#27272a' },
			timeScale: { borderColor: '#27272a', timeVisible: false },
			handleScroll: { vertTouchDrag: false },
		});

		series = chart.addHistogramSeries({
			priceLineVisible: false,
			lastValueVisible: false,
		});

		if (data?.length) {
			const coloredData = data.map(d => ({
				...d,
				color: d.color || (d.value >= 0 ? upColor : downColor),
			}));
			series.setData(coloredData);
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
</script>

<div class="{className}" bind:this={container}></div>
