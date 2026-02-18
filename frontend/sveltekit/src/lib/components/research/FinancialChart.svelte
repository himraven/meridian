<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import type { EChartsType } from 'echarts';

  interface Props {
    title: string;
    years: number[];
    series: Array<{
      name: string;
      type: 'bar' | 'line';
      data: number[];
      color?: string;
      yAxisIndex?: number;
    }>;
    formatLeft?: (v: number) => string;
    formatRight?: (v: number) => string;
    hasRightAxis?: boolean;
    height?: string;
  }

  let {
    title,
    years,
    series,
    formatLeft = (v) => v.toFixed(0),
    formatRight = (v) => v.toFixed(0),
    hasRightAxis = false,
    height = '280px'
  }: Props = $props();

  let container: HTMLDivElement;
  let chart: EChartsType | null = null;

  function buildOption() {
    const yAxes: object[] = [
      {
        type: 'value',
        axisLabel: {
          color: '#71717a',
          fontSize: 11,
          fontFamily: "'JetBrains Mono', monospace",
          formatter: formatLeft
        },
        splitLine: { lineStyle: { color: '#27272a', width: 1 } },
        axisLine: { show: false },
        axisTick: { show: false }
      }
    ];

    if (hasRightAxis) {
      yAxes.push({
        type: 'value',
        axisLabel: {
          color: '#71717a',
          fontSize: 11,
          fontFamily: "'JetBrains Mono', monospace",
          formatter: formatRight
        },
        splitLine: { show: false },
        axisLine: { show: false },
        axisTick: { show: false }
      });
    }

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#18181b',
        borderColor: '#3f3f46',
        borderWidth: 1,
        textStyle: { color: '#a1a1aa', fontSize: 12, fontFamily: "'JetBrains Mono', monospace" },
        axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(255,255,255,0.03)' } }
      },
      legend: {
        bottom: 4,
        textStyle: { color: '#71717a', fontSize: 11, fontFamily: "'JetBrains Mono', monospace" },
        icon: 'circle',
        itemWidth: 8,
        itemHeight: 8
      },
      grid: {
        left: '2%',
        right: hasRightAxis ? '4%' : '2%',
        bottom: '12%',
        top: '8%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: years.map(String),
        axisLabel: {
          color: '#71717a',
          fontSize: 11,
          fontFamily: "'JetBrains Mono', monospace"
        },
        axisLine: { lineStyle: { color: '#27272a' } },
        axisTick: { show: false }
      },
      yAxis: yAxes,
      series: series.map(s => ({
        name: s.name,
        type: s.type,
        data: s.data,
        yAxisIndex: s.yAxisIndex ?? 0,
        itemStyle: {
          color: s.color ?? '#a1a1aa',
          borderRadius: s.type === 'bar' ? [2, 2, 0, 0] : undefined
        },
        lineStyle: s.type === 'line' ? { color: s.color, width: 2 } : undefined,
        symbol: s.type === 'line' ? 'circle' : undefined,
        symbolSize: s.type === 'line' ? 4 : undefined,
        barMaxWidth: 32
      }))
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
    if (chart) {
      chart.setOption(buildOption(), true);
    }
  });

  onDestroy(() => {
    chart?.dispose();
  });
</script>

<div class="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-5 hover:border-[var(--border-hover)] transition-colors">
  <h3 class="text-sm font-medium text-[var(--text-primary)] mb-4">{title}</h3>
  <div bind:this={container} style="width:100%; height:{height}"></div>
</div>
