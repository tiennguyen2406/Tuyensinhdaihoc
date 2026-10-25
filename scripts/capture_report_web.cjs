/* Anh bao cao tu GitHub Pages that, khong khoi dong crawler hoac server. */
const path = require('node:path');
const fs = require('node:fs');
const { chromium } = require('../.venv/browser-check/node_modules/playwright');
const out = path.resolve(__dirname, '../docs/fig');
const url = 'https://tiennguyen2406.github.io/Tuyensinhdaihoc/';
(async () => {
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 }, deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForFunction(() => document.querySelectorAll('.uni-card').length === 292);
  const shot = name => page.screenshot({ path: path.join(out, `web_${name}.png`) });
  await shot('uni');
  await page.locator('#uni-q').fill('BKA');
  await page.locator('#uni-ac li').first().click();
  await page.locator('#uni-out tbody tr').first().waitFor();
  await shot('school');
  await page.locator('#uni-out .dean-block').scrollIntoViewIfNeeded();
  await shot('dean');
  await page.locator('#uni-out .tuition-card').scrollIntoViewIfNeeded();
  await shot('tuition');
  for (const detail of await page.locator('#uni-out .dean-block details[open]').all()) {
    await detail.locator(':scope > summary').click();
  }
  await page.setViewportSize({ width: 1280, height: 1250 });
  await page.locator('#uni-out .dean-block').evaluate(e => scrollTo(0, e.getBoundingClientRect().top + scrollY - 75));
  await shot('school_info');
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.locator('[data-tab="major"]').click();
  await page.locator('#major-q').fill('7480201');
  await page.locator('#major-ac li').first().click();
  await page.locator('#major-out tbody tr').first().waitFor();
  await page.evaluate(() => scrollTo(0, 0));
  await shot('major');
  await page.locator('[data-tab="advice"]').click();
  await page.locator('#adv-method').selectOption('THPT');
  await page.locator('#adv-combo').selectOption('A00');
  await page.locator('#adv-score').fill('24');
  await page.locator('#advice-form button[type=submit]').click();
  await page.locator('#advice-out tbody tr').first().waitFor();
  await shot('advice');
  await page.locator('[data-tab="network"]').click();
  await page.waitForFunction(() => typeof netObj !== 'undefined' && netObj && netObj.body.nodeIndices.length > 0);
  await page.waitForTimeout(1800);
  await page.evaluate(() => { netObj.stopSimulation(); netObj.fit({ animation: false }); });
  await shot('network');
  await page.locator('[data-tab="coverage"]').click();
  await page.locator('#coverage-out tbody tr').first().waitFor();
  await shot('coverage');
  await page.setViewportSize({ width: 375, height: 900 });
  await page.locator('[data-tab="advice"]').click();
  await page.evaluate(() => scrollTo(0, 0));
  if (await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)) throw Error('Mobile overflow');
  await shot('mobile');
  if (errors.length) throw Error(errors.join('\n'));
  console.log(JSON.stringify({ url, desktop: '1280px', mobile: '375x900', images: 10, pageErrors: errors.length }));
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
