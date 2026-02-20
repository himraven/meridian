#!/usr/bin/env node
/**
 * Meridian × 小红书 Card Generator
 * 
 * Generates beautiful 1080×1440 card images from Meridian data.
 * Uses Playwright to render HTML templates and screenshot them.
 * 
 * Usage:
 *   node generate.js top-signals          # Top conviction signals card
 *   node generate.js congress-trades      # This week's congress trades
 *   node generate.js knowledge <slug>     # Knowledge article card
 *   node generate.js confluence <ticker>  # Single ticker confluence card
 *   node generate.js weekly-recap         # Weekly recap summary card
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const http = require('http');

const TEMPLATES_DIR = path.join(__dirname, 'templates');
const OUTPUT_DIR = path.join(__dirname, 'output');
const DATA_DIR = process.env.DATA_DIR || '/home/raven/smart-money-platform/data';
const CONTENT_DIR = '/home/raven/meridian/content/knowledge';

// ── Helpers ──────────────────────────────────────────────────────────

function loadJSON(filename) {
  const filepath = path.join(DATA_DIR, filename);
  if (!fs.existsSync(filepath)) return {};
  return JSON.parse(fs.readFileSync(filepath, 'utf-8'));
}

function loadTemplate() {
  return fs.readFileSync(path.join(TEMPLATES_DIR, 'base.html'), 'utf-8');
}

function scoreColor(score) {
  if (score >= 70) return 'var(--green)';
  if (score >= 40) return 'var(--amber)';
  return 'var(--text-muted)';
}

const SOURCE_LABELS = {
  congress: 'GOV', ark: 'ARK', darkpool: 'DP',
  insider: 'INS', institution: '13F', 
  superinvestor: 'SUP', short_interest: 'SI'
};

function sourcePills(sources) {
  return sources.map(s => 
    `<span class="source-pill source-${s}">${SOURCE_LABELS[s] || s.toUpperCase()}</span>`
  ).join('');
}

function today() {
  return new Date().toISOString().slice(0, 10);
}

// ── Card Generators ──────────────────────────────────────────────────

function generateTopSignals() {
  const ranking = loadJSON('ranking_v3.json') || loadJSON('ranking_v2.json');
  const signals = (ranking.signals || [])
    .filter(s => s.score >= 50)
    .sort((a, b) => b.score - a.score)
    .slice(0, 5);

  const rows = signals.map((s, i) => `
    <div class="signal-row">
      <span class="signal-rank">${i + 1}</span>
      <span class="signal-ticker">${s.ticker}</span>
      <span class="signal-score" style="color: ${scoreColor(s.score)}">${Math.round(s.score)}</span>
      <div class="signal-sources">${sourcePills(s.sources || [])}</div>
      <span class="signal-direction ${s.direction === 'bullish' ? 'dir-bullish' : 'dir-bearish'}">
        ${s.direction === 'bullish' ? '↑ BULL' : '↓ BEAR'}
      </span>
    </div>
  `).join('');

  const topScore = signals[0]?.score || 0;
  const topTicker = signals[0]?.ticker || '—';

  return `
    <div class="header">
      <div class="brand">
        <div class="brand-icon">M</div>
        <span class="brand-name">Meridian</span>
      </div>
      <span class="date-badge">${today()}</span>
    </div>

    <div class="title-section">
      <div class="category-tag">🔥 Smart Money Signals</div>
      <div class="title">Top Conviction<br>Signals Today</div>
      <div class="subtitle">Where institutional, congressional, and insider money converges</div>
    </div>

    <div class="hero-stat">
      <span class="hero-value">${Math.round(topScore)}</span>
      <span class="hero-label">${topTicker} conviction score — ${signals[0]?.sources?.length || 0} smart money sources aligned</span>
    </div>

    <div class="signal-list">
      ${rows}
    </div>

    <div class="footer">
      <span class="footer-left">Data: SEC EDGAR · FINRA · Public filings</span>
      <span class="footer-right"><span class="footer-url">meridianfin.io</span></span>
    </div>
  `;
}

function generateCongressTrades() {
  const data = loadJSON('congress.json');
  const trades = (data.trades || [])
    .sort((a, b) => (b.transaction_date || '').localeCompare(a.transaction_date || ''))
    .slice(0, 6);

  const rows = trades.map(t => {
    const isBuy = (t.type || '').toLowerCase().includes('purchase') || (t.type || '').toLowerCase().includes('buy');
    const party = (t.party || '').toUpperCase();
    return `
      <div class="trade-row">
        <span class="trade-party ${party === 'R' ? 'party-r' : 'party-d'}">${party}</span>
        <span class="trade-member">${(t.representative || t.member || 'Unknown').split(' ').slice(0,3).join(' ')}</span>
        <span class="trade-ticker">${t.ticker || '?'}</span>
        <span class="trade-amount" style="color: ${isBuy ? 'var(--green)' : 'var(--red)'}">
          ${isBuy ? '买入' : '卖出'} ${t.amount || ''}
        </span>
      </div>
    `;
  }).join('');

  const buyCount = trades.filter(t => (t.type||'').toLowerCase().includes('purchase')).length;

  return `
    <div class="header">
      <div class="brand">
        <div class="brand-icon">M</div>
        <span class="brand-name">Meridian</span>
      </div>
      <span class="date-badge">${today()}</span>
    </div>

    <div class="title-section">
      <div class="category-tag">🏛️ Congressional Trading</div>
      <div class="title">国会议员<br>最新交易</div>
      <div class="subtitle">What are U.S. Congress members buying and selling?</div>
    </div>

    <div class="hero-stat">
      <span class="hero-value">${trades.length}</span>
      <span class="hero-label">recent trades tracked — ${buyCount} buys, ${trades.length - buyCount} sells</span>
    </div>

    <div style="flex:1; display:flex; flex-direction:column; gap:0;">
      ${rows}
    </div>

    <div class="footer">
      <span class="footer-left">Source: House/Senate STOCK Act Disclosures</span>
      <span class="footer-right"><span class="footer-url">meridianfin.io</span></span>
    </div>
  `;
}

function generateKnowledgeCard(slug) {
  const filepath = path.join(CONTENT_DIR, `${slug}.json`);
  if (!fs.existsSync(filepath)) {
    console.error(`Article not found: ${slug}`);
    process.exit(1);
  }
  const article = JSON.parse(fs.readFileSync(filepath, 'utf-8'));
  
  const takeaways = (article.key_takeaways || []).slice(0, 4).map(t => `
    <div class="takeaway-item">
      <span class="takeaway-icon">→</span>
      <span class="takeaway-text">${t}</span>
    </div>
  `).join('');

  const layerLabel = { L1: 'SIGNAL GUIDE', L2: 'DEEP DIVE', L3: 'EXPERT INSIGHT', recurring: 'WEEKLY RECAP' };
  const layerColor = { L1: 'var(--green)', L2: 'var(--blue)', L3: 'var(--purple)', recurring: 'var(--amber)' };
  const layer = article.layer || 'L1';

  return `
    <div class="header">
      <div class="brand">
        <div class="brand-icon">M</div>
        <span class="brand-name">Meridian</span>
      </div>
      <span class="date-badge">${article.updated_at || today()}</span>
    </div>

    <div class="title-section knowledge-card">
      <div class="category-tag" style="color: ${layerColor[layer]}">${layerLabel[layer] || 'KNOWLEDGE'}</div>
      <div class="title">${article.title}</div>
      <div class="subtitle">${article.subtitle || ''}</div>
    </div>

    ${article.hero_stat ? `
    <div class="hero-stat">
      <span class="hero-value" style="font-size: 56px">${article.hero_stat.value}</span>
      <span class="hero-label">${article.hero_stat.label}</span>
    </div>
    ` : ''}

    <div class="takeaway-list" style="flex:1;">
      ${takeaways}
    </div>

    ${article.content_zh ? `
    <div style="padding: 20px 24px; background: var(--bg-surface); border: 1px solid var(--border); border-radius: 12px; margin-bottom: 20px;">
      <span class="mono dimmed" style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.1em;">TL;DR</span>
      <p style="font-size: 16px; color: var(--text-secondary); line-height: 1.6; margin-top: 8px;">${article.content_zh}</p>
    </div>
    ` : ''}

    <div class="footer">
      <span class="footer-left">📖 Read full article on meridianfin.io</span>
      <span class="footer-right"><span class="footer-url">meridianfin.io/knowledge/${slug}</span></span>
    </div>
  `;
}

function generateConfluenceCard(ticker) {
  // Fetch from API
  return new Promise((resolve, reject) => {
    http.get(`http://localhost:8502/api/ticker/${ticker}`, (res) => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => {
        try {
          const d = JSON.parse(data);
          const c = d.confluence || {};
          const sources = c.sources || [];
          const score = c.score || 0;
          const direction = c.direction || 'neutral';

          const scoreRows = [
            { label: 'Congress', key: 'congress_score', color: 'var(--congress)' },
            { label: 'ARK', key: 'ark_score', color: 'var(--ark)' },
            { label: 'Dark Pool', key: 'darkpool_score', color: 'var(--darkpool)' },
            { label: 'Insider', key: 'insider_score', color: 'var(--insider)' },
            { label: '13F', key: 'institution_score', color: 'var(--institution)' },
            { label: 'Superinvestor', key: 'superinvestor_score', color: 'var(--superinvestor)' },
            { label: 'Short Interest', key: 'short_interest_score', color: 'var(--short)' },
          ].filter(r => (c[r.key] || 0) > 0);

          const bars = scoreRows.map(r => {
            const val = c[r.key] || 0;
            return `
              <div style="display:flex; align-items:center; gap:16px; margin-bottom:14px;">
                <span style="width:140px; font-size:15px; color:var(--text-secondary);">${r.label}</span>
                <div class="score-bar-bg" style="flex:1; height:8px;">
                  <div class="score-bar-fill" style="width:${val}%; background:${r.color};"></div>
                </div>
                <span class="mono" style="font-size:16px; font-weight:600; color:${r.color}; width:40px; text-align:right;">${Math.round(val)}</span>
              </div>
            `;
          }).join('');

          resolve(`
            <div class="header">
              <div class="brand">
                <div class="brand-icon">M</div>
                <span class="brand-name">Meridian</span>
              </div>
              <span class="date-badge">${today()}</span>
            </div>

            <div class="title-section">
              <div class="category-tag">📊 Signal Confluence</div>
              <div class="title" style="font-size:64px;">${ticker}</div>
              <div class="subtitle">${d.company || ''} — Smart Money Signal Breakdown</div>
            </div>

            <div class="hero-stat">
              <span class="hero-value" style="color:${direction === 'bullish' ? 'var(--green)' : direction === 'bearish' ? 'var(--red)' : 'var(--text-muted)'}">${Math.round(score)}</span>
              <span class="hero-label">Conviction score from ${sources.length} source${sources.length > 1 ? 's' : ''} — ${direction.toUpperCase()}</span>
            </div>

            <div style="flex:1; display:flex; flex-direction:column; justify-content:center; padding: 20px 0;">
              ${bars}
            </div>

            <div style="display:flex; gap:10px; flex-wrap:wrap; margin-bottom:24px;">
              ${sourcePills(sources)}
            </div>

            <div class="footer">
              <span class="footer-left">Conviction scored by Meridian V7 Engine</span>
              <span class="footer-right"><span class="footer-url">meridianfin.io/ticker/${ticker}</span></span>
            </div>
          `);
        } catch(e) { reject(e); }
      });
    }).on('error', reject);
  });
}

// ── Main ─────────────────────────────────────────────────────────────

async function main() {
  const [,, cardType, ...args] = process.argv;

  if (!cardType) {
    console.log('Usage: node generate.js <type> [args]');
    console.log('Types: top-signals | congress-trades | knowledge <slug> | confluence <TICKER> | weekly-recap');
    process.exit(1);
  }

  let content;
  let filename;

  switch (cardType) {
    case 'top-signals':
      content = generateTopSignals();
      filename = `top-signals-${today()}`;
      break;
    case 'congress-trades':
      content = generateCongressTrades();
      filename = `congress-trades-${today()}`;
      break;
    case 'knowledge':
      content = generateKnowledgeCard(args[0]);
      filename = `knowledge-${args[0]}`;
      break;
    case 'confluence':
      content = await generateConfluenceCard(args[0]?.toUpperCase());
      filename = `confluence-${args[0]?.toUpperCase()}-${today()}`;
      break;
    default:
      console.error(`Unknown type: ${cardType}`);
      process.exit(1);
  }

  // Render
  const template = loadTemplate();
  const html = template.replace('{{CONTENT}}', content);

  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1440 } });
  await page.setContent(html, { waitUntil: 'networkidle' });
  
  // Wait for fonts
  await page.waitForTimeout(1500);

  const outputPath = path.join(OUTPUT_DIR, `${filename}.png`);
  await page.screenshot({ path: outputPath, type: 'png' });
  await browser.close();

  const size = fs.statSync(outputPath).size;
  console.log(`✅ ${outputPath} (${(size/1024).toFixed(0)}KB)`);
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
