// Run with Node and Playwright available. BROWSER_CHANNEL=msedge uses installed Edge.
// All requests are fulfilled locally; fixtures never touch catalogue data or the build.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require('playwright');

const site = path.join(__dirname, '../site');
const meta = {as_of: '2026-01-01', dicts: {
  networks: ['Alpha', 'Beta'], brands: [], producers: [], countries: [], categories: ['Вино', 'Виски']
}};
const record = (id, st, net, cat, name = id) =>
  [id, st, [net], name, -1, -1, -1, null, cat, 750, null, 12, null, null, null, -1, null, null, false];
const records = [
  record('one', 'v', 0, 0), record('two', 'v', 0, 0), record('three', 'v', 1, 1),
  record('four', 'n', 0, 0), record('five', 'v', 1, 1, 'AAA ' + 'LongUnbrokenDrinkName'.repeat(12)),
  record('missing', 'v', 0, 0), record('invalid', 'v', 1, 1), record('nonvegan-missing', 'n', 1, 0),
  ...Array.from({length: 26}, (_, i) => record('extra-' + i, 'v', 0, 0))
];
const price_levels = Object.fromEntries(['one', 'two', 'three', 'four', 'five'].map((id, i) => [id, {level: i + 1}]));
price_levels.invalid = {level: 6};
for (let i = 0; i < 26; i++) price_levels['extra-' + i] = {level: 1};

