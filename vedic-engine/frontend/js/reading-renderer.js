/* ═══════════════════════════════════════════════════════════════
   READING-RENDERER.JS — Transforms API JSON into reading cards
   ═══════════════════════════════════════════════════════════════ */

const PLANET_COLORS = {
  Sun: 'var(--planet-sun)', Moon: 'var(--planet-moon)', Mars: 'var(--planet-mars)',
  Mercury: 'var(--planet-mercury)', Jupiter: 'var(--planet-jupiter)',
  Venus: 'var(--planet-venus)', Saturn: 'var(--planet-saturn)',
  Rahu: 'var(--planet-rahu)', Ketu: 'var(--planet-ketu)',
};

const PLANET_SYMBOLS = {
  Sun: '☉', Moon: '☽', Mars: '♂', Mercury: '☿', Jupiter: '♃',
  Venus: '♀', Saturn: '♄', Rahu: '☊', Ketu: '☋',
};

function esc(s) {
  if (!s) return '';
  const d = document.createElement('div');
  d.appendChild(document.createTextNode(String(s)));
  return d.innerHTML;
}

function renderReading(data) {
  const container = document.getElementById('readingContent');
  const chart = data.chart_summary || {};

  let html = '';

  // ═══ HEADER CARD ═══
  html += `
    <div class="r-card r-header">
      <div class="r-card__label">Reading Complete</div>
      <h1 class="r-header__name">${esc(data.subject_name)}</h1>
      <div class="r-header__meta">
        ${chart.ascendant ? `<div class="r-meta-item"><span class="r-meta-item__label">Ascendant (लग्न)</span><span class="r-meta-item__value">${esc(chart.ascendant)}</span></div>` : ''}
        ${chart.moon_sign ? `<div class="r-meta-item"><span class="r-meta-item__label">Moon Sign (राशि)</span><span class="r-meta-item__value">${esc(chart.moon_sign)}</span></div>` : ''}
        ${chart.sun_sign ? `<div class="r-meta-item"><span class="r-meta-item__label">Sun Sign (सूर्य)</span><span class="r-meta-item__value">${esc(chart.sun_sign)}</span></div>` : ''}
        ${chart.yoga_count != null ? `<div class="r-meta-item"><span class="r-meta-item__label">Yogas Found</span><span class="r-meta-item__value">${chart.yoga_count}</span></div>` : ''}
      </div>
      ${data.overview ? `<p class="r-overview">${esc(data.overview)}</p>` : ''}
    </div>
  `;

  // ═══ PLANETARY STRENGTHS ═══
  if (data.chart_summary?.planetary_strengths) {
    html += renderPlanets(data.chart_summary.planetary_strengths);
  }

  // ═══ YOGAS ═══
  if (data.chart_summary?.yogas && data.chart_summary.yogas.length > 0) {
    html += renderYogas(data.chart_summary.yogas);
  }

  // ═══ DOSHAS ═══
  if (data.chart_summary?.doshas && data.chart_summary.doshas.length > 0) {
    html += renderDoshas(data.chart_summary.doshas);
  }

  // ═══ DASHA ═══
  if (data.chart_summary?.dasha) {
    html += renderDasha(data.chart_summary.dasha);
  }

  // ═══ AI READING SECTIONS ═══
  if (data.sections && data.sections.length > 0) {
    html += `<div class="r-card">
      <div class="r-card__label">Detailed Analysis</div>
      <h2 class="r-card__title">Your Reading</h2>
      ${data.sections.map(s => `
        <div class="r-section">
          <h3 class="r-section__title">${esc(s.title)}</h3>
          <p class="r-section__insight">${esc(s.insight)}</p>
          ${s.actions && s.actions.length ? `
            <ul class="r-section__actions">
              ${s.actions.map(a => `<li>${esc(a)}</li>`).join('')}
            </ul>
          ` : ''}
        </div>
      `).join('')}
    </div>`;
  }

  // ═══ KEY PERIODS ═══
  if (data.key_periods && data.key_periods.length > 0) {
    html += `
      <div class="r-card">
        <div class="r-card__label">Key Periods (काल)</div>
        <h2 class="r-card__title">Periods Ahead</h2>
        <div class="key-periods__list">
          ${data.key_periods.map(kp => `
            <div class="kp-item">
              <span class="kp-item__period">${esc(kp.period)}</span>
              <span class="kp-item__theme">${esc(kp.theme)}</span>
              <span class="kp-item__guidance">${esc(kp.guidance)}</span>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  // ═══ CLOSING ═══
  if (data.closing) {
    html += `<div class="r-closing">${esc(data.closing)}</div>`;
  }

  // ═══ FOOTER ═══
  html += `
    <div class="r-footer">
      <button class="btn btn--ghost" onclick="goToSection('form')">New Reading</button>
      <button class="btn btn--ghost" onclick="downloadReading()">Download JSON</button>
    </div>
  `;

  if (data.processing_time_ms) {
    html += `<div class="r-meta-footer">Generated in ${data.processing_time_ms}ms &middot; Reading ID: ${esc(data.reading_id) || '—'}</div>`;
  }

  container.innerHTML = html;
}

// ─── Planet Strength Meters ───
function renderPlanets(strengths) {
  const entries = Object.entries(strengths);
  if (!entries.length) return '';

  const meters = entries.map(([name, data]) => {
    const score = data.score != null ? data.score : 5;
    const color = PLANET_COLORS[name] || 'var(--text-dim)';
    const symbol = PLANET_SYMBOLS[name] || '●';
    const dignity = data.dignity || 'neutral';

    return `
      <div class="planet-meter">
        <div class="planet-meter__dot" style="background:${color}"></div>
        <div class="planet-meter__info">
          <div class="planet-meter__name">
            <span>${symbol} ${esc(name)}</span>
            <span class="planet-meter__score">${score}/10 · ${dignity}</span>
          </div>
          <div class="planet-meter__bar">
            <div class="planet-meter__fill" data-score="${score}" style="background:${color}"></div>
          </div>
        </div>
      </div>
    `;
  }).join('');

  return `
    <div class="r-card">
      <div class="r-card__label">Planetary Strength (ग्रह बल)</div>
      <h2 class="r-card__title">Graha Positions</h2>
      <div class="r-planets__grid">${meters}</div>
    </div>
  `;
}

// ─── Yoga Cards ───
function renderYogas(yogas) {
  const items = yogas.map(y => {
    const strength = y.strength || 'moderate';
    const areas = (y.life_area_impact || []).map(a => `<span class="area-tag">${esc(a)}</span>`).join('');

    return `
      <div class="yoga-item yoga-item--${strength}">
        <div>
          <span class="yoga-badge yoga-badge--${strength}">${strength}</span>
        </div>
        <div>
          <div class="yoga-item__name">${esc(y.name)}</div>
          <div class="yoga-item__desc">${esc(y.description)}</div>
          ${areas ? `<div class="yoga-item__areas">${areas}</div>` : ''}
        </div>
      </div>
    `;
  }).join('');

  return `
    <div class="r-card">
      <div class="r-card__label">Yogas Detected (योग)</div>
      <h2 class="r-card__title">Planetary Combinations</h2>
      <div class="r-yogas__list">${items}</div>
    </div>
  `;
}

// ─── Dosha Cards ───
function renderDoshas(doshas) {
  const items = doshas.map(d => {
    const severity = d.severity || 'moderate';
    return `
      <div class="dosha-item">
        <div class="dosha-severity dosha-severity--${severity}"></div>
        <div>
          <div class="dosha-item__name">${esc(d.name)} <span style="font-size:0.75rem;color:var(--text-muted);font-weight:400">(${severity})</span></div>
          <div class="dosha-item__desc">${esc(d.description)}</div>
        </div>
      </div>
    `;
  }).join('');

  return `
    <div class="r-card">
      <div class="r-card__label">Doshas Active (दोष)</div>
      <h2 class="r-card__title">Afflictions & Remediation</h2>
      ${items}
    </div>
  `;
}

// ─── Dasha Timeline ───
function renderDasha(dasha) {
  if (!dasha.current_mahadasha) return '';

  const md = dasha.current_mahadasha;
  const ad = dasha.current_antardasha;
  const narrative = dasha.mahadasha_narrative || '';

  return `
    <div class="r-card">
      <div class="r-card__label">Current Dasha (दशा)</div>
      <h2 class="r-card__title">Planetary Period</h2>
      <div class="dasha-current">
        <div class="dasha-period">
          <div class="dasha-period__type">Mahadasha</div>
          <div class="dasha-period__lord">${PLANET_SYMBOLS[md.lord] || ''} ${esc(md.lord)}</div>
        </div>
        ${ad ? `
          <div class="dasha-period">
            <div class="dasha-period__type">Antardasha</div>
            <div class="dasha-period__lord">${PLANET_SYMBOLS[ad.lord] || ''} ${esc(ad.lord)}</div>
          </div>
        ` : ''}
      </div>
      ${narrative ? `<p class="dasha-narrative">${esc(narrative)}</p>` : ''}
    </div>
  `;
}

// ─── Download ───
function downloadReading() {
  if (!window._readingData) return;
  const blob = new Blob([JSON.stringify(window._readingData, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `reading-${window._readingData.reading_id || 'export'}.json`;
  a.click();
  URL.revokeObjectURL(url);
}
