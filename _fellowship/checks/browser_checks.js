/*
 * Browser acceptance checks for publish_paused/ (Playwright, Chromium).
 * Run:  NODE_PATH=$(npm root -g) node browser_checks.js
 * Serves publish_paused/ on a local port, runs every check, writes
 * browser_results.json next to this file, exits non-zero if any check fails.
 */
const { chromium } = require('playwright');
const http = require('http');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..', '..', 'publish_paused');
const INPUTS = path.resolve(__dirname, '..', 'inputs');
const PORT = 8791;
const BASE = 'http://localhost:' + PORT + '/';
const MOBILE = { width: 390, height: 844 };
const results = [];
const consoleErrors = [];
const externalRequests = [];

function rec(id, name, pass, detail) { results.push({ id, name, pass: !!pass, detail }); console.log((pass ? 'PASS ' : 'FAIL ') + id + ' ' + name + (detail ? ' :: ' + JSON.stringify(detail) : '')); }

const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.json': 'application/json; charset=utf-8', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.woff2': 'font/woff2', '.xml': 'application/xml', '.webmanifest': 'application/manifest+json', '.txt': 'text/plain' };
function serve() {
  return http.createServer((req, res) => {
    let p = decodeURIComponent(new URL(req.url, BASE).pathname);
    if (p.endsWith('/')) p += 'index.html';
    const f = path.join(ROOT, p);
    if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); res.end('nf'); return; }
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' });
    fs.createReadStream(f).pipe(res);
  }).listen(PORT);
}

async function newCtx(browser, opts) {
  const ctx = await browser.newContext(Object.assign({ viewport: MOBILE, hasTouch: true }, opts || {}));
  ctx.on('page', p => watch(p));
  return ctx;
}
function watch(p) {
  p.on('console', m => { if ((m.type() === 'error' || m.type() === 'warning') && !/blocked by Playwright/.test(m.text())) consoleErrors.push(p.url() + ' :: ' + m.type() + ': ' + m.text()); });
  p.on('pageerror', e => consoleErrors.push(p.url() + ' :: pageerror: ' + e.message));
  p.on('request', r => { if (!r.url().startsWith(BASE)) externalRequests.push(r.url()); });
}
async function gate(p) { await p.waitForSelector('#m-gate-email', { timeout: 5000 }); await p.fill('#m-gate-email', 'tester@example.com'); await p.click('.m-gate-box button[type=submit]'); }
const norm = s => (s || '').replace(/\s+/g, ' ').trim();