(async () => {
  const browser = await chromium.launch({channel: process.env.BROWSER_CHANNEL || undefined});
  try {
    for (const lang of ['ru', 'en']) {
      const page = await browser.newPage({viewport: {width: 1280, height: 900}});
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      let omitPrices = false;
      await page.addInitScript(() => localStorage.setItem('okleyka-age-18', '1'));
      await page.route('http://okleika.test/**', async route => {
        const pathname = new URL(route.request().url()).pathname;
        if (pathname === '/data/meta.json') return route.fulfill({json: meta});
        if (pathname === '/data/verified.json') return route.fulfill({json: {
          records, assessments: [], ...(omitPrices ? {} : {price_levels})
        }});
        if (pathname === '/content-en.js') return route.fulfill({contentType: 'text/javascript', body: ''});
        const file = path.resolve(site, '.' + (pathname === '/' ? '/index.html' : pathname));
        if (!file.startsWith(site + path.sep) || !fs.existsSync(file)) return route.fulfill({status: 404, body: ''});
        const contentType = {'.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.woff2': 'font/woff2', '.svg': 'image/svg+xml'}[path.extname(file)];
        return route.fulfill({path: file, contentType});
      });
      const load = async (extra = '') => {
        await page.goto(`http://okleika.test/?lang=${lang}${extra}`);
        await page.locator('[data-group="price"] input').first().waitFor({state: 'attached'});
      };
      const option = value => page.locator(`[data-group="price"] input[value="${value}"]`);
      const resultCount = async expected => assert.equal(Number((await page.locator('#count').innerText()).split(/\s/)[0]), expected);
      const counts = async expected => assert.deepEqual(await page.locator('[data-group="price"] .n').allTextContents(), expected.map(String));
      const selected = async expected => assert.deepEqual(await page.locator('[data-group="price"] input:checked').evaluateAll(nodes => nodes.map(n => n.value)), expected);

      await load('&p=2');
      assert.equal(await page.locator('[data-group="price"] legend').textContent(), lang === 'en' ? 'Price level' : 'Ценовой уровень');
      assert.equal(await option('5').getAttribute('aria-label'), lang === 'en' ? 'Price level 5 of 5' : 'Ценовой уровень 5 из 5');
      assert.equal(await option('__none').getAttribute('aria-label'), lang === 'en' ? 'No price' : 'Без цены');
      await counts([27, 1, 1, 0, 1, 2]);
      await option('1').check();
      assert.equal(new URL(page.url()).searchParams.has('p'), false, 'Changing price resets pagination');
      await resultCount(27);
      await option('2').check();
      await option('__none').check();
      await resultCount(30);
      await counts([27, 1, 1, 0, 1, 2]); // Counts exclude their own facet.
      assert.equal(new URL(page.url()).searchParams.get('price'), '1|2|__none');
      await page.reload();
      await page.locator('[data-group="price"] input').first().waitFor({state: 'attached'});
      await selected(['1', '2', '__none']);
      await resultCount(30);
      await page.locator('[data-group="net"] input[value="Beta"]').check();
      await resultCount(1);
      await counts([0, 0, 1, 0, 1, 1]);
      await page.locator('[data-group="st"] input[value="n"]').check();
      await resultCount(2);
      await page.locator('[data-group="kind"] input[value="Вино"]').check();
      await resultCount(1);
      await counts([0, 0, 0, 0, 0, 1]);
      await page.locator('#results a[data-id]').first().click();
      await page.locator('#card-view').waitFor({state: 'visible'});
      assert.equal(new URL(page.url()).searchParams.get('price'), '1|2|__none');
      await page.locator('[data-back]').click();
      await page.locator('#list-view').waitFor({state: 'visible'});
      await selected(['1', '2', '__none']);
      await page.locator('[data-remove="price"][data-v="1"]').click();
      await selected(['2', '__none']);
      await page.locator('#reset-all').click();
      await selected([]);
      await resultCount(32);
      assert.equal(new URL(page.url()).searchParams.has('price'), false);
      await option('4').check();
      await resultCount(0);
      await page.locator('.empty [data-remove="price"]').click();
      await resultCount(32);
      await page.locator('#q').fill('two');
      await page.locator('#q').press('Enter');
      await counts([0, 1, 0, 0, 0, 0]);
      await option('2').check();
      await resultCount(1);

      await load('&price=5');
      const otherLang = lang === 'ru' ? 'en' : 'ru';
      await page.locator(`.nav .language-flag[aria-label="${otherLang === 'en' ? 'English' : 'Русский'}"]`).click();
      await page.waitForURL(`**lang=${otherLang}&price=5`);
      await page.locator('[data-group="price"] input').first().waitFor({state: 'attached'});
      await selected(['5']);
      await load('&price=5');
      for (const width of [320, 375, 768, 900, 901, 1280]) {
        await page.setViewportSize({width, height: 900});
        const layout = await page.locator('.row > a').first().evaluate(row => {
          const rect = el => { const {x, y, width, height, right, bottom} = el.getBoundingClientRect(); return {x, y, width, height, right, bottom}; };
          return {row: rect(row), price: rect(row.querySelector(':scope > .price-band')), status: rect(row.querySelector('.pill')), body: rect(row.querySelector('.body')), overflow: document.documentElement.scrollWidth > innerWidth};
        });
        const overlaps = (a, b) => a.x < b.right && b.x < a.right && a.y < b.bottom && b.y < a.bottom;
        assert.equal(overlaps(layout.price, layout.status), false, `${lang}/${width}: status overlap`);
        assert.equal(overlaps(layout.price, layout.body), false, `${lang}/${width}: title overlap`);
        assert.ok(Math.abs(layout.price.right - layout.row.right) < 1, `${lang}/${width}: price at right edge`);
        assert.ok(layout.price.y <= layout.row.y + 17, `${lang}/${width}: price at top`);
        assert.equal(layout.overflow, false, `${lang}/${width}: horizontal overflow`);
      }
      assert.equal(await page.locator('.row .price-band').getAttribute('title'), null);
      assert.equal(await page.locator('.row .price-band').innerText(), '$$$$$');
      await page.locator('#results a[data-id]').click();
      assert.equal(await page.locator('.card-status .price-band').innerText(), '$$$$$');
      assert.equal(await page.locator('.card-status .price-band').getAttribute('title'), null);
      await page.locator('[data-back]').click();
      await page.locator('#list-view').waitFor({state: 'visible'});
      await page.locator('[data-remove="all"]').click();
      await selected([]);
      await resultCount(32);

      await page.setViewportSize({width: 320, height: 900});
      await page.locator('#open-filters').click();
      await option('5').check();
      await option('__none').check();
      assert.equal(await page.locator('#open-filters .badge').innerText(), '2');
      assert.equal(await page.locator('#show-results').innerText(), lang === 'en' ? 'Show 3 entries' : 'Показать 3 записи');
      await page.locator('#reset-mobile').click();
      await selected([]);
      await resultCount(32);
      assert.equal(new URL(page.url()).searchParams.has('price'), false);
      await page.locator('#show-results').click();

      await load('&price=6%7Cgarbage%7C5');
      await selected(['5']);
      await resultCount(1);
      omitPrices = true;
      await load('&price=__none');
      await resultCount(32);
      await counts([0, 0, 0, 0, 0, 32]);
      assert.equal(await page.locator('.row .price-band').count(), 0);
      assert.deepEqual(errors, []);
      await page.close();
      console.log(`${lang}: multi-select, counts, URL/reload/back, category/network/status intersections, pagination, resets, empty/missing prices, accessible labels and six responsive widths passed`);
    }
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
