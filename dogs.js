// Two camp dogs. Bones are posed by hand; fur is a stack of shells that lift off the skin.
import * as THREE from 'three';
import { G } from './world.js';
const PARENT = { spine: 'hips', chest: 'spine', neck: 'chest', head: 'neck', muzzle: 'head', earl: 'head', earr: 'head', tail0: 'hips', tail1: 'tail0', tail2: 'tail1', tail3: 'tail2', fl0: 'chest', fl1: 'fl0', fl2: 'fl1', fl3: 'fl2', fr0: 'chest', fr1: 'fr0', fr2: 'fr1', fr3: 'fr2', bl0: 'hips', bl1: 'bl0', bl2: 'bl1', bl3: 'bl2', br0: 'hips', br1: 'br0', br2: 'br1', br3: 'br2' };
const furVS = `#include <common>
#include <skinning_pars_vertex>
uniform float uLayer,uLen; varying vec2 vU; varying vec3 vN; varying vec3 vP; varying vec3 vW;
void main(){ vU=uv; vP=position;
#include <skinbase_vertex>
  vec3 objectNormal=normal;
#include <skinnormal_vertex>
  vec3 transformed=position+normal*uLayer*uLen+vec3(0.,-.3,-.2)*uLayer*uLayer*uLen;
#include <skinning_vertex>
  vec4 w=modelMatrix*vec4(transformed,1.); vW=w.xyz; vN=normalize(mat3(modelMatrix)*objectNormal); gl_Position=projectionMatrix*viewMatrix*w; }`;
