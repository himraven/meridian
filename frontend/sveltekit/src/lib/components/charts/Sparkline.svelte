<script lang="ts">
	import { onMount } from 'svelte';
	
	interface Props {
		data: number[];
		width?: number;
		height?: number;
		color?: string;
		lineWidth?: number;
		showDots?: boolean;
		class?: string;
	}
	
	let { 
		data, 
		width = 150, 
		height = 40,
		color = '#22c55e',
		lineWidth = 2,
		showDots = false,
		class: className = ''
	}: Props = $props();
	
	let canvas: HTMLCanvasElement;
	
	function drawSparkline() {
		if (!canvas || !data || data.length === 0) return;
		
		const ctx = canvas.getContext('2d');
		if (!ctx) return;
		
		// Retina / HiDPI support
		const dpr = typeof window !== 'undefined' ? (window.devicePixelRatio || 1) : 1;
		canvas.width = width * dpr;
		canvas.height = height * dpr;
		ctx.scale(dpr, dpr);
		
		// Enable anti-aliasing (default on, but ensure smooth rendering)
		ctx.imageSmoothingEnabled = true;
		ctx.imageSmoothingQuality = 'high';
		
		// Clear canvas
		ctx.clearRect(0, 0, width, height);
		
		// Calculate min/max for scaling with padding
		const min = Math.min(...data);
		const max = Math.max(...data);
		const range = max - min || 1;
		const padding = 2;
		const drawHeight = height - padding * 2;
		
		// Calculate points
		const points = data.map((value, index) => ({
			x: (index / (data.length - 1)) * width,
			y: padding + drawHeight - ((value - min) / range) * drawHeight
		}));
		
		// Draw area fill (subtle gradient)
		const gradient = ctx.createLinearGradient(0, 0, 0, height);
		gradient.addColorStop(0, color + '33'); // 20% opacity at top
		gradient.addColorStop(1, color + '00'); // transparent at bottom
		
		ctx.beginPath();
		ctx.moveTo(points[0].x, points[0].y);
		for (let i = 1; i < points.length; i++) {
			// Smooth curve using quadratic bezier
			const xMid = (points[i - 1].x + points[i].x) / 2;
			ctx.quadraticCurveTo(points[i - 1].x, points[i - 1].y, xMid, (points[i - 1].y + points[i].y) / 2);
		}
		ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y);
		ctx.lineTo(points[points.length - 1].x, height);
		ctx.lineTo(points[0].x, height);
		ctx.closePath();
		ctx.fillStyle = gradient;
		ctx.fill();
		
		// Draw line with smooth curves
		ctx.strokeStyle = color;
		ctx.lineWidth = lineWidth;
		ctx.lineCap = 'round';
		ctx.lineJoin = 'round';
		
		ctx.beginPath();
		ctx.moveTo(points[0].x, points[0].y);
		for (let i = 1; i < points.length; i++) {
			const xMid = (points[i - 1].x + points[i].x) / 2;
			ctx.quadraticCurveTo(points[i - 1].x, points[i - 1].y, xMid, (points[i - 1].y + points[i].y) / 2);
		}
		ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y);
		ctx.stroke();
		
		// Draw endpoint dot
		if (showDots && points.length > 0) {
			const last = points[points.length - 1];
			ctx.fillStyle = color;
			ctx.beginPath();
			ctx.arc(last.x, last.y, 2.5, 0, Math.PI * 2);
			ctx.fill();
		}
	}
	
	onMount(() => {
		drawSparkline();
	});
	
	$effect(() => {
		data;
		drawSparkline();
	});
</script>

<div class="inline-block {className}">
	<canvas 
		bind:this={canvas}
		style="width: {width}px; height: {height}px;"
	></canvas>
</div>
