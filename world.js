// The camp and forest: ground, pines, baked gear, sky, rain, fire and lights.
import * as THREE from 'three';
export const G = { uTime: { value: 0 }, uSky: { value: new THREE.Color() }, uFog: { value: new THREE.Color() }, uFogD: { value: .02 }, uWarm: { value: new THREE.Color() }, uFire: { value: new THREE.Color() }, uWet: { value: 1 }, uRain: { value: 1 }, uRise: { value: 1 }, uTop: { value: new THREE.Color() }, uEnv: { value: 1 }, uBulb: { value: [1, 1, 1, 1, 1, 1] }, uLamp: { value: 1 }, uWind: { value: .6 }, uCam: { value: new THREE.Vector3() }, uSpecFlash: { value: 0 } };
// Times of day. h is the hour; values are linear light.
const K = [
  { h: 0, sky: [.045, .058, .09], top: [.012, .017, .03], fog: [.009, .013, .024], fogd: .03, warm: 1, fire: 1, rain: 1, wet: 1 },
  { h: 4.8, sky: [.045, .058, .09], top: [.016, .022, .038], fog: [.011, .015, .026], fogd: .03, warm: 1, fire: 1, rain: .7, wet: 1 },
  { h: 6.2, sky: [.5, .56, .66], top: [.42, .47, .55], fog: [.3, .34, .39], fogd: .026, warm: .3, fire: .4, rain: .25, wet: 1 },
  { h: 8, sky: [1.9, 1.84, 1.62], top: [1.5, 1.62, 1.82], fog: [.62, .7, .62], fogd: .0095, warm: 0, fire: .1, rain: 0, wet: .75 },
  { h: 12, sky: [1.7, 1.76, 1.76], top: [1.3, 1.36, 1.42], fog: [.52, .6, .56], fogd: .017, warm: 0, fire: 0, rain: .6, wet: 1 },
  { h: 15, sky: [1.25, 1.34, 1.4], top: [.98, 1.06, 1.14], fog: [.38, .46, .45], fogd: .022, warm: 0, fire: 0, rain: 1, wet: 1 },
  { h: 17.4, sky: [.6, .68, .78], top: [.5, .56, .64], fog: [.22, .27, .29], fogd: .026, warm: .35, fire: .3, rain: 1, wet: 1 },
  { h: 18.6, sky: [.16, .2, .28], top: [.15, .19, .27], fog: [.075, .095, .14], fogd: .028, warm: .8, fire: .8, rain: 1, wet: 1 },
  { h: 19.6, sky: [.06, .075, .11], top: [.04, .053, .085], fog: [.02, .028, .044], fogd: .03, warm: 1, fire: 1, rain: 1, wet: 1 },
  { h: 24, sky: [.045, .058, .09], top: [.012, .017, .03], fog: [.009, .013, .024], fogd: .03, warm: 1, fire: 1, rain: 1, wet: 1 }];
