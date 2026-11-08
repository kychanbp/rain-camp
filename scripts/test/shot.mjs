// Usage: node shot.mjs out page hour "x,y,z,yaw,pitch" ...
import { chromium } from 'playwright-core';
import http from 'http'; import fs from 'fs'; import path from 'path';
const WEB = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../../web');
const types = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.webp': 'image/webp', '.m4a': 'audio/mp4', '.mp3':'audio/mpeg', '.bin': 'application/octet-stream' };
const srv = http.createServer((q, r) => { const p = path.join(WEB, decodeURIComponent(q.url.split('?')[0]).replace(/\/$/, '/index.html')); fs.readFile(p, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' }); r.end(d); }); }).listen(8791);
const [out, page, ...views] = process.argv.slice(2); const SETUP = process.env.SETUP;
const b = await chromium.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: false, args: ['--use-angle=metal', '--window-size=1400,850'] });
const p = await b.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 2 });
p.on('console', m => { const t = m.text(); if (m.type() === 'error' || (m.type() === 'warning' && /shader|THREE|WebGL/i.test(t))) console.log('[' + m.type() + ']', t.slice(0, 1800)); });
p.on('pageerror', e => console.log('[pageerror]', e.message));
await p.goto(`http://localhost:8791/${page}`);
await p.waitForFunction('window.__ready===true', null, { timeout: 90000 }).catch(e => console.log('not ready'));
await p.waitForTimeout(2500);
await p.evaluate(()=>{for(const i of ['fade','help','prompt','now','tabs','pad'])document.getElementById(i)&&(document.getElementById(i).style.display='none');document.getElementById('home')?.remove()});
if (SETUP) await p.evaluate(SETUP); await p.waitForTimeout(+process.env.WAIT || 0);
for (let i = 0; i < views.length; i++) {
  const [h, ...v] = views[i].split(',').map(Number);
  await p.evaluate(([h, v]) => { window.__hour = h; window.__shot = v; }, [h, v]);
  await p.waitForTimeout(1200);
  const f = `${out}_${i}.jpg`; await p.screenshot({ path: f, type: 'jpeg', quality: 88 }); console.log('saved', f);
}
console.log(JSON.stringify(await p.evaluate(() => ({ calls: __renderer.info.render.calls, tris: __renderer.info.render.triangles }))));
await b.close(); srv.close();
