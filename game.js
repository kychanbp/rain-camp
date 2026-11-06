// The meditation game. Each task is a run of breaths, and the breath moves the world.
import * as THREE from 'three';
import { G, light, cookU } from './world.js';
const smooth = t => t * t * (3 - 2 * t), clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
export const ORDER = ['raise', 'awning', 'lights', 'sear', 'salad', 'share', 'fire', 'grill', 'sleep', 'coffee', 'pack'];
// x, y, z in metres. p is where the eye sits, l is where it looks.
export const TASKS = {
  raise: { n: 8, hour: [15, 15.5], at: [4.3, 4.6], view: { p: [4.1, 1.5, 4.5], l: [.4, .75, 0] } },
  awning: { n: 4, hour: [15.5, 15.8], at: [-1, 4], view: { p: [-.6, 1.5, 5.4], l: [-.9, 1.5, .8] } },
  lights: { n: 6, hour: [15.8, 16.4], at: [-1, 1.2], view: { p: [-1.5, 1.3, 1.1], l: [.4, 1.75, -.9] } },
  sear: { n: 4, hour: [16.4, 17.3], at: [-1.6, .3], view: { p: [-1.92, 1.3, .62], l: [-2.46, .9, .37] } },
  salad: { n: 3, hour: [17.3, 17.8], at: [-1.6, .1], view: { p: [-1.84, 1.26, -.42], l: [-2.32, .88, -.1] } },
  share: { n: 3, hour: [17.8, 18.3], at: [-.4, .9], view: { p: [-1.25, .92, .1], l: [-.15, .28, 1.0] } },
  fire: { n: 6, hour: [18.6, 20.6], at: [-.98, -.25], view: { p: [-.98, .98, -.26], l: [-.82, .54, 1.2] } },
  grill: { n: 4, hour: [20.6, 21], at: [-.98, -.25], view: { p: [-1.02, .92, .1], l: [-1.0, .47, .74] } },
  sleep: { n: 6, hour: [21, 22], at: [.0, .0], view: { p: [.7, 1.72, -.72], l: [1.5, 1.42, .9] } },
  coffee: { n: 8, hour: [7.4, 8.2], at: [-.98, -.25], view: { p: [-1.24, .8, .2], l: [-1.13, .47, .62] } },
  pack: { n: 5, hour: [8.4, 9], at: [4.3, 4.6], view: { p: [4.1, 1.5, 4.5], l: [.4, .75, 0] } }
};
const c_tarp = c => c.W.tarp;
export class Breath {
  constructor(ui) { this.ui = ui; this.lens = { s: [3, 4], m: [4, 6], l: [5, 8] }; this.len = 'm'; this.auto = false; this.reset(0, null); this.total = 0; }
  reset(n, fn) { this.n = n; this.i = 0; this.fn = fn; this.phase = 'wait'; this.t = 0; this.k = 0; this.idle = 0; this.down = false; this.dur = 4; this.lvl = 0; this.fall = false; }
  press() { this.down = true; if (this.phase === 'wait' || (this.phase === 'out' && this.k > .55)) { if (this.phase === 'out') this.finish(); if (this.i < this.n) this.begin(); } }
  release() { this.down = false; if (this.phase === 'in' && !this.useAuto()) this.toOut(); }
  useAuto() { return this.auto || this.fall; }
  begin() { this.phase = 'in'; this.t = 0; this.idle = 0; this.dur = this.lens[this.len][0]; this.fn?.('in', this.i); }
  toOut() { this.inTook = Math.max(1, this.t); this.phase = 'out'; this.t = 0; this.dur = this.useAuto() ? this.lens[this.len][1] : clamp(this.inTook * 1.5, 2.6, 9); this.lvl0 = this.lvl; this.fn?.('out', this.i); }
  finish() { this.i++; this.total++; this.phase = 'wait'; this.t = 0; this.idle = 0; this.fn?.('done', this.i - 1); }
  update(dt) {
    this.t += dt;
    if (this.phase === 'wait') { this.idle += dt; this.lvl += (0 - this.lvl) * Math.min(1, dt * 2); if (this.useAuto() ? this.idle > .9 : this.down) { if (this.i < this.n) this.begin(); } else if (!this.auto && this.idle > 8) this.fall = true; this.k = 0; return; }
    this.k = clamp(this.t / this.dur);
    if (this.phase === 'in') { this.lvl = smooth(Math.min(1, this.t / (this.useAuto() ? this.dur : 4.5))); if (this.useAuto() ? this.k >= 1 : this.t > 7) this.toOut(); }
    else if (this.phase === 'out') { this.lvl = (this.lvl0 ?? 1) * (1 - smooth(this.k)); if (this.k >= 1) this.finish(); }
  }
}
export class Game {
  constructor(c) { this.c = c; this.b = new Breath(); this.cur = null; this.done = {}; this.line = ''; this.st = { rise: 1, bulbs: [0, 0, 0, 0, 0, 0], lamps: 0, hob: 0, cook: 0, fire: 0, flip: 0, salad: 0, tomato: 1, avocado: 1, coffee: 0, sizzle: 0, grind: 0, birds: 0, sleep: false, gear: 1, brown: 0, beer: 0, tarp: 0, dinner: 1 }; this.nextIdx = 0; }
  // Put every object in the state that fits the current point in the evening
  apply() {
    const { W, audio } = this.c, s = this.st, M = W.move; G.uRise.value = s.rise; G.uBulb.value = s.bulbs; W.inner.visible = s.gear > .5; if (W.gear) W.gear.visible = s.gear > .5;
    const show = (n, on) => { if (M[n]) M[n].visible = on; };
    for (const i of [0, 1, 2]) { const st = M['steak' + i]; if (!st) continue; show('steak' + i, s.gear > .5 && s.meal !== 'eaten'); } cookU.value = clamp(s.cook); if (M.steak0) M.steak0.children[0].material.roughness = .46 - .16 * clamp(s.cook);
    for (const n of ['tongs', 'knife']) show(n, s.gear > .5); show('hobring', s.hob > .01); for (const c of (M.hobring?.children ?? [])) if (c.material.emissive) c.material.emissiveIntensity = s.hob * 3.5;
    for (const i of [0, 1, 2]) { const st = M['steak' + i]; if (st?.userData.raw) { const f = clamp(s.flip ?? 0) > .5 || s.cook > .85; st.userData.raw.visible = !f; st.userData.seared.visible = f; } }
    for (const i of [0, 1, 2]) { show('tomato' + i, s.gear > .5 && s.tomato > (i / 3)); } const din = !!(s.gear > .5 && s.dinner); show('avocado', din && s.avocado > .99); show('tomcut', din && s.tomato < .99 && s.salad < .7); show('avocut', din && s.avocado < .99 && s.salad < .98); if (M.salad) { M.salad.visible = din && s.salad > .02; M.salad.scale.setScalar(.7 + .3 * s.salad); }
    for (const n of ['sausage0', 'sausage1', 'sausage2', 'mush0', 'mush1']) { const o = M[n]; if (!o) continue; o.visible = !!(s.gear > .5 && s.dinner) && !o.userData.off; const m = o.children[0].material; if (!m.userData.c0) m.userData.c0 = m.color.clone(); m.color.copy(m.userData.c0).lerp(new THREE.Color(.08, .03, .018), s.brown); }
    show('beerfill', !!(s.gear > .5 && s.beer > .02 && s.dinner)); show('foam', !!(s.gear > .5 && s.beer > .6 && s.dinner)); show('bottle', !!(s.gear > .5 && s.dinner)); if (M.beerfill) { M.beerfill.scale.y = Math.max(.02, s.beer); M.foam.position.y = M.foam.userData.home.p.y - .1 * (1 - s.beer); } if (c_tarp(this.c)) { const t = this.c.W.tarp; t.visible = s.tarp > .02; t.scale.z = s.tarp; }
    const morning = s.gear > .5; for (const n of ['grinder', 'crank', 'perc', 'cup']) show(n, morning); show('coffee', s.coffee > .01); if (M.coffee) { const h = M.coffee.userData.home; M.coffee.position.y = h.p.y - .03 + .03 * s.coffee; M.coffee.scale.setScalar(.72 + .28 * s.coffee); }
  }
  start(id) {
    const t = TASKS[id], c = this.c; this.cur = id; this.task = t; this.rtxt = c.T().r[id]; c.begin(t, id); this.k0 = this.c.hour; this.flash = false; this.onStart(id); this.b.reset(t.n, (p, i) => this.onBreath(p, i)); c.ritualUI(true, this.rtxt[0], this.rtxt[1]); this.b.fall = false; this.setLine(this.rtxt[1]);
  }
  setLine(l) { if (l && l !== this.line) { this.line = l; this.c.ritualLine(l); } }
  onStart(id) { const s = this.st, D = this.c.dogs, a = this.c.audio;
    if (id === 'raise') { s.rise = 0; s.gear = 0; s.bulbs = [0, 0, 0, 0, 0, 0]; s.lamps = 0; s.fire = 0; D.moss.go(5.3, 3.4, 'sit'); D.birch.go(2.6, 4.9, 'sit'); this.apply(); }
    if (id === 'sear') { D.moss.go(-1.2, 1.1, 'sit'); D.birch.go(-.4, 2.4, 'sit'); }
    if (id === 'grill') { s.beer = 0; }
    if (id === 'share') { D.moss.go(-.3, .55, 'stand'); D.moss.face = [-.2, 1.5]; D.birch.go(.08, .5, 'stand'); D.birch.face = [.05, 1.5]; }
    if (id === 'fire') { D.moss.eat = D.birch.eat = false; this.c.W.kibble.visible = false; D.moss.face = D.birch.face = null; D.moss.go(-.45, -.75, 'lie'); D.birch.go(-1.75, 1.7, 'lie'); }
    if (id === 'sleep') { D.moss.go(1.2, -.3, 'sleep'); D.birch.go(-1.75, 1.7, 'sleep'); s.sleep = true; }
    if (id === 'coffee') { s.coffee = 0; s.birds = 1; s.fire = 0; s.dinner = 0; D.moss.go(-1.9, 2.6, 'stand'); D.birch.go(-.1, 4, 'stand'); }
    if (id === 'pack') { D.moss.go(5.4, 3.5, 'sit'); D.birch.go(2.7, 5, 'sit'); }
  }
  onBreath(p, i) { const id = this.cur, a = this.c.audio, s = this.st, t = this.rtxt; if (!id) return;
    if (p === 'in') { const l = t[i + 1]; this.setLine(l ?? t[t.length - 1]); if (id === 'raise') a.play('pump_up', .5); if (id === 'pack') a.play('pump_up', .25, .7); }
    if (p === 'out') {
      if (id === 'raise') a.play('pump_down', .7); if (id === 'pack') a.play('pump_down', .7, .7);
      if (id === 'salad') { a.play('chop', .7); a.play('chop', .6, 1.1, 0, .55); a.play('chop', .6, .95, 0, 1.1); }
      if (id === 'fire' && i === 0) { a.play('match', .7); } if (id === 'grill' && i === 0) a.play('pour', .45, 1.25);
      if (id === 'coffee' && i === 5) a.play('pour', .6); if (id === 'coffee' && i >= 6) a.play('sip', .5);
      if (id === 'sear' && i === 1) a.play('tap', .3);
    }
    if (p === 'done') { a.play('tap', .1, 1.4); if (i + 1 >= this.task.n) setTimeout(() => this.finish(), 900); }
  }
  finish() { const id = this.cur; if (!id) return; this.cur = null; this.done[id] = (this.done[id] ?? 0) + 1; this.nextIdx = ORDER.indexOf(id) + 1; const c = this.c, s = this.st;
    c.ritualUI(false); this.line = '';
    if (id === 'raise') { c.dip(() => { s.gear = 1; s.rise = 1; this.apply(); }); }
    if (id === 'sear') { s.hob = .15; s.sizzle = 0; } if (id === 'awning') s.tarp = 0;
    if (id === 'sleep') return c.sleepThrough(() => this.after(id));
    if (id === 'pack') return c.endCard();
    this.after(id);
  }
  after(id) { this.c.save(); this.apply(); this.c.free(); if (this.nextIdx < ORDER.length) this.c.offer(ORDER[this.nextIdx]); }
  // Hands follow the tool in use during close-up tasks
  reach() {
    const id = this.cur, b = this.b, c = this.c, H = c.W.hands, M = c.W.move; if (!id) return; const at = (o, x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z).applyMatrix4(o.matrixWorld);
    if (id === 'sear' && b.i === 2) H.want('R', at(M.tongs, .25, 0, 0), 'grip', .4);
    if (id === 'salad') { H.want('R', at(M.knife, -.13, 0, .03)); H.want('L', new THREE.Vector3(-2.2, .96, -.28), 'relax', 1.2); }
    if (id === 'grill' && b.i === 0) H.want('R', at(M.bottle, 0, .1, 0), 'grip', 1.5);
    if (id === 'coffee') { if (b.i < 3) { H.want('L', at(M.grinder, 0, .07, 0), 'grip', 1.4); H.want('R', at(M.crank, .08, 0, .07), 'grip', 0); } else if (b.i === 5) H.want('R', at(M.perc, .1, .1, 0), 'grip', 1.5); else if (b.i >= 6) { H.want('R', at(M.cup, .1, .05, 0), 'grip', 1.4); H.want('L', at(M.cup, -.08, .05, 0), 'grip', 1.4); } }
  }
  update(dt) {
    const id = this.cur, b = this.b, s = this.st, c = this.c, M = c.W.move; b.update(dt); c.breathUI(b, this.task?.n ?? 0);
    if (!id) { s.sizzle += (0 - s.sizzle) * dt; return; }
    const t = this.task, prog = clamp((b.i + (b.phase === 'out' ? b.k : 0)) / t.n), out = b.phase === 'out' ? smooth(b.k) : 0;
    c.setHour(t.hour[0] + (t.hour[1] - t.hour[0]) * prog);
    if (id === 'raise') { s.rise += (prog - s.rise) * Math.min(1, dt * 1.2); G.uRise.value = s.rise; const p = M.pumprod; p.position.y = p.userData.home.p.y + .3 * b.lvl; }
    if (id === 'pack') { if (s.gear > .5 && !this.flash) { this.flash = true; c.dip(() => { s.gear = 0; this.apply(); }); } s.rise += ((1 - prog) - s.rise) * Math.min(1, dt * 1.2); G.uRise.value = s.rise; }
    if (id === 'lights') { const v = prog * 6; for (let g = 0; g < 6; g++) s.bulbs[g] = clamp(v - g); s.lamps = clamp(prog * 1.2); }
    if (id === 'sear') { s.hob = clamp(s.hob + dt * .4); s.sizzle = clamp(prog * 3) * .6; s.cook = clamp(prog * 1.5); const fl = clamp((prog - .5) / .22); s.flip = fl * 2; const T = M.tongs, h = T.userData.home, ph = Math.sin(Math.PI * fl); T.position.set(h.p.x - .24 * ph, h.p.y + .12 * ph, h.p.z + .05 * ph); T.rotation.y = ph * .7; for (const i of [0, 1, 2]) { const st = M['steak' + i], u = clamp(fl * 1.3 - i * .15); st.rotation.x = Math.PI * smooth(u); st.position.y = st.userData.home.p.y + Math.sin(Math.PI * u) * .08; } }
    if (id === 'salad') { const K = M.knife, h = K.userData.home; K.position.set(h.p.x + .03, h.p.y + .1 * (b.lvl) + .04, h.p.z); s.tomato = 1 - clamp(prog * 3); s.avocado = 1 - clamp(prog * 3 - 1); s.salad = clamp(prog * 1.05); }
    if (id === 'share') { c.W.kibble.visible = true; c.dogs.moss.eat = b.i >= 1 && b.i < 3; c.dogs.birch.eat = b.i >= 1 && b.i < 3; if (b.i >= 1) c.dogs.moss.happy = 2; if (b.i >= 2) c.dogs.birch.happy = 2; if (prog > .98) { s.meal = 'eaten'; } }
    if (id === 'fire') { s.fire += (clamp(prog * 6) - s.fire) * Math.min(1, dt * 1.5); s.brown = prog * .3; }
    if (id === 'coffee') { const gr = b.i < 3 && b.phase !== 'wait'; s.grind = gr ? .55 : 0; M.crank.rotation.z += dt * (gr ? 5.5 : 0); s.perc = clamp((b.i - 2.6) / 2); const P = M.perc, h = P.userData.home; const tip = b.i === 5 ? (b.phase === 'in' ? b.k : b.phase === 'out' ? Math.sin(b.k * Math.PI * .5 + Math.PI * .5) : 0) : 0; P.rotation.y = tip * -.9; P.position.x = h.p.x - .13 * tip; P.position.y = h.p.y + .1 * tip; if (b.i === 5 && b.phase === 'out') s.coffee = Math.max(s.coffee, b.k); const C = M.cup, ch = C.userData.home; const sip = b.i >= 6 ? b.lvl : 0; C.position.set(ch.p.x + sip * .05, ch.p.y + sip * .32, ch.p.z - sip * .3); M.coffee.position.set(ch.p.x, M.coffee.userData.home.p.y - .03 + .03 * s.coffee + sip * .32, ch.p.z - sip * .3); M.coffee.position.x += sip * .05; }
    if (id === 'sleep') { s.fire = Math.max(0, s.fire - dt * .1); }
    if (id === 'awning') { const v = [1, .85, .7, 0][Math.min(3, b.i)]; const v0 = b.i === 3 ? clamp(1 - out * 1.1) * .7 : v; s.tarp += ((b.i === 0 ? prog * 4 * .9 + .1 : v0) - s.tarp) * Math.min(1, dt * 1.5); }
    if (id === 'grill') { const B = M.bottle, h = B.userData.home; const tip = b.i === 0 ? (b.phase === 'in' ? b.k : b.phase === 'out' ? 1 - b.k * .9 : 0) : 0; B.position.set(h.p.x - .1 * tip, h.p.y + .12 * tip, h.p.z); B.rotation.z = tip * 1.5; if (b.i === 0 && b.phase === 'out') s.beer = Math.max(s.beer, b.k); s.brown = clamp(.3 + prog * .7); const u = clamp((prog - .3) * 3); for (const i of [0, 1, 2]) { const o = M['sausage' + i]; o.rotation.x = Math.PI * smooth(clamp(u * 1.4 - i * .2)); } }
    this.apply();
  }
}