const lerp = (a, b, t) => a + (b - a) * t;
const out_cook = { value: 0 }; export const cookU = out_cook;
export const light = { warm: 1, fire: 1, hour: 15, rainMix: 1, heavy: 1, flash: 0, extraWarm: 1 };
export function applyTime(hour, rainOverride) {
  let i = 0; while (i < K.length - 2 && K[i + 1].h <= hour) i++;
  const a = K[i], b = K[i + 1], t = (hour - a.h) / (b.h - a.h), s = t * t * (3 - 2 * t);
  const c = (n) => [0, 1, 2].map(j => lerp(a[n][j], b[n][j], s));
  G.uSky.value.setRGB(...c('sky')); G.uTop.value.setRGB(...c('top')); G.uFog.value.setRGB(...c('fog')); G.uFogD.value = lerp(a.fogd, b.fogd, s);
  const dark = lerp(a.warm, b.warm, s), fl = lerp(a.fire, b.fire, s);
  light.dark = dark; light.fireScale = fl; light.hour = hour;
  G.uRain.value = (rainOverride ?? lerp(a.rain, b.rain, s)); G.uWet.value = lerp(a.wet, b.wet, s);
}
// ---- textures
const loader = new THREE.TextureLoader();
function tex(url, srgb, rep = true) { const t = loader.load(url); t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace; if (rep) t.wrapS = t.wrapT = THREE.RepeatWrapping; t.anisotropy = 8; return t; }
// Shared chunk: exposure to the sky drives wetness. All baked things add light from these three stored amounts.
const fogFrag = `float fD=length(vW-cameraPosition);float fF=1.-exp(-fD*fD*uFogD*uFogD);`;
export function bakedMaterial(def, opts = {}) {
  const P = { color: new THREE.Color(...def.color), roughness: def.rough, metalness: def.metal ?? 0 };
  if (opts.map) P.map = opts.map; if (opts.normalMap) { P.normalMap = opts.normalMap; P.normalScale = new THREE.Vector2(.8, .8); }
  if (def.transparent) { P.transparent = true; P.opacity = 1 - def.transparent; P.depthWrite = false; P.side = THREE.DoubleSide; } else P.side = opts.double ? THREE.DoubleSide : THREE.FrontSide;
  P.envMap = opts.env; P.envMapIntensity = opts.envI ?? 1;
  const m = new THREE.MeshStandardMaterial(P); const tent = opts.tent, sc = opts.scale, name0 = '';
  m.onBeforeCompile = s => {
    Object.assign(s.uniforms, { uSky: G.uSky, uWarm: G.uWarm, uFire: G.uFire, uWet: G.uWet, uTime: G.uTime, uRise: G.uRise, uEnv: G.uEnv, uDrops: { value: opts.drops ?? null }, uCookMap: { value: opts.cook ?? null }, uCook: out_cook });
    s.vertexShader = s.vertexShader.replace('#include <common>', `#include <common>
      attribute vec3 bake; varying vec3 vBk; varying vec3 vWp; uniform float uRise;`)
      .replace('#include <begin_vertex>', `#include <begin_vertex>
      vBk = bake * bake;
      ${tent ? `{ float h = clamp(position.y / 3.2, 0., 1.); float k = smoothstep(0., 1., clamp(uRise * 1.25 - h * .25, 0., 1.));
        float nz = sin(position.x * 3.1 + position.z * 2.3) * .05 + sin(position.x * 7.3 - position.z * 5.1) * .025 + sin(position.y * 6. + position.x) * .03;
        vec3 flat_ = vec3(position.x * (.82 + h * .08) + sin(position.y * 3.) * .15, .05 + h * .22 + nz, position.z * (.8 + h * .08) + cos(position.y * 2.4) * .12);
        transformed = mix(flat_, transformed, k); }` : ''}`)
      .replace('#include <worldpos_vertex>', `#include <worldpos_vertex>
      vWp = (modelMatrix * vec4(transformed, 1.)).xyz;`);
    s.fragmentShader = s.fragmentShader.replace('#include <common>', `#include <common>
      varying vec3 vBk; varying vec3 vWp; uniform vec3 uSky, uWarm, uFire; uniform float uWet, uTime, uEnv; ${opts.drops ? 'uniform sampler2D uDrops;' : ''} ${opts.cook ? 'uniform sampler2D uCookMap; uniform float uCook;' : ''}`)
      .replace('#include <map_fragment>', `#include <map_fragment>
      ${opts.cook ? 'diffuseColor.rgb=mix(diffuseColor.rgb,texture2D(uCookMap,vMapUv).rgb,uCook);' : ''}
      ${opts.mud ? `{ float n=sin(vWp.x*9.+sin(vWp.y*14.)*1.5)*.5+sin(vWp.x*27.+vWp.y*9.)*.3; float m=smoothstep(.95,.48,vWp.y+n*.12); diffuseColor.rgb=mix(diffuseColor.rgb,vec3(.1,.06,.035),m*.72); }` : ''}`)
      .replace('#include <roughnessmap_fragment>', `#include <roughnessmap_fragment>
      float wetK = smoothstep(.22, .6, vBk.x) * uWet; roughnessFactor = mix(roughnessFactor, roughnessFactor * ${opts.wetRough ?? '.55'}, wetK); roughnessFactor = max(roughnessFactor, .05);
      diffuseColor.rgb *= mix(1., ${opts.wetDark ?? '.75'}, wetK);`)
      .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
      ${opts.drops ? `{ vec3 wn = normalize((vec4(normal, 0.) * viewMatrix).xyz); float up = abs(wn.y); vec2 q = up > .5 ? vWp.xz * 1.9 : vec2(vWp.x + vWp.z, vWp.y * .55 - uTime * .018) * 1.7;
        vec3 d = texture2D(uDrops, q).xyz * 2. - 1.; normal = normalize(normal + (viewMatrix * vec4(d.x, 0., d.y, 0.)).xyz * .55 * wetK); }` : ''}`)
      .replace('#include <lights_fragment_maps>', `#include <lights_fragment_maps>
      { vec3 wn = normalize((vec4(normal, 0.) * viewMatrix).xyz); float h = .74 + .26 * wn.y;
        ${opts.fill ? 'irradiance += uSky * ' + opts.fill + ' * PI;' : ''}
        ${opts.glow ? 'irradiance += uWarm * clamp((vWp.y + .2) / 2.6, .15, 1.) * ' + opts.glow + ' * PI;' : ''}
        irradiance += ((vBk.x + .05 + .1 * smoothstep(.2, 1.2, uSky.g)) * uSky * h + vBk.y * ${(sc?.warm ?? 1).toFixed(3)} * uWarm + vBk.z * ${(sc?.fire ?? 1).toFixed(3)} * uFire) * PI; }
      #ifdef USE_ENVMAP
      iblIrradiance = vec3(0.); radiance *= (.15 + .85 * smoothstep(.1, .55, vBk.x)) * uEnv;
      #endif`);
  };
  m.customProgramCacheKey = () => (tent ? 't' : 'n') + (opts.drops ? 'd' : '') + (opts.wetRough ?? '') + (opts.wetDark ?? '') + (opts.scale ? opts.scale.warm : '') + (opts.cook ? 'c' : '') + (opts.mud ? 'm' : '') + (opts.glow ?? '') + (opts.fill ?? '');
  return m;
}
function makeEnv(renderer) {
  const c = document.createElement('canvas'); c.width = 512; c.height = 256; const x = c.getContext('2d');
  const g = x.createLinearGradient(0, 0, 0, 256); g.addColorStop(0, '#9aa2a8'); g.addColorStop(.42, '#c6ccce'); g.addColorStop(.5, '#6f7a70'); g.addColorStop(.58, '#2d3424'); g.addColorStop(1, '#241a10'); x.fillStyle = g; x.fillRect(0, 0, 512, 256);
  for (let i = 0; i < 90; i++) { const px = Math.random() * 512, w = 1 + Math.random() * 5; x.fillStyle = `rgba(20,20,16,${.35 + Math.random() * .5})`; x.fillRect(px, 16 + Math.random() * 40, w, 110); }
  for (let i = 0; i < 300; i++) { x.fillStyle = `rgba(26,34,22,${.3 + Math.random() * .4})`; x.beginPath(); x.arc(Math.random() * 512, 10 + Math.random() * 70, 4 + Math.random() * 12, 0, 7); x.fill(); }
  const t = new THREE.CanvasTexture(c); t.mapping = THREE.EquirectangularReflectionMapping; t.colorSpace = THREE.SRGBColorSpace;
  const pm = new THREE.PMREMGenerator(renderer); const rt = pm.fromEquirectangular(t); pm.dispose(); t.dispose(); return rt.texture;
}
// ---- ground
export async function buildWorld(scene, renderer, Q) {
  const out = { move: {}, world: null };
  const env = out.env = makeEnv(renderer);
  const [W, heightBuf, tj, tbin, camp, cbin] = await Promise.all([fetch('assets/world.json').then(r => r.json()), fetch('assets/height.bin').then(r => r.arrayBuffer()), fetch('assets/trees/trees.json').then(r => r.json()), fetch('assets/trees/trees.bin').then(r => r.arrayBuffer()), fetch('assets/camp/camp.json').then(r => r.json()), fetch('assets/camp/camp.bin').then(r => r.arrayBuffer())]);
  out.world = W; const H = new Float32Array(heightBuf), N = W.n, S = W.size;
  const heightAt = out.heightAt = (x, z) => { const u = (x / S + .5) * (N - 1), v = (z / S + .5) * (N - 1), i = Math.max(0, Math.min(N - 2, u | 0)), j = Math.max(0, Math.min(N - 2, v | 0)), a = u - i, b = v - j; return (H[j * N + i] * (1 - a) + H[j * N + i + 1] * a) * (1 - b) + (H[(j + 1) * N + i] * (1 - a) + H[(j + 1) * N + i + 1] * a) * b; };
  // ground mesh: fine near the camp, coarse far away
  const seg = Q.mobile ? 160 : 256, gg = new THREE.PlaneGeometry(S, S, seg, seg).rotateX(-Math.PI / 2); { const p = gg.attributes.position; for (let i = 0; i < p.count; i++) p.setY(i, heightAt(p.getX(i), p.getZ(i))); gg.computeVertexNormals(); }
  const nd = tex('assets/tex/needles_c.webp', 1), ndn = tex('assets/tex/needles_n.webp'), grc = tex('assets/tex/grass_c.webp', 1), grn = tex('assets/tex/grass_n.webp'), muc = tex('assets/tex/mud_c.webp', 1), mun = tex('assets/tex/mud_n.webp'), rip = tex('assets/tex/ripple_n.webp'), splat = tex('assets/splat.png', 0, false), lm = tex('assets/camp/ground_lm.png', 0, false), drops = out.drops = tex('assets/tex/drops_n.webp');
  splat.wrapS = splat.wrapT = lm.wrapS = lm.wrapT = THREE.ClampToEdgeWrapping; lm.flipY = true;
  const gm = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 1, metalness: 0, envMap: env });
  const GM = camp.ground;
  gm.onBeforeCompile = s => {
    Object.assign(s.uniforms, { uN: { value: nd }, uNn: { value: ndn }, uGr: { value: grc }, uGn: { value: grn }, uMu: { value: muc }, uMn: { value: mun }, uRip: { value: rip }, uSplat: { value: splat }, uLm: { value: lm }, uSky: G.uSky, uWarm: G.uWarm, uFire: G.uFire, uWet: G.uWet, uTime: G.uTime, uRain: G.uRain, uRise: G.uRise, uEnv: G.uEnv });
    s.fragmentShader = s.fragmentShader.replace('#include <lights_fragment_begin>', THREE.ShaderChunk.lights_fragment_begin.replace('#if ( NUM_POINT_LIGHTS > 0 ) && defined( RE_Direct )', '#if 0'));
    s.vertexShader = s.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vWp;').replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvWp=(modelMatrix*vec4(transformed,1.)).xyz;');
    s.fragmentShader = s.fragmentShader.replace('#include <common>', `#include <common>
      varying vec3 vWp; uniform sampler2D uN,uNn,uGr,uGn,uMu,uMn,uRip,uSplat,uLm; uniform vec3 uSky,uWarm,uFire; uniform float uWet,uTime,uRain,uRise,uEnv; vec4 gLm; float gPud; vec3 gNor;
      vec4 tn(sampler2D t,vec2 p){ vec4 a=texture2D(t,p); vec2 q=mat2(.8,-.6,.6,.8)*p*.53+.31; vec4 b=texture2D(t,q); float m=smoothstep(.35,.65,texture2D(t,p*.09).g*1.6); return mix(a,b,.25+.5*m); }`)
      .replace('#include <map_fragment>', `
      vec2 sp=vWp.xz/${S.toFixed(1)}+.5; vec4 sl=texture2D(uSplat,vec2(sp.x,sp.y)); float eN=texture2D(uGr,vWp.xz/9.).g; float gr=smoothstep(.22,.82,sl.r+(eN-.4)*.5); float wr=sl.g; float pat=sl.b;
      vec3 c1=tn(uN,vWp.xz/1.9).rgb*(1.05+pat*.5)*vec3(1.32,.98,.72); vec3 n1=tn(uNn,vWp.xz/1.9).xyz*2.-1.;
      vec3 c2=tn(uGr,vWp.xz/2.2).rgb*vec3(.62,.82,.42); vec3 n2=tn(uGn,vWp.xz/2.2).xyz*2.-1.;
      vec3 c3=texture2D(uMu,vWp.xz/3.).rgb*.75; vec3 n3=texture2D(uMn,vWp.xz/3.).xyz*2.-1.;
      float gh=smoothstep(.0,.35,dot(c2,vec3(.3,.6,.1))-.2+sl.r*.3); float mixg=gr*(.6+.4*gh);
      vec3 alb=mix(c1,c2,mixg); alb=mix(alb,c3*(1.-.4*gr),wr*.8); vec3 nn=normalize(mix(mix(n1,n2,mixg),n3,wr*.8));
      float pud=smoothstep(.22,.6,sl.a+(c1.r-.3)*.2)*uWet; gPud=pud;
      diffuseColor.rgb=alb*mix(1.,.34,pud)*mix(1.,.7,uWet);
      vec2 lu=(vec2(vWp.x,-vWp.z)-vec2(${GM.x0.toFixed(1)},${GM.y0.toFixed(1)}))/${GM.size.toFixed(1)}; float inL=smoothstep(0.,.08,min(min(lu.x,lu.y),min(1.-lu.x,1.-lu.y)));
      vec4 l=texture2D(uLm,vec2(lu.x,lu.y)); l*=l; l.r=max(mix(l.a,l.r,smoothstep(.55,.98,uRise)),.14)*${GM.sky.toFixed(3)}; gLm=mix(vec4(.58,0.,0.,.58),l,inL);
      float rr=smoothstep(.02,.3,uRain);
      vec3 rp=texture2D(uRip,vWp.xz*.33+vec2(0.,uTime*.07)).xyz*2.-1.; vec3 rq=texture2D(uRip,vWp.xz*.41-vec2(uTime*.09,uTime*.03)).xyz*2.-1.;
      gNor=normalize(mix(nn,vec3((rp.xy+rq.xy)*.34*rr,1.),pud));`)
      .replace('#include <roughnessmap_fragment>', `float roughnessFactor=mix(mix(.62,.34,uWet),.14,pud)+.18*(1.-uWet);`)
      .replace('#include <metalnessmap_fragment>', 'float metalnessFactor=0.;')
      .replace('#include <normal_fragment_maps>', `normal=normalize((viewMatrix*vec4(gNor.x,gNor.z,-gNor.y,0.)).xyz);`)
      .replace('#include <lights_fragment_maps>', `#include <lights_fragment_maps>
      irradiance+=(gLm.r*uSky*(.92+.2*gNor.z)+(gLm.g*${GM.warm.toFixed(4)}+.006*exp(-length(vWp.xz+vec2(1.,-1.))/6.5))*uWarm*${(1 / .32).toFixed(3)}+gLm.b*${GM.fire.toFixed(4)}*uFire*${(1 / .32).toFixed(3)})*PI;
      iblIrradiance=vec3(0.); radiance*=(.2+.8*smoothstep(.2,.6,gLm.r))*uEnv*(.5+.2*gPud);
      vec3 vd=normalize(vViewPosition); float fr=pow(1.-max(dot(normal,vd),0.),3.); reflectedLight.indirectSpecular+=(gLm.g*${GM.warm.toFixed(4)}*uWarm*.5+gLm.b*${GM.fire.toFixed(4)}*uFire*.5)*(.06+fr*1.6+gPud*2.)*uWet;`);
  };
  const ground = new THREE.Mesh(gg, gm); ground.receiveShadow = false; scene.add(ground); out.ground = ground;
  // sky dome
  const sky = new THREE.Mesh(new THREE.SphereGeometry(400, 24, 16), new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false, fog: false, uniforms: { uTop: G.uTop, uFog: G.uFog, uTime: G.uTime }, vertexShader: 'varying vec3 vD;void main(){vD=normalize(position);vec4 p=projectionMatrix*modelViewMatrix*vec4(position,1.);gl_Position=p.xyww;}',
    fragmentShader: `varying vec3 vD;uniform vec3 uTop,uFog;uniform float uTime;
    float n(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);float a=fract(sin(dot(i,vec2(12.9,78.2)))*43758.5),b=fract(sin(dot(i+vec2(1,0),vec2(12.9,78.2)))*43758.5),c=fract(sin(dot(i+vec2(0,1),vec2(12.9,78.2)))*43758.5),d=fract(sin(dot(i+vec2(1,1),vec2(12.9,78.2)))*43758.5);return mix(mix(a,b,f.x),mix(c,d,f.x),f.y);}
    void main(){vec3 d=normalize(vD);float h=max(d.y,0.);vec2 q=d.xz/(h+.25)*1.4+uTime*.012;float c=n(q)*.5+n(q*2.1)*.3+n(q*4.3)*.2;vec3 col=mix(uFog,uTop*(.72+c*.55),smoothstep(0.,.24,h));gl_FragColor=vec4(col,1.);
#include <tonemapping_fragment>
    #include <colorspace_fragment>
    }` })); sky.frustumCulled = false; sky.renderOrder = -10; scene.add(sky); out.sky = sky;
  await buildTrees(scene, W, tj, tbin, Q, out, heightAt);
  await buildCamp(scene, camp, cbin, env, Q, out, heightAt);
  buildGrass(scene, W, Q, out, heightAt);
  buildRain(scene, Q, out);
  buildLights(scene, camp, Q, out);
  return out;
}
function makeGeo(buf, e, wantCol) {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(buf, e.p, e.nv * 3), 3));
  if (e.n !== undefined) g.setAttribute('normal', new THREE.BufferAttribute(new Float32Array(buf, e.n, e.nv * 3), 3));
  g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(buf, e.u, e.nv * 2), 2));
  if (e.c !== undefined && wantCol) g.setAttribute('ao', new THREE.BufferAttribute(new Float32Array(buf, e.c, e.nv), 1));
  g.setIndex(new THREE.BufferAttribute(new Uint32Array(buf, e.i, e.ni), 1)); return g;
}
const treeVS = wind => `attribute float ao; varying vec2 vU; varying vec3 vNw; varying float vA; varying vec3 vW; uniform float uTime, uWind;
void main(){ vU=uv; vA=${wind ? 'ao' : '1.'}; vec3 p=position; vec4 w=modelMatrix*instanceMatrix*vec4(p,1.); vNw=normalize(mat3(modelMatrix)*mat3(instanceMatrix)*normal);
  ${wind ? `float h=clamp(position.y/16.,0.,1.); float ph=instanceMatrix[3][0]*.13+instanceMatrix[3][2]*.17; w.x+=(sin(uTime*.9+ph)+.4*sin(uTime*2.1+ph*2.+p.y))*h*h*.32*uWind; w.z+=cos(uTime*.7+ph)*h*h*.2*uWind; float f=sin(uTime*3.3+p.x*3.+p.z*2.+ph)*.02*uWind; w.xyz+=f*vec3(1.,.5,1.);` : ''}
  vW=w.xyz; gl_Position=projectionMatrix*viewMatrix*w; }`;
