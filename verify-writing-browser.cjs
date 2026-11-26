const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const { pathToFileURL } = require('node:url');
const root = __dirname;
const base = process.env.ROOM_URL || pathToFileURL(root + '/dist/').href;
(async () => {
 const browser = await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe', headless:true});
 const page = await browser.newPage({reducedMotion:'reduce'});
 const errors = [];
 page.on('pageerror', error => errors.push(error.message));
 await page.goto(base + 'writing.html');
 assert.equal(await page.title(), 'Writing Practice Â· Chinese Practice Room');
 assert.equal(await page.locator('header nav [aria-current="page"]').textContent(), 'Writing');
 await page.locator('#restart').click();
 await page.locator('#flashcard').focus();
 await page.keyboard.press('Space');
 assert.equal(await page.locator('#answer').isVisible(), true);
 assert.equal(await page.locator('#ratings button:focus').count(), 0);
 await page.keyboard.press('Space');
 assert.equal(await page.locator('#answer').isVisible(), true, 'Space must not submit a rating');
 for (let key = 1; key <= 4; key++) {
   if (key > 1) await page.keyboard.press('Space');
   assert.equal(await page.locator('#ratings button:focus').count(), 0);
   await page.keyboard.press(String(key));
   assert.equal(await page.locator('#answer').isVisible(), false);
 }
 // Check every writing word on both sides of the card and both prompt directions.
 const lessons = await page.evaluate(() => WRITING_LESSONS);
 const slider = page.locator('#lesson');
 const focus = page.locator('#focus-lesson');
 await slider.fill(String(lessons.length));
 assert.match(await page.locator('#progress').textContent(), new RegExp(` · ${lessons.flatMap(lesson => lesson.words).length} words$`));
 await focus.check();
 assert.match(await page.locator('#progress').textContent(), new RegExp(` · ${lessons.at(-1).words.length} words$`));
 let checked = 0;
 for (const direction of ['pinyin','hanzi']) {
   await page.locator(`input[value="${direction}"]`).check();
   for (const lesson of lessons) {
     await slider.fill(String(lesson.number));
     await page.locator('#restart').click();
     for (const word of lesson.words) {
       assert.equal(await page.locator('#prompt').textContent(), word[direction]);
       assert.equal(word.pinyin, word.pinyin.normalize('NFC'));
       assert.ok(!/\p{M}|\uFFFD|\s{2,}|^\s|\s$/u.test(word.pinyin));
       await page.locator('#reveal').click();
       assert.equal(await page.locator('#translation').textContent(), word[direction === 'pinyin' ? 'hanzi' : 'pinyin']);
       assert.equal(await page.locator('#ratings button:focus').count(), 0);
       if (word.hanzi === 'æ‰¾' && direction === 'pinyin') {
         assert.equal(word.pinyin, 'zhÇŽo');
         assert.ok((await page.locator('#prompt').evaluate(el => getComputedStyle(el).fontFamily)).includes('Segoe UI'));
         await page.screenshot({path: process.env.PINYIN_SCREENSHOT || path.join(require('node:os').tmpdir(), 'reading-room-pinyin.png'), fullPage:true});
       }
       await page.keyboard.press('3');
       checked++;
     }
   }
 }
 // Replaying stroke animation must also leave ratings unfocused.
 await page.locator('#restart').click();
 await page.locator('#reveal').click();
 await page.locator('#animate').click();
 assert.equal(await page.locator('#ratings button:focus').count(), 0);
 for (const file of ['index.html','writing.html']) {
   await page.goto(base + file);
   for (const width of [360, 768, 1280]) {
     await page.setViewportSize({width, height:900});
     assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, `${file} at ${width}px`);
     assert.equal(await page.locator('header nav a').count(), 2);
   }
 }
 assert.deepEqual(errors, []);
 await browser.close();
 console.log(`PASS: ${checked} cards across both directions; Space, all four ratings, animation focus, titles, navigation and responsive widths.`);
})().catch(error => {console.error(error); process.exit(1);});
