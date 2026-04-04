/* ═══════════════════════════════════════════════════════════════
   COSMOS.JS — Living celestial background
   Orbiting planets, twinkling stars, shooting stars, nebula glow
   ═══════════════════════════════════════════════════════════════ */

(function() {
  const canvas = document.getElementById('cosmosCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  let W, H, cx, cy;
  let animId;
  let mouse = { x: -1000, y: -1000 };

  function resize() {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
    cx = W / 2;
    cy = H / 2;
  }
  window.addEventListener('resize', resize);
  resize();

  // Track mouse for subtle parallax
  document.addEventListener('mousemove', e => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
  });

  // ─── STARS ───
  const STAR_COUNT = Math.min(350, Math.floor(W * H / 4000));

  class Star {
    constructor() { this.reset(true); }
    reset(init) {
      this.x = Math.random() * W;
      this.y = Math.random() * H;
      this.baseRadius = 0.3 + Math.random() * 1.5;
      this.radius = this.baseRadius;
      // Twinkle: each star has its own phase and speed
      this.twinklePhase = Math.random() * Math.PI * 2;
      this.twinkleSpeed = 0.005 + Math.random() * 0.025;
      this.maxAlpha = 0.3 + Math.random() * 0.7;
      this.alpha = init ? Math.random() * this.maxAlpha : 0;
      // Color — mostly white, some warm gold, some cool blue
      const r = Math.random();
      if (r < 0.12) this.color = { r: 210, g: 172, b: 71 };       // gold
      else if (r < 0.2) this.color = { r: 140, g: 160, b: 220 };   // cool blue
      else if (r < 0.25) this.color = { r: 220, g: 140, b: 100 };  // warm orange
      else this.color = { r: 255, g: 255, b: 255 };                 // white
    }
    update(t) {
      this.twinklePhase += this.twinkleSpeed;
      const wave = Math.sin(this.twinklePhase);
      this.alpha = this.maxAlpha * (0.4 + 0.6 * ((wave + 1) / 2));
      this.radius = this.baseRadius * (0.8 + 0.2 * ((wave + 1) / 2));
    }
    draw() {
      const { r, g, b } = this.color;
      // Glow
      if (this.baseRadius > 1.0) {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius * 3, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${r},${g},${b},${this.alpha * 0.08})`;
        ctx.fill();
      }
      // Core
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${r},${g},${b},${this.alpha})`;
      ctx.fill();
    }
  }

  const stars = Array.from({ length: STAR_COUNT }, () => new Star());

  // ─── SHOOTING STARS ───
  class ShootingStar {
    constructor() { this.alive = false; }
    spawn() {
      this.alive = true;
      this.x = Math.random() * W * 0.8;
      this.y = Math.random() * H * 0.4;
      this.angle = Math.PI / 6 + Math.random() * Math.PI / 6; // 30-60 deg
      this.speed = 6 + Math.random() * 8;
      this.length = 60 + Math.random() * 100;
      this.alpha = 1;
      this.decay = 0.015 + Math.random() * 0.01;
      this.traveled = 0;
    }
    update() {
      if (!this.alive) return;
      const dx = Math.cos(this.angle) * this.speed;
      const dy = Math.sin(this.angle) * this.speed;
      this.x += dx;
      this.y += dy;
      this.traveled += this.speed;
      this.alpha -= this.decay;
      if (this.alpha <= 0 || this.x > W + 50 || this.y > H + 50) this.alive = false;
    }
    draw() {
      if (!this.alive) return;
      const tailX = this.x - Math.cos(this.angle) * Math.min(this.traveled, this.length);
      const tailY = this.y - Math.sin(this.angle) * Math.min(this.traveled, this.length);
      const grad = ctx.createLinearGradient(this.x, this.y, tailX, tailY);
      grad.addColorStop(0, `rgba(255,255,255,${this.alpha})`);
      grad.addColorStop(0.3, `rgba(210,172,71,${this.alpha * 0.5})`);
      grad.addColorStop(1, `rgba(210,172,71,0)`);
      ctx.beginPath();
      ctx.moveTo(this.x, this.y);
      ctx.lineTo(tailX, tailY);
      ctx.strokeStyle = grad;
      ctx.lineWidth = 1.5;
      ctx.stroke();
      // Head glow
      ctx.beginPath();
      ctx.arc(this.x, this.y, 2, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255,255,255,${this.alpha})`;
      ctx.fill();
    }
  }

  const shootingStars = Array.from({ length: 3 }, () => new ShootingStar());
  let nextShoot = 3000 + Math.random() * 5000;
  let shootTimer = 0;

  // ─── ORBITING PLANETS ───
  const PLANET_DEFS = [
    { name: 'Sun',     color: '#cd7f32', size: 5,   orbit: 0.22, speed: 0.0003, glow: '#cd7f3240', glowSize: 18 },
    { name: 'Moon',    color: '#c0c0c0', size: 3.5, orbit: 0.12, speed: 0.002,  glow: '#c0c0c025', glowSize: 10 },
    { name: 'Mars',    color: '#c0392b', size: 3,   orbit: 0.30, speed: 0.0004, glow: '#c0392b30', glowSize: 10 },
    { name: 'Jupiter', color: '#d4a017', size: 6,   orbit: 0.38, speed: 0.00015,glow: '#d4a01730', glowSize: 22 },
    { name: 'Saturn',  color: '#4a6fa5', size: 5,   orbit: 0.44, speed: 0.0001, glow: '#4a6fa525', glowSize: 18 },
    { name: 'Venus',   color: '#ecf0f1', size: 3.2, orbit: 0.17, speed: 0.0006, glow: '#ecf0f120', glowSize: 10 },
    { name: 'Mercury', color: '#2ecc71', size: 2.5, orbit: 0.09, speed: 0.003,  glow: '#2ecc7120', glowSize: 8 },
  ];

  class OrbitalPlanet {
    constructor(def) {
      Object.assign(this, def);
      this.angle = Math.random() * Math.PI * 2;
      this.orbitRadius = Math.min(W, H) * this.orbit;
      this.eccentricity = 0.85 + Math.random() * 0.3; // slight ellipse
    }
    update(dt) {
      this.angle += this.speed * dt;
      this.orbitRadius = Math.min(W, H) * this.orbit; // recalc on resize
    }
    getPos() {
      return {
        x: cx + Math.cos(this.angle) * this.orbitRadius,
        y: cy + Math.sin(this.angle) * this.orbitRadius * this.eccentricity,
      };
    }
    draw() {
      const { x, y } = this.getPos();
      // Orbit path (very faint)
      ctx.beginPath();
      ctx.ellipse(cx, cy, this.orbitRadius, this.orbitRadius * this.eccentricity, 0, 0, Math.PI * 2);
      ctx.strokeStyle = 'rgba(210,172,71,0.03)';
      ctx.lineWidth = 0.5;
      ctx.stroke();
      // Glow
      const glowGrad = ctx.createRadialGradient(x, y, 0, x, y, this.glowSize);
      glowGrad.addColorStop(0, this.glow);
      glowGrad.addColorStop(1, 'transparent');
      ctx.beginPath();
      ctx.arc(x, y, this.glowSize, 0, Math.PI * 2);
      ctx.fillStyle = glowGrad;
      ctx.fill();
      // Planet body
      ctx.beginPath();
      ctx.arc(x, y, this.size, 0, Math.PI * 2);
      ctx.fillStyle = this.color;
      ctx.fill();
      // Saturn ring
      if (this.name === 'Saturn') {
        ctx.beginPath();
        ctx.ellipse(x, y, this.size * 2.2, this.size * 0.5, -0.3, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(74,111,165,0.5)`;
        ctx.lineWidth = 1.2;
        ctx.stroke();
      }
    }
  }

  const planets = PLANET_DEFS.map(d => new OrbitalPlanet(d));

  // ─── NEBULA GLOW ───
  function drawNebula() {
    // Subtle radial glow at center — shifts slowly with time
    const t = Date.now() * 0.0001;
    const nx = cx + Math.sin(t) * 80;
    const ny = cy + Math.cos(t * 0.7) * 60;
    const nebSize = Math.min(W, H) * 0.45;

    const neb1 = ctx.createRadialGradient(nx, ny, 0, nx, ny, nebSize);
    neb1.addColorStop(0, 'rgba(93,53,135,0.04)');
    neb1.addColorStop(0.5, 'rgba(93,53,135,0.015)');
    neb1.addColorStop(1, 'transparent');
    ctx.fillStyle = neb1;
    ctx.fillRect(0, 0, W, H);

    // Secondary warm nebula
    const n2x = cx + Math.cos(t * 0.5) * 120;
    const n2y = cy + Math.sin(t * 0.3) * 90;
    const neb2 = ctx.createRadialGradient(n2x, n2y, 0, n2x, n2y, nebSize * 0.6);
    neb2.addColorStop(0, 'rgba(210,172,71,0.02)');
    neb2.addColorStop(1, 'transparent');
    ctx.fillStyle = neb2;
    ctx.fillRect(0, 0, W, H);
  }

  // ─── MOUSE PARALLAX on stars ───
  function parallaxOffset(depth) {
    // depth 0 = no movement, 1 = max movement
    const px = (mouse.x - cx) / cx; // -1 to 1
    const py = (mouse.y - cy) / cy;
    return { x: px * 15 * depth, y: py * 15 * depth };
  }

  // ─── ANIMATION LOOP ───
  let lastTime = performance.now();

  function animate(time) {
    const dt = time - lastTime;
    lastTime = time;

    ctx.clearRect(0, 0, W, H);

    // Nebula layer
    drawNebula();

    // Stars with parallax
    const p1 = parallaxOffset(0.2);
    ctx.save();
    ctx.translate(p1.x, p1.y);
    stars.forEach(s => { s.update(time); s.draw(); });
    ctx.restore();

    // Shooting stars
    shootTimer += dt;
    if (shootTimer > nextShoot) {
      const avail = shootingStars.find(s => !s.alive);
      if (avail) avail.spawn();
      shootTimer = 0;
      nextShoot = 4000 + Math.random() * 8000;
    }
    shootingStars.forEach(s => { s.update(); s.draw(); });

    // Orbital planets with slight parallax
    const p2 = parallaxOffset(0.08);
    ctx.save();
    ctx.translate(p2.x, p2.y);
    planets.forEach(p => { p.update(dt); p.draw(); });
    ctx.restore();

    animId = requestAnimationFrame(animate);
  }

  animId = requestAnimationFrame(animate);

  // Cleanup on page hide (perf)
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      cancelAnimationFrame(animId);
    } else {
      lastTime = performance.now();
      animId = requestAnimationFrame(animate);
    }
  });
})();