const treeFS = `uniform sampler2D uMap; uniform vec3 uSky,uFog,uWarm,uCam,uTint; uniform float uFogD,uLift; varying vec2 vU; varying vec3 vNw; varying float vA; varying vec3 vW;
void main(){ vec4 t=texture2D(uMap,vU,-1.1); vec2 dx=dFdx(vU*2048.),dy=dFdy(vU*2048.); float lod=max(0.,.5*log2(max(dot(dx,dx),dot(dy,dy)))); float al=clamp((t.a*(1.+lod*.2)-.22)/.3,0.,1.); if(al<.05) discard; vec3 n=normalize(vNw); float s=.72+.28*n.y; float d=length(vW-cameraPosition); float gl=exp(-length(vW.xz+vec2(1.,0.))/6.5);
  vec3 c=t.rgb*uTint*vA*(uSky*s*uLift*.62+uWarm*gl*.07); float f=1.-exp(-d*d*uFogD*uFogD); gl_FragColor=vec4(mix(c,uFog,f),al);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}`;
function buildTrees(scene, W, tj, buf, Q, out, heightAt) {
  const dtex = tex('assets/trees/tufts.png', 1, false), farB = tex('assets/trees/pinebark_c.webp', 1), trunkC = tex('assets/trees/trunk_c.webp', 1), barkC = tex('assets/trees/bark_c.webp', 1);
  const mk = (map, wind, tint, lift, dbl) => new THREE.ShaderMaterial({ alphaToCoverage: !!dbl, side: dbl ? THREE.DoubleSide : THREE.FrontSide, uniforms: { uMap: { value: map }, uSky: G.uSky, uFog: G.uFog, uFogD: G.uFogD, uWarm: G.uWarm, uCam: G.uCam, uTime: G.uTime, uWind: G.uWind, uTint: { value: new THREE.Color(...tint) }, uLift: { value: lift } }, vertexShader: treeVS(wind), fragmentShader: treeFS });
  const card = mk(dtex, true, [.66, .68, .6], .95, true), trunk = mk(farB, false, [.55, .54, .52], 1.05), bark = mk(barkC, false, [.8, .72, .66], 1.05), farT = mk(farB, false, [.42, .42, .4], 1.);
  const place = (list, prefix, far) => {
    const by = [[], [], []]; for (const t of list) by[t.k].push(t);
    by.forEach((ls, k) => { if (!ls.length) return; const key = prefix + k, e = tj[key]; const parts = far ? [['lo', card, true], ['lotrunk', farT]] : [['cards', card, true], ['trunk', trunk], ['bark', bark]];
      for (const [p, m, w] of parts) { if (!e[p]) continue; const g = makeGeo(buf, e[p], w); if (p === 'cards' || p === 'lo') g.setAttribute('ao', new THREE.BufferAttribute(new Float32Array(buf, e[p].c, e[p].nv), 1));
        const im = new THREE.InstancedMesh(g, m, ls.length); const o = new THREE.Object3D(); ls.forEach((t, i) => { o.position.set(t.x, heightAt(t.x, t.z) - .05, t.z); o.rotation.y = t.r; o.scale.setScalar(t.s); o.updateMatrix(); im.setMatrixAt(i, o.matrix); }); im.frustumCulled = false; scene.add(im); } }); };
  const dist = t => Math.hypot(t.x + 2, t.z - 1), limit = Q.mobile ? 56 : 105;
  const near = Q.mobile ? 12 : 34, ts = W.trees.filter(t => dist(t) < limit), ss = W.saps;
  place(ts.filter(t => dist(t) < near), 'pine', false); place(ts.filter(t => dist(t) >= near), 'pine', true); place(ss.filter(t => dist(t) < near), 'sap', false); place(ss.filter(t => dist(t) >= near), 'sap', true);
}
async function buildCamp(scene, camp, buf, env, Q, out, heightAt) {
  out.camp = camp;
  const cache = {}, fabN = tex('assets/tex/fabric_n.webp'), woodC = tex('assets/tex/wood_c.webp', 1), woodN = tex('assets/tex/wood_n.webp'); fabN.repeat.set(1, 1);
  const sc = { warm: camp.scale.warm, fire: camp.scale.fire };
  const getMat = (name, tent) => { const key = name + (tent ? '_t' : ''); if (cache[key]) return cache[key]; const d = camp.mats[name] ?? { color: [.5, .5, .5], rough: .6 }, o = { env, scale: sc, tent, double: tent || /sleepbag|dogbed|mapping/.test(name) };
    if (d.food) { o.map = tex(`assets/tex/${d.food}_c.webp`, 1, false); o.map.flipY = false; if (d.food === 'steak') o.cook = tex('assets/tex/seared_c.webp', 1, false), o.cook.flipY = false; }
    if (d.map) o.map = tex('assets/camp/' + d.map, 1); if (d.nmap) o.normalMap = tex('assets/camp/' + d.nmap);
    if (d.map) { o.map.wrapS = o.map.wrapT = THREE.RepeatWrapping; o.map.flipY = false; if (o.normalMap) o.normalMap.flipY = false; }
    if (d.tile === 'fabric') o.normalMap = fabN; if (d.tile === 'wood') { o.map = woodC; o.normalMap = woodN; }
    if (/paint/.test(name)) { o.drops = out.drops; o.envI = 1.7; o.wetRough = '.75'; o.wetDark = '.92'; o.mud = true; } if (/roof/.test(name)) { o.drops = out.drops; o.envI = 1.2; o.wetRough = '.7'; o.wetDark = '.95'; } if (/beam/.test(name)) { o.envI = 2.4; o.wetRough = '.6'; o.wetDark = '.98'; } if (/fabric/.test(name)) { o.envI = .5; o.wetDark = '.95'; } if (/glass/.test(name)) { o.envI = 4; }
    if (/^paint$/.test(name)) o.scale = { warm: sc.warm * .3, fire: sc.fire }; if (/^(fabric|wallin|roof)$/.test(name)) { o.scale = { warm: sc.warm * 4.5, fire: sc.fire * 2 }; o.glow = name === 'roof' ? '.03' : '.15'; } if (name === 'beam') o.glow = '.05'; if (name === 'glass') { d.transparent = .22; d.rough = .05; d.color = [.008, .01, .012]; } if (name === 'tumbler') { d.color = [.25, .27, .26]; d.transparent = .9; o.envI = 2; } if (/^(cabin|seat)$/.test(name)) o.fill = '.1'; if (name === 'beam') d.rough = .5; if (name === 'stones') d.color = [.075, .07, .066]; if (name === 'slat') d.rough = .56; const cm = { tomato: [.34, .045, .03], avg: [.3, .36, .1], onionc: [.42, .2, .28] }; if (cm[name]) { d.color = cm[name]; d.rough = .42; } const dd = /^(fabric|roof|wallin|roofbag)$/.test(name) ? { ...d, color: d.color.map(c => c * 2.6) } : d; const m = bakedMaterial(dd, o); if (d.emit) { m.emissive = new THREE.Color(...d.color); m.emissiveIntensity = 0; m.userData.emit = d.emit; } m.name = name; return cache[key] = m; };
  const root = new THREE.Group(); scene.add(root); out.root = root; out.mats = cache; out.tentMeshes = [];
  const moves = out.move, inner = out.inner = new THREE.Group(); root.add(inner);
  for (const e of camp.groups) {
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(buf, e.p, e.nv * 3), 3)); g.setAttribute('normal', new THREE.BufferAttribute(new Int8Array(buf, e.n, e.nv * 3), 3, true)); g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(buf, e.u, e.nv * 2), 2)); g.setAttribute('bake', new THREE.BufferAttribute(new Uint8Array(buf, e.c, e.nv * 3), 3, true)); g.setIndex(new THREE.BufferAttribute(new Uint32Array(buf, e.i, e.ni), 1));
    const isTent = ['beams', 'fabric', 'roof', 'guy'].includes(e.name), mesh = new THREE.Mesh(g, getMat(e.mat, isTent)); mesh.frustumCulled = false;
    if (e.tag === 'move') { let o = moves[e.name]; if (!o) { o = moves[e.name] = new THREE.Group(); o.position.fromArray(e.pivot); o.userData.home = { p: o.position.clone(), q: o.quaternion.clone() }; root.add(o); } o.add(mesh); }
    else if (e.name === 'inside') inner.add(mesh); else if (e.name === 'gear') (out.gear ??= (() => { const g = new THREE.Group(); root.add(g); return g; })()).add(mesh); else root.add(mesh);
    if (/^(glass|net|tumbler|beer)$/.test(e.mat)) mesh.renderOrder = 5;
  }
}
function buildGrass(scene, W, Q, out, heightAt) {
  const c = document.createElement('canvas'), img = new Image(); img.src = 'assets/grassmap.png';
  const go = () => {
    c.width = c.height = W.n >> 1; const x = c.getContext('2d', { willReadFrequently: true }); x.drawImage(img, 0, 0, c.width, c.height); const dat = x.getImageData(0, 0, c.width, c.height).data; const g01 = (px, pz) => { const u = Math.floor((px / W.size + .5) * c.width), v = Math.floor((pz / W.size + .5) * c.height); return dat[(v * c.width + u) * 4] / 255; };
    // one clump: bent ribbons with a colour that runs from dark root to pale tip
    const blade = (n, H, w) => { const pos = [], col = [], idx = []; let v = 0; for (let b = 0; b < n; b++) { const a = Math.random() * 6.28, r = Math.random() * .1, bx = Math.cos(a) * r, bz = Math.sin(a) * r, dir = Math.random() * 6.28, h = H * (.6 + Math.random() * .6), lean = .2 + Math.random() * .5, sx = -Math.sin(dir) * w, sz = Math.cos(dir) * w, seg = 3; for (let i = 0; i <= seg; i++) { const t = i / seg, cx = bx + Math.cos(dir) * lean * t * t * h, cz = bz + Math.sin(dir) * lean * t * t * h, y = h * t * (1 - .25 * t), k = 1 - t * .9; pos.push(cx - sx * k, y, cz - sz * k, cx + sx * k, y, cz + sz * k); const sh = .34 + .46 * t; col.push(sh, sh, sh, sh, sh, sh); if (i < seg) idx.push(v, v + 1, v + 2, v + 1, v + 3, v + 2); v += 2; } } const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3)); g.setIndex(idx); return g; };
    const geo = blade(Q.mobile ? 4 : 6, .42, .014), n = Q.mobile ? 5000 : 30000, m = new THREE.ShaderMaterial({ side: THREE.DoubleSide, uniforms: { uSky: G.uSky, uFog: G.uFog, uFogD: G.uFogD, uTime: G.uTime, uWarm: G.uWarm, uWind: G.uWind }, vertexColors: true,
      vertexShader: `attribute vec3 tint; varying vec3 vC; varying vec3 vW; uniform float uTime,uWind; void main(){ vC=color*tint; vec4 w=modelMatrix*instanceMatrix*vec4(position,1.); float k=position.y*position.y*3.; float ph=w.x*.7+w.z*.9; w.x+=sin(uTime*1.3+ph)*k*.05*uWind; w.z+=cos(uTime*1.+ph)*k*.04*uWind; float dp=step(.97,fract(uTime*.31+ph*.13)); w.y-=dp*k*.02; vW=w.xyz; gl_Position=projectionMatrix*viewMatrix*w; }`,
      fragmentShader: `uniform vec3 uSky,uFog,uWarm; uniform float uFogD; varying vec3 vC; varying vec3 vW; void main(){ float d=length(vW-cameraPosition); float gl=exp(-length(vW.xz+vec2(1.,-1.))/5.); vec3 c=vC*(uSky+uWarm*gl*.12); gl_FragColor=vec4(mix(c,uFog,1.-exp(-d*d*uFogD*uFogD)),1.);
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
      }` });
    const tint = new Float32Array(n * 3), im = new THREE.InstancedMesh(geo, m, n), o = new THREE.Object3D(); let i = 0, tries = 0;
    while (i < n && tries++ < n * 14) { const px = -60 + Math.random() * 120, pz = 1 + Math.random() * 36, g = g01(px, pz); if (px > -8 && px < 2.7 && pz < 1.7) continue; if (g < .3 + Math.random() * .25) continue; o.position.set(px, heightAt(px, pz), pz); o.rotation.y = Math.random() * 6.28; const s = .5 + Math.random() * .8; o.scale.set(s, s * (.6 + Math.random() * .7), s); o.updateMatrix(); im.setMatrixAt(i, o.matrix); const v = .85 + Math.random() * .3, y = Math.random() * .22; tint.set([(.2 + y * .5) * v, (.33 + y * .1) * v, .1 * v], i * 3); i++; }
    im.count = i; geo.setAttribute('tint', new THREE.InstancedBufferAttribute(tint, 3)); im.frustumCulled = false; scene.add(im); out.grass = im;
  };
  if (img.complete) go(); else img.onload = go;
}
function buildRain(scene, Q, out) {
  // streaks in a box that follows the camera. Nothing falls through the tent roof or the car.
  const n = Q.mobile ? 3500 : 14000, seed = new Float32Array(n * 4 * 4), corner = new Float32Array(n * 4 * 2), idx = new Uint32Array(n * 6);
  for (let i = 0; i < n; i++) { const a = Math.random(), b = Math.random(), c = Math.random(), d = Math.random(); for (let k = 0; k < 4; k++) { seed.set([a, b, c, d], (i * 4 + k) * 4); corner.set([k === 0 || k === 3 ? -1 : 1, k < 2 ? 0 : 1], (i * 4 + k) * 2); } idx.set([i * 4, i * 4 + 1, i * 4 + 2, i * 4, i * 4 + 2, i * 4 + 3], i * 6); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(n * 4 * 3), 3)); g.setAttribute('seed', new THREE.BufferAttribute(seed, 4)); g.setAttribute('corner', new THREE.BufferAttribute(corner, 2)); g.setIndex(new THREE.BufferAttribute(idx, 1));
  const m = new THREE.ShaderMaterial({ transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, uniforms: { uTime: G.uTime, uCam: G.uCam, uSky: G.uTop, uWarm: G.uWarm, uRain: G.uRain, uFog: G.uFog },
    vertexShader: `attribute vec4 seed; attribute vec2 corner; uniform float uTime,uRain; uniform vec3 uCam; varying float vA; varying float vG; varying float vY;
    void main(){ const vec3 B=vec3(26.,16.,26.); float sp=7.5+seed.w*2.5; vec3 p=seed.xyz*B; p.y-=uTime*sp; p.x+=uTime*1.3; p.z+=uTime*.6;
      p=mod(p-uCam+B*.5,B)-B*.5+uCam; p.y=max(p.y,uCam.y-8.);
      float inT=step(-2.65,p.x)*step(p.x,2.65)*step(abs(p.z),1.75)*step(p.y,3.2); float inC=step(-7.2,p.x)*step(p.x,-2.8)*step(abs(p.z),1.05)*step(p.y,2.3);
      float on=step(seed.w*.96,uRain)*(1.-inT)*(1.-inC); vec3 dir=normalize(vec3(.17,-1.,.08)); vec3 wp=p+dir*corner.y*(.6+seed.w*.7);
      vec3 toCam=normalize(uCam-wp); vec3 side=normalize(cross(dir,toCam)); float d=length(uCam-wp); wp+=side*corner.x*(.0009+d*.00042);
      vA=corner.y*(1.-corner.y)*4.*on*smoothstep(1.2,4.,d)*smoothstep(22.,8.,d)*(.25+.75*seed.y*seed.y); vY=corner.x; vG=exp(-length(wp.xz+vec2(1.,0.))/4.5); gl_Position=projectionMatrix*viewMatrix*vec4(wp,1.); }`,
    fragmentShader: `uniform vec3 uSky,uWarm; varying float vA,vG,vY; void main(){ float k=1.-vY*vY; vec3 c=(uSky*.055+uWarm*vG*.13)*vA*k; gl_FragColor=vec4(c,1.);
    #include <colorspace_fragment>
    }` });
  const r = new THREE.Mesh(g, m); r.frustumCulled = false; r.renderOrder = 8; scene.add(r); out.rain = r;
  // a far curtain of rain
  const cg = new THREE.CylinderGeometry(17, 17, 26, 28, 1, true), cm = new THREE.ShaderMaterial({ side: THREE.BackSide, transparent: true, depthWrite: false, uniforms: { uTime: G.uTime, uRain: G.uRain, uSky: G.uFog }, vertexShader: 'varying vec2 vU;void main(){vU=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',
    fragmentShader: `varying vec2 vU;uniform float uTime,uRain;uniform vec3 uSky;float h(float x){return fract(sin(x*91.17)*43758.5);}
    void main(){ float a=0.; for(int i=0;i<2;i++){ float f=i==0?620.:310.; float x=vU.x*f; float id=floor(x); float sp=2.1+h(id)*.8; float y=fract(vU.y*2.2+uTime*sp*(i==0?.33:.2)+h(id+3.)); a+=smoothstep(.09,.0,abs(fract(x)-.5)*.5)*smoothstep(.0,.12,y)*smoothstep(.55,.12,y)*step(.5,h(id+7.)); }
      gl_FragColor=vec4(uSky*2.2+.015,a*.05*uRain*smoothstep(.0,.25,vU.y));
#include <colorspace_fragment>
    }` });
  const c = new THREE.Mesh(cg, cm); c.position.y = 8; c.frustumCulled = false; c.renderOrder = 7; if (!Q.mobile) scene.add(c); out.curtain = c;
  // splashes and rings on the ground and on the car and tent
  const ns = Q.mobile ? 280 : 1100, sg = new THREE.InstancedBufferGeometry(); sg.setAttribute('position', new THREE.Float32BufferAttribute([-1, 0, -1, 1, 0, -1, 1, 0, 1, -1, 0, 1], 3)); sg.setIndex([0, 2, 1, 0, 3, 2]); const sa = new Float32Array(ns * 3); for (let i = 0; i < ns; i++) sa.set([Math.random(), Math.random(), Math.random()], i * 3); sg.setAttribute('s', new THREE.InstancedBufferAttribute(sa, 3)); sg.instanceCount = ns;
  const sm = new THREE.ShaderMaterial({ transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, uniforms: { uTime: G.uTime, uCam: G.uCam, uSky: G.uTop, uRain: G.uRain }, vertexShader: `attribute vec3 s; uniform float uTime,uRain; uniform vec3 uCam; varying vec2 vU; varying float vA; void main(){ float T=uTime*(.9+s.z*.9)+s.z*40.; float cyc=floor(T); float t=fract(T); vec2 B=vec2(18.,18.); vec2 p=fract(s.xy+vec2(fract(sin(cyc*12.3+s.x)*91.),fract(sin(cyc*7.1+s.y)*67.)))*B-B*.5+uCam.xz; float inT=step(-2.65,p.x)*step(p.x,2.65)*step(abs(p.y),1.75); vec3 w=vec3(p.x,.04,p.y); float r=.006+t*.022; w.xz+=position.xz*r; vU=position.xz; vA=(1.-t)*(1.-inT)*step(s.x,uRain+.02); gl_Position=projectionMatrix*viewMatrix*vec4(w,1.); }`, fragmentShader: `uniform vec3 uSky; varying vec2 vU; varying float vA; void main(){ float d=length(vU); float k=smoothstep(.6,.84,d)*smoothstep(1.,.86,d); gl_FragColor=vec4(uSky*.05*k*vA,1.);
#include <colorspace_fragment>
  }` });
  const sp = new THREE.Mesh(sg, sm); sp.frustumCulled = false; sp.renderOrder = 6; sp.visible = true; scene.add(sp); out.splash = sp;
  // drips falling off the eaves of the tent
  const nd = 90, dg = new THREE.InstancedBufferGeometry(); dg.setAttribute('position', new THREE.Float32BufferAttribute([-1, 0, 0, 1, 0, 0, 1, 1, 0, -1, 1, 0], 3)); dg.setIndex([0, 1, 2, 0, 2, 3]); const da = new Float32Array(nd * 3); for (let i = 0; i < nd; i++) { const t = Math.random(), side = i % 4; da.set(side === 0 ? [-2.5 + t * 5, -1.66 * -1, Math.random()] : side === 1 ? [-2.5 + t * 5, -1.66, Math.random()] : side === 2 ? [2.56, -1.6 + t * 3.2, Math.random()] : [-1.9 + t * 4, 1.66, Math.random()], i * 3); } dg.setAttribute('d', new THREE.InstancedBufferAttribute(da, 3)); dg.instanceCount = nd;
  const dm = new THREE.ShaderMaterial({ transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, uniforms: { uTime: G.uTime, uCam: G.uCam, uSky: G.uTop, uRain: G.uRain, uWarm: G.uWarm, uRise: G.uRise }, vertexShader: `attribute vec3 d; uniform float uTime,uRain,uRise; uniform vec3 uCam; varying float vA; void main(){ float T=uTime*(.55+d.z*.5)+d.z*17.; float t=fract(T); vec3 w=vec3(d.x,2.42-4.9*t*t*1.05,d.y); w.y=max(w.y,.02); vec3 r=normalize(cross(vec3(0.,1.,0.),uCam-w)); w+=r*position.x*.0028+vec3(0.,1.,0.)*position.y*.16; vA=step(.02,uRain+.0)*step(.98,uRise)*step(.04,w.y); gl_Position=projectionMatrix*viewMatrix*vec4(w,1.); }`, fragmentShader: `uniform vec3 uSky,uWarm; varying float vA; void main(){ gl_FragColor=vec4((uSky*.05+uWarm*.02)*vA,1.);
#include <colorspace_fragment>
  }` });
  const dr = new THREE.Mesh(dg, dm); dr.frustumCulled = false; dr.renderOrder = 7; scene.add(dr); out.drips = dr;
}
function glowTexture() { const c = document.createElement('canvas'); c.width = c.height = 128; const x = c.getContext('2d'), g = x.createRadialGradient(64, 64, 0, 64, 64, 64); g.addColorStop(0, '#ffffff'); g.addColorStop(.07, '#ffe0b0'); g.addColorStop(.16, '#ffb466aa'); g.addColorStop(.42, '#b4602822'); g.addColorStop(1, '#00000000'); x.fillStyle = g; x.fillRect(0, 0, 128, 128); return new THREE.CanvasTexture(c); }
export const flameMat = () => new THREE.ShaderMaterial({ transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide, uniforms: { uTime: G.uTime, seed: { value: Math.random() * 50 }, uOn: { value: 1 } },
  vertexShader: `varying vec2 vU; void main(){ vU=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
  fragmentShader: `varying vec2 vU; uniform float uTime,seed,uOn; float n(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);float a=fract(sin(dot(i,vec2(12.9,78.2)))*43758.5),b=fract(sin(dot(i+vec2(1,0),vec2(12.9,78.2)))*43758.5),c=fract(sin(dot(i+vec2(0,1),vec2(12.9,78.2)))*43758.5),d=fract(sin(dot(i+vec2(1,1),vec2(12.9,78.2)))*43758.5);return mix(mix(a,b,f.x),mix(c,d,f.x),f.y);}
    void main(){ vec2 p=vU; float t=uTime*1.6+seed; float q=n(vec2(p.x*5.+seed,p.y*2.6-t*1.5))*.5+n(vec2(p.x*11.-seed,p.y*5.-t*2.6))*.28; float w=.5-abs(p.x-.5+(q-.4)*.22*p.y); float h=1.-p.y; float f=smoothstep(0.,.4,w-.38*(p.y*p.y)-.5*p.y*(1.-q*1.2)*.42)*h; f=pow(max(f,0.),1.2);
      vec3 c=mix(vec3(.9,.14,.015),vec3(1.,.55,.08),smoothstep(.1,.5,f)); c=mix(c,vec3(1.,.9,.6),smoothstep(.45,.9,f)); vec3 blue=vec3(.05,.15,.8)*smoothstep(.2,.0,p.y)*f*1.4; gl_FragColor=vec4(c*f*.34*uOn,1.);
#include <colorspace_fragment>
    }` });
function buildLights(scene, camp, Q, out) {
  const glow = out.glow = glowTexture(), b = camp.bulbs, n = b.length;
  const g = new THREE.InstancedBufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute([-1, -1, 0, 1, -1, 0, 1, 1, 0, -1, 1, 0], 3)); g.setIndex([0, 1, 2, 0, 2, 3]); const a = new Float32Array(n * 4); b.forEach((p, i) => a.set([p[0], p[1], p[2], p[3]], i * 4)); g.setAttribute('b', new THREE.InstancedBufferAttribute(a, 4)); g.instanceCount = n;
  const m = new THREE.ShaderMaterial({ transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, uniforms: { uMap: { value: glow }, uBulb: G.uBulb, uTime: G.uTime, uRise: G.uRise }, vertexShader: `attribute vec4 b; uniform float uBulb[6]; uniform float uTime,uRise; varying vec2 vU; varying float vA; void main(){ vU=position.xy*.5+.5; vec4 mv=viewMatrix*vec4(b.xyz,1.); vA=uBulb[int(b.w+.5)]*(.9+.1*sin(uTime*2.+b.x*7.))*step(.98,uRise); float s=.085; mv.xy+=position.xy*s; gl_Position=projectionMatrix*mv; }`, fragmentShader: `uniform sampler2D uMap; varying vec2 vU; varying float vA; void main(){ vec4 t=texture2D(uMap,vU); gl_FragColor=vec4(t.rgb*t.a*vA*1.15,1.);
#include <colorspace_fragment>
  }` });
  const bm = new THREE.Mesh(g, m); bm.frustumCulled = false; bm.renderOrder = 9; scene.add(bm); out.bulbs = bm;
  // lantern and car lamp halos
  const halo = (x, y, z, s, col, key) => { const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: glow, color: col, blending: THREE.AdditiveBlending, transparent: true, depthWrite: false, depthTest: true })); sp.position.set(x, y, z); sp.scale.setScalar(s); sp.renderOrder = 9; scene.add(sp); sp.userData.key = key; sp.userData.col = new THREE.Color(col); return sp; };
  out.halos = [halo(-2.0, 1.0, 0.62, .5, 0xffb060, 'lamp'), halo(-1.42, .53, .95, .4, 0xffb060, 'lamp'), halo(-2.38, 2.03, 1.67, .85, 0xffa050, 'lamp'), halo(1.3, 1.42, -1.25, .5, 0xffb060, 'lamp')];
  // fire: quads inside the glass box
  const fg = new THREE.Group(), fx = -.77, fz = .72, fy = .50; const mats = [];
  for (let i = 0; i < 9; i++) { const f = flameMat(), w = .11 + Math.random() * .08, h = .12 + Math.random() * .12, q = new THREE.Mesh(new THREE.PlaneGeometry(w, h).translate(0, h / 2, 0), f); q.position.set(fx - .14 + Math.random() * .28, fy - .02, fz - .08 + Math.random() * .16); q.rotation.y = Math.random() * 3.14; fg.add(q); mats.push(f); }
  for (let i = 0; i < 4; i++) { const f = flameMat(), w = .09, h = .15, q = new THREE.Mesh(new THREE.PlaneGeometry(w, h).translate(0, h / 2, 0), f); q.position.set(fx - .09 + i * .06, fy, fz); q.rotation.y = 1.57; fg.add(q); mats.push(f); }
  fg.traverse(o => { o.frustumCulled = false; o.renderOrder = 10; }); out.fireCards = fg.children; scene.add(fg); out.fire = fg; out.fireMats = mats;
  const pl = out.kitchenLight = new THREE.PointLight(0xffa860, 0, 4.2, 1.6); pl.position.set(-2.4, 1.45, .25); scene.add(pl); const pf = out.fireLight = new THREE.PointLight(0xff8a3c, 0, 5, 1.7); pf.position.set(fx, fy + .25, fz); scene.add(pf);
  const fh = halo(fx, fy + .14, fz, .8, 0xff8a30, 'fire'); out.fireHalo = fh; out.halos.push(fh);
}
