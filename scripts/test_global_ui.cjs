const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'../_site');
const data=JSON.parse(fs.readFileSync(path.join(root,'data/verified.json')));
(async()=>{
 const browser=await chromium.launch({channel:process.env.BROWSER_CHANNEL||'msedge'});
 try {
  for(const lang of ['ru','en']) {
   const page=await browser.newPage({viewport:{width:1280,height:900}}),errors=[];
   page.on('pageerror',e=>errors.push(e.message));
   await page.addInitScript(()=>localStorage.setItem('okleyka-age-18','1'));
   await page.route('http://okleika.test/**',route=>{
    const pathname=new URL(route.request().url()).pathname;
    const file=path.resolve(root,'.'+(pathname==='/'?'/index.html':pathname));
    if(!file.startsWith(root+path.sep)||!fs.existsSync(file))return route.fulfill({status:404,body:''});
    return route.fulfill({path:file});
   });
   const load=async query=>{await page.goto('http://okleika.test/?lang='+lang+query);await page.locator(query.includes('&id=')?'#card-view h1':'#results .row').first().waitFor();};
   await load('');
   const retail=data.records.filter(r=>r[1]==='v'&&r[2].length).length;
   assert.equal(Number((await page.locator('#count').innerText()).replace(/[^0-9]/g,'')),retail);
   assert.ok(await page.locator('#global-count a').count());
   assert.equal(await page.locator('#archive-link').isVisible(),false);
   assert.ok(!(await page.locator('body').innerText()).includes('Пятёрочка'));
   for(const id of await page.locator('#results [data-id]').evaluateAll(es=>es.map(e=>e.dataset.id)))assert.ok(data.records.find(r=>r[0]===id)[2].length);
   await page.locator('#global-count a').click();
   await page.waitForURL('**coverage=global');
   await page.locator('#results .section-divider').waitFor();
   for(const id of await page.locator('#results [data-id]').evaluateAll(es=>es.map(e=>e.dataset.id)))assert.equal(data.records.find(r=>r[0]===id)[2].length,0);
   assert.equal(await page.locator('#results .where').count(),0);
   await load('&q='+encodeURIComponent('Ржаная мягкая'));
   assert.ok(await page.locator('[data-id="reply-bash-rzhanaya-soft"]').count());
   await load('&id=sp-87a7dd7147');
   await page.locator('#card-view').waitFor({state:'visible'});
   assert.equal(await page.locator('.card-status .price-band').innerText(),'$$$$$');
   assert.ok(page.url().includes('id=rfa-44091d2819c0'));
   await load('&coverage=global');
   for(const width of [375,1280]){
    await page.setViewportSize({width,height:900});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   }
   if(process.env.QA_SCREENSHOT_DIR)await page.screenshot({path:path.join(process.env.QA_SCREENSHOT_DIR,'global-'+lang+'.png'),fullPage:false});
   assert.deepEqual(errors,[]);await page.close();
   console.log(lang+': separated counts, retail priority, global search, no fake shops, Hennessy price and responsive layout passed');
  }
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
