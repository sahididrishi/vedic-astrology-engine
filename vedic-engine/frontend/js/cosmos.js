/* ═══ COSMOS — Ambient celestial canvas ═══
   Subtle, natural, performance-first.
   Stars breathe. Faint nebula drifts. Occasional comet. Nothing showy. */

(function() {
  const c = document.getElementById('cosmosCanvas');
  if (!c) return;
  const gl = c.getContext('2d');
  let W, H, dpr, id;

  function size() {
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = window.innerWidth;
    H = window.innerHeight;
    c.width = W * dpr;
    c.height = H * dpr;
    c.style.width = W + 'px';
    c.style.height = H + 'px';
    gl.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  window.addEventListener('resize', size);
  size();

  // Stars: natural distribution — denser near center, sparser at edges (Gaussian)
  const N = Math.min(300, Math.floor((W * H) / 5000));
  const stars = [];
  for (let i = 0; i < N; i++) {
    // Box-Muller for Gaussian-ish distribution
    const u1 = Math.random(), u2 = Math.random();
    const mag = Math.sqrt(-2 * Math.log(u1 + 0.001));
    const gx = mag * Math.cos(2 * Math.PI * u2);
    const gy = mag * Math.sin(2 * Math.PI * u2);

    const r = Math.random();
    stars.push({
      x: W / 2 + gx * W * 0.28,
      y: H / 2 + gy * H * 0.28,
      r: 0.4 + Math.pow(Math.random(), 3) * 1.8, // power curve = mostly tiny, few big
      phase: Math.random() * Math.PI * 2,
      speed: 0.003 + Math.random() * 0.012,
      max: 0.25 + Math.random() * 0.55,
      cr: r < 0.08 ? 201 : r < 0.14 ? 148 : r < 0.18 ? 220 : 255,
      cg: r < 0.08 ? 162 : r < 0.14 ? 163 : r < 0.18 ? 180 : 255,
      cb: r < 0.08 ? 39  : r < 0.14 ? 210 : r < 0.18 ? 140 : 255,
    });
  }

  // Comets: spawn occasionally
  let comet = null;
  let cometTimer = 5000 + Math.random() * 10000;

  function spawnComet() {
    comet = {
      x: Math.random() * W * 0.6,
      y: Math.random() * H * 0.25,
      vx: 4 + Math.random() * 5,
      vy: 2 + Math.random() * 3,
      life: 1,
      len: 50 + Math.random() * 80,
    };
  }

  // Nebula: two soft blobs that drift
  let t0 = performance.now();

  function draw(now) {
    const dt = now - t0; t0 = now;
    gl.clearRect(0, 0, W, H);
    const sec = now * 0.001;

    // Nebula
    const nx = W * 0.45 + Math.sin(sec * 0.05) * W * 0.08;
    const ny = H * 0.4 + Math.cos(sec * 0.03) * H * 0.06;
    const ns = Math.min(W, H) * 0.5;
    const g1 = gl.createRadialGradient(nx, ny, 0, nx, ny, ns);
    g1.addColorStop(0, 'rgba(100,60,160,0.025)');
    g1.addColorStop(1, 'transparent');
    gl.fillStyle = g1;
    gl.fillRect(0, 0, W, H);

    const n2x = W * 0.6 + Math.cos(sec * 0.04) * W * 0.1;
    const n2y = H * 0.55 + Math.sin(sec * 0.025) * H * 0.07;
    const g2 = gl.createRadialGradient(n2x, n2y, 0, n2x, n2y, ns * 0.5);
    g2.addColorStop(0, 'rgba(201,162,39,0.012)');
    g2.addColorStop(1, 'transparent');
    gl.fillStyle = g2;
    gl.fillRect(0, 0, W, H);

    // Stars
    for (const s of stars) {
      s.phase += s.speed;
      const a = s.max * (0.35 + 0.65 * ((Math.sin(s.phase) + 1) * 0.5));
      const rad = s.r * (0.85 + 0.15 * ((Math.sin(s.phase) + 1) * 0.5));

      if (rad > 1.2) {
        gl.beginPath();
        gl.arc(s.x, s.y, rad * 3.5, 0, Math.PI * 2);
        gl.fillStyle = `rgba(${s.cr},${s.cg},${s.cb},${a * 0.04})`;
        gl.fill();
      }

      gl.beginPath();
      gl.arc(s.x, s.y, rad, 0, Math.PI * 2);
      gl.fillStyle = `rgba(${s.cr},${s.cg},${s.cb},${a})`;
      gl.fill();
    }

    // Comet
    cometTimer -= dt;
    if (cometTimer <= 0 && !comet) {
      spawnComet();
      cometTimer = 8000 + Math.random() * 15000;
    }
    if (comet) {
      comet.x += comet.vx;
      comet.y += comet.vy;
      comet.life -= 0.008;
      if (comet.life <= 0 || comet.x > W + 100 || comet.y > H + 100) {
        comet = null;
      } else {
        const tx = comet.x - (comet.vx / Math.hypot(comet.vx, comet.vy)) * comet.len;
        const ty = comet.y - (comet.vy / Math.hypot(comet.vx, comet.vy)) * comet.len;
        const cg = gl.createLinearGradient(comet.x, comet.y, tx, ty);
        cg.addColorStop(0, `rgba(255,255,255,${comet.life * 0.7})`);
        cg.addColorStop(0.15, `rgba(201,162,39,${comet.life * 0.25})`);
        cg.addColorStop(1, 'transparent');
        gl.beginPath();
        gl.moveTo(comet.x, comet.y);
        gl.lineTo(tx, ty);
        gl.strokeStyle = cg;
        gl.lineWidth = 1;
        gl.stroke();

        gl.beginPath();
        gl.arc(comet.x, comet.y, 1.5, 0, Math.PI * 2);
        gl.fillStyle = `rgba(255,255,255,${comet.life})`;
        gl.fill();
      }
    }

    id = requestAnimationFrame(draw);
  }

  id = requestAnimationFrame(draw);

  document.addEventListener('visibilitychange', () => {
    if (document.hidden) cancelAnimationFrame(id);
    else { t0 = performance.now(); id = requestAnimationFrame(draw); }
  });
})();
