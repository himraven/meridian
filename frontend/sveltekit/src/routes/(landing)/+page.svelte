<script lang="ts">
	import { onMount } from 'svelte';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	// ── Animated counters ────────────────────────────────────────────
	let counters = $state({
		signals: 0,
		sources: 0,
		markets: 0,
	});

	const targets = { signals: 166, sources: 4, markets: 3 };
	let statsVisible = $state(false);
	let statsRef: HTMLElement;

	// ── Scroll-triggered fade-in ─────────────────────────────────────
	let visibleSections = $state(new Set<string>());

	onMount(() => {
		// Counter animation
		const statsObserver = new IntersectionObserver(
			(entries) => {
				entries.forEach((entry) => {
					if (entry.isIntersecting && !statsVisible) {
						statsVisible = true;
						animateCounters();
					}
				});
			},
			{ threshold: 0.3 }
		);
		if (statsRef) statsObserver.observe(statsRef);

		// Fade-in sections
		const fadeObserver = new IntersectionObserver(
			(entries) => {
				entries.forEach((entry) => {
					if (entry.isIntersecting) {
						const id = (entry.target as HTMLElement).dataset.fadeId;
						if (id) visibleSections = new Set([...visibleSections, id]);
					}
				});
			},
			{ threshold: 0.1, rootMargin: '0px 0px -60px 0px' }
		);

		document.querySelectorAll('[data-fade-id]').forEach((el) => fadeObserver.observe(el));

		return () => {
			statsObserver.disconnect();
			fadeObserver.disconnect();
		};
	});

	function animateCounters() {
		const duration = 1800;
		const start = performance.now();

		function step(now: number) {
			const elapsed = now - start;
			const progress = Math.min(elapsed / duration, 1);
			const ease = 1 - Math.pow(1 - progress, 3);

			counters = {
				signals: Math.round(targets.signals * ease),
				sources: Math.round(targets.sources * ease),
				markets: Math.round(targets.markets * ease),
			};

			if (progress < 1) requestAnimationFrame(step);
		}
		requestAnimationFrame(step);
	}

	function isVisible(id: string) {
		return visibleSections.has(id);
	}

	// ── Signal helpers ───────────────────────────────────────────────
	function getScoreColor(score: number): string {
		if (score >= 80) return '#fafafa';
		if (score >= 65) return '#a1a1aa';
		return '#71717a';
	}
</script>

<!-- ══════════════════════════════════════════════════════════
     LANDING NAV
════════════════════════════════════════════════════════════ -->
<nav class="landing-nav">
	<a href="/" class="nav-logo">
		<span class="logo-mark">M</span>
		<span class="logo-text">Meridian</span>
	</a>
	<a href="/dashboard" class="nav-cta">
		Enter Dashboard
		<svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
			<path d="M2.5 7H11.5M11.5 7L8 3.5M11.5 7L8 10.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
		</svg>
	</a>
</nav>

<!-- ══════════════════════════════════════════════════════════
     HERO SECTION
