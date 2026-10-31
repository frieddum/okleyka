const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {chromium} = require('playwright');
const root = path.resolve(__dirname, '../_site');
(async () => {
  const browser = await chromium.launch({channel: process.env.BROWSER_CHANNEL || 'msedge'});
  try {
    for (const width of [390, 1280]) for (const lang of ['ru', 'en']) {
      const page = await browser.newPage({viewport: {width, height: 900}});
      const errors = [];
      page.on('pageerror', e => errors.push(e.message));
      await page.route('http://okleika.test/**', route => {
        const pathname = new URL(route.request().url()).pathname;
        const file = path.resolve(root, '.' + (pathname === '/' ? '/index.html' : pathname));
        if (!file.startsWith(root + path.sep) || !fs.existsSync(file)) return route.fulfill({status:404, body:''});
        return route.fulfill({path:file});
      });
      await page.goto('http://okleika.test/drink-499a3aaef3.html?lang=' + lang);
      await page.locator('.age-yes').click();
      assert.equal(await page.locator('h1').count(), 1);
      assert.ok((await page.locator('article').innerText()).includes('2016-01'));
      assert.equal(await page.locator('link[rel="canonical"]').getAttribute('href'), 'https://okleika.win/drink-499a3aaef3.html');
      assert.ok(await page.locator('a[href="https://www.barnivore.com/wine/920/veuve-clicquot"]').count());
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
      if (process.env.SEO_SCREENSHOT_DIR) {
        await page.screenshot({path:path.join(process.env.SEO_SCREENSHOT_DIR, 'card-' + width + '-' + lang + '.png'), fullPage:true});
      }
      await page.goto('http://okleika.test/?id=499a3aaef3&lang=' + lang);
      await page.locator('#card-view h1').waitFor();
      assert.ok((await page.locator('link[rel="canonical"]').getAttribute('href')).endsWith('/drink-499a3aaef3.html'));
      await page.locator('#card-view a[href^="drink-"]').click();
      await page.locator('article h1').waitFor();
      assert.equal(errors.length, 0, errors.join('\n'));
      await page.goto('http://okleika.test/catalog.html?lang=' + lang);
      assert.equal(await page.locator('article li').count(), 100);
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
      await page.close();
    }
    const context = await browser.newContext({javaScriptEnabled:false});
    const page = await context.newPage();
    await page.goto(require('node:url').pathToFileURL(path.join(root, 'drink-499a3aaef3.html')).href);
    assert.ok((await page.locator('article').innerText()).includes('2016-01'));
    await context.close();
    console.log('Search UI: desktop/mobile, RU/EN, age gate, links, canonical, no-JS content passed.');
  } finally { await browser.close(); }
})().catch(e => {console.error(e); process.exitCode=1;});
