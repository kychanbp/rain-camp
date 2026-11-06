// Usage: node task.mjs out hour task1,task2 ... Jumps into tasks and photographs them part way through.
import { chromium } from 'playwright-core';
import http from 'http'; import fs from 'fs'; import path from 'path';
const WEB = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../../web');
const types = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.webp': 'image/webp', '.m4a': 'audio/mp4', '.bin': 'application/octet-stream' };
const srv = http.createServer((q, r) => { const p = path.join(WEB, decodeURIComponent(q.url.split('?')[0]).replace(/\/$/, '/index.html')); fs.readFile(p, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' }); r.end(d); }); }).listen(8794);
const [out, tasks] = process.argv.slice(2);
const b = await chromium.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: false, args: ['--use-angle=metal', '--autoplay-policy=no-user-gesture-required', '--window-size=1400,850'] });
const p = await b.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 2 });
p.on('console', m => { if (m.type() === 'error') console.log('[err]', m.text().slice(0, 900)); }); p.on('pageerror', e => console.log('[pageerror]', e.message));
await p.goto('http://localhost:8794/index.html?auto=free'); await p.waitForFunction('window.__ready===true', null, { timeout: 120000 }); await p.waitForTimeout(1500);
await p.evaluate(() => { __game.b.auto = true; __game.b.lens.m = [2.5, 3]; for (const i of ['help']) document.getElementById(i).style.display = 'none'; });
for (const t of tasks.split(',')) {
  const [id, at] = t.split(':'); await p.evaluate(id => { const g = __game; if (id === 'coffee') { g.st.dinner = 0; } if (id === 'grill' || id === 'fire') { g.st.fire = 1; } __launch(id); }, id);
  await p.waitForFunction(n => __game.b.i >= n, +(at ?? 1), { timeout: 60000 }).catch(() => console.log('slow', id)); await p.waitForTimeout(2200);
  await p.screenshot({ path: `${out}_${id}.jpg`, type: 'jpeg', quality: 85 }); console.log('shot', id);
  await p.evaluate(() => { document.getElementById('ritSkip').click(); }); await p.waitForTimeout(1800);
}
await b.close(); srv.close();
