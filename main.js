import * as THREE from 'three';
import { VRButton } from 'three/addons/webxr/VRButton.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { BokehPass } from 'three/addons/postprocessing/BokehPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { G, buildWorld, applyTime, light, bakedMaterial } from './world.js';
import { loadDogs } from './dogs.js';
import { Sound } from './audio.js';
import { STR } from './i18n.js';
import { loadModels, loadHands } from './models.js';
import { Game, TASKS, ORDER, Breath } from './game.js';
const $ = id => document.getElementById(id), params = new URLSearchParams(location.search);
let lang = (() => { try { return localStorage.getItem('lang'); } catch { return null; } })() || (navigator.language?.startsWith('zh') ? 'zh' : 'en'); let L = STR[lang];
if (params.get('lang')) { lang = params.get('lang'); L = STR[lang]; }
const T = () => L;
function applyLang() { L = STR[lang]; document.documentElement.lang = lang === 'zh' ? 'zh-Hans' : 'en'; document.title = L.appTitle; document.querySelectorAll('[data-t]').forEach(e => e.textContent = L[e.dataset.t] ?? ''); $('langHome').textContent = lang === 'zh' ? 'English' : '简体中文'; $('lEn').classList.toggle('on', lang === 'en'); $('lZh').classList.toggle('on', lang === 'zh'); }
function setLang(l) { lang = l; try { localStorage.setItem('lang', l); } catch { } applyLang(); if (started) { buildTasks(); buildJournal(); poseUi(); } }
applyLang();
const MOBILE = params.get('mobile') === '1' || (matchMedia('(pointer:coarse)').matches && Math.min(screen.width, screen.height) < 900 && !/OculusBrowser|Quest|Pico/i.test(navigator.userAgent)), QUEST = /OculusBrowser|Quest|Pico/i.test(navigator.userAgent);
const Q = { mobile: MOBILE || QUEST };
const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, MOBILE ? 1.6 : 2)); renderer.setSize(innerWidth, innerHeight); renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1; renderer.xr.enabled = true; renderer.xr.setReferenceSpaceType('local-floor');
document.body.prepend(renderer.domElement); window.__renderer = renderer;
const scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(MOBILE && innerHeight > innerWidth ? 74 : 62, innerWidth / innerHeight, .04, 900), rig = new THREE.Group(); rig.add(cam); scene.add(rig); scene.fog = new THREE.FogExp2(0x777777, .02);
addEventListener('resize', () => { cam.aspect = innerWidth / innerHeight; cam.fov = MOBILE && innerHeight > innerWidth ? 74 : 62; cam.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); composer?.setSize(innerWidth, innerHeight); });
// Film look on desktops: glow around lights, soft focus in close-ups, a gentle grade. Phones and headsets draw directly.
let composer = null, bokeh = null, grade = null;
function initPost() {
  if (Q.mobile || params.get('post') === '0') return;
  const rt = new THREE.WebGLRenderTarget(1, 1, { type: THREE.HalfFloatType, samples: 4 }); composer = new EffectComposer(renderer, rt); composer.setPixelRatio(renderer.getPixelRatio()); composer.setSize(innerWidth, innerHeight);
  composer.addPass(new RenderPass(scene, cam)); composer.addPass(new UnrealBloomPass(new THREE.Vector2(innerWidth, innerHeight), .26, .72, .92));
  bokeh = new BokehPass(scene, cam, { focus: 1, aperture: .00022, maxblur: .007 }); bokeh.enabled = false; composer.addPass(bokeh); composer.addPass(new OutputPass());
  grade = new ShaderPass({ uniforms: { tDiffuse: { value: null }, uT: { value: 0 } }, vertexShader: 'varying vec2 vUv;void main(){vUv=uv;gl_Position=vec4(position.xy,0.,1.);}', fragmentShader: `uniform sampler2D tDiffuse;uniform float uT;varying vec2 vUv;float h(vec2 p){return fract(sin(dot(p,vec2(12.9898,78.233))+uT)*43758.5453);}
    void main(){vec4 c=texture2D(tDiffuse,vUv);vec2 q=vUv-.5;float v=1.-dot(q,q)*.62;vec3 r=c.rgb;float l=dot(r,vec3(.3,.59,.11));r=mix(vec3(l),r,1.06);r=mix(r,r*r*(3.-2.*r),.22);r+=mix(vec3(.004,.009,.012),vec3(0.),smoothstep(0.,.45,l));gl_FragColor=vec4(r*v+(h(vUv*913.)-.5)*.014,1.);}` });
  composer.addPass(grade);
}
const audio = new Sound(); let W, dogs, game, started = false, hour = 15, hourShown = 15, rainAmt = 1, rainScale = 1, manualHour = null;
const state = { x: 2.3, z: 8.5, yaw: .1, pitch: -.03, view: null, viewK: 0, eyeH: 1.62, mode: null, stepD: 0, speed: 1 }, keys = {};
const stats = (() => { try { return JSON.parse(localStorage.getItem('raincamp')) ?? {}; } catch { return {}; } })(); stats.noted ??= {}; stats.breaths ??= 0; stats.min ??= 0; stats.nights ??= 0;
function saveStats() { try { localStorage.setItem('raincamp', JSON.stringify(stats)); } catch { } }
// ---- things to notice. Each has a place to look at.
const NOTES = [['cone', 3.2, .05, 2.6], ['mush', -6, .08, 4.3], ['drop', 6.1, 1.4, 5.3], ['bark', 7.3, 1.5, -2.5], ['puddle', 1.4, .05, 7], ['log', 4.3, .3, -4.1], ['stump', -8.8, .4, -3.7], ['moss2', -1.6, .08, 5.6], ['rope', 3.3, .8, 2.2], ['tyre', -6.3, .4, 1.1], ['boots', -.15, .15, 1.75], ['paw', .6, .03, 3.6]];
const notice = { id: null, t: 0 };
function checkNotice(dt) {
  if (state.mode || !started) return; const f = new THREE.Vector3(); cam.getWorldDirection(f); let best = null;
  for (const n of NOTES) { if (stats.noted[n[0]]) continue; const dx = n[1] - cam.position.x, dy = n[2] - cam.position.y, dz = n[3] - cam.position.z, d = Math.hypot(dx, dy, dz); if (d > 3.2) continue; const c = (dx * f.x + dy * f.y + dz * f.z) / d; if (c > .9) { best = n; break; } }
  if (best && best[0] === notice.id) notice.t += dt; else { notice.id = best?.[0] ?? null; notice.t = 0; }
  $('nProg').style.opacity = notice.id && notice.t > 2 ? 1 : 0; $('nArc').style.strokeDashoffset = 100 - 100 * Math.min(1, notice.t / 6);
  if (notice.id && notice.t > 6) { stats.noted[notice.id] = 1; saveStats(); audio.play('chime', .3, 1 + Math.random() * .06); const e = L.n[notice.id]; toast(e[0], e[1]); notice.id = null; buildJournal(); }
}
let toastT; function toast(a, b) { const t = $('toast'); t.innerHTML = ''; const x = document.createElement('b'); x.textContent = a; const y = document.createElement('small'); y.textContent = b ?? ''; t.append(x, y); t.style.opacity = 1; clearTimeout(toastT); toastT = setTimeout(() => t.style.opacity = 0, 5200); }
// ---- world bits added here: cones, mushrooms
function withBake(g, sky = .7) { const n = g.attributes.position.count, a = new Uint8Array(n * 3); for (let i = 0; i < n; i++) a[i * 3] = Math.sqrt(sky) * 255; g.setAttribute('bake', new THREE.BufferAttribute(a, 3, true)); return g; }
function addSmallThings() {
  // cone: overlapping scales in a spiral
  const pos = [], idx = []; let v = 0; const n = 72; for (let i = 0; i < n; i++) { const t = i / n, a = i * 2.4, h = .12 * t, r = .036 * Math.sin(Math.PI * (t * .86 + .1)) + .006, cx = Math.cos(a) * r, cz = Math.sin(a) * r; const w = .013, l = .018; const ux = -Math.sin(a), uz = Math.cos(a); const q = [[cx - ux * w, h - .004, cz - uz * w], [cx + ux * w, h - .004, cz + uz * w], [cx * 1.28 + ux * w * .7, h + l, cz * 1.28 + uz * w * .7], [cx * 1.28 - ux * w * .7, h + l, cz * 1.28 - uz * w * .7], [cx * .6, h + l * .3, cz * .6]]; for (const p of q) pos.push(...p); idx.push(v, v + 1, v + 2, v, v + 2, v + 3, v, v + 3, v + 4, v + 1, v + 4, v + 2); v += 5; }
  const cg = new THREE.BufferGeometry(); cg.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); cg.setIndex(idx); cg.computeVertexNormals(); cg.setAttribute('uv', new THREE.Float32BufferAttribute(new Float32Array(v * 2), 2)); cg.rotateZ(1.45); withBake(cg, .65);
  const cm = bakedMaterial({ color: [.16, .085, .045], rough: .6 }, { env: W.env, double: false }), nc = MOBILE ? 60 : 180, ci = new THREE.InstancedMesh(cg, cm, nc), o = new THREE.Object3D(); ci.frustumCulled = false;
  for (let i = 0; i < nc; i++) { const r = i === 0 ? 0 : 4 + Math.random() * 30, a = Math.random() * 6.28; let x = 3.2, z = 2.6; if (i) { x = -1 + Math.cos(a) * r; z = Math.sin(a) * r * .8 - 2; if (x > -8 && x < 3 && Math.abs(z) < 2) continue; } o.position.set(x, W.heightAt(x, z) + .03, z); o.rotation.y = Math.random() * 6.28; o.scale.setScalar(.9 + Math.random() * .7); o.updateMatrix(); ci.setMatrixAt(i, o.matrix); } scene.add(ci);
  const prof = [[0, .13], [.02, .13], [.042, .127], [.058, .116], [.06, .11], [.04, .112], [.01, .11]].map(p => new THREE.Vector2(p[0], p[1])), mg = new THREE.LatheGeometry(prof, 16), sg = new THREE.CylinderGeometry(.0055, .009, .115, 8).translate(0, .057, 0); withBake(mg, .6); withBake(sg, .6);
  const mm = bakedMaterial({ color: [.62, .47, .36], rough: .5 }, { env: W.env, double: true }), sm = bakedMaterial({ color: [.68, .6, .5], rough: .7 }, { env: W.env });
  for (const [x, z, s] of [[-6, 4.3, 1.5], [-6.13, 4.42, 1.1], [3.8, -3.7, 1.3], [8.6, 1.6, 1.4], [-11, -2, 1.4]]) { const c = new THREE.Mesh(mg, mm), t = new THREE.Mesh(sg, sm), g = new THREE.Group(); g.add(c, t); g.position.set(x, W.heightAt(x, z), z); g.scale.setScalar(s); scene.add(g); }
  // fallen twigs on the needles, and kibble in the bowls
  { const n = MOBILE ? 90 : 320, g = withBake(new THREE.CylinderGeometry(.004, .009, 1, 5).rotateZ(1.5), .6), m = bakedMaterial({ color: [.09, .06, .04], rough: .8 }, { env: W.env }), im = new THREE.InstancedMesh(g, m, n), o = new THREE.Object3D(); let i = 0; while (i < n) { const r = 3 + Math.random() * 34, a = Math.random() * 6.28, x = -1 + Math.cos(a) * r, z = -2 + Math.sin(a) * r * .9; if (x > -8 && x < 3 && Math.abs(z) < 2 || z > 7) continue; o.position.set(x, W.heightAt(x, z) + .012, z); o.rotation.set(0, Math.random() * 6.28, (Math.random() - .5) * .05); o.scale.set(.2 + Math.random() * .7, 1, 1); o.updateMatrix(); im.setMatrixAt(i++, o.matrix); } im.frustumCulled = false; scene.add(im);
    const kg = withBake(new THREE.IcosahedronGeometry(.011, 0), .4), km = bakedMaterial({ color: [.2, .1, .05], rough: .7 }, { env: W.env }), ki = new THREE.InstancedMesh(kg, km, 70); for (let j = 0; j < 70; j++) { const c = j % 2 ? [-.2, 1.2] : [.05, 1.15], r = Math.sqrt(Math.random()) * .07, a = Math.random() * 6.28; o.position.set(c[0] + Math.cos(a) * r, .03 + Math.random() * .012, c[1] + Math.sin(a) * r); o.rotation.set(Math.random() * 3, Math.random() * 3, 0); o.scale.setScalar(.8 + Math.random() * .5); o.updateMatrix(); ki.setMatrixAt(j, o.matrix); } ki.frustumCulled = false; W.kibble = ki; ki.visible = false; scene.add(ki); }
  // the awning that does not fit
  { const g = new THREE.PlaneGeometry(4.4, 3, 24, 16).rotateX(-Math.PI / 2 + .1).translate(0, 0, 1.5); const p = g.attributes.position; for (let i = 0; i < p.count; i++) { const x = p.getX(i), z = p.getZ(i); p.setY(i, p.getY(i) - .22 * Math.sin(z / 3 * Math.PI) * (1 - (x / 2.2) ** 2) + Math.sin(x * 5 + z * 3) * .02); } g.computeVertexNormals(); withBake(g, .5); const m = bakedMaterial({ color: [.075, .078, .084], rough: .78 }, { env: W.env, envI: .35, double: true, tent: false, wetRough: '.85' }); W.tarp = new THREE.Mesh(g, m); W.tarp.position.set(-.3, 2.42, 1.62); W.tarp.visible = false; W.tarp.frustumCulled = false; scene.add(W.tarp);
    const pm = bakedMaterial({ color: [.5, .5, .5], rough: .4, metal: .8 }, { env: W.env }), pg = withBake(new THREE.CylinderGeometry(.014, .014, 2.2, 8), .7); for (const x of [-2.3, 1.7]) { const c = new THREE.Mesh(pg, pm); c.position.set(x + .3, -1.15, 3); W.tarp.add(c); } }
  // morning sun between the trunks
  { const sm = new THREE.ShaderMaterial({ transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide, uniforms: { uK: { value: 0 }, uT: G.uTime }, vertexShader: 'varying vec2 vU;void main(){vU=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}', fragmentShader: `varying vec2 vU;uniform float uK,uT;void main(){float e=smoothstep(0.,.25,vU.x)*smoothstep(1.,.75,vU.x)*smoothstep(0.,.2,vU.y)*smoothstep(1.,.5,vU.y);float s=.6+.4*sin(vU.x*19.+uT*.1)*sin(vU.x*7.-uT*.07);gl_FragColor=vec4(vec3(1.,.9,.68)*e*s*uK*.1,1.);\n#include <colorspace_fragment>\n}` }), g = new THREE.Group(); for (const [x, z, w] of [[7, -9, 9], [-6, -13, 12], [14, 2, 8], [-16, 6, 10], [2, 16, 11], [-12, 19, 9]]) { const q = new THREE.Mesh(new THREE.PlaneGeometry(w, 26), sm); q.position.set(x, 11, z); q.rotation.set(0, Math.atan2(x, z), .32); g.add(q); q.frustumCulled = false; q.renderOrder = 7; } scene.add(g); W.shafts = sm; }
  // the car's cabin glows at night through its glass
  const am = new THREE.MeshBasicMaterial({ color: 0xffa040, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide }); W.carGlow = am; for (const z of [-.85, .85]) { const p = new THREE.Mesh(new THREE.PlaneGeometry(1.25, .5), am); p.position.set(-3.8, 1.55, z); scene.add(p); }
  // steam and smoke: soft quads that rise
  const smoke = []; const sm2 = () => new THREE.SpriteMaterial({ map: W.glow, color: 0xd8d4cc, transparent: true, opacity: 0, depthWrite: false }); for (let i = 0; i < 8; i++) { const s = new THREE.Sprite(sm2()); s.userData.t = i / 8; s.renderOrder = 11; scene.add(s); smoke.push(s); } W.smoke = smoke;
}
const updateSmoke = (dt, on, x, y, z) => { for (const s of W.smoke) { s.userData.t = (s.userData.t + dt * .28) % 1; const t = s.userData.t; s.position.set(x + Math.sin(t * 7 + s.id) * .05 * t * 3, y + t * .55, z + Math.cos(t * 5 + s.id) * .04 * t * 3); s.scale.setScalar(.1 + t * .35); s.material.opacity = on * .22 * Math.sin(Math.PI * t); } };
// Generated models take the place of the first drafts. Rotations turn each from its picture pose into place.
async function addModels() {
  const sc = { warm: W.camp.scale.warm, fire: W.camp.scale.fire }, mk = await loadModels(W, sc), M = W.move, F = -Math.PI / 2;
  const swap = (name, list) => { const g = M[name]; if (!g) return; const has = list.filter(Boolean); if (!has.length) return; for (const c of g.children) c.visible = false; g.add(...has); g.userData.gen = has; };
  for (const i of [0, 1, 2]) { const r = mk('steak_raw', { flat: true, pos: [0, .014, 0], size: .13, rot: [F, 0, i * 2], sky: .2, warm: .35, rough: .38 }), c = mk('steak_seared', { flat: true, pos: [0, .014, 0], size: .125, rot: [F, 0, i * 2 + 1], sky: .2, warm: .1, tint: .7, rough: .36 }); if (r && c) { c.visible = false; swap('steak' + i, [r, c]); M['steak' + i].userData.raw = r; M['steak' + i].userData.seared = c; } }
  swap('tomcut', [mk('tomato_half', { flat: true, size: .075, rot: [F, 0, 0], pos: [0, .012, 0], sky: .2, warm: .35, rough: .3 })]);
  swap('avocut', [mk('avocado_half', { flat: true, size: .1, rot: [F + .15, 0, .4], pos: [.0, .03, 0], sky: .2, warm: .35, rough: .42 })]);
  swap('salad', [mk('salad_bowl', { flat: true, size: .27, rot: [F, 0, 0], pos: new THREE.Vector3(-2.12, .925, .3).sub(M.salad.position).toArray(), sky: .2, warm: .35, rough: .42 })]);
  swap('sausage0', [mk('sausage', { size: .15, rot: [0, 0, 0], sky: .15, warm: .2, fire: .3, rough: .36 })]); for (const n of ['sausage1', 'sausage2']) if (M.sausage0?.userData.gen) M[n].userData.off = true;
  swap('mush0', [mk('mushroom', { size: .06, sky: .15, warm: .2, fire: .3 })]); swap('mush1', [mk('mushroom', { size: .055, rot: [0, 2, 0], sky: .15, warm: .2, fire: .3 })]);
  swap('bottle', [mk('bottle', { size: .25, sky: .25, warm: .3, fire: .25, rough: .12, env: 2 })]); swap('perc', [mk('percolator', { size: .24, sky: .3, warm: .1, fire: .1, rough: .25, metal: .6, env: 2 })]);
  swap('grinder', [mk('grinder', { size: .22, sky: .3, warm: .1, fire: .1, rough: .3, metal: .5, env: 1.6 })]); swap('cup', [mk('cup', { size: .12, sky: .3, warm: .1, rough: .4 })]);
  // things that stand still
  const put = (k, o) => { const m = mk(k, o); if (m) { (W.gear ?? W.root).add(m); } return m; };
  put('lantern', { size: .24, pos: [-2.0, .88, .62], sky: .2, warm: .5, rough: .3, metal: .4 }); put('lantern', { size: .22, pos: [-1.42, .42, .95], sky: .2, warm: .5, fire: .3, rough: .3, metal: .4 }); put('lantern', { size: .22, pos: [1.3, 1.31, -1.25], sky: .2, warm: .5, rough: .3, metal: .4 }); put('lantern', { size: .28, pos: [-2.38, 1.9, 1.67], sky: .5, warm: .5, rough: .3, metal: .4 });
  put('grillpan', { flat: true, size: .4, pos: [-2.47, .95, .38], rot: [F, 0, 0], sky: .2, warm: .08, tint: .3, rough: .55, metal: 0, env: .5 }); put('oilbottle', { size: .19, pos: [-1.95, .88, .14], sky: .2, warm: .35, rough: .12, env: 2 }); put('powerbox', { size: .34, pos: [-3.25, .86, -.35], rot: [0, Math.PI / 2, 0], sky: .1, warm: .12, rough: .5 });
  for (const [x, y, z, s, r] of [[-3.8, .88, .4, .62, 1.5], [-3.8, .88, -.4, .6, 1.7], [-3.8, 1.2, .4, .56, 1.4], [-3.8, 1.2, -.42, .54, 1.6]]) put('case', { size: s, pos: [x, y, z], rot: [0, r, 0], sky: .08, warm: .6, rough: .7 });
}
// ---- time of day and light levels
function setHour(h) { hour = h; }
function updateLight(dt, t) {
  hourShown = hour; const force = manualHour; const hr = force ?? hourShown; applyTime(hr); const s = game.st, rainNow = G.uRain.value * rainScale; G.uRain.value = rainNow; const dark = light.dark;
  G.uEnv.value = Math.min(1, G.uSky.value.g * .85);
  const lamp = Math.max(...s.bulbs) > 0 ? (s.bulbs.reduce((a, b) => a + b, 0) / 6) : 0; const w = G.uWarm.value.setRGB(1, .6, .27).multiplyScalar((.25 + lamp * .75) * (lamp > 0 || s.lamps ? 1 : 0) * (2.4)); const fl = (.84 + .1 * Math.sin(t * 9.1) + .06 * Math.sin(t * 23)) * s.fire; G.uFire.value.setRGB(1, .47, .15).multiplyScalar(fl * 1.4); scene.fog.color.copy(G.uFog.value); scene.fog.density = G.uFogD.value;
  for (const m of Object.values(W.mats)) if (m.userData.emit === 'warm') m.emissiveIntensity = lamp * (m.name === 'led' ? 5 : .7);
  W.kitchenLight.intensity = lamp * (['sleep', 'lights'].includes(game.cur) ? 2.6 : 1.5); if (game.cur === 'sleep' || game.cur === 'lights') W.kitchenLight.position.set(1.1, 2.1, -.3); else W.kitchenLight.position.set(-2.4, 1.45, .25); { const day = Math.min(1, G.uSky.value.g); W.fireLight.intensity = fl * 1.1 + day * (1 - s.fire) * 1.3; W.fireLight.color.setRGB(1, s.fire > .3 ? .54 : .94, s.fire > .3 ? .24 : .85); } W.fire.visible = s.fire > .02; W.fireMats.forEach(f => f.uniforms.uOn.value = s.fire);
  W.halos.forEach(h => { h.material.opacity = (h.userData.key === 'fire' ? s.fire * (.4 + .35 * dark) : lamp * (.25 + .75 * dark)); }); W.carGlow.opacity = 0; W.shafts.uniforms.uK.value = Math.max(0, 1 - Math.abs(hr - 8.4) / 1.8) * (1 - G.uRain.value * 3 > 0 ? 1 - G.uRain.value * 3 : 0);
  W.rain.visible = W.splash.visible = rainNow > .02; if (W.curtain) W.curtain.visible = rainNow > .02;
  G.uWind.value = .5 + rainNow * .5;
}
let flash = 0;
// ---- walking
const OUT = [-2.62, 2.62, -1.72, 1.72];
const treeHit = (x, z) => W.world.trees.some(t => (t.x - x) ** 2 + (t.z - z) ** 2 < .3);
function free(x, z) {
  if (Math.hypot(x + 1, z) > 88) return false;
  if (x > -7.5 && x < -2.75 && Math.abs(z) < 1.25) return false;                // car
  if (game.st.rise > .5) {
    if (x > OUT[0] && x < OUT[1] && z > OUT[2] && z < OUT[3]) {                  // tent: enter by the door
      const door = x > -2.2 && x < .12 && z > 1.2, inside = x > -2.25 && x < .02 && z > -1.32 && z < 1.32; if (!(door || inside)) return false;
      if (x > -1.5 && x < -.42 && z > .4 && z < 1.05) return false;              // fire table
      if (x > -1.6 && x < -.4 && z > -.5 && z < 0) return false;                  // bench
      if (x < -1.85 && z > -.55 && z < .75) return false;                         // kitchen
    }
  }
  return !treeHit(x, z);
}
function move(dx, dz) { if (free(state.x + dx, state.z + dz)) { state.x += dx; state.z += dz; } else if (free(state.x + dx, state.z)) state.x += dx; else if (free(state.x, state.z + dz)) state.z += dz; else return 0; return 1; }
const inside = () => (Math.abs(state.x) < 2.5 && Math.abs(state.z) < 1.6 && game.st.rise > .7) ? 1 : 0;
// ---- input
let drag = null, dragId = null, moved = 0; const cv = renderer.domElement;
cv.addEventListener('pointerdown', e => { audio.wake(); if (state.mode === 'ritual') { game.b.press(); dragId = e.pointerId; try { cv.setPointerCapture(e.pointerId); } catch { } return; } if (drag) return; drag = [e.clientX, e.clientY]; moved = 0; dragId = e.pointerId; try { cv.setPointerCapture(e.pointerId); } catch { } });
const pEnd = e => { if (e.pointerId !== dragId) return; dragId = null; if (state.mode === 'ritual') { game.b.release(); return; } const tap = drag && moved < 8 && e.type === 'pointerup'; drag = null; if (tap && started) tapAt(e.clientX, e.clientY); };
cv.addEventListener('pointerup', pEnd); cv.addEventListener('pointercancel', pEnd);
cv.addEventListener('pointermove', e => { if (!drag || e.pointerId !== dragId) return; moved += Math.abs(e.clientX - drag[0]) + Math.abs(e.clientY - drag[1]); state.yaw -= (e.clientX - drag[0]) * .0035; state.pitch = THREE.MathUtils.clamp(state.pitch - (e.clientY - drag[1]) * .0035, -1.3, 1.35); drag = [e.clientX, e.clientY]; });
const ray = new THREE.Raycaster();
function tapAt(cx, cy) { const n = new THREE.Vector2(cx / innerWidth * 2 - 1, -cy / innerHeight * 2 + 1); ray.setFromCamera(n, cam); for (const d of Object.values(dogs)) { const p = d.root.position.clone(); p.y += .5; if (ray.ray.distanceToPoint(p) < .55 && p.distanceTo(cam.position) < 7) { d.happy = 4; audio.play('thump', .5); audio.play('thump', .4, 1, 0, .22); audio.play('pant', .35); toast(`${L[d.name]} ${L.dogHello}`); if (d.state === 'sleep') d.state = 'lie'; return; } } }
addEventListener('keydown', e => { keys[e.code] = true; if (e.code === 'Space') { e.preventDefault(); if (state.mode === 'ritual' && !e.repeat) game.b.press(); } if (e.code === 'KeyM') rest('lie'); if (e.code === 'KeyN') rest('sit'); if (e.code === 'KeyH' && started) setHud(document.body.classList.contains('nohud')); if (e.code === 'KeyF' && started && fsCan()) fsSet(!fsEl()); if (e.code === 'Escape') sheet(null); });
addEventListener('keyup', e => { keys[e.code] = false; if (e.code === 'Space' && state.mode === 'ritual') game.b.release(); });
const stick = $('stick'), knob = $('knob'), joy = { x: 0, y: 0, id: null };
function joyMove(e) { const r = stick.getBoundingClientRect(), R = r.width / 2, dx = e.clientX - r.left - R, dy = e.clientY - r.top - R, max = R - 22, d = Math.hypot(dx, dy), k = d > max ? max / d : 1; knob.style.transform = `translate(${dx * k}px,${dy * k}px)`; const dead = v => Math.abs(v) < .12 ? 0 : (v - Math.sign(v) * .12) / .88; joy.x = dead(dx * k / max); joy.y = dead(-dy * k / max); }
function joyEnd(e) { if (e.pointerId !== joy.id) return; joy.id = null; joy.x = joy.y = 0; knob.style.transform = ''; stick.classList.remove('on'); }
stick.addEventListener('pointerdown', e => { e.preventDefault(); if (joy.id !== null) return; joy.id = e.pointerId; stick.classList.add('on'); try { stick.setPointerCapture(e.pointerId); } catch { } joyMove(e); if (state.mode === 'rest') getUp(); });
stick.addEventListener('pointermove', e => { if (e.pointerId === joy.id) joyMove(e); }); stick.addEventListener('pointerup', joyEnd); stick.addEventListener('pointercancel', joyEnd); stick.addEventListener('lostpointercapture', joyEnd); stick.addEventListener('contextmenu', e => e.preventDefault());
// ---- sit and lie
const SEATS = { sit: [{ p: [-.98, .96, -.26], l: [-.85, .6, 1.5] }, { p: [1.9, .95, 3.6], l: [0, 1.1, 0] }], lie: [{ p: [.95, 1.68, -.46], l: [1.55, 1.82, 1.6] }] };
function rest(mode) {
  if (state.mode === 'ritual') return; if (state.mode === 'rest' && state.rest === mode) return getUp();
  const list = SEATS[mode]; let b = list[0], bd = 1e9; for (const s of list) { const d = Math.hypot(s.p[0] - state.x, s.p[2] - state.z); if (d < bd) { bd = d; b = s; } }
  if (mode === 'sit' && state.x > 2.6 || mode === 'sit' && Math.abs(state.z) > 3) b = { p: [state.x, .95, state.z], l: [state.x - Math.sin(state.yaw) * 4, 1.1, state.z - Math.cos(state.yaw) * 4] };
  state.ret = [state.x, state.z]; state.mode = 'rest'; state.rest = mode; state.view = b; state.viewK = 0; document.body.classList.add('quiet'); poseUi();
}
function getUp() { if (state.ret && state.rest === 'lie') { state.x = -.6; state.z = .2; } state.mode = null; state.rest = null; state.view = null; state.yaw = Math.atan2(cam.position.x - state.x, cam.position.z - state.z) * 0 + state.yaw; document.body.classList.remove('quiet'); poseUi(); }
function poseUi() { for (const [id, lab, m, w] of [['bSit', 'sitLabel', 'sit', L.sit], ['bLie', 'lieLabel', 'lie', L.lie]]) { const on = state.rest === m; $(id).classList.toggle('on', on); $(id).setAttribute('aria-pressed', on); $(lab).textContent = on ? L.up : w; } }
$('bSit').onclick = () => rest('sit'); $('bLie').onclick = () => rest('lie');
let muted = false; $('bSound').onclick = () => { muted = !muted; audio.setMuted(muted); $('soundLabel').textContent = muted ? L.muted : L.sound; $('bSound').classList.toggle('on', muted); $('waves').style.display = muted ? 'none' : ''; };
$('vol').oninput = e => audio.setVolume(+e.target.value);
const seg = (ids, cb) => ids.forEach(([id, v]) => $(id).onclick = () => { ids.forEach(([x]) => $(x).classList.remove('on')); $(id).classList.add('on'); cb(v); });
seg([['spSlow', 1], ['spFast', 1.8]], v => state.speed = v); seg([['rL', .4], ['rS', .72], ['rH', 1]], v => { rainScale = v; }); seg([['t15', 15], ['t18', 18.2], ['t21', 21], ['t8', 8]], v => { hour = v; const s = game.st; if (v > 17 || v < 6) { s.bulbs = [1, 1, 1, 1, 1, 1]; s.lamps = 1; s.fire = v > 19 ? 1 : 0; } else { s.fire = 0; if (v === 8) s.birds = 1; } if (v !== 8) s.birds = 0; game.apply(); sheet(null); });
seg([['pHold', false], ['pAuto', true]], v => { game.b.auto = v; }); seg([['lS', 's'], ['lM', 'm'], ['lL', 'l']], v => game.b.len = v);
function setHud(on) { document.body.classList.toggle('nohud', !on); $('bHide').setAttribute('aria-checked', !on); if (!on) sheet(null); } $('bHide').onclick = () => setHud(false); $('show').onclick = () => setHud(true);
function sheet(id) { for (const [k, btn] of [['sheetRooms', 'bRooms'], ['sheetJournal', 'bJournal'], ['sheetSet', 'bSettings'], ['sheetIos', 'bFullTab']]) { const on = k === id; $(k).classList.toggle('open', on); if (k !== 'sheetIos') { $(btn).classList.toggle('on', on); $(btn).setAttribute('aria-expanded', on); } } $('scrim').classList.toggle('on', !!id); }
const tog = id => () => sheet($(id).classList.contains('open') ? null : id); $('bRooms').onclick = () => { buildTasks(); tog('sheetRooms')(); }; $('bJournal').onclick = () => { buildJournal(); tog('sheetJournal')(); }; $('bSettings').onclick = tog('sheetSet'); $('scrim').onclick = () => sheet(null); $('iosClose').onclick = () => sheet(null);
$('lEn').onclick = () => setLang('en'); $('lZh').onclick = () => setLang('zh'); $('langHome').onclick = () => setLang(lang === 'zh' ? 'en' : 'zh');
function buildTasks() { const r = $('rooms'); r.innerHTML = ''; ORDER.forEach((id, i) => { const b = document.createElement('button'); b.className = 'task' + (game.done[id] ? ' d' : '') + (i === game.nextIdx ? ' n' : ''); const c = document.createElement('i'); c.textContent = game.done[id] ? '✓' : ''; const t = document.createElement('span'); t.textContent = L.r[id][0]; b.append(c, t); if (i === game.nextIdx) { const s = document.createElement('small'); s.textContent = L.here; b.append(s); } b.onclick = () => { sheet(null); launch(id); }; r.append(b); }); }
function buildJournal() { const s = $('stats'); s.innerHTML = ''; for (const [v, l] of [[Math.round(stats.min), L.statMin], [stats.breaths, L.statBreath], [stats.nights, L.statNight]]) { const d = document.createElement('div'), b = document.createElement('b'); b.textContent = v; d.append(b, l); s.append(d); } const n = $('notes'); n.innerHTML = ''; for (const a of NOTES) { const d = document.createElement('div'); if (stats.noted[a[0]]) { const e = L.n[a[0]], m = document.createElement('small'); d.textContent = e[0]; m.textContent = e[1]; d.append(m); } else { d.className = 'un'; d.textContent = '· · ·'; } n.append(d); } }
// ---- eyes closed
let eyesShut = false, eyesT, wake = null;
async function keepAwake(on) { try { if (on && !wake && navigator.wakeLock) { wake = await navigator.wakeLock.request('screen'); wake.addEventListener('release', () => { wake = null; }); } else if (!on) { await wake?.release(); wake = null; } } catch { } }
function setEyes(shut) { if (shut === eyesShut) return; eyesShut = shut; const e = $('eyes'); clearTimeout(eyesT); sheet(null); if (shut) { e.classList.add('show'); requestAnimationFrame(() => requestAnimationFrame(() => e.classList.add('on'))); e.classList.remove('hint'); eyesT = setTimeout(() => { e.classList.add('hint'); eyesT = setTimeout(() => e.classList.remove('hint'), 4500); }, 3000); } else { e.classList.remove('on', 'hint'); eyesT = setTimeout(() => e.classList.remove('show'), 2800); } }
$('bEyes').onclick = () => setEyes(true); $('eyes').onclick = () => { audio.wake(); if (!sleeping) setEyes(false); }; document.addEventListener('visibilitychange', () => { if (!document.hidden && started) keepAwake(true); });
// ---- full screen
const fsEl = () => document.fullscreenElement ?? document.webkitFullscreenElement, fsCan = () => !!(document.documentElement.requestFullscreen || document.documentElement.webkitRequestFullscreen), standalone = () => matchMedia('(display-mode: fullscreen), (display-mode: standalone)').matches || navigator.standalone === true;
function fsSet(on) { const d = document.documentElement; if (on) (d.requestFullscreen ?? d.webkitRequestFullscreen)?.call(d)?.catch?.(() => { }); else (document.exitFullscreen ?? document.webkitExitFullscreen)?.call(document)?.catch?.(() => { }); }
const fsLabel = () => { const on = !!fsEl(); $('fsLabel').textContent = on ? L.exit : L.full; $('fsIn').style.display = on ? 'none' : ''; $('fsOut').style.display = on ? '' : 'none'; $('bFullTab').classList.toggle('on', on); }; document.addEventListener('fullscreenchange', fsLabel); document.addEventListener('webkitfullscreenchange', fsLabel);
$('bFullTab').onclick = () => { if (fsCan()) fsSet(!fsEl()); else sheet('sheetIos'); }; if (standalone()) $('bFullTab').style.display = 'none';
// ---- ritual flow, used by the game
function launch(id) {
  if (state.mode === 'rest') getUp(); $('prompt').classList.remove('on'); const t = TASKS[id], d = Math.hypot(t.at[0] - state.x, t.at[1] - state.z), go = () => { game.start(id); };
  if (d > 9) { dip(() => { state.x = t.at[0]; state.z = t.at[1]; go(); }, .7); } else go();
}
function dip(mid, s = 1) { const f = $('fade'); f.style.transition = `opacity ${s}s`; f.style.opacity = 1; setTimeout(() => { mid?.(); f.style.opacity = 0; }, s * 1000 + 80); }
let sleeping = false;
const ctx = {
  T, get W() { return W; }, get dogs() { return dogs; }, audio, get hour() { return hour; }, setHour,
  begin(t, id) { state.mode = 'ritual'; state.view = t.view; state.viewK = 0; document.body.classList.add('inrit'); $('prompt').classList.remove('on'); if (document.activeElement) document.activeElement.blur?.(); },
  ritualUI(on, name, line) { $('ritual').classList.toggle('on', !!on); if (on) { $('ritName').textContent = name; $('ritHint').textContent = game.b.auto ? '' : L.hold; } },
  ritualLine(l) { const e = $('ritLine'); e.style.opacity = 0; setTimeout(() => { e.textContent = l; e.style.opacity = 1; }, 450); },
  breathUI(b, n) { $('orb').style.transform = `scale(${.45 + .55 * b.lvl})`; $('ringP').style.strokeDashoffset = 339.3 * (1 - (n ? (b.i + (b.phase === 'out' ? b.k : 0)) / n : 0)); $('ringT').textContent = b.phase === 'in' ? L.in : b.phase === 'out' ? L.out : ''; if (state.mode === 'ritual') $('ritHint').textContent = b.useAuto() ? (b.fall && !b.auto ? L.noHold : '') : (b.phase === 'in' ? L.release : L.hold); if (b.total !== ctx.lastTot) { stats.breaths += (b.total - (ctx.lastTot ?? b.total)); ctx.lastTot = b.total; saveStats(); } },
  dip, free() { state.mode = null; state.view = null; document.body.classList.remove('inrit'); const dir = new THREE.Vector3(); cam.getWorldDirection(dir); state.yaw = Math.atan2(-dir.x, -dir.z); state.pitch = Math.asin(dir.y); state.x = cam.position.x; state.z = cam.position.z; if (!free(state.x, state.z)) { state.x = -.7; state.z = .2; if (game.st.rise < .5) { state.x = 4.1; state.z = 4.5; } } },
  offer(id) { const p = $('prompt'); $('pText').textContent = L.r[id][0]; $('pGo').textContent = L.start; p.classList.add('on'); $('pGo').onclick = () => launch(id); },
  sleepThrough(then) { sleeping = true; setEyes(true); game.st.dinner = 0; stats.nights++; saveStats(); let k = 0; const h0 = 22; const id = setInterval(() => { k += .05 / 14; hour = (h0 + k * 9.4) % 24; if (k > .55) game.st.lamps = game.st.lamps; if (k >= 1) { clearInterval(id); hour = 7.2; game.st.bulbs = [0, 0, 0, 0, 0, 0]; game.st.lamps = 0; game.st.fire = 0; game.st.birds = 1; game.st.brown = 0; game.st.meal = 'eaten'; game.apply(); sleeping = false; state.view = TASKS.sleep.view; setEyes(false); setTimeout(then, 2500); } }, 50); },
  endCard() { $('endBody').textContent = L.endBody.replace('{m}', Math.round(stats.min)).replace('{b}', stats.breaths); $('endCard').classList.add('on'); state.mode = 'end'; },
  save() { saveStats(); }
};
$('endStay').onclick = () => { $('endCard').classList.remove('on'); game.st.rise = 1; game.st.gear = 1; game.apply(); ctx.free(); state.x = 4.1; state.z = 4.5; };
$('endAgain').onclick = () => { $('endCard').classList.remove('on'); game.done = {}; game.nextIdx = 0; game.st.meal = null; game.st.cook = 0; Object.assign(game.st, { tomato: 1, avocado: 1, salad: 0, hob: 0, coffee: 0, birds: 0, dinner: 1, beer: 0, brown: 0 }); hour = 15; const M = W.move; for (const i of [0, 1, 2]) { M['steak' + i].rotation.x = 0; M['steak' + i].position.y = M['steak' + i].userData.home.p.y; } launch('raise'); };
$('ritSkip').onclick = () => { if (game.cur) { const b = game.b; b.i = b.n; b.phase = 'wait'; if (game.cur === 'raise') game.st.rise = 1; if (game.cur === 'lights') { game.st.bulbs = [1, 1, 1, 1, 1, 1]; game.st.lamps = 1; } if (game.cur === 'fire') game.st.fire = 1; if (game.cur === 'awning') game.st.tarp = 0; if (game.cur === 'grill') { game.st.beer = 1; game.st.brown = 1; } if (game.cur === 'pack') game.st.rise = 0; if (game.cur === 'salad') { game.st.salad = 1; game.st.tomato = 0; game.st.avocado = 0; } if (game.cur === 'sear') { game.st.cook = 1; } if (game.cur === 'coffee') game.st.coffee = 1; setHour(TASKS[game.cur].hour[1]); game.finish(); } };
// ---- start
async function enter(guided) {
  audio.unlock(); $('enter').disabled = $('enter2').disabled = true; $('load').textContent = MOBILE ? L.loadingPhone : L.loading;
  try {
    if (!W) { W = await buildWorld(scene, renderer, Q); dogs = await loadDogs(scene, Q, W.heightAt, W.env); addSmallThings(); await addModels(); W.hands = await loadHands(scene, W, { warm: W.camp.scale.warm, fire: W.camp.scale.fire }); initPost(); game = new Game(ctx); window.__W = W; window.__game = game; window.__dogs = dogs; }
    await audio.start().catch(e => console.warn('audio', e));
  } catch (e) { console.error(e); $('load').textContent = String(e); return; }
  const s = game.st; if (guided) { hour = 15; s.rise = 0; s.gear = 0; state.x = 4.1; state.z = 4.5; state.yaw = .8; game.apply(); } else { hour = params.has('hour') ? +params.get('hour') : 17.9; s.bulbs = [1, 1, 1, 1, 1, 1]; s.lamps = 1; s.fire = 0; game.nextIdx = 3; game.done.raise = game.done.lights = game.done.awning = 1; s.sleep = false; dogs.moss.state = 'lie'; dogs.birch.state = 'stand'; game.apply(); }
  $('home').classList.add('hide'); document.body.classList.add('playing'); $('enter').disabled = $('enter2').disabled = false; $('load').textContent = L.headphones; started = true; keepAwake(true); $('fade').style.opacity = 0; buildTasks(); buildJournal(); audio.resume();
  $('help').textContent = (matchMedia('(pointer:coarse)').matches ? L.helpTouch : L.helpMouse); setTimeout(() => $('help').style.opacity = 0, 9000);
  if (guided) setTimeout(() => launch('raise'), 2600); else ctx.offer('sear');
  renderer.setAnimationLoop(frame); window.__ready = true;
}
$('enter').onclick = () => enter(true); $('enter2').onclick = () => enter(false);
$('bHome').onclick = () => { sheet(null); setEyes(false); keepAwake(false); if (fsEl()) fsSet(false); audio.stop(); renderer.setAnimationLoop(null); started = false; document.body.classList.remove('playing', 'quiet', 'inrit'); $('ritual').classList.remove('on'); $('prompt').classList.remove('on'); $('home').classList.remove('hide'); $('fade').style.opacity = 1; game.cur = null; state.mode = null; };
if (navigator.xr) { navigator.xr.isSessionSupported('immersive-vr').then(ok => { if (ok) document.body.appendChild(VRButton.createButton(renderer, { optionalFeatures: ['local-floor'] })); }).catch(() => { }); }
function xrInput(dt) { const s = renderer.xr.getSession(); if (!s) return; for (const src of s.inputSources) { const g = src.gamepad; if (!g) continue; const ax = g.axes, x = ax[2] ?? 0, y = ax[3] ?? 0; if (src.handedness === 'left' && !state.mode) { const f = -y * 1.2 * dt, st = x * 1.2 * dt; const qy = new THREE.Euler().setFromQuaternion(cam.getWorldQuaternion(new THREE.Quaternion()), 'YXZ').y; move(-Math.sin(qy) * f + Math.cos(qy) * st, -Math.cos(qy) * f - Math.sin(qy) * st); } const tr = g.buttons[0]?.pressed; if (state.mode === 'ritual') { if (tr && !src.__dn) game.b.press(); if (!tr && src.__dn) game.b.release(); } src.__dn = tr; } }
// ---- every frame
const clock = new THREE.Clock(); let eyeLook = new THREE.Vector3(), stepSide = 0, tPlay = 0;
function frame() {
  const dt = Math.min(.05, clock.getDelta()), t = clock.elapsedTime; G.uTime.value = t; if (!game) return;
  xrInput(dt); game.update(dt); for (const d of Object.values(dogs)) d.update(dt, t, W);
  const xr = renderer.xr.isPresenting;
  // walk
  if (!state.mode) { const f = ((keys.KeyW || keys.ArrowUp) ? 1 : 0) - ((keys.KeyS || keys.ArrowDown) ? 1 : 0) + joy.y, st = ((keys.KeyD || keys.ArrowRight) ? 1 : 0) - ((keys.KeyA || keys.ArrowLeft) ? 1 : 0); state.yaw -= joy.x * 1.5 * dt; const sp = 1.45 * state.speed, m = Math.min(1, Math.hypot(f, st)), dx = (-Math.sin(state.yaw) * f + Math.cos(state.yaw) * st) * sp * dt, dz = (-Math.cos(state.yaw) * f - Math.sin(state.yaw) * st) * sp * dt; if (m > .05 && move(dx, dz)) { state.stepD += sp * m * dt; if (state.stepD > .72) { state.stepD = 0; stepSide ^= 1; audio.play('step' + (Math.random() * 4 | 0), .22, .9 + Math.random() * .2, stepSide ? .12 : -.12); } } }
  const gy = W.heightAt(state.x, state.z);
  if (!xr) {
    if (state.view) { state.viewK = Math.min(1, state.viewK + dt * .42); const k = state.viewK * state.viewK * (3 - 2 * state.viewK), v = state.view; if (state.viewK < 1) { cam.position.lerp(new THREE.Vector3(...v.p), k * .09 + .004); eyeLook.lerp(new THREE.Vector3(...v.l), k * .09 + .004); } else { cam.position.lerp(new THREE.Vector3(...v.p), .05); eyeLook.lerp(new THREE.Vector3(...v.l), .05); } const sway = Math.sin(t * .4) * .006; const brea = game.b.lvl * .012; cam.position.y += (sway + brea) * dt * 6; cam.lookAt(eyeLook); }
    else { const bob = Math.sin(state.stepD / .72 * Math.PI * 2) * .012 * ((joy.y || keys.KeyW) ? 1 : 0); cam.position.set(state.x, gy + 1.62 + bob, state.z); cam.rotation.set(state.pitch, state.yaw, 0, 'YXZ'); eyeLook.copy(cam.position).add(new THREE.Vector3(-Math.sin(state.yaw) * 3, Math.sin(state.pitch) * 3, -Math.cos(state.yaw) * 3)); }
    if (window.__shot) { const [x, y, z, yw, p] = window.__shot; cam.position.set(x, y, z); cam.rotation.set(p, yw, 0, 'YXZ'); }
    if (window.__hour !== undefined) manualHour = window.__hour;
  } else { const tgt = state.view ? state.view.p : [state.x, gy, state.z]; rig.position.set(tgt[0], state.view ? tgt[1] - 1.2 : tgt[1], tgt[2]); }
  game.reach?.(dt, t); cam.updateMatrixWorld(); W.hands.update(cam, dt);
  G.uCam.value.copy(cam.position); W.sky.position.copy(cam.position); if (W.fire.visible) for (const c of W.fireCards) c.rotation.y = Math.atan2(cam.position.x - c.position.x, cam.position.z - c.position.z);
  if (W.curtain) W.curtain.position.set(cam.position.x, 8, cam.position.z);
  updateLight(dt, t);
  const s = game.st, inT = inside(), rainNow = G.uRain.value, ins = (state.view && state.view.p[0] > -3 && state.view.p[0] < 2.4 && Math.abs(state.view.p[2]) < 1.6) ? 1 : inT, fd = Math.hypot(cam.position.x + .77, cam.position.z - .72);
  audio.mix(dt, { rain: rainNow, heavy: rainScale, inside: ins, wet: G.uWet.value, fire: s.fire * Math.min(.9, 1.1 / (1 + fd * fd * .5)), firePan: 0, sizzle: s.sizzle, grind: s.grind, birds: s.birds * (1 - rainNow), quiet: !!sleeping, onThunder() { flash = 1; } });
  updateSmoke(dt, Math.max(s.sizzle > .1 ? 1 : 0, game.cur === 'coffee' && game.b.i >= 3 ? .8 : 0), game.cur === 'coffee' ? -.9 : -2.47, game.cur === 'coffee' ? .63 : 1.03, game.cur === 'coffee' ? .6 : .38);
  flash = Math.max(0, flash - dt * 2.6); G.uSky.value.multiplyScalar(1 + flash * .7 * (Math.sin(t * 37) * .5 + .5));
  checkNotice(dt); if (started) { stats.min += dt / 60; tPlay += dt; if (tPlay > 20) { tPlay = 0; saveStats(); } }
  const name = $('nowName'); if (name) { const hr = manualHour ?? hour; const lbl = hr >= 6 && hr < 12 ? L.tMorning : hr < 17 ? L.tAfternoon : hr < 19 ? L.tDusk : L.tNight; if (name.textContent !== lbl) name.textContent = lbl; }
  if (composer && !xr) { const close = state.mode === 'ritual' && game.cur && !['raise', 'pack', 'awning'].includes(game.cur); bokeh.enabled = close; if (close) { bokeh.uniforms.focus.value = cam.position.distanceTo(eyeLook); } grade.uniforms.uT.value = t % 10; composer.render(dt); }
  else renderer.render(scene, cam);
}
if (params.get('auto')) enter(params.get('auto') === 'guided');
window.__state = state; window.__launch = id => launch(id);
