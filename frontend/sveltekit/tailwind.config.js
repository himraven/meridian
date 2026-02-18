/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {
			colors: {
				'bg-base':        '#09090b',
				'bg-surface':     '#18181b',
				'bg-elevated':    '#27272a',
				'border-default': '#27272a',
				'border-hover':   '#3f3f46',
				'border-focus':   '#52525b',
				'text-primary':   '#fafafa',
				'text-secondary': '#a1a1aa',
				'text-muted':     '#71717a',
				'text-dimmed':    '#52525b',
				'green':          '#22c55e',
				'red':            '#ef4444',
				'amber':          '#f59e0b',
				'blue':           '#3b82f6',
			},
			fontFamily: {
				body: ['Inter', '-apple-system', 'system-ui', 'sans-serif'],
				mono: ['JetBrains Mono', 'SF Mono', 'Cascadia Code', 'monospace'],
			},
		}
	},
	plugins: []
};
