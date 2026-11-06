// Sound: rain layers change with where you are, fire and sizzle follow what is lit. All made offline by scripts/make_audio.py.
const A = 'assets/audio/';
export class Sound {
  constructor() { this.ios = /iPhone|iPad|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1); this.vol = 1; this.buf = {}; this.loops = {}; this.muted = false; this.ctx = null; }
  unlock() {
    try { if (navigator.audioSession) navigator.audioSession.type = 'playback'; } catch { }
    if (this.ios && !this.keep) { const a = this.keep = new Audio('assets/silent.m4a'); a.loop = true; a.playsInline = true; a.play().catch(() => { }); }
    if (!this.ctx) { const AC = window.AudioContext || window.webkitAudioContext; this.ctx = new AC({ latencyHint: 'playback' }); }
    const c = this.ctx, s = c.createBufferSource(); s.buffer = c.createBuffer(1, 1, c.sampleRate); s.connect(c.destination); s.start(); c.resume?.();
  }
  wake() { const c = this.ctx; if (c && c.state !== 'running') { this.keep?.play().catch(() => { }); c.resume?.(); } }
  async start() {
    if (this.master) return; this.unlock(); const c = this.ctx;
    this.master = c.createGain(); this.master.gain.value = 0;
    const lim = c.createDynamicsCompressor(); lim.threshold.value = -8; lim.ratio.value = 5; lim.attack.value = .01; lim.release.value = .3; this.master.connect(lim); lim.connect(c.destination);
    this.meta = await fetch(A + 'loops.json').then(r => r.json());
    await Promise.all(Object.keys(this.meta).map(n => this.load(n)));
    for (const n of Object.keys(this.meta)) this.loop(n);
    this.master.gain.setTargetAtTime(this.muted ? 0 : this.vol, c.currentTime, 1.5);
    Promise.all(['pump_up', 'pump_down', 'match', 'chop', 'pour', 'sip', 'tap', 'chime', 'pant', 'thump', 'step0', 'step1', 'step2', 'step3', 'thunder0', 'thunder1'].map(n => this.load(n)));
    this.t = 12 + Math.random() * 30;
  }
  async load(n) { if (this.buf[n]) return this.buf[n]; const b = await fetch(A + n + '.m4a').then(r => r.arrayBuffer()); return this.buf[n] = await this.ctx.decodeAudioData(b); }
  loop(n) { const c = this.ctx, s = c.createBufferSource(), g = c.createGain(), p = c.createStereoPanner(), f = c.createBiquadFilter(), m = this.meta[n]; s.buffer = this.buf[n]; s.loop = true; s.loopStart = m.start; s.loopEnd = Math.min(m.end, s.buffer.duration - .01); f.type = 'lowpass'; f.frequency.value = 18000; g.gain.value = 0; s.connect(f); f.connect(g); g.connect(p); p.connect(this.master); s.start(0, m.start + Math.random() * 10); this.loops[n] = { g, p, f }; }
  set(n, v, tc = .8) { const l = this.loops[n]; if (l) l.g.gain.setTargetAtTime(v, this.ctx.currentTime, tc); }
  play(n, gain = 1, rate = 1, pan = 0, delay = 0) { const b = this.buf[n]; if (!b || !this.master) return; const c = this.ctx, s = c.createBufferSource(), g = c.createGain(), p = c.createStereoPanner(); s.buffer = b; s.playbackRate.value = rate; g.gain.value = gain; p.pan.value = pan; s.connect(g); g.connect(p); p.connect(this.master); s.start(c.currentTime + delay); return s; }
  // every frame: inside, how hard it rains, hour, what burns
  mix(dt, m) {
    if (!this.master || !this.loops.rain_forest) return; const r = m.rain, inT = m.inside;
    this.set('rain_forest', r * (.72 - inT * .46) * (.55 + .45 * m.heavy));
    this.loops.rain_forest.f.frequency.setTargetAtTime(inT > .5 ? 5200 : 18000, this.ctx.currentTime, .5);
    this.set('rain_tent', r * (.12 + inT * .62) * (.55 + .45 * m.heavy)); this.set('drips', (.1 + inT * .3) * Math.min(1, r * 3 + .18 * m.wet));
    this.set('wind', .1 + r * .1); this.set('fire', m.fire); this.loops.fire.p.pan.setTargetAtTime(m.firePan, this.ctx.currentTime, .3);
    this.set('sizzle', m.sizzle); this.set('grind', m.grind, .08); this.set('birds', m.birds * (1 - inT * .4), 2);
    this.t -= dt; if (this.t < 0 && r > .55 && !m.quiet) { this.t = 40 + Math.random() * 90; this.play(Math.random() < .5 ? 'thunder0' : 'thunder1', .3 + Math.random() * .25, .9 + Math.random() * .2, Math.random() - .5); m.onThunder?.(); }
  }
  setVolume(v) { this.vol = v; if (this.master && !this.muted) this.master.gain.setTargetAtTime(v, this.ctx.currentTime, .1); }
  setMuted(m) { this.muted = m; if (this.master) this.master.gain.setTargetAtTime(m ? 0 : this.vol, this.ctx.currentTime, .2); }
  stop() { if (this.master) this.master.gain.setTargetAtTime(0, this.ctx.currentTime, .4); }
  resume() { if (this.master) this.master.gain.setTargetAtTime(this.muted ? 0 : this.vol, this.ctx.currentTime, 1); }
}
