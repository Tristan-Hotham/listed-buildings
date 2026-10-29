// Headless screenshots for checking the page (Playwright). Usage: node code/shots.js URL OUTPREFIX [width]
const { chromium } = require('playwright');
(async () => {
  const [url, out, width] = process.argv.slice(2);
  const W = +(width || 1300);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: W, height: W < 600 ? 844 : 1000 }, deviceScaleFactor: 1 });
  await p.route(/cdnjs\.cloudflare\.com\/ajax\/libs\/leaflet\/1\.9\.4\/(leaflet\.min\.(js|css))/, r => { const f = r.request().url().endsWith('.js') ? 'leaflet.js' : 'leaflet.css'; r.fulfill({ path: '/tmp/claude-0/lf/node_modules/leaflet/dist/' + f }); });
  await p.route(/fonts\.(googleapis|gstatic)\.com|arcgisonline|postcodes\.io/, r => r.fulfill({ body: '', contentType: 'text/css' }));
  const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await p.goto(url, { waitUntil: 'networkidle' }); await p.waitForTimeout(3000);
  await p.evaluate(() => document.getElementById('lmap').scrollIntoView({ block: 'start' }));
  await p.waitForTimeout(800);
  await p.screenshot({ path: out + '_map.png' });
  // zoom to Bath, colour by type
  await p.evaluate(() => { lmap.setView([51.381, -2.359], 15, { animate: false }); });
  await p.waitForTimeout(1500);
  await p.screenshot({ path: out + '_bath.png' });
  await p.evaluate(() => { document.querySelector('#modeBtns [data-m="built"]').click(); lmap.setView([52.4, -3.6], 8, { animate: false }); });
  await p.waitForTimeout(1500);
  await p.screenshot({ path: out + '_built.png' });
  await p.evaluate(() => { document.querySelector('#modeBtns [data-m="county"]').click(); lmap.fitBounds([[49.9, -8.2], [58.7, 1.8]]); });
  await p.waitForTimeout(1500);
  await p.screenshot({ path: out + '_county.png' });
  // click a dot near York Minster
  await p.evaluate(() => { document.querySelector('#modeBtns [data-m="grade"]').click(); lmap.setView([53.962, -1.082], 16, { animate: false }); });
  await p.waitForTimeout(1200);
  const box = await (await p.$('#lmap')).boundingBox();
  const cp = await p.evaluate(() => { const c = lmap.getCenter(); let best = -1, bd = 1e9; for (let i = 0; i < PT.n; i++) { const d = (PT.lat[i] - c.lat) ** 2 + (PT.lon[i] - c.lng) ** 2; if (d < bd) { bd = d; best = i; } } const q = lmap.latLngToContainerPoint([PT.lat[best], PT.lon[best]]); return [q.x, q.y]; });
  await p.mouse.click(box.x + cp[0], box.y + cp[1]);
  await p.waitForTimeout(1500);
  await p.screenshot({ path: out + '_click.png', fullPage: false });
  await p.screenshot({ path: out + '_full.png', fullPage: true });
  const sw = await p.evaluate(() => document.documentElement.scrollWidth);
  console.log('errors', JSON.stringify(errs), 'scrollWidth', sw);
  await b.close();
})();