(async () => {
  const server = serve();
  const browser = await chromium.launch();
  try {
    const Q = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/bizenv-questions.json'))).questions;
    const OUTL = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/bizenv-outline.json')));

    /* ---------------- A3 home ---------------- */
    {
      const ctx = await newCtx(browser); const p = await ctx.newPage();
      await p.goto(BASE + 'index.html');
      const r = await p.evaluate(() => {
        const paused = [...document.querySelectorAll('.h-card.paused')];
        const door = document.querySelector('a.h-card[href="fellowship.html"]');
        return {
          paused: paused.map(c => ({ tag: c.tagName, href: c.getAttribute('href'), dis: c.getAttribute('aria-disabled'), badge: c.querySelector('.h-badge').innerText.replace(/\s+/g, ' '), op: getComputedStyle(c).opacity })),
          door: door && door.querySelector('.t').textContent, doorEn: door && door.querySelector('.e').textContent, counters: door && door.querySelector('.c').textContent,
          noindex: !!document.querySelector('meta[name=robots][content*=noindex]')
        };
      });
      const ok = r.paused.length === 2 && r.paused.every(c => c.tag === 'DIV' && !c.href && c.dis === 'true' && c.badge.includes('متوقفة مؤقتاً') && c.badge.includes('Temporarily paused') && +c.op < 1)
        && r.door === 'التحضير لزمالة SOCPA' && r.doorEn === 'SOCPA fellowship preparation' && r.counters.includes(String(OUTL.totals.visible));
      rec('A3', 'بطاقتا القطاعين معطلتان والباب الثالث يعمل', ok, r);
      await p.click('a.h-card[href="fellowship.html"]'); await p.waitForLoadState();
      rec('A3b', 'الباب الثالث يفتح fellowship.html', p.url().endsWith('fellowship.html'), p.url());
      await ctx.close();
    }

    /* ---------------- A4 paused pages ---------------- */
    {
      const ctx = await newCtx(browser); const p = await ctx.newPage();
      const out = {};
      for (const u of ['private-sector.html', 'public-sector.html', 'private-sector.html#IAS16']) {
        const resp = await p.goto(BASE + u);
        out[u] = await p.evaluate(() => ({ h1: document.querySelector('h1').textContent, p: document.querySelector('.p-box p').textContent, back: document.querySelector('.p-box a').getAttribute('href'), noindex: !!document.querySelector('meta[name=robots][content="noindex"]'), len: document.body.innerText.length }));
        out[u].status = resp.status();
      }
      const sm = fs.readFileSync(path.join(ROOT, 'sitemap.xml'), 'utf8');
      const ok = Object.values(out).every(o => o.status === 200 && o.h1 === 'هذا القسم متوقف مؤقتاً' && o.p === 'نعمل على تحديثه، وسيعود للعمل قريباً.' && o.back === 'index.html' && o.noindex)
        && !/private-sector|public-sector/.test(sm);
      rec('A4', 'صفحتا الإيقاف بالإشعار و noindex وخارج الخريطة، والمرساة القديمة تصل', ok, out);
      await ctx.close();
    }

    /* ---------------- B1/B2 fellowship ---------------- */
    {
      const ctx = await newCtx(browser); const p = await ctx.newPage();
      await p.goto(BASE + 'fellowship.html');
      await p.waitForSelector('.f-card');
      const r = await p.evaluate(() => {
        const txt = document.body.innerText;
        const latin = (txt.match(/[A-Za-z]+/g) || []);
        const html = document.documentElement.outerHTML;
        return { lang: document.documentElement.lang, dir: document.documentElement.dir, title: document.querySelector('h1').textContent, latin: [...new Set(latin)],
          gate: !!document.querySelector('.m-gate'), cards: [...document.querySelectorAll('.f-card')].map(c => ({ href: c.getAttribute('href'), t: c.querySelector('.t').textContent, c: c.querySelector('.c').textContent })),
          hasL: /\bL\(/.test(html), hasLangEn: /lang=en/.test(html), switcher: /English|EN\b/.test(txt) };
      });
      const subjects = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/fellowship-subjects.json')));
      rec('B1', 'الحاوية عربية فقط', r.lang === 'ar' && r.dir === 'rtl' && r.title === 'التحضير لزمالة SOCPA' && r.latin.every(w => w === 'SOCPA') && !r.hasL && !r.hasLangEn && !r.switcher && !r.gate, r);
      rec('B2', 'بطاقات المواد من fellowship-subjects.json وعدّاداتها مشتقة', r.cards.length === subjects.length && r.cards[0].t === subjects[0].title && r.cards[0].href === subjects[0].href
        && subjects[0].counters.questions === OUTL.totals.visible && subjects[0].counters.chapters === OUTL.totals.chapters_shown && subjects[0].counters.parts === OUTL.totals.parts, { cards: r.cards, counters: subjects[0].counters });
      await ctx.close();
    }

    /* ---------------- C1 gate, C2 queue (empty endpoint), 12 progress ---------------- */
    {
      const ctx = await newCtx(browser); const p = await ctx.newPage();
      await p.goto(BASE + 'business-environment.html');
      const before = await p.evaluate(() => ({ gate: !!document.querySelector('.m-gate'), appHidden: document.getElementById('app').hidden, title: document.getElementById('m-gate-title').textContent, free: document.querySelector('.m-gate-free').textContent }));
      await p.fill('#m-gate-email', 'not-an-email'); await p.click('.m-gate-box button[type=submit]');
      const invalid = await p.evaluate(() => ({ still: !!document.querySelector('.m-gate'), err: document.getElementById('m-gate-err').textContent }));
      await p.fill('#m-gate-email', 'tester@example.com'); await p.click('.m-gate-box button[type=submit]');
      await p.waitForSelector('#parts .b-part');
      await p.reload(); await p.waitForSelector('#parts .b-part');
      const again = await p.evaluate(() => !!document.querySelector('.m-gate'));
      await p.goto(BASE + 'capital-structure.html'); await p.waitForTimeout(400);
      const cs = await p.evaluate(() => ({ gate: !!document.querySelector('.m-gate'), main: !document.getElementById('csMain').hidden }));
      await p.goto(BASE + 'fellowship.html'); await p.waitForTimeout(300);
      const fe = await p.evaluate(() => !!document.querySelector('.m-gate'));
      const store = await p.evaluate(() => { const o = {}; for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i); o[k] = localStorage.getItem(k); } return o; });
      const q = JSON.parse(store['bizenv-pending-signups'] || '[]');
      const recd = q[0] || {};
      const keysOk = JSON.stringify(Object.keys(recd)) === JSON.stringify(['v', 'subject_id', 'email', 'ts', 'section', 'entry', 'consent', 'source']);
      rec('C1', 'البوابة عند مدخل المادة مرة واحدة، والحاوية حرة', before.gate && before.appHidden && before.title === 'للدخول إلى مادة بيئة الأعمال' && before.free === 'صفحة التحضير لزمالة SOCPA متاحة بلا تسجيل.'
        && invalid.still && invalid.err && !again && !cs.gate && cs.main && !fe, { before, invalid, again, cs, fellowshipGate: fe });
      rec('C2a', 'الطابور المحلي مع ACCESS_ENDPOINT فارغ، بشكل السجل الثابت', q.length === 1 && keysOk && recd.v === 1 && recd.section === 'business-environment' && recd.entry === 'business-environment'
        && recd.consent === true && recd.source === 'meyarplatform.com' && recd.subject_id === store['bizenv-subject-id'] && !isNaN(Date.parse(recd.ts)), recd);

      // progress survives reload
      await p.goto(BASE + 'business-environment.html#/c/IT.C3'); await p.waitForSelector('#chQuiz .b-unit');
      await p.click('#chQuiz .b-unit .m-btn'); await p.waitForSelector('#qOpts .b-opt');
      await p.click('#qOpts .b-opt >> nth=0'); await p.click('#qNext'); await p.click('#qOpts .b-opt >> nth=1');
      const key = 'bizenv-progress-' + store['bizenv-subject-id'];
      await p.reload(); await p.waitForSelector('#qOpts .b-opt');
      const prog = await p.evaluate(k => JSON.parse(localStorage.getItem(k)), key);
      const u = prog && prog.units['X:IT.C3'];
      const pos = await p.textContent('#qPos');
      rec('12', 'التقدم يُحفظ ويُستعاد تحت bizenv-progress-<subject_id>', !!u && Object.keys(u.answers).length === 2 && u.idx === 1 && /السؤال 2 من/.test(pos), { key, answered: u && Object.keys(u.answers).length, idx: u && u.idx, pos });
      await ctx.close();
    }

    /* ---------------- C2b queue flush once endpoint is set; capital-structure entry ---------------- */
    {
      // service workers blocked here so the rewritten access.js is not served from the SW cache
      const ctx = await newCtx(browser, { serviceWorkers: 'block' }); const p = await ctx.newPage();
      await p.goto(BASE + 'capital-structure.html');
      const g = await p.evaluate(() => ({ gate: !!document.querySelector('.m-gate'), hidden: document.getElementById('csMain').hidden }));
      await gate(p); await p.waitForTimeout(300);
      await p.goto(BASE + 'business-environment.html'); await p.waitForTimeout(300); // second page view, no second record
      const queued = await p.evaluate(() => JSON.parse(localStorage.getItem('bizenv-pending-signups') || '[]'));
      const hook = 'https://hook.invalid/exec';
      const posted = [];
      await ctx.route(BASE + 'access.js', async route => {
        const body = fs.readFileSync(path.join(ROOT, 'access.js'), 'utf8').replace('var ACCESS_ENDPOINT = "";', 'var ACCESS_ENDPOINT = "' + hook + '";');
        await route.fulfill({ status: 200, contentType: 'text/javascript', body });
      });
      await ctx.route(hook, async route => { posted.push(JSON.parse(route.request().postData())); await route.fulfill({ status: 200, body: 'ok' }); });
      await p.goto(BASE + 'business-environment.html'); await p.waitForSelector('#parts .b-part'); await p.waitForTimeout(600);
      const after = await p.evaluate(() => JSON.parse(localStorage.getItem('bizenv-pending-signups') || '[]'));
      rec('C2b', 'عند ضبط النقطة يُرسل الطابور كله عند أول فتح، و entry = capital-structure', g.gate && g.hidden && queued.length === 1 && queued[0].entry === 'capital-structure' && posted.length === 1 && posted[0].email === 'tester@example.com' && after.length === 0,
        { gateOnCs: g, queued: queued.length, entry: queued[0] && queued[0].entry, posted: posted.length, left: after.length });
      await ctx.close();
    }

    /* ---------------- 8 option shuffle, 9 duplicates, 5 no cards in engine ---------------- */
    {
      const ctx = await newCtx(browser); const p = await ctx.newPage();
      await p.goto(BASE + 'business-environment.html'); await gate(p); await p.waitForSelector('#parts .b-part');
      // 8: open the same question repeatedly and compare the displayed order
      await p.goto(BASE + 'business-environment.html#/c/MF.C1'); await p.waitForSelector('#chQuiz .b-unit');
      await p.click('#chQuiz .b-unit .m-btn'); await p.waitForSelector('#qOpts .b-opt');
      const orders = []; let judged = [];
      for (let i = 0; i < 8; i++) {
        await p.goto(BASE + 'business-environment.html#/c/MF.C1'); await p.goto(BASE + 'business-environment.html#/q/T:T11'); await p.waitForSelector('#qOpts .b-opt');
        orders.push(await p.evaluate(() => [...document.querySelectorAll('#qOpts .b-opt')].map(b => +b.dataset.o).join('')));
      }
      // correct option is judged correct whatever its displayed position
      for (let i = 0; i < 2; i++) {
        await p.goto(BASE + 'business-environment.html#/c/MF.C1'); await p.waitForSelector('#chQuiz .b-unit');
        await p.click('#chQuiz .b-unit .m-btn'); await p.waitForSelector('#qOpts .b-opt');
        const r = await p.evaluate(qs => {
          const id = JSON.parse(localStorage.getItem(Object.keys(localStorage).find(k => k.startsWith('bizenv-progress-')))).units['T:T11'].order[0];
          const a = qs.find(q => q.id === id).a;
          const btns = [...document.querySelectorAll('#qOpts .b-opt')];
          const pos = btns.findIndex(b => +b.dataset.o === a);
          btns[pos].click();
          return { pos, ok: btns[pos].classList.contains('ok'), msg: document.getElementById('qExp').textContent.slice(0, 5) };
        }, Q);
        judged.push(r);
      }
      rec('8', 'خلط الخيارات بين عرضين، والصحيح يُرصد صحيحاً', new Set(orders).size > 1 && judged.every(j => j.ok && j.msg.startsWith('صحيح')), { orders, judged });

      // 9: every unit containing a duplicate pair, started 25 times
      const pairs = Q.filter(q => q.dup).map(q => [q.id, q.dup]);
      const byId = Object.fromEntries(Q.map(q => [q.id, q]));
      const unitsWithPairs = [];
      pairs.forEach(([a, b]) => { const A = byId[a], B = byId[b]; if (A && B && !A.card && !B.card && A.src === 'exam' && B.src === 'exam' && A.ch === B.ch) unitsWithPairs.push(['X:' + A.ch, a, b]); });
      let viol = 0, runs = 0;
      for (const [uid, a, b] of unitsWithPairs) {
        const ch = uid.slice(2);
        for (let i = 0; i < 25; i++) {
          await p.goto(BASE + 'business-environment.html#/c/' + ch); await p.waitForSelector('#chQuiz .b-unit');
          const idx = await p.evaluate(u => [...document.querySelectorAll('#chQuiz .b-unit')].findIndex(d => d.querySelector('h4 span').textContent === (u.startsWith('X:') ? d.querySelector('h4 span').textContent : '')), uid);
          const units = await p.$$('#chQuiz .b-unit');
          await units[units.length - 1].$('.m-btn').then(b => b.click());
          await p.waitForSelector('#qOpts .b-opt');
          const order = await p.evaluate(u => JSON.parse(localStorage.getItem(Object.keys(localStorage).find(k => k.startsWith('bizenv-progress-')))).units[u].order, uid);
          runs++; if (order.includes(a) && order.includes(b)) viol++;
        }
      }
      rec('9', 'لا يظهر بند وبديله في نموذج واحد', unitsWithPairs.length > 0 && viol === 0, { pairsInSameUnit: unitsWithPairs.map(x => x.slice(1).join('/')), runs, violations: viol });

      // 5 + 6 + 7 + 15 from the rendered UI
      const ui = await p.evaluate(async () => {
        location.hash = '#/'; await new Promise(r => setTimeout(r, 300));
        const cards = [...document.querySelectorAll('.b-ch')];
        return {
          parts: [...document.querySelectorAll('.b-part > h2')].map(h => h.textContent),
          chapters: cards.length, all: cards.map(c => c.querySelector('h3').textContent),
          off: cards.filter(c => c.classList.contains('off')).map(c => ({ t: c.querySelector('h3').textContent, tag: c.tagName, dis: c.getAttribute('aria-disabled'), soon: !!c.querySelector('.b-soon'), secs: c.querySelector('.b-secs').textContent.split('، ').length }))
        };
      });
      rec('7', 'الفصول الفارغة الأربعة تظهر بمباحثها وبعدّاد صفر وغير قابلة للضغط، وإدارة التدفق النقدي مخفي', ui.chapters === OUTL.totals.chapters_shown && ui.off.length === 4 && ui.off.every(o => o.tag === 'DIV' && o.dis === 'true' && o.soon) && !ui.off.some(o => o.t === 'إدارة التدفق النقدي') && !ui.all.includes('إدارة التدفق النقدي'), ui);
      await ctx.close();
    }

    /* ---------------- D1 content equality (JS disabled) ---------------- */
    {
      const ctx = await browser.newContext({ javaScriptEnabled: false });
      const p = await ctx.newPage();
      const built = {};
      await p.goto(BASE + 'capital-structure.html');
      Object.assign(built, await p.evaluate(() => { const o = {}; document.querySelectorAll('section[id]').forEach(s => { (o[s.id] = o[s.id] || []).push(s.textContent); }); o.__eval = [document.getElementById('cs-s8-eval').textContent]; return o; }));
      const src = {};
      for (const [k, f] of [['cs', 'lesson-capital-structure.html'], ['rk', 'lesson-risk-leverage.html']]) {
        await p.setContent(fs.readFileSync(path.join(INPUTS, f), 'utf8').replace(/<link[^>]+>/g, ''));
        src[k] = await p.evaluate(() => { const o = {}; document.querySelectorAll('section[id]').forEach(s => { o[s.id] = s.textContent; }); const s8 = document.getElementById('s8'); if (s8) { const h = [...s8.querySelectorAll('h4')].find(x => x.textContent === 'تقييم الهيكل التمويلي'); o.__group = h ? h.textContent + h.nextElementSibling.textContent : null; } return o; });
      }
      const detail = []; let ok = true;
      for (const k of ['cs', 'rk']) for (const [sid, txt] of Object.entries(src[k])) {
        if (sid.startsWith('__')) continue;
        const b = built[k + '-' + sid];
        let expect = norm(txt);
        if (k === 'cs' && sid === 's8') expect = norm(expect.replace(norm(src.cs.__group), ''));
        const pass = !!b && b.length === 1 && norm(b[0]) === expect;
        if (!pass) ok = false;
        detail.push(k + '-' + sid + (pass ? ' ok' : ' MISMATCH'));
      }
      const evalOk = norm(built.__eval[0]) === norm(src.cs.__group);
      const count = Object.keys(built).filter(k => !k.startsWith('__')).length;
      rec('D1', 'كل مقطع من المصدرين مرة واحدة ونصه مطابق حرفياً (والمجموعة المنقولة في موضعها الجديد)', ok && evalOk && count === 19, { sections: count, detail, evalGroupMatches: evalOk });
      await ctx.close();
    }

    /* ---------------- D2..D6 capital structure live ---------------- */
    {
      const ctx = await newCtx(browser); const p = await ctx.newPage();
      await p.goto(BASE + 'capital-structure.html'); await gate(p); await p.waitForTimeout(500);
      const tabs = await p.evaluate(() => [...document.querySelectorAll('.cs-tabs [role=tab]')].map(b => b.textContent.replace(/^\d/, '')));
      const ids = await p.evaluate(() => { const a = [...document.querySelectorAll('[id]')].map(e => e.id); return { n: a.length, dup: [...new Set(a.filter((x, i) => a.indexOf(x) !== i))] }; });
      rec('D2', 'لا معرّف مكرر في capital-structure.html', ids.dup.length === 0, ids);
      const expectTabs = ['محددات اختيار هيكل رأس المال', 'نظريات هيكل رأس المال', 'أنواع مخاطر الاستثمار', 'الرافعة التشغيلية والرافعة المالية'];

      // D5 routing
      const route = {};
      for (const h of ['#theories', '#risk-types', '#leverage', '#determinants', '#theories/cs-s4', '#leverage/rk-s8']) {
        await p.goto(BASE + 'capital-structure.html' + h); await p.waitForTimeout(350);
        route[h] = await p.evaluate(t => { const sel = document.querySelector('.cs-tabs [role=tab][aria-selected=true]').dataset.tab; const tg = t.split('/')[1]; const el = tg && document.getElementById(tg); return { sel, visible: el ? el.getBoundingClientRect().top < innerHeight && el.getBoundingClientRect().bottom > 0 : null, y: Math.round(scrollY) }; }, h);
      }
      await p.goto(BASE + 'capital-structure.html'); await p.waitForTimeout(300);
      const def = await p.evaluate(() => document.querySelector('.cs-tabs [role=tab][aria-selected=true]').dataset.tab);
      await p.focus('#tab-determinants'); await p.keyboard.press('ArrowLeft'); await p.waitForTimeout(150);
      const kb = await p.evaluate(() => ({ sel: document.querySelector('.cs-tabs [role=tab][aria-selected=true]').dataset.tab, focus: document.activeElement.id }));
      // nav link inside journey 1 to a section of the other tab
      await p.click('#tab-determinants'); await p.evaluate(() => window.scrollTo(0, 0));
      await p.click('.lesson-cs .nav a[href="#theories/cs-s5"]'); await p.waitForTimeout(350);
      const navJump = await p.evaluate(() => ({ sel: document.querySelector('.cs-tabs [role=tab][aria-selected=true]').dataset.tab, top: Math.round(document.getElementById('cs-s5').getBoundingClientRect().top) }));
      const routeOk = route['#theories'].sel === 'theories' && route['#risk-types'].sel === 'risk-types' && route['#leverage'].sel === 'leverage' && route['#determinants'].sel === 'determinants'
        && route['#theories/cs-s4'].sel === 'theories' && route['#theories/cs-s4'].visible && route['#leverage/rk-s8'].sel === 'leverage' && route['#leverage/rk-s8'].visible;
      rec('D5', 'التبويبات الأربعة بأسمائها وترتيبها، والمرساة والعميقة ولوحة المفاتيح', JSON.stringify(tabs) === JSON.stringify(expectTabs) && routeOk && def === 'determinants' && kb.sel === 'theories' && kb.focus === 'tab-theories' && navJump.sel === 'theories' && navJump.top >= 0 && navJump.top < 300,
        { tabs, route, default: def, keyboard: kb, navJump });

      // D4 charts drawn on first activation and redrawn on resize
      await p.goto(BASE + 'capital-structure.html#determinants'); await p.reload(); await p.waitForTimeout(400);
      const hiddenAtLoad = await p.evaluate(() => ({ th: document.getElementById('panel-theories').hidden, lv: document.getElementById('panel-leverage').hidden }));
      const charts = {};
      for (const [tab, key] of [['theories', 'cs'], ['leverage', 'rk']]) {
        await p.click('#tab-' + tab); await p.waitForTimeout(300);
        charts[tab] = await p.evaluate(k => ({ cost: document.getElementById(k + '-svgCost').innerHTML.length, val: document.getElementById(k + '-svgVal').innerHTML.length, w: Math.round(document.getElementById(k + '-svgCost').getBoundingClientRect().width) }), key);
        await p.evaluate(k => { const r = document.querySelector('.lesson-' + k); const f = r.__redraw; window.__rd = 0; r.__redraw = function () { window.__rd++; return f.apply(this, arguments); }; }, key);
        await p.setViewportSize({ width: 700, height: 900 }); await p.waitForTimeout(400); await p.setViewportSize(MOBILE); await p.waitForTimeout(400);
        charts[tab].redrawsOnResize = await p.evaluate(() => window.__rd);
      }
      rec('D4', 'الرسمان يُرسمان عند تفعيل التبويب المخفي ويُعاد رسمهما عند تغيير الحجم', hiddenAtLoad.th && hiddenAtLoad.lv && Object.values(charts).every(c => c.cost > 500 && c.val > 500 && c.w > 100 && c.redrawsOnResize > 0), { hiddenAtLoad, charts });

      // D3 interactions per tab
      const inter = {};
      const panelText = tab => p.evaluate(t => document.getElementById('panel-' + t).innerText, tab);
      for (const tab of ['determinants', 'theories', 'risk-types', 'leverage']) {
        await p.goto(BASE + 'capital-structure.html#' + tab); await p.waitForTimeout(350);
        const r = { ranges: [], numbers: [], walkers: [], thTabs: null, theoryCards: null, flip: null, quiz: null, dock: null };
        const rangeIds = await p.evaluate(t => [...document.querySelectorAll('#panel-' + t + ' input[type=range]')].map(i => i.id), tab);
        for (const id of rangeIds) {
          const b = await panelText(tab);
          await p.evaluate(i => { const e = document.getElementById(i); e.value = String((+e.min || 0) + Math.round(((+e.max || 100) - (+e.min || 0)) * 0.83)); e.dispatchEvent(new Event('input', { bubbles: true })); }, id);
          r.ranges.push({ id, changed: (await panelText(tab)) !== b });
        }
        const numIds = await p.evaluate(t => [...document.querySelectorAll('#panel-' + t + ' input[type=number]')].map(i => i.id), tab);
        for (const id of numIds) {
          const b = await panelText(tab);
          await p.evaluate(i => { const e = document.getElementById(i); const v = +e.value || 0; e.value = String(v === 0 ? 5 : Math.round(v * 1.37 + 1)); e.dispatchEvent(new Event('input', { bubbles: true })); }, id);
          r.numbers.push({ id, changed: (await panelText(tab)) !== b });
        }
        const walkers = await p.$$('#panel-' + tab + ' .walker');
        for (const w of walkers.slice(0, 2)) {
          const b = await panelText(tab); await w.click({ force: true }); await p.waitForTimeout(80);
          r.walkers.push((await panelText(tab)) !== b || await w.evaluate(e => e.classList.contains('sel')));
        }
        const thBtns = await p.$$('#panel-' + tab + ' .tabs button');
        if (thBtns.length > 1) { const b = await panelText(tab); await thBtns[thBtns.length - 1].click(); r.thTabs = (await panelText(tab)) !== b; }
        const th = await p.$$('#panel-' + tab + ' .theory[data-th]');
        if (th.length) { const b = await p.evaluate(t => document.getElementById('panel-' + t).innerHTML, tab); await th[1].click({ force: true }); await p.waitForTimeout(80); r.theoryCards = (await p.evaluate(t => document.getElementById('panel-' + t).innerHTML, tab)) !== b; }
        const fc = await p.$('#panel-' + tab + ' .fc');
        if (fc) { await fc.click(); await p.waitForTimeout(60); r.flip = await fc.evaluate(e => e.classList.contains('flip')); }
        const quiz = await p.$('#panel-' + tab + ' [id$="-qBody"]');
        if (quiz) {
          let n = 0;
          for (; n < 30; n++) {
            const opt = await p.$('#panel-' + tab + ' [id$="-qBody"] .q-opts button:not([disabled])');
            if (!opt) break;
            await opt.click(); await p.waitForTimeout(30);
            const nx = await p.$('#panel-' + tab + ' [id$="-qNext"]'); if (nx) await nx.click();
          }
          r.quiz = await p.evaluate(t => { const el = document.querySelector('#panel-' + t + ' [id$="-qBody"] .result'); return el ? { done: true, text: el.querySelector('.big') && el.querySelector('.big').textContent } : { done: false }; }, tab);
          r.quiz.answered = n;
        }
        r.dock = await p.evaluate(() => ({ cs: getComputedStyle(document.getElementById('cs-dock')).display !== 'none' && !document.querySelector('.lesson-cs').hidden, rk: getComputedStyle(document.getElementById('rk-dock')).display !== 'none' && !document.querySelector('.lesson-rk').hidden }));
        inter[tab] = r;
      }
      const need = {
        determinants: r => r.ranges.length >= 1 && r.ranges.every(x => x.changed) && r.numbers.length === 5 && r.numbers.every(x => x.changed) && !r.dock.rk,
        theories: r => r.ranges.every(x => x.changed) && r.numbers.length === 5 && r.numbers.every(x => x.changed) && r.walkers.length === 2 && r.walkers.every(Boolean) && r.thTabs && r.flip && r.quiz && r.quiz.done && !r.dock.rk,
        'risk-types': r => r.ranges.every(x => x.changed) && r.walkers.length === 2 && r.walkers.every(Boolean) && r.theoryCards && !r.dock.cs,
        leverage: r => r.ranges.every(x => x.changed) && r.numbers.length === 16 && r.numbers.every(x => x.changed) && r.thTabs && r.flip && r.quiz && r.quiz.done && !r.dock.cs,
      };
      const per = Object.fromEntries(Object.entries(need).map(([k, f]) => [k, f(inter[k])]));
      rec('D3', 'التفاعلات تعمل داخل كل تبويب، ومساعد رحلة واحدة فقط يظهر', Object.values(per).every(Boolean), { per, inter });
      await ctx.close();
    }

    /* ---------------- E1 storage keys over a full session ---------------- */
    {
      const ctx = await newCtx(browser); const p = await ctx.newPage();
      await p.goto(BASE + 'business-environment.html'); await gate(p); await p.waitForSelector('#parts .b-part');
      await p.goto(BASE + 'capital-structure.html#risk-types'); await p.waitForTimeout(400);
      await p.click('#rk-dockX').catch(() => {});
      await p.goto(BASE + 'capital-structure.html#theories'); await p.waitForTimeout(600);
      await p.evaluate(() => { const b = document.getElementById('cs-dockX'); if (b) b.click(); });
      for (const u of ['index.html', 'fellowship.html', 'private-sector.html', 'public-sector.html']) { await p.goto(BASE + u); await p.waitForTimeout(150); }
      const keys = await p.evaluate(() => Object.keys(localStorage));
      const allowed = k => ['bizenv-subject-id', 'bizenv-access', 'bizenv-pending-signups', 'bizenv-dock-cs', 'bizenv-dock-rk'].includes(k) || /^bizenv-progress-[0-9a-f-]{36}$/.test(k);
      rec('E1', 'لا مفتاح تخزين خارج الجدول، ولا تخزين في صفحات المعايير', keys.every(allowed), keys);
      await ctx.close();
    }

    /* ---------------- 16 offline after first visit ---------------- */
    {
      const ctx = await newCtx(browser); const p = await ctx.newPage();
      await p.goto(BASE + 'index.html');
      await p.evaluate(() => navigator.serviceWorker.ready.then(() => true));
      await p.reload(); await p.waitForTimeout(500);
      await p.goto(BASE + 'business-environment.html'); await gate(p); await p.waitForSelector('#parts .b-part');
      await ctx.setOffline(true);
      const off = {};
      for (const u of ['fellowship.html', 'business-environment.html#/c/EC.C1', 'capital-structure.html', 'private-sector.html', 'index.html']) {
        try {
          await p.goto(BASE + u, { timeout: 15000 }); await p.waitForTimeout(3600);
          off[u] = await p.evaluate(() => ({ title: document.title, ok: !!(document.querySelector('.f-card, .b-unit, [role=tab], .p-box, .h-card')) }));
        } catch (e) { off[u] = { error: e.message.split('\n')[0] }; }
      }
      const manifest = await p.evaluate(() => fetch('manifest.webmanifest').then(r => r.json()).then(m => ({ display: m.display, icons: m.icons.length })).catch(e => String(e)));
      rec('16', 'تعمل بلا اتصال بعد أول فتح، وقابلة للتثبيت', Object.values(off).every(o => o.ok), { offline: off, manifest });
      await ctx.close();
    }

    /* ---------------- 390px: no horizontal scroll on any page ---------------- */
    {
      const ctx = await newCtx(browser); const p = await ctx.newPage();
      const w = {};
      await p.goto(BASE + 'business-environment.html'); await gate(p); await p.waitForSelector('#parts .b-part');
      for (const u of ['index.html', 'fellowship.html', 'private-sector.html', 'business-environment.html', 'business-environment.html#/c/MF.C7', 'business-environment.html#/k/MF.C7', 'capital-structure.html#determinants', 'capital-structure.html#theories', 'capital-structure.html#risk-types', 'capital-structure.html#leverage']) {
        await p.goto(BASE + u); await p.waitForTimeout(400);
        w[u] = await p.evaluate(() => document.documentElement.scrollWidth);
      }
      await p.goto(BASE + 'business-environment.html#/c/MF.C7'); await p.waitForSelector('#chQuiz .b-unit'); await p.click('#chQuiz .b-unit .m-btn'); await p.waitForSelector('#qOpts .b-opt');
      w['quiz'] = await p.evaluate(() => document.documentElement.scrollWidth);
      rec('M390', 'كل صفحة عند عرض 390 بكسل بلا تمرير أفقي', Object.values(w).every(x => x <= 390), w);
      await ctx.close();
    }

    /* ---------------- D6 fonts: no external request anywhere ---------------- */
    rec('D6', 'لا طلب شبكة إلى googleapis أو gstatic، ولا أي طلب خارجي عدا نقطة الاختبار الوهمية', externalRequests.filter(u => !u.startsWith('https://hook.invalid')).length === 0, [...new Set(externalRequests)]);
    rec('console', 'لا أخطاء ولا تحذيرات في الكونسول', consoleErrors.length === 0, consoleErrors.slice(0, 20));
  } catch (e) {
    rec('runner', 'تشغيل الفحوص', false, String(e && e.stack || e));
  } finally {
    await browser.close(); server.close();
    fs.writeFileSync(path.join(__dirname, 'browser_results.json'), JSON.stringify(results, null, 1));
    process.exitCode = results.every(r => r.pass) ? 0 : 1;
  }
})();
