import { chromium, devices } from 'playwright-core';
import http from 'http'; import fs from 'fs'; import path from 'path';
const WEB = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../../web');
const types = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.webp': 'image/webp', '.m4a': 'audio/mp4', '.bin': 'application/octet-stream' };
const srv = http.createServer((q, r) => { const p = path.join(WEB, decodeURIComponent(q.url.split('?')[0]).replace(/\/$/, '/index.html')); fs.readFile(p, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' }); r.end(d); }); }).listen(8793);
const out = process.argv[2];
const b = await chromium.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: false, args: ['--use-angle=metal', '--autoplay-policy=no-user-gesture-required'] });
for (const [nm, vp] of [['port', { width: 390, height: 844 }], ['land', { width: 844, height: 390 }]]) {
  const ct = await b.newContext({ viewport: vp, deviceScaleFactor: 1, hasTouch: true, isMobile: true, userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Version/17.0 Mobile/15E148 Safari/604.1' });
  const p = await ct.newPage(); p.on('pageerror', e => console.log('[pageerror]', e.message));
  await p.goto(`http://localhost:8793/index.html?mobile=1`); await p.waitForTimeout(800); await p.screenshot({ path: `${out}_${nm}_home.jpg`, quality: 80, type: 'jpeg' });
  await p.click('#enter2'); await p.waitForFunction('window.__ready===true', null, { timeout: 120000 }); await p.waitForTimeout(3500); await p.screenshot({ path: `${out}_${nm}_free.jpg`, quality: 80, type: 'jpeg' });
  await p.click('#bJournal'); await p.waitForTimeout(600); await p.screenshot({ path: `${out}_${nm}_journal.jpg`, quality: 80, type: 'jpeg' }); await p.click('#scrim', { position: { x: 20, y: 20 } }); await p.waitForTimeout(300);
  await p.click('#bSettings'); await p.waitForTimeout(600); await p.screenshot({ path: `${out}_${nm}_set.jpg`, quality: 80, type: 'jpeg' }); await p.click('#scrim', { position: { x: 20, y: 20 } }); await p.waitForTimeout(300);
  await p.click('#pGo'); await p.waitForTimeout(3000); await p.tap('#act'); await p.waitForTimeout(800); await p.screenshot({ path: `${out}_${nm}_rit.jpg`, quality: 80, type: 'jpeg' });
  console.log(nm, JSON.stringify(await p.evaluate(() => ({ calls: __renderer.info.render.calls, tris: __renderer.info.render.triangles })))); await ct.close();
}
await b.close(); srv.close();
