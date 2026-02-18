<script lang="ts">
	interface Props {
		type?: 'line' | 'card' | 'table' | 'circle';
		width?: string;
		height?: string;
		class?: string;
	}
	
	let { 
		type = 'line', 
		width = 'w-full', 
		height = 'h-4',
		class: className = ''
	}: Props = $props();
	
	const baseClass = 'animate-pulse bg-accent/30 rounded';
	
	const typeClasses = {
		line: `${height} ${width}`,
		card: 'h-48 w-full',
		table: 'h-96 w-full',
		circle: 'rounded-full'
	};
</script>

<div class="{baseClass} {typeClasses[type]} {className}"></div>
