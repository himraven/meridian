<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import type { EChartsType } from 'echarts';

  interface Props {
    indicators: Array<{ name: string; max: number }>;
    current: number[];
    industryAvg: number[];
    height?: string;
  }

  let {
    indicators,
    current,
    industryAvg,
    height = '320px'
  }: Props = $props();

  let container: HTMLDivElement;
  let chart: EChartsType | null = null;

  function buildOption() {
    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        backgroundColor: '#18181b',
        borderColor: '#3f3f46',
        borderWidth: 1,
        textStyle: { color: '#a1a1aa', fontSize: 12, fontFamily: "'JetBrains Mono', monospace" }
      },
      legend: {
        bottom: 4,
        textStyle: { color: '#71717a', fontSize: 11, fontFamily: "'JetBrains Mono', monospace" },
        icon: 'circle',
        itemWidth: 8,
        itemHeight: 8
      },
      radar: {
        indicator: indicators,
        shape: 'polygon',
        splitNumber: 4,
        nameGap: 8,
        name: {
          textStyle: {
            color: '#71717a',
            fontSize: 11,
            fontFamily: "'JetBrains Mono', monospace"
          }
        },
        splitArea: {
          areaStyle: {
            color: ['rgba(255,255,255,0.01)', 'rgba(255,255,255,0.02)']
          }
        },
        axisLine: { lineStyle: { color: '#27272a' } },
        splitLine: { lineStyle: { color: '#27272a', width: 1 } }
      },
      series: [
        {
          type: 'radar',
          data: [
            {
              name: 'Current',
              value: current,
              lineStyle: { color: '#22c55e', width: 2 },
              itemStyle: { color: '#22c55e' },
              areaStyle: { color: 'rgba(34,197,94,0.08)' }
            },
            {
              name: 'Industry Avg',
              value: industryAvg,
              lineStyle: { color: '#52525b', width: 1.5, type: 'dashed' },
              itemStyle: { color: '#52525b' },
              areaStyle: { color: 'rgba(82,82,91,0.05)' }
            }
          ]
        }
      ]
    };
  }

  onMount(() => {
    let resizeObserver: ResizeObserver | null = null;
    function onWindowResize() { chart?.resize(); }

    (async () => {
      const echarts = await import('echarts');
      chart = echarts.init(container, null, { renderer: 'canvas' });
      chart.setOption(buildOption());

      resizeObserver = new ResizeObserver(() => chart?.resize());
      resizeObserver.observe(container);
      window.addEventListener('resize', onWindowResize);
    })();

    return () => {
      resizeObserver?.disconnect();
      window.removeEventListener('resize', onWindowResize);
    };
  });

  $effect(() => {
    if (chart) chart.setOption(buildOption(), true);
  });

  onDestroy(() => chart?.dispose());
</script>

<div bind:this={container} style="width:100%; height:{height}"></div>
