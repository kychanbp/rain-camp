// Generated 3D objects and the camper's hands.
import * as THREE from 'three';
import { bakedMaterial } from './world.js';
const loader = new THREE.TextureLoader();
export function bakeAttr(g, sky, warm = .3, fire = .05) { const n = g.attributes.position.count, a = new Uint8Array(n * 3); for (let i = 0; i < n; i++) { a[i * 3] = Math.sqrt(sky) * 255; a[i * 3 + 1] = Math.sqrt(warm * .05) * 255; a[i * 3 + 2] = Math.sqrt(fire * .05) * 255; } g.setAttribute('bake', new THREE.BufferAttribute(a, 3, true)); return g; }
export async function loadModels(W, scale) {
  const meta = await fetch('assets/models/models.json').then(r => r.json()), out = {}; const names = Object.keys(meta);
  await Promise.all(names.map(async k => { const e = meta[k], buf = await fetch(`assets/models/${k}.bin`).then(r => r.arrayBuffer()), g = new THREE.BufferGeometry(); let o = 0; g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(buf, o, e.nv * 3), 3)); o += e.nv * 12; g.setAttribute('normal', new THREE.BufferAttribute(new Int8Array(buf, o, e.nv * 3), 3, true)); o += e.nv * 3; o += (4 - o % 4) % 4; g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(buf, o, e.nv * 2), 2)); o += e.nv * 8; g.setIndex(new THREE.BufferAttribute(new Uint32Array(buf, o, e.ni), 1)); const t = loader.load(`assets/models/${k}.webp`); t.colorSpace = THREE.SRGBColorSpace; t.flipY = false; t.anisotropy = 8; out[k] = { geo: g, tex: t, e }; }));
  const mats = {};
  // size is the longest side in metres; rot turns the model from picture pose to its place in the world
  return (k, { size, rot = [0, 0, 0], pos = [0, 0, 0], flat = false, tint = 0, sky = .3, warm = .25, fire = .05, rough = .5, metal = 0, env = 1 }) => {
    const m = out[k]; if (!m) return null; const g = bakeAttr(m.geo.clone(), sky, warm, fire); if (flat) g.translate(0, -m.e.ext[1] / 2, 0); const key = k + rough + metal + env + tint;
    const mat = mats[key] ??= bakedMaterial({ color: [1, 1, 1], rough, metal }, { env: W.env, envI: env, map: m.tex, scale, double: false }); if (tint) mat.color.setRGB(tint, tint, tint);
    const me = new THREE.Mesh(g, mat); me.scale.setScalar(size); me.rotation.set(...rot); me.position.set(...pos); me.frustumCulled = false; return me;
  };
}
export async function loadHands(scene, W, scale) {
  const meta = await fetch('assets/hands/hands.json').then(r => r.json()), buf = await fetch('assets/hands/hands.bin').then(r => r.arrayBuffer()), t = loader.load('assets/hands/body_c.webp'), n = loader.load('assets/hands/body_n.webp'); t.colorSpace = THREE.SRGBColorSpace; t.flipY = false; n.flipY = false;
  const mat = bakedMaterial({ color: [.95, .86, .8], rough: .55 }, { env: W.env, envI: .5, map: t, normalMap: n, scale, double: true }), H = {};
  for (const side of 'RL') { const g0 = new THREE.Group(); g0.visible = false; g0.userData = { k: 0, want: 0 }; for (const pose of ['grip', 'relax']) { const e = meta[`${side}_${pose}`], g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(buf, e.p, e.nv * 3), 3)); g.setAttribute('normal', new THREE.BufferAttribute(new Float32Array(buf, e.n, e.nv * 3), 3)); g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(buf, e.u, e.nv * 2), 2)); bakeAttr(g, .35, .35, .1); const me = new THREE.Mesh(g, mat); me.frustumCulled = false; me.visible = pose === 'relax'; me.name = pose; g0.add(me); } { const g = bakeAttr(new THREE.CylinderGeometry(.06, .045, .7, 16, 1, true).rotateZ(Math.PI / 2), .35, .35, .1), uv = g.attributes.uv; const m = bakedMaterial({ color: [.075, .085, .04], rough: .75 }, { env: W.env, envI: .3, scale, double: true }), c = new THREE.Mesh(g, m); c.position.x = -.41; c.frustumCulled = false; g0.add(c); } scene.add(g0); H[side] = g0; }
  const tgt = {}, x = new THREE.Vector3(), y = new THREE.Vector3(), z = new THREE.Vector3(), m4 = new THREE.Matrix4(), q = new THREE.Quaternion();
  // Reach: wrist goes to p, forearm comes up from below the camera. Call each frame with the wanted hands.
  return {
    want(side, p, pose = 'grip', roll = 0) { tgt[side] = { p, pose, roll }; },
    update(cam, dt) { for (const s of 'RL') { const h = H[s], w = tgt[s]; h.userData.want = w ? 1 : 0; h.userData.k += (h.userData.want - h.userData.k) * Math.min(1, dt * 3); h.visible = h.userData.k > .01; if (!h.visible) continue; const sign = s === 'R' ? 1 : -1, r = new THREE.Vector3(1, 0, 0).applyQuaternion(cam.quaternion), u = new THREE.Vector3(0, 1, 0).applyQuaternion(cam.quaternion), f = new THREE.Vector3(0, 0, -1).applyQuaternion(cam.quaternion), el = cam.position.clone().addScaledVector(r, sign * .38).addScaledVector(u, -.52).addScaledVector(f, -.05), off = el.clone().addScaledVector(f, .1).addScaledVector(u, -.2); if (w) { h.userData.p ??= w.p.clone(); h.userData.p.lerp(w.p, Math.min(1, dt * 6)); for (const c of h.children) if (c.name) c.visible = c.name === w.pose; } const pt = (h.userData.p ?? off).clone().lerp(off, 1 - h.userData.k); x.copy(pt).sub(el).normalize(); y.set(0, 1, 0).applyAxisAngle(x, w?.roll ?? 0); z.crossVectors(x, y).normalize(); y.crossVectors(z, x); m4.makeBasis(x, y, z); q.setFromRotationMatrix(m4); h.quaternion.copy(q); h.position.copy(pt); } for (const k in tgt) delete tgt[k]; }
  };
}