════════════════════════════════════════════════════════════ -->
<section class="hero">
	<!-- Animated SVG background -->
	<div class="hero-bg" aria-hidden="true">
		<!-- Grid overlay -->
		<div class="grid-overlay"></div>

		<!-- SVG network constellation -->
		<svg class="network-svg" viewBox="0 0 1200 700" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
			<defs>
				<radialGradient id="nodeGlow" cx="50%" cy="50%" r="50%">
					<stop offset="0%" stop-color="#a1a1aa" stop-opacity="0.5"/>
					<stop offset="100%" stop-color="#a1a1aa" stop-opacity="0"/>
				</radialGradient>
				<filter id="blur4">
					<feGaussianBlur stdDeviation="4"/>
				</filter>
				<filter id="blur2">
					<feGaussianBlur stdDeviation="2"/>
				</filter>
				<linearGradient id="lineGrad1" x1="0%" y1="0%" x2="100%" y2="0%">
					<stop offset="0%" stop-color="#71717a" stop-opacity="0"/>
					<stop offset="50%" stop-color="#71717a" stop-opacity="0.4"/>
					<stop offset="100%" stop-color="#71717a" stop-opacity="0"/>
				</linearGradient>
				<linearGradient id="lineGrad2" x1="0%" y1="0%" x2="100%" y2="0%">
					<stop offset="0%" stop-color="#52525b" stop-opacity="0"/>
					<stop offset="50%" stop-color="#52525b" stop-opacity="0.3"/>
					<stop offset="100%" stop-color="#52525b" stop-opacity="0"/>
				</linearGradient>
			</defs>

			<!-- Connection lines (data flows) -->
			<g class="connections" opacity="0.5">
				<line x1="180" y1="120" x2="420" y2="200" stroke="#52525b" stroke-width="0.5" class="conn-line" style="--delay: 0s"/>
				<line x1="420" y1="200" x2="640" y2="150" stroke="#52525b" stroke-width="0.5" class="conn-line" style="--delay: 0.4s"/>
				<line x1="640" y1="150" x2="850" y2="220" stroke="#52525b" stroke-width="0.5" class="conn-line" style="--delay: 0.8s"/>
				<line x1="850" y1="220" x2="1050" y2="140" stroke="#52525b" stroke-width="0.5" class="conn-line" style="--delay: 1.2s"/>
				<line x1="420" y1="200" x2="380" y2="380" stroke="#3f3f46" stroke-width="0.5" class="conn-line" style="--delay: 0.2s"/>
				<line x1="640" y1="150" x2="680" y2="340" stroke="#3f3f46" stroke-width="0.5" class="conn-line" style="--delay: 0.6s"/>
				<line x1="850" y1="220" x2="800" y2="400" stroke="#52525b" stroke-width="0.5" class="conn-line" style="--delay: 1.0s"/>
				<line x1="380" y1="380" x2="680" y2="340" stroke="#52525b" stroke-width="0.5" class="conn-line" style="--delay: 0.3s"/>
				<line x1="680" y1="340" x2="800" y2="400" stroke="#3f3f46" stroke-width="0.5" class="conn-line" style="--delay: 0.7s"/>
				<line x1="180" y1="120" x2="380" y2="380" stroke="#52525b" stroke-width="0.3" class="conn-line" style="--delay: 1.5s"/>
				<line x1="800" y1="400" x2="1050" y2="500" stroke="#3f3f46" stroke-width="0.5" class="conn-line" style="--delay: 0.9s"/>
				<line x1="380" y1="380" x2="200" y2="520" stroke="#52525b" stroke-width="0.3" class="conn-line" style="--delay: 1.1s"/>
				<line x1="680" y1="340" x2="550" y2="520" stroke="#3f3f46" stroke-width="0.3" class="conn-line" style="--delay: 1.3s"/>
				<line x1="1050" y1="140" x2="1100" y2="380" stroke="#52525b" stroke-width="0.3" class="conn-line" style="--delay: 0.5s"/>
				<line x1="1100" y1="380" x2="1050" y2="500" stroke="#3f3f46" stroke-width="0.3" class="conn-line" style="--delay: 1.4s"/>
			</g>

			<!-- Flowing data pulses along connections -->
			<g class="data-pulses">
				<circle r="2.5" fill="#fafafa" opacity="0.7" class="pulse-dot">
					<animateMotion dur="3s" repeatCount="indefinite" begin="0s">
						<mpath href="#path1"/>
					</animateMotion>
				</circle>
				<circle r="2" fill="#a1a1aa" opacity="0.6" class="pulse-dot">
					<animateMotion dur="4s" repeatCount="indefinite" begin="1s">
						<mpath href="#path2"/>
					</animateMotion>
				</circle>
				<circle r="2.5" fill="#fafafa" opacity="0.7" class="pulse-dot">
					<animateMotion dur="3.5s" repeatCount="indefinite" begin="2s">
						<mpath href="#path3"/>
					</animateMotion>
				</circle>
				<circle r="1.5" fill="#a1a1aa" opacity="0.5" class="pulse-dot">
					<animateMotion dur="5s" repeatCount="indefinite" begin="0.5s">
						<mpath href="#path1"/>
					</animateMotion>
				</circle>
				<circle r="2" fill="#fafafa" opacity="0.5" class="pulse-dot">
					<animateMotion dur="4.5s" repeatCount="indefinite" begin="1.5s">
						<mpath href="#path3"/>
					</animateMotion>
				</circle>
			</g>

			<!-- Hidden paths for pulse animation -->
			<defs>
				<path id="path1" d="M180,120 L420,200 L640,150 L850,220 L1050,140"/>
				<path id="path2" d="M380,380 L680,340 L800,400 L1050,500"/>
				<path id="path3" d="M200,520 L380,380 L420,200 L640,150 L680,340"/>
			</defs>

			<!-- Nodes (data points) -->
			<g class="nodes">
				<!-- Primary nodes — larger, brighter -->
				<g class="node primary" style="--pulse-delay: 0s">
					<circle cx="420" cy="200" r="14" fill="url(#nodeGlow)" filter="url(#blur4)"/>
					<circle cx="420" cy="200" r="3" fill="#a1a1aa" class="node-core"/>
					<circle cx="420" cy="200" r="6" fill="none" stroke="#52525b" stroke-width="0.8" class="node-ring" opacity="0.5"/>
				</g>
				<g class="node primary" style="--pulse-delay: 0.8s">
					<circle cx="640" cy="150" r="12" fill="url(#nodeGlow)" filter="url(#blur4)"/>
					<circle cx="640" cy="150" r="3" fill="#a1a1aa" class="node-core"/>
					<circle cx="640" cy="150" r="6" fill="none" stroke="#52525b" stroke-width="0.8" class="node-ring" opacity="0.5"/>
				</g>
				<g class="node primary" style="--pulse-delay: 1.4s">
					<circle cx="680" cy="340" r="16" fill="url(#nodeGlow)" filter="url(#blur4)"/>
					<circle cx="680" cy="340" r="4" fill="#a1a1aa" class="node-core"/>
					<circle cx="680" cy="340" r="8" fill="none" stroke="#52525b" stroke-width="0.8" class="node-ring" opacity="0.5"/>
				</g>

				<!-- Secondary nodes -->
				<g class="node secondary" style="--pulse-delay: 0.3s">
					<circle cx="180" cy="120" r="8" fill="url(#nodeGlow)" filter="url(#blur2)"/>
					<circle cx="180" cy="120" r="2" fill="#71717a" class="node-core"/>
				</g>
				<g class="node secondary" style="--pulse-delay: 1.1s">
					<circle cx="850" cy="220" r="10" fill="url(#nodeGlow)" filter="url(#blur2)"/>
					<circle cx="850" cy="220" r="2.5" fill="#71717a" class="node-core"/>
				</g>
				<g class="node secondary" style="--pulse-delay: 0.6s">
					<circle cx="1050" cy="140" r="8" fill="url(#nodeGlow)" filter="url(#blur2)"/>
					<circle cx="1050" cy="140" r="2" fill="#a1a1aa" class="node-core"/>
				</g>
				<g class="node secondary" style="--pulse-delay: 1.7s">
					<circle cx="380" cy="380" r="10" fill="url(#nodeGlow)" filter="url(#blur2)"/>
					<circle cx="380" cy="380" r="2.5" fill="#71717a" class="node-core"/>
				</g>
				<g class="node secondary" style="--pulse-delay: 0.9s">
					<circle cx="800" cy="400" r="9" fill="url(#nodeGlow)" filter="url(#blur2)"/>
					<circle cx="800" cy="400" r="2" fill="#a1a1aa" class="node-core"/>
				</g>
				<g class="node secondary" style="--pulse-delay: 0.2s">
					<circle cx="1050" cy="500" r="7" fill="url(#nodeGlow)" filter="url(#blur2)"/>
					<circle cx="1050" cy="500" r="2" fill="#71717a" class="node-core"/>
				</g>
				<g class="node secondary" style="--pulse-delay: 1.3s">
					<circle cx="200" cy="520" r="6" fill="url(#nodeGlow)" filter="url(#blur2)"/>
					<circle cx="200" cy="520" r="1.5" fill="#71717a" class="node-core"/>
				</g>
				<g class="node secondary" style="--pulse-delay: 2.0s">
					<circle cx="550" cy="520" r="7" fill="url(#nodeGlow)" filter="url(#blur2)"/>
					<circle cx="550" cy="520" r="2" fill="#a1a1aa" class="node-core"/>
				</g>
				<g class="node secondary" style="--pulse-delay: 0.5s">
					<circle cx="1100" cy="380" r="6" fill="url(#nodeGlow)" filter="url(#blur2)"/>
					<circle cx="1100" cy="380" r="1.5" fill="#71717a" class="node-core"/>
				</g>

				<!-- Ticker labels near key nodes -->
				<text x="430" y="188" font-family="JetBrains Mono, monospace" font-size="9" fill="#a1a1aa" opacity="0.6" letter-spacing="0.05em">NVDA</text>
				<text x="650" y="138" font-family="JetBrains Mono, monospace" font-size="9" fill="#a1a1aa" opacity="0.6" letter-spacing="0.05em">MSFT</text>
				<text x="690" y="328" font-family="JetBrains Mono, monospace" font-size="9" fill="#a1a1aa" opacity="0.6" letter-spacing="0.05em">AAPL</text>
				<text x="860" y="208" font-family="JetBrains Mono, monospace" font-size="9" fill="#71717a" opacity="0.5" letter-spacing="0.05em">TSM</text>
				<text x="390" y="368" font-family="JetBrains Mono, monospace" font-size="9" fill="#71717a" opacity="0.5" letter-spacing="0.05em">META</text>
			</g>
		</svg>

		<!-- Radial fade from center -->
		<div class="hero-vignette"></div>
	</div>

	<!-- Hero content -->
	<div class="hero-content">
		<div class="hero-badge">
			<span class="badge-dot"></span>
			<span>Live Signal Intelligence</span>
		</div>

		<h1 class="hero-headline">
			Where Smart Money<br>
			<span class="headline-accent">Converges</span>
		</h1>

		<p class="hero-sub">
			Institutional-grade intelligence: Congress trades, dark pool flows,<br class="hide-mobile">
			13F filings, and ARK moves — all in one signal engine.
		</p>

		<div class="hero-actions">
			<a href="/dashboard" class="btn-primary">
				Enter Dashboard
				<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
					<path d="M3 8H13M13 8L9 4M13 8L9 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
				</svg>
			</a>
			<a href="#signals" class="btn-ghost">
				See Live Signals
			</a>
		</div>

		<!-- Subtle social proof -->
		<div class="hero-proof">
			<div class="proof-item">
				<span class="proof-num">166+</span>
				<span class="proof-label">Active signals</span>
			</div>
			<div class="proof-divider"></div>
			<div class="proof-item">
				<span class="proof-num">4</span>
				<span class="proof-label">Data sources</span>
			</div>
			<div class="proof-divider"></div>
			<div class="proof-item">
				<span class="proof-num">3</span>
				<span class="proof-label">Markets tracked</span>
			</div>
		</div>
	</div>
