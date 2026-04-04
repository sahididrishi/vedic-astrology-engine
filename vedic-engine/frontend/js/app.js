/* ═══════════════════════════════════════════════════════════════
   APP.JS — Navigation, form handling, API calls, oracle sequence
   ═══════════════════════════════════════════════════════════════ */

let currentStep = 1;
const totalSteps = 3;

// ─── Section Navigation ───
function goToSection(id) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('section--active'));
  const target = document.getElementById(id);
  if (target) {
    target.classList.add('section--active');
    if (id === 'loading') startOracle();
  }
}

// ─── Form Step Navigation ───
function nextStep() {
  if (!validateStep(currentStep)) return;
  if (currentStep < totalSteps) {
    currentStep++;
    updateFormStep();
  }
}

function prevStep() {
  if (currentStep > 1) {
    currentStep--;
    updateFormStep();
  }
}

function updateFormStep() {
  // Steps
  document.querySelectorAll('.form-step').forEach(s => s.classList.remove('active'));
  document.querySelector(`.form-step[data-step="${currentStep}"]`).classList.add('active');

  // Progress indicators
  document.querySelectorAll('.progress-step').forEach(s => {
    const step = parseInt(s.dataset.step);
    s.classList.remove('active', 'done');
    if (step === currentStep) s.classList.add('active');
    else if (step < currentStep) s.classList.add('done');
  });

  // Progress lines
  const fills = document.querySelectorAll('.progress-line__fill');
  fills.forEach((fill, i) => {
    fill.style.width = (i < currentStep - 1) ? '100%' : '0%';
  });
}

function validateStep(step) {
  if (step === 1) {
    const name = document.getElementById('full_name');
    if (!name.value.trim()) {
      name.focus();
      shakeField(name);
      return false;
    }
  }
  if (step === 2) {
    const date = document.getElementById('birth_date');
    const time = document.getElementById('birth_time');
    if (!date.value) { date.focus(); shakeField(date); return false; }
    if (!time.value) { time.focus(); shakeField(time); return false; }
  }
  return true;
}

function shakeField(el) {
  el.style.animation = 'none';
  el.offsetHeight; // reflow
  el.style.animation = 'shake 0.4s ease';
  el.style.borderColor = '#e74c3c';
  setTimeout(() => { el.style.borderColor = ''; el.style.animation = ''; }, 800);
}

// Add shake keyframes
const shakeStyle = document.createElement('style');
shakeStyle.textContent = `@keyframes shake { 0%,100%{transform:translateX(0)} 25%{transform:translateX(-8px)} 75%{transform:translateX(8px)} }`;
document.head.appendChild(shakeStyle);

// ─── Focus Cards ───
document.querySelectorAll('.focus-card').forEach(card => {
  card.addEventListener('click', () => {
    document.querySelectorAll('.focus-card').forEach(c => c.classList.remove('active'));
    card.classList.add('active');
  });
});

// ─── Form Submit ───
document.getElementById('readingForm').addEventListener('submit', async function(e) {
  e.preventDefault();
  if (!validateStep(3)) return;

  const city = document.getElementById('birth_city');
  const country = document.getElementById('birth_country');
  if (!city.value.trim()) { city.focus(); shakeField(city); return; }
  if (!country.value.trim()) { country.focus(); shakeField(country); return; }

  // Build payload
  const fd = new FormData(e.target);
  const payload = {};
  fd.forEach((v, k) => { if (v) payload[k] = v; });

  // Switch to loading
  goToSection('loading');

  // Make API call
  try {
    const apiUrl = document.getElementById('cfgUrl').value || 'http://localhost:8000';
    const apiKey = document.getElementById('cfgKey').value;

    const headers = { 'Content-Type': 'application/json' };
    if (apiKey) headers['Authorization'] = `Bearer ${apiKey}`;

    const resp = await fetch(`${apiUrl}/api/v1/reading`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });

    if (!resp.ok) {
      const errData = await resp.json().catch(() => ({}));
      throw new Error(errData.detail?.message || errData.detail || `API error ${resp.status}`);
    }

    const data = await resp.json();
    window._readingData = data;
    window._chartData = payload;

    // Let the oracle animation finish naturally
    awaitingData = data;
  } catch (err) {
    oracleError = err.message;
  }
});

// ─── Oracle Sequence ───
let awaitingData = null;
let oracleError = null;

const ORACLE_STEPS = [
  { text: 'Mapping celestial positions...', sanskrit: 'ग्रह स्थिति', duration: 2000 },
  { text: 'Calculating planetary strengths...', sanskrit: 'ग्रह बल', duration: 2500 },
  { text: 'Detecting yoga combinations...', sanskrit: 'योग विश्लेषण', duration: 2500 },
  { text: 'Checking dosha alignments...', sanskrit: 'दोष परीक्षा', duration: 2000 },
  { text: 'Interpreting Vimshottari Dasha...', sanskrit: 'दशा फल', duration: 2500 },
  { text: 'Consulting the stars...', sanskrit: 'ज्योतिष', duration: 3000 },
];

function startOracle() {
  awaitingData = null;
  oracleError = null;

  // Start mandala animation
  document.querySelectorAll('.mandala-ring, .mandala-tri, .mandala-bindu').forEach(el => {
    el.classList.remove('animating');
    void el.offsetHeight;
    el.classList.add('animating');
  });

  const stepEl = document.getElementById('oracleStep');
  const progressEl = document.getElementById('oracleProgress');
  let stepIndex = 0;
  let totalDuration = ORACLE_STEPS.reduce((a, s) => a + s.duration, 0);
  let elapsed = 0;

  function runStep() {
    if (stepIndex >= ORACLE_STEPS.length) {
      // All steps done — check for data
      const waitForData = setInterval(() => {
        if (awaitingData) {
          clearInterval(waitForData);
          renderReading(awaitingData);
          goToSection('reading');
          // Animate planet meters after section is visible
          setTimeout(animatePlanetMeters, 300);
        } else if (oracleError) {
          clearInterval(waitForData);
          document.getElementById('errorMessage').textContent = oracleError;
          goToSection('error');
        }
      }, 200);
      return;
    }

    const step = ORACLE_STEPS[stepIndex];
    stepEl.style.opacity = 0;
    setTimeout(() => {
      stepEl.innerHTML = `${step.text} <span style="display:block;font-size:0.75rem;color:var(--gold);opacity:0.5;margin-top:4px;font-style:normal">${step.sanskrit}</span>`;
      stepEl.style.opacity = 1;
    }, 300);

    elapsed += step.duration;
    progressEl.style.width = `${(elapsed / totalDuration) * 100}%`;

    stepIndex++;
    setTimeout(runStep, step.duration);
  }

  runStep();
}

function animatePlanetMeters() {
  document.querySelectorAll('.planet-meter__fill').forEach(bar => {
    const target = bar.dataset.score;
    requestAnimationFrame(() => { bar.style.width = `${target * 10}%`; });
  });
}

// ─── Config Toggle ───
function toggleConfig() {
  document.getElementById('configPanel').classList.toggle('open');
}
