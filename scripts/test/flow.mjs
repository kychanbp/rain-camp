// Plays the whole evening with the fastest breath, capturing a picture of each task.
import { chromium } from 'playwright-core';
import http from 'http'; import fs from 'fs'; import path from 'path';
const WEB = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../../web');
const types = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.webp': 'image/webp', '.m4a': 'audio/mp4', '.bin': 'application/octet-stream' };
const srv = http.createServer((q, r) => { const p = path.join(WEB, decodeURIComponent(q.url.split('?')[0]).replace(/\/$/, '/index.html')); fs.readFile(p, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' }); r.end(d); }); }).listen(8792);
const out = process.argv[2], viewport = JSON.parse(process.argv[3] ?? '{"width":1280,"height":720}'), q = process.argv[4] ?? '';
const b = await chromium.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: false, args: ['--use-angle=metal', '--autoplay-policy=no-user-gesture-required', '--window-size=1400,850'] });
const p = await b.newPage({ viewport, deviceScaleFactor: 2 });
p.on('console', m => { if (m.type() === 'error') console.log('[err]', m.text().slice(0, 1200)); }); p.on('pageerror', e => console.log('[pageerror]', e.message));
await p.goto(`http://localhost:8792/index.html?auto=guided${q}`);
await p.waitForFunction('window.__ready===true', null, { timeout: 120000 }).catch(() => console.log('not ready'));
await p.evaluate(() => { const g = __game; g.b.tapLen = [.4, .6]; });
const seen = {}; const t0 = Date.now();
for (let k = 0; k < 700 && Date.now() - t0 < 420000; k++) {
  const st = await p.evaluate(() => ({ cur: __game.cur, i: __game.b.i, n: __game.b.n, idx: __game.nextIdx, end: document.getElementById('endCard').classList.contains('on'), prompt: document.getElementById('prompt').classList.contains('on'), eyes: document.getElementById('eyes').classList.contains('on'), }));
  if (st.cur) { const key = st.cur + (st.i >= st.n - 1 ? '_b' : st.i >= 1 ? '_a' : ''); if (!seen[key] && (st.i >= 1 || false)) { seen[key] = 1; await p.waitForTimeout(st.i ? 500 : 1800); await p.screenshot({ path: `${out}_${key}.jpg`, type: 'jpeg', quality: 86 }); console.log('shot', key); } }
  if (st.end) { await p.screenshot({ path: `${out}_end.jpg`, type: 'jpeg', quality: 86 }); console.log('END'); break; }
  if (st.prompt && !st.cur) { await p.click('#pGo'); }
  if (st.cur) { const ok = await p.evaluate(() => { const b = document.getElementById('act'); if (b && !b.disabled && b.offsetParent) { b.click(); return 1; } return 0; }); }
  await p.waitForTimeout(250);
}
const info = await p.evaluate(() => ({ calls: __renderer.info.render.calls, tris: __renderer.info.render.triangles, done: Object.keys(__game.done), breaths: __game.b.total }));
console.log(JSON.stringify(info)); await b.close(); srv.close();
