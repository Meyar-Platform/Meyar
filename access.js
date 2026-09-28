/*
 * access.js, email gate for the SOCPA fellowship section (business-environment).
 *
 * Public interface, the only thing the rest of the code calls:
 *     ensureAccess(entryId) -> Promise<boolean>
 * plus two helpers the quiz engine needs to key progress:
 *     MeyarAccess.subjectId()      stable id, generated once
 *     MeyarAccess.progressKey()    "bizenv-progress-<subject_id>"
 *
 * What this gate is and is not:
 *   The pages are static files on GitHub Pages and the data files can be
 *   opened directly by anyone who knows their address. This gate does NOT
 *   protect content. Its purpose is to know who uses the platform and to build
 *   a list for a future subscription. Replacing it with real authentication
 *   means replacing this file alone.
 *
 * ACCESS_ENDPOINT:
 *   Fill it with the URL of a Google Apps Script web app that appends each
 *   record to a Google Sheet owned by the platform owner.
 *   While it is EMPTY (as delivered) the gate still works fully: every sign-up
 *   record is kept in a local queue under "bizenv-pending-signups". The first
 *   time a page loads after ACCESS_ENDPOINT is set, the whole queue is sent
 *   automatically and each record is removed once its request completes, so
 *   nobody who signed up before the endpoint existed is lost.
 *
 * Record shape (fixed, import-ready; v is the record version):
 *   {"v":1,"subject_id":"<uuid>","email":"<email>","ts":"<ISO8601>",
 *    "section":"business-environment","entry":"business-environment|capital-structure",
 *    "consent":true,"source":"meyarplatform.com"}
 *
 * Local storage keys used here, and only these:
 *   bizenv-subject-id, bizenv-access, bizenv-pending-signups
 * Every read and write is wrapped in try/catch; with storage blocked the gate
 * still lets the visitor in for the current page view.
 */