</section>

<!-- ══════════════════════════════════════════════════════════
     FEATURES SECTION
════════════════════════════════════════════════════════════ -->
<section class="features-section" id="features">
	<div class="section-container">
		<div
			class="section-header fade-in"
			class:visible={isVisible('features-header')}
			data-fade-id="features-header"
		>
			<div class="section-eyebrow">Signal Sources</div>
			<h2 class="section-title">Four signals.<br>One edge.</h2>
			<p class="section-desc">
				We aggregate the data that institutional traders act on — before it becomes common knowledge.
			</p>
		</div>

		<div class="features-grid">
			<div
				class="feature-card fade-in"
				class:visible={isVisible('feat-1')}
				data-fade-id="feat-1"
				style="--card-delay: 0ms"
			>
				<div class="feature-icon">
					<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
						<path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="#52525b" stroke-width="1.5" stroke-linejoin="round"/>
						<path d="M2 17L12 22L22 17" stroke="#52525b" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
						<path d="M2 12L12 17L22 12" stroke="#52525b" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
					</svg>
				</div>
				<h3 class="feature-title">Congress Trades</h3>
				<p class="feature-desc">
					Track politicians' stock moves the moment they're disclosed. Follow the money where regulation meets market access.
				</p>
				<div class="feature-tag">GOV</div>
			</div>

			<div
				class="feature-card fade-in"
				class:visible={isVisible('feat-2')}
				data-fade-id="feat-2"
				style="--card-delay: 80ms"
			>
				<div class="feature-icon">
					<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
						<path d="M21 16V8C21 6.9 20.1 6 19 6H5C3.9 6 3 6.9 3 8V16C3 17.1 3.9 18 5 18H19C20.1 18 21 17.1 21 16Z" stroke="#52525b" stroke-width="1.5"/>
						<path d="M7 12H9M11 12H13" stroke="#52525b" stroke-width="1.5" stroke-linecap="round"/>
						<path d="M3 10H21" stroke="#52525b" stroke-width="1.5"/>
					</svg>
				</div>
				<h3 class="feature-title">Dark Pool Flow</h3>
				<p class="feature-desc">
					Institutional block trades executed off-exchange. The hidden liquidity that moves markets before the crowd sees anything.
				</p>
				<div class="feature-tag">DP</div>
			</div>

			<div
				class="feature-card fade-in"
				class:visible={isVisible('feat-3')}
				data-fade-id="feat-3"
				style="--card-delay: 160ms"
			>
				<div class="feature-icon">
					<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
						<rect x="3" y="3" width="18" height="18" rx="2" stroke="#52525b" stroke-width="1.5"/>
						<path d="M7 8H17M7 12H14M7 16H11" stroke="#52525b" stroke-width="1.5" stroke-linecap="round"/>
					</svg>
				</div>
				<h3 class="feature-title">13F Filings</h3>
				<p class="feature-desc">
					Quarterly portfolio disclosures from hedge funds and institutions managing over $100M. See exactly what the smart money holds.
				</p>
				<div class="feature-tag">13F</div>
			</div>

			<div
				class="feature-card fade-in"
				class:visible={isVisible('feat-4')}
				data-fade-id="feat-4"
				style="--card-delay: 240ms"
			>
				<div class="feature-icon">
					<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
						<path d="M5 18L9 14L13 16L19 8" stroke="#52525b" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
						<circle cx="19" cy="8" r="2" stroke="#52525b" stroke-width="1.5"/>
					</svg>
				</div>
				<h3 class="feature-title">ARK Innovation</h3>
				<p class="feature-desc">
					Real-time position changes from Cathie Wood's high-conviction funds. Know what's being added or trimmed before markets open.
				</p>
				<div class="feature-tag">ARK</div>
			</div>
		</div>
	</div>
