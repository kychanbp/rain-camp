import { chromium } from 'playwright-core';
const b = await chromium.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: false, args: ['--use-angle=metal', '--autoplay-policy=no-user-gesture-required'] });
const p = await b.newPage({ viewport: { width: 1280, height: 720 } }); const bad = [];
p.on('pageerror', e => bad.push(e.message)); p.on('response', r => { if (r.status() >= 400) bad.push(r.status() + ' ' + r.url()); });
await p.goto('https://kychanbp.github.io/rain-camp/?auto=free'); await p.waitForFunction('window.__ready===true', null, { timeout: 120000 }); await p.waitForTimeout(3000);
console.log('ready', await p.title(), JSON.stringify(bad.slice(0, 5))); await b.close();