(function () {
  "use strict";

  var ACCESS_ENDPOINT = ""; // يُملأ برابط Google Apps Script

  var K_SUBJECT = "bizenv-subject-id";
  var K_ACCESS = "bizenv-access";
  var K_QUEUE = "bizenv-pending-signups";
  var SECTION = "business-environment";
  var SOURCE = "meyarplatform.com";
  var memory = {};

  function lsGet(k) {
    try { var v = window.localStorage.getItem(k); return v === null ? (k in memory ? memory[k] : null) : v; }
    catch (e) { return k in memory ? memory[k] : null; }
  }
  function lsSet(k, v) {
    memory[k] = v;
    try { window.localStorage.setItem(k, v); return true; } catch (e) { return false; }
  }
  function readJSON(k, fallback) {
    try { var v = lsGet(k); return v ? JSON.parse(v) : fallback; } catch (e) { return fallback; }
  }

  function uuid() {
    try { if (window.crypto && crypto.randomUUID) return crypto.randomUUID(); } catch (e) {}
    var b = new Uint8Array(16);
    try { crypto.getRandomValues(b); } catch (e) { for (var i = 0; i < 16; i++) b[i] = Math.floor(Math.random() * 256); }
    b[6] = (b[6] & 15) | 64; b[8] = (b[8] & 63) | 128;
    var h = Array.prototype.map.call(b, function (x) { return (x + 256).toString(16).slice(1); }).join("");
    return h.slice(0, 8) + "-" + h.slice(8, 12) + "-" + h.slice(12, 16) + "-" + h.slice(16, 20) + "-" + h.slice(20);
  }

  function subjectId() {
    var id = lsGet(K_SUBJECT);
    if (!id) { id = uuid(); lsSet(K_SUBJECT, id); }
    return id;
  }

  function progressKey() { return "bizenv-progress-" + subjectId(); }

  function hasAccess() {
    var a = readJSON(K_ACCESS, null);
    return !!(a && a.subject_id && a.email);
  }

  function queue() { var q = readJSON(K_QUEUE, []); return Array.isArray(q) ? q : []; }
  function saveQueue(q) { lsSet(K_QUEUE, JSON.stringify(q)); }

  var flushing = false;
  function flushQueue() {
    if (!ACCESS_ENDPOINT || flushing) return Promise.resolve();
    var q = queue();
    if (!q.length) return Promise.resolve();
    flushing = true;
    var sent = [];
    return Promise.all(q.map(function (rec) {
      return fetch(ACCESS_ENDPOINT, {
        method: "POST",
        mode: "no-cors",
        headers: { "Content-Type": "text/plain;charset=utf-8" },
        body: JSON.stringify(rec)
      }).then(function () { sent.push(rec.subject_id + "|" + rec.ts); }, function () {});
    })).then(function () {
      var rest = queue().filter(function (r) { return sent.indexOf(r.subject_id + "|" + r.ts) === -1; });
      saveQueue(rest);
      flushing = false;
    });
  }

  function validEmail(v) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v) && v.length <= 254;
  }

  function record(email, entryId) {
    return {
      v: 1,
      subject_id: subjectId(),
      email: email,
      ts: new Date().toISOString(),
      section: SECTION,
      entry: entryId,
      consent: true,
      source: SOURCE
    };
  }

  function showGate(entryId, resolve) {
    var wrap = document.createElement("div");
    wrap.className = "m-gate";
    wrap.setAttribute("role", "dialog");
    wrap.setAttribute("aria-modal", "true");
    wrap.setAttribute("aria-labelledby", "m-gate-title");
    wrap.innerHTML =
      '<form class="m-gate-box" novalidate>' +
      '<h2 id="m-gate-title">للدخول إلى مادة بيئة الأعمال</h2>' +
      '<p>اكتب بريدك الإلكتروني للمتابعة. نستخدمه لمعرفة من يستفيد من المنصة وللتواصل بشأن التحديثات، ولا يُشارك مع أي جهة.</p>' +
      '<div class="m-gate-row">' +
      '<input type="email" id="m-gate-email" name="email" autocomplete="email" inputmode="email" required aria-label="البريد الإلكتروني" placeholder="البريد الإلكتروني">' +
      '<button type="submit" class="m-btn">متابعة</button>' +
      '</div>' +
      '<div class="m-gate-err" id="m-gate-err" role="alert"></div>' +
      '<div class="m-gate-free"><a href="fellowship.html">صفحة التحضير لزمالة SOCPA</a> متاحة بلا تسجيل.</div>' +
      '</form>';
    document.body.appendChild(wrap);
    var form = wrap.querySelector("form");
    var input = wrap.querySelector("#m-gate-email");
    var err = wrap.querySelector("#m-gate-err");
    setTimeout(function () { try { input.focus(); } catch (e) {} }, 30);
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var email = (input.value || "").trim();
      if (!validEmail(email)) { err.textContent = "اكتب بريداً إلكترونياً صحيحاً."; input.focus(); return; }
      var rec = record(email, entryId);
      var q = queue(); q.push(rec); saveQueue(q);
      lsSet(K_ACCESS, JSON.stringify({ subject_id: rec.subject_id, email: email, ts: rec.ts }));
      wrap.parentNode.removeChild(wrap);
      flushQueue();
      resolve(true);
    });
  }

  var pending = null;
  function ensureAccess(entryId) {
    subjectId();
    if (hasAccess()) { flushQueue(); return Promise.resolve(true); }
    if (pending) return pending;
    pending = new Promise(function (resolve) {
      var go = function () { showGate(entryId || SECTION, resolve); };
      if (document.body) go(); else document.addEventListener("DOMContentLoaded", go);
    });
    return pending;
  }

  window.ensureAccess = ensureAccess;
  window.MeyarAccess = { ensureAccess: ensureAccess, subjectId: subjectId, progressKey: progressKey };
})();