</section>

<!-- ══════════════════════════════════════════════════════════
     LIVE SIGNALS SECTION
════════════════════════════════════════════════════════════ -->
<section class="signals-section" id="signals">
	<div class="section-container">
		<div
			class="section-header fade-in"
			class:visible={isVisible('signals-header')}
			data-fade-id="signals-header"
		>
			<div class="section-eyebrow">Live Intelligence</div>
			<h2 class="section-title">Real signals.<br>Right now.</h2>
			<p class="section-desc">
				These aren't hypotheticals. This is the live feed your dashboard is running on.
			</p>
		</div>

		<div
			class="signals-list fade-in"
			class:visible={isVisible('signals-list')}
			data-fade-id="signals-list"
		>
			{#if data.signals && data.signals.length > 0}
				<div class="signals-header-row">
					<span>Ticker</span>
					<span>Company</span>
					<span class="hide-mobile">Direction</span>
					<span>Conviction</span>
				</div>
				{#each data.signals as signal, i}
					<div class="signal-item" style="--item-delay: {i * 60}ms">
						<div class="sig-ticker">{signal.ticker}</div>
						<div class="sig-company">{signal.company ?? '—'}</div>
						<div class="sig-badge hide-mobile">
							<span class="direction-badge bullish">
								<span class="badge-arrow">↑</span>
								Bullish
							</span>
						</div>
						<div class="sig-score-cell">
							<div class="score-bar-wrap">
								<div
									class="score-bar-fill"
									style="width: {Math.min(signal.score, 100)}%; background: {getScoreColor(signal.score)}"
								></div>
							</div>
							<span class="score-num" style="color: {getScoreColor(signal.score)}">{Math.round(signal.score)}</span>
						</div>
					</div>
				{/each}
				<div class="signals-cta-row">
					<a href="/dashboard" class="signals-view-all">
						View all signals in dashboard
						<svg width="14" height="14" viewBox="0 0 14 14" fill="none">
							<path d="M2.5 7H11.5M11.5 7L8 3.5M11.5 7L8 10.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
						</svg>
					</a>
				</div>
			{:else}
				<div class="signals-empty">
					<div class="empty-pulse"></div>
					<p>Signal engine initializing…</p>
					<a href="/dashboard" class="btn-primary" style="margin-top: 1.5rem">Open Dashboard</a>
				</div>
			{/if}
		</div>
	</div>
</section>

<!-- ══════════════════════════════════════════════════════════
     STATS SECTION
════════════════════════════════════════════════════════════ -->
<section class="stats-section" bind:this={statsRef}>
	<div class="section-container">
		<div class="stats-grid">
			<div class="stat-item">
				<div class="stat-number">
					<span class="stat-counter">{counters.signals}</span><span class="stat-plus">+</span>
				</div>
				<div class="stat-label">Active Signals</div>
				<div class="stat-sub">High-conviction opportunities tracked daily</div>
			</div>

			<div class="stat-item">
				<div class="stat-number">
					<span class="stat-counter">{counters.sources}</span>
				</div>
				<div class="stat-label">Data Sources</div>
				<div class="stat-sub">Congress, Dark Pool, 13F, ARK</div>
			</div>

			<div class="stat-item">
				<div class="stat-number">
					<span class="stat-counter">{counters.markets}</span>
				</div>
				<div class="stat-label">Markets</div>
				<div class="stat-sub">US · Hong Kong · China A-Shares</div>
			</div>

			<div class="stat-item">
				<div class="stat-number stat-text">Daily</div>
				<div class="stat-label">Updates</div>
				<div class="stat-sub">Signals refreshed every market day</div>
			</div>
		</div>
	</div>
</section>

<!-- ══════════════════════════════════════════════════════════
     FOOTER
════════════════════════════════════════════════════════════ -->
<footer class="landing-footer">
	<div class="footer-inner">
		<div class="footer-left">
			<a href="/" class="footer-logo">
				<span class="logo-mark small">M</span>
				<span>Meridian</span>
			</a>
			<p class="footer-tagline">Follow the signal. Ignore the noise.</p>
		</div>
		<div class="footer-links">
			<a href="/dashboard">Dashboard</a>
			<a href="/signals">Signals</a>
			<a href="/congress">Congress</a>
			<a href="/darkpool">Dark Pool</a>
		</div>
		<div class="footer-copy">
			<span>© 2026 Meridian</span>
		</div>
	</div>
</footer>

<style>
	/* ══════════════════════════════════════════════════════════════
	   Unified with Dashboard Design Tokens
	   Zinc-based neutral dark. Same palette as app.css.
	   Accent: only the dashboard's semantic green (#22c55e) sparingly.
	   ══════════════════════════════════════════════════════════════ */

	/* ── Nav ────────────────────────────────────────────────────── */
	.landing-nav {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		z-index: 50;
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0 2rem;
		height: 60px;
		background: rgba(9, 9, 11, 0.85);
		backdrop-filter: blur(12px);
		-webkit-backdrop-filter: blur(12px);
		border-bottom: 1px solid #27272a;
	}

	.nav-logo {
		display: flex;
		align-items: center;
		gap: 10px;
		text-decoration: none;
	}

	.logo-mark {
		width: 32px;
		height: 32px;
		background: #27272a;
		border: 1px solid #3f3f46;
		border-radius: 8px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-family: 'DM Sans', sans-serif;
		font-weight: 700;
		font-size: 16px;
		color: #fafafa;
		letter-spacing: -0.02em;
		flex-shrink: 0;
	}

	.logo-mark.small {
		width: 26px;
		height: 26px;
		font-size: 13px;
		border-radius: 6px;
	}

	.logo-text {
		font-family: 'DM Sans', sans-serif;
		font-weight: 600;
		font-size: 17px;
		color: #fafafa;
		letter-spacing: -0.02em;
	}

	.nav-cta {
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 7px 16px;
		background: #18181b;
		border: 1px solid #3f3f46;
		border-radius: 8px;
		font-size: 13px;
		font-weight: 500;
		color: #fafafa;
		text-decoration: none;
		transition: background 0.2s, border-color 0.2s;
	}

	.nav-cta:hover {
		background: #27272a;
		border-color: #52525b;
	}

	/* ── Hero ───────────────────────────────────────────────────── */
	.hero {
		position: relative;
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
		padding-top: 60px;
	}

	.hero-bg {
		position: absolute;
		inset: 0;
		z-index: 0;
	}

	.grid-overlay {
		position: absolute;
		inset: 0;
		background-image:
			linear-gradient(rgba(161, 161, 170, 0.03) 1px, transparent 1px),
			linear-gradient(90deg, rgba(161, 161, 170, 0.03) 1px, transparent 1px);
		background-size: 60px 60px;
	}

	.network-svg {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		opacity: 0.65;
	}

	/* Connection line animation */
	.conn-line {
		animation: line-pulse 4s ease-in-out infinite;
		animation-delay: var(--delay, 0s);
	}

	@keyframes line-pulse {
		0%, 100% { opacity: 0.2; }
		50% { opacity: 0.55; }
	}

	/* Node core pulse */
	.node-core {
		animation: node-breathe 3s ease-in-out infinite;
		animation-delay: var(--pulse-delay, 0s);
	}

	.node-ring {
		animation: ring-expand 3s ease-in-out infinite;
		animation-delay: var(--pulse-delay, 0s);
	}

	@keyframes node-breathe {
		0%, 100% { opacity: 0.6; r: 3px; }
		50% { opacity: 0.9; r: 4px; }
	}

	@keyframes ring-expand {
		0% { r: 5px; opacity: 0.3; }
		50% { r: 9px; opacity: 0.08; }
		100% { r: 5px; opacity: 0.3; }
	}

	.hero-vignette {
		position: absolute;
		inset: 0;
		background: radial-gradient(ellipse 80% 80% at 50% 50%, transparent 20%, #09090b 80%);
	}

	/* Hero content */
	.hero-content {
		position: relative;
		z-index: 1;
		text-align: center;
		max-width: 800px;
		padding: 0 1.5rem;
	}

	.hero-badge {
		display: inline-flex;
		align-items: center;
		gap: 8px;
		padding: 6px 14px;
		border: 1px solid #3f3f46;
		border-radius: 999px;
		background: #18181b;
		font-size: 12px;
		font-weight: 500;
		color: #a1a1aa;
		letter-spacing: 0.03em;
		margin-bottom: 2.5rem;
	}

	.badge-dot {
		width: 6px;
		height: 6px;
		background: #22c55e;
		border-radius: 50%;
		animation: dot-pulse 2s ease-in-out infinite;
		flex-shrink: 0;
	}

	@keyframes dot-pulse {
		0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.3); }
		50% { opacity: 0.8; box-shadow: 0 0 0 4px rgba(34, 197, 94, 0); }
	}

	.hero-headline {
		font-family: 'DM Sans', -apple-system, sans-serif;
		font-size: clamp(3rem, 8vw, 5.5rem);
		font-weight: 800;
		line-height: 1.05;
		letter-spacing: -0.03em;
		color: #fafafa;
		margin-bottom: 1.5rem;
	}

	.headline-accent {
		color: #fafafa;
		-webkit-text-fill-color: #fafafa;
	}

	.hero-sub {
		font-size: clamp(1rem, 2.5vw, 1.15rem);
		color: #71717a;
		line-height: 1.65;
		margin-bottom: 2.5rem;
		max-width: 560px;
		margin-left: auto;
		margin-right: auto;
	}

	.hero-actions {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1rem;
		margin-bottom: 3.5rem;
		flex-wrap: wrap;
	}

	.btn-primary {
		display: inline-flex;
		align-items: center;
		gap: 8px;
		padding: 13px 28px;
		background: #fafafa;
		border-radius: 10px;
		font-size: 15px;
		font-weight: 600;
		color: #09090b;
		text-decoration: none;
		transition: transform 0.15s, box-shadow 0.15s;
		box-shadow: 0 0 20px rgba(250, 250, 250, 0.15), 0 0 60px rgba(250, 250, 250, 0.05);
	}

	.btn-primary:hover {
		transform: translateY(-1px);
		box-shadow: 0 0 28px rgba(250, 250, 250, 0.25), 0 0 80px rgba(250, 250, 250, 0.08);
	}

	.btn-ghost {
		display: inline-flex;
		align-items: center;
		gap: 8px;
		padding: 12px 24px;
		border: 1px solid #3f3f46;
		border-radius: 10px;
		font-size: 15px;
		font-weight: 500;
		color: #a1a1aa;
		text-decoration: none;
		transition: border-color 0.2s, color 0.2s;
	}

	.btn-ghost:hover {
		border-color: #52525b;
		color: #fafafa;
	}

	/* Social proof strip */
	.hero-proof {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 2rem;
	}

	.proof-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 2px;
	}

	.proof-num {
		font-family: 'DM Sans', sans-serif;
		font-size: 1.5rem;
		font-weight: 700;
		color: #fafafa;
		letter-spacing: -0.03em;
	}

	.proof-label {
		font-size: 11px;
		color: #52525b;
		text-transform: uppercase;
		letter-spacing: 0.06em;
	}

	.proof-divider {
		width: 1px;
		height: 32px;
		background: #27272a;
	}

	/* ── Features ───────────────────────────────────────────────── */
	.features-section {
		padding: 7rem 0;
		border-top: 1px solid #27272a;
	}

	.section-container {
		max-width: 1100px;
		margin: 0 auto;
		padding: 0 1.5rem;
	}

	.section-header {
		text-align: center;
		margin-bottom: 4rem;
	}

	.section-eyebrow {
		font-family: 'JetBrains Mono', monospace;
		font-size: 11px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.12em;
		color: #71717a;
		margin-bottom: 1rem;
	}

	.section-title {
		font-family: 'DM Sans', sans-serif;
		font-size: clamp(2rem, 5vw, 3.2rem);
		font-weight: 700;
		line-height: 1.1;
		letter-spacing: -0.03em;
		color: #fafafa;
		margin-bottom: 1rem;
	}

	.section-desc {
		font-size: 15px;
		color: #71717a;
		max-width: 440px;
		margin: 0 auto;
		line-height: 1.65;
	}

	.features-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 1px;
		background: #27272a;
		border: 1px solid #27272a;
		border-radius: 16px;
		overflow: hidden;
	}

	.feature-card {
		background: #18181b;
		padding: 2.5rem;
		position: relative;
		transition: background 0.2s;
		animation-delay: var(--card-delay, 0ms);
	}

	.feature-card::after {
		content: '';
		position: absolute;
		inset: 0;
		background: radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.02) 0%, transparent 60%);
		opacity: 0;
		transition: opacity 0.3s;
	}

	.feature-card:hover {
		background: #1c1c20;
	}

	.feature-card:hover::after {
		opacity: 1;
	}

	.feature-icon {
		width: 48px;
		height: 48px;
		border: 1px solid #3f3f46;
		border-radius: 12px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: #27272a;
		margin-bottom: 1.5rem;
	}

	.feature-title {
		font-family: 'DM Sans', sans-serif;
		font-size: 1.05rem;
		font-weight: 600;
		color: #fafafa;
		margin-bottom: 0.75rem;
		letter-spacing: -0.01em;
	}

	.feature-desc {
		font-size: 14px;
		color: #71717a;
		line-height: 1.65;
		margin-bottom: 1.5rem;
	}

	.feature-tag {
		font-family: 'JetBrains Mono', monospace;
		font-size: 10px;
		font-weight: 600;
		letter-spacing: 0.08em;
		color: #a1a1aa;
		background: #27272a;
		border: 1px solid #3f3f46;
		border-radius: 4px;
		padding: 3px 8px;
		display: inline-block;
	}

	/* ── Live Signals ───────────────────────────────────────────── */
	.signals-section {
		padding: 7rem 0;
		border-top: 1px solid #27272a;
	}

	.signals-list {
		background: #18181b;
		border: 1px solid #27272a;
		border-radius: 16px;
		overflow: hidden;
	}

	.signals-header-row {
		display: grid;
		grid-template-columns: 100px 1fr 120px 160px;
		padding: 12px 24px;
		border-bottom: 1px solid #27272a;
		font-family: 'JetBrains Mono', monospace;
		font-size: 10px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: #52525b;
	}

	.signal-item {
		display: grid;
		grid-template-columns: 100px 1fr 120px 160px;
		padding: 16px 24px;
		border-bottom: 1px solid rgba(39, 39, 42, 0.6);
		align-items: center;
		transition: background 0.15s;
	}

	.signal-item:last-of-type {
		border-bottom: none;
	}

	.signal-item:hover {
		background: #1c1c20;
	}

	.sig-ticker {
		font-family: 'JetBrains Mono', monospace;
		font-size: 14px;
		font-weight: 700;
		color: #fafafa;
		letter-spacing: 0.04em;
	}

	.sig-company {
		font-size: 13px;
		color: #71717a;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		padding-right: 1rem;
	}

	.direction-badge {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		padding: 4px 10px;
		border-radius: 6px;
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.03em;
	}

	.direction-badge.bullish {
		background: rgba(34, 197, 94, 0.1);
		color: #22c55e;
		border: 1px solid rgba(34, 197, 94, 0.2);
	}

	.badge-arrow {
		font-size: 13px;
	}

	.sig-score-cell {
		display: flex;
		align-items: center;
		gap: 10px;
	}

	.score-bar-wrap {
		flex: 1;
		height: 4px;
		background: #27272a;
		border-radius: 999px;
		overflow: hidden;
	}

	.score-bar-fill {
		height: 100%;
		border-radius: 999px;
		transition: width 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94);
	}

	.score-num {
		font-family: 'JetBrains Mono', monospace;
		font-size: 13px;
		font-weight: 700;
		min-width: 32px;
		text-align: right;
	}

	.signals-cta-row {
		padding: 16px 24px;
		border-top: 1px solid #27272a;
	}

	.signals-view-all {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		font-size: 13px;
		font-weight: 500;
		color: #a1a1aa;
		text-decoration: none;
		transition: gap 0.2s, color 0.2s;
	}

	.signals-view-all:hover {
		gap: 10px;
		color: #fafafa;
	}

	.signals-empty {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 4rem;
		gap: 1rem;
		color: #52525b;
		font-size: 14px;
	}

	.empty-pulse {
		width: 40px;
		height: 40px;
		border: 2px solid #3f3f46;
		border-top-color: #a1a1aa;
		border-radius: 50%;
		animation: empty-spin 1s linear infinite;
	}

	@keyframes empty-spin {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}

	/* ── Stats ──────────────────────────────────────────────────── */
	.stats-section {
		padding: 6rem 0;
		border-top: 1px solid #27272a;
	}

	.stats-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 1px;
		background: #27272a;
		border: 1px solid #27272a;
		border-radius: 16px;
		overflow: hidden;
	}

	.stat-item {
		background: #18181b;
		padding: 2.5rem 2rem;
		text-align: center;
	}

	.stat-number {
		font-family: 'DM Sans', sans-serif;
		font-size: 3rem;
		font-weight: 800;
		color: #fafafa;
		letter-spacing: -0.04em;
		line-height: 1;
		margin-bottom: 0.75rem;
		display: flex;
		align-items: baseline;
		justify-content: center;
		gap: 2px;
	}

	.stat-number.stat-text {
		font-size: 2.4rem;
	}

	.stat-counter {
		font-variant-numeric: tabular-nums;
	}

	.stat-plus {
		font-size: 1.8rem;
		color: #71717a;
	}

	.stat-label {
		font-family: 'DM Sans', sans-serif;
		font-size: 14px;
		font-weight: 600;
		color: #a1a1aa;
		margin-bottom: 0.35rem;
	}

	.stat-sub {
		font-size: 12px;
		color: #52525b;
		line-height: 1.5;
	}

	/* ── Footer ─────────────────────────────────────────────────── */
	.landing-footer {
		border-top: 1px solid #27272a;
		padding: 2.5rem 0;
	}

	.footer-inner {
		max-width: 1100px;
		margin: 0 auto;
		padding: 0 1.5rem;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 2rem;
		flex-wrap: wrap;
	}

	.footer-left {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.footer-logo {
		display: flex;
		align-items: center;
		gap: 8px;
		text-decoration: none;
		font-family: 'DM Sans', sans-serif;
		font-weight: 600;
		font-size: 15px;
		color: #a1a1aa;
	}

	.footer-tagline {
		font-size: 12px;
		color: #52525b;
		font-style: italic;
	}

	.footer-links {
		display: flex;
		gap: 1.5rem;
	}

	.footer-links a {
		font-size: 13px;
		color: #52525b;
		text-decoration: none;
		transition: color 0.15s;
	}

	.footer-links a:hover {
		color: #a1a1aa;
	}

	.footer-copy {
		font-size: 12px;
		color: #3f3f46;
	}

	/* ── Fade-in animation ──────────────────────────────────────── */
	.fade-in {
		opacity: 0;
		transform: translateY(28px);
		transition: opacity 0.7s ease, transform 0.7s ease;
	}

	.fade-in.visible {
		opacity: 1;
		transform: translateY(0);
	}

	/* ── Mobile ─────────────────────────────────────────────────── */
	@media (max-width: 768px) {
		.landing-nav {
			padding: 0 1rem;
		}

		.logo-text {
			display: none;
		}

		.hero-proof {
			gap: 1.25rem;
		}

		.proof-num {
			font-size: 1.2rem;
		}

		.features-grid {
			grid-template-columns: 1fr;
		}

		.feature-card {
			padding: 1.75rem;
		}

		.signals-header-row,
		.signal-item {
			grid-template-columns: 80px 1fr 130px;
		}

		.hide-mobile {
			display: none;
		}

		.stats-grid {
			grid-template-columns: repeat(2, 1fr);
		}

		.stat-item {
			padding: 2rem 1.5rem;
		}

		.stat-number {
			font-size: 2.4rem;
		}

		.footer-inner {
			flex-direction: column;
			text-align: center;
			gap: 1.25rem;
		}

		.footer-links {
			justify-content: center;
			flex-wrap: wrap;
		}

		.hero-sub br.hide-mobile {
			display: none;
		}
	}

	@media (max-width: 480px) {
		.stats-grid {
			grid-template-columns: 1fr;
		}

		.signals-header-row,
		.signal-item {
			grid-template-columns: 70px 1fr 110px;
		}
	}
</style>