const furFS = `uniform float uLayer,uFogD,uDens,uWetF; uniform vec3 uSky,uFog,uWarmHere,uFireHere; uniform sampler2D uMap; varying vec2 vU; varying vec3 vN,vP,vW;
float h(vec3 p){return fract(sin(dot(p,vec3(127.1,311.7,74.7)))*43758.5453);}
void main(){ vec3 vC=texture2D(uMap,vU).rgb; if(uLayer>0.){ vec3 q=vP*uDens; q.z*=.38; vec3 c=floor(q); float s=h(c); vec2 f=fract(q.xz)-.5; if(s<uLayer*1.02||length(f)>(1.-uLayer)*.7) discard; float d0=length(vW-cameraPosition); if(d0>3.4) discard; }
  vec3 n=normalize(vN); float sh=.7+.3*n.y; float ao=mix(.86,1.02,uLayer); float st=sin(vP.z*170.+sin(vP.y*60.)*2.)*sin(vP.y*210.+vP.x*90.); vec3 alb=vC*mix(1.,.72,uWetF)*(1.+.05*st);
  vec3 v=normalize(cameraPosition-vW); float rim=pow(1.-max(dot(n,v),0.),3.); vec3 L=(uSky*sh*(.62+.45*rim)+uWarmHere*(.55+.45*n.y)+uFireHere*(.6+.4*n.y))*ao; float sp=pow(max(dot(n,normalize(v+vec3(0.,1.,0.))),0.),26.); vec3 col=alb*L+uSky*sp*.05*(.4+uWetF); float d=length(vW-cameraPosition); gl_FragColor=vec4(mix(col,uFog,1.-exp(-d*d*uFogD*uFogD)),1.);
#include <tonemapping_fragment>
#include <colorspace_fragment>
}`;
const ease = (a, b, k) => a + (b - a) * k;
function shadowBlob(scene, tex) { const m = new THREE.Mesh(new THREE.CircleGeometry(.55, 20).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false, color: 0x000000, opacity: .55 })); m.scale.set(.85, 1, 1.5); scene.add(m); return m; }
function blobTex() { const c = document.createElement('canvas'); c.width = c.height = 64; const x = c.getContext('2d'), g = x.createRadialGradient(32, 32, 2, 32, 32, 32); g.addColorStop(0, '#fff'); g.addColorStop(.5, '#fffa'); g.addColorStop(1, '#fff0'); x.fillStyle = g; x.fillRect(0, 0, 64, 64); return new THREE.CanvasTexture(c); }
export class Dog {
  constructor(name, meta, buf, scene, Q, heightAt, start, dens, fur, envMap) {
    const n = meta.nv, g = this.geo = new THREE.BufferGeometry(); let o = 0; const pad = v => (4 - v % 4) % 4;
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(buf, o, n * 3), 3)); o += n * 12;
    g.setAttribute('normal', new THREE.BufferAttribute(new Int8Array(buf, o, n * 3), 3, true)); o += n * 3 + pad(n * 3);
    g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(buf, o, n * 2), 2)); o += n * 8;
    g.setAttribute('skinIndex', new THREE.BufferAttribute(new Uint16Array(buf, o, n * 4), 4)); o += n * 8;
    g.setAttribute('skinWeight', new THREE.BufferAttribute(new Uint8Array(buf, o, n * 4), 4, true)); o += n * 4;
    g.setIndex(new THREE.BufferAttribute(new Uint32Array(buf, o, meta.ni), 1));
    const tex = new THREE.TextureLoader().load(`assets/models/${meta.tex}.webp`); tex.colorSpace = THREE.SRGBColorSpace; tex.flipY = false; tex.anisotropy = 8;
    this.bones = {}; const bs = meta.bones.map(b => { const x = new THREE.Bone(); x.name = b; this.bones[b] = x; return x; }); const J = meta.joints;
    const root = new THREE.Group(); this.root = root; root.add(this.bones.hips); this.bones.hips.position.fromArray(J.hips);
    for (const b of meta.bones) { const p = PARENT[b]; if (!p) continue; this.bones[p].add(this.bones[b]); this.bones[b].position.set(J[b][0] - J[p][0], J[b][1] - J[p][1], J[b][2] - J[p][2]); }
    root.updateMatrixWorld(true); const sk = new THREE.Skeleton(bs); scene.add(root); this.hips0 = this.bones.hips.position.clone();
    const layers = Q.mobile ? 1 : 7; this.u = { uWarmHere: { value: new THREE.Color() }, uFireHere: { value: new THREE.Color() }, uWetF: { value: 1 } }; this.meshes = [];
    for (let i = 0; i < layers; i++) {
      const m = new THREE.ShaderMaterial({ uniforms: { ...this.u, uMap: { value: tex }, uLayer: { value: i / layers }, uLen: { value: fur }, uDens: { value: dens }, uSky: G.uSky, uFog: G.uFog, uFogD: G.uFogD }, vertexShader: furVS, fragmentShader: furFS, side: i ? THREE.DoubleSide : THREE.FrontSide });
      const mesh = new THREE.SkinnedMesh(g, m); mesh.bind(sk, new THREE.Matrix4()); mesh.frustumCulled = false; root.add(mesh); this.meshes.push(mesh);
    }
    this.h = heightAt; this.x = start[0]; this.z = start[1]; this.yaw = start[2] ?? 0; this.state = 'lie'; this.pose = { sit: 0, lie: 1, sleep: 0, walk: 0, beg: 0 }; this.goal = null; this.phase = Math.random() * 7; this.wag = 0; this.t = Math.random() * 10; this.next = 4 + Math.random() * 8; this.name = name; this.S = meta.S; this.speed = 0;
    this.shadow = shadowBlob(scene, Dog.blob ??= blobTex());
  }
  go(x, z, then = 'stand') { this.goal = { x, z }; this.after = then; }
  set(state) { this.goal = null; this.state = state; }
  update(dt, t, world) {
    this.t += dt; const S = this.S; let want = this.state;
    if (this.goal) { const dx = this.goal.x - this.x, dz = this.goal.z - this.z, d = Math.hypot(dx, dz); if (d < .3) { this.state = this.after; this.goal = null; } else { want = 'walk'; const ty = Math.atan2(dx, dz); let dy = ty - this.yaw; dy = Math.atan2(Math.sin(dy), Math.cos(dy)); this.yaw += dy * Math.min(1, dt * 3.2); const sp = Math.min(1.25, d * 1.5) * (Math.abs(dy) > 1 ? .4 : 1); this.speed = sp; this.x += Math.sin(this.yaw) * sp * dt; this.z += Math.cos(this.yaw) * sp * dt; } }
    else { this.speed = 0; if (this.face) { let dy = Math.atan2(this.face[0] - this.x, this.face[1] - this.z) - this.yaw; dy = Math.atan2(Math.sin(dy), Math.cos(dy)); this.yaw += dy * Math.min(1, dt * 2.5); } }
    const P = this.pose, k = Math.min(1, dt * 3), tgt = { sit: want === 'sit' ? 1 : 0, lie: want === 'lie' || want === 'sleep' ? 1 : 0, sleep: want === 'sleep' ? 1 : 0, walk: want === 'walk' ? 1 : 0, beg: 0 }; for (const a in tgt) P[a] = ease(P[a], tgt[a], k);
    this.phase += dt * (3.5 + this.speed * 7.5); const ph = this.phase, B = this.bones, sw = P.walk * (.36 + this.speed * .22), Y = (b, x, y = 0, z = 0) => B[b].rotation.set(x, y, z);
    // legs: walking gait plus the folded poses
    const sL = Math.sin(ph), sR = Math.sin(ph + Math.PI), bL = Math.sin(ph + .9), bR = Math.sin(ph + .9 + Math.PI), lift = v => Math.max(0, Math.cos(v)) * .5 * P.walk;
    const hipD = P.sit * .29 * S + P.lie * .39 * S, tilt = -P.sit * .72 + P.lie * (.02), breathe = Math.sin(t * (P.sleep > .5 ? 1.5 : 2.4)) * .012;
    B.hips.position.y = this.hips0.y - hipD + Math.abs(Math.sin(ph)) * .012 * P.walk; B.hips.position.z = this.hips0.z + P.sit * .06;
    Y('hips', tilt + Math.sin(ph * 2) * .02 * P.walk, Math.sin(ph) * .05 * P.walk, Math.sin(ph) * .03 * P.walk); Y('spine', P.sit * .1 + breathe, 0, 0); Y('chest', P.sit * .08 - breathe);
    const fA = P.lie * -.95 + P.sit * .54, fB = P.lie * -.55, fC = P.lie * .1;
    Y('fl0', sL * sw + fA, 0, P.lie * .08); Y('fl1', -lift(ph) * .9 + fB - P.sit * .0, 0); Y('fl2', fC + lift(ph) * .3);
    Y('fr0', sR * sw + fA, 0, -P.lie * .08); Y('fr1', -lift(ph + Math.PI) * .9 + fB, 0); Y('fr2', fC + lift(ph + Math.PI) * .3);
    const hA = -P.sit * .62 - P.lie * 1.38, hB = P.sit * 2.35 + P.lie * 2.55, hC = -P.sit * 2.05 - P.lie * 1.95;
    Y('bl0', bL * sw + hA, 0, P.lie * .34 + P.sit * .12); Y('bl1', lift(bL) * .8 + hB); Y('bl2', hC - lift(bL) * .3);
    Y('br0', bR * sw + hA, 0, -P.lie * .34 - P.sit * .12); Y('br1', lift(bR) * .8 + hB); Y('br2', hC - lift(bR) * .3);
    // head and neck: looks up when sitting, rests on the paws when asleep
    const hx = -tilt * .85 * (1 - P.lie) + P.sleep * .85 + (this.look ? Math.sin(t * .4) * .08 : 0), hy = Math.sin(this.t * .35 + this.phase * .02) * .45 * (1 - P.sleep);
    const et = this.eat ? 1 : 0; this.eatK = (this.eatK ?? 0) + (et - (this.eatK ?? 0)) * Math.min(1, dt * 3); const ek = this.eatK; Y('neck', hx * .6 + P.walk * .12 + ek * (1.05 + Math.sin(t * 7) * .05), hy * .5 * (1 - ek), 0); Y('head', ek * .35 + hx * .4 + P.sleep * .25 - P.walk * .14 + Math.sin(ph * 2) * .02 * P.walk, hy * .5, 0);
    const pant = (1 - P.sleep) * .02; this.wag = ease(this.wag, this.happy ? 1 : .08 + P.walk * .35, dt * 2.5); if (this.happy) this.happy = Math.max(0, this.happy - dt);
    const w = Math.sin(t * 10) * this.wag * .75 * (1 - P.sleep); Y('tail0', -.25 + P.sit * .9 + P.lie * .55 - this.wag * .25, w); Y('tail1', .2, w * .7); Y('tail2', .15, w * .6);
    Y('earl', .1 * Math.sin(ph) * P.walk, 0, .08); Y('earr', .1 * Math.sin(ph) * P.walk, 0, -.08);
    const gy = this.h(this.x, this.z); this.root.position.set(this.x, gy, this.z); this.root.rotation.y = this.yaw; this.shadow.position.set(this.x, gy + .02, this.z); this.shadow.rotation.y = this.yaw;
    const inTent = Math.abs(this.x) < 2.4 && Math.abs(this.z) < 1.5, gl = Math.exp(-Math.hypot(this.x + 1, this.z - .3) / 3.2);
    this.u.uWarmHere.value.copy(G.uWarm.value).multiplyScalar(gl * .42); const fd = Math.hypot(this.x + .77, this.z - .72); this.u.uFireHere.value.copy(G.uFire.value).multiplyScalar(.5 / (1 + fd * fd * 1.4)); this.u.uWetF.value = inTent ? .25 : G.uWet.value;
  }
}
export async function loadDogs(scene, Q, heightAt, env) {
  const meta = await fetch('assets/dogs/dogs.json').then(r => r.json()), [a, b] = await Promise.all([fetch('assets/dogs/moss.bin').then(r => r.arrayBuffer()), fetch('assets/dogs/birch.bin').then(r => r.arrayBuffer())]);
  return { moss: new Dog('moss', meta.moss, a, scene, Q, heightAt, [1.3, -.3, -1.2], 460, .011, env), birch: new Dog('birch', meta.birch, b, scene, Q, heightAt, [-2.1, 4.6, 1.8], 560, .006, env) };
}
