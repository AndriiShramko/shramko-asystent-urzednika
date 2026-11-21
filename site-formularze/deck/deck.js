/*
 * deck.js — the engine. Texts are in slides.js, drawings in scenes.js.
 *
 * Modes (from the URL):
 *   index.html#3             audience window, slide 3
 *   index.html?presenter=1   presenter window (normally opened with key P)
 *   index.html?print=1       all slides, final frames, for the PDF
 *
 * The two windows talk through three channels at once (whichever works):
 *   1. window.opener / popup reference + postMessage (works from file://)
 *   2. BroadcastChannel
 *   3. localStorage "storage" event
 * Every message carries the sender id and a sequence number, so duplicates
 * arriving through several channels are applied once.
 */
(function () {
  'use strict';
  var D = window.DECK;
  var SLIDES = D.slides;
  var N = SLIDES.length;
  var params = new URLSearchParams(location.search);
  var MODE = params.get('print') ? 'print' : params.get('presenter') ? 'presenter' : 'audience';
  var app = document.getElementById('app');
  var metrics = {};

  /* ---------------- helpers ---------------- */
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  function clamp(i) { return Math.max(0, Math.min(N - 1, i | 0)); }
  function hashIndex() {
    var m = /^#(\d+)/.exec(location.hash);
    return m ? clamp(parseInt(m[1], 10) - 1) : 0;
  }
  function setHash(i) {
    try { history.replaceState(null, '', '#' + (i + 1)); } catch (e) { location.hash = '#' + (i + 1); }
  }

  /* metrics.json / status.json over http; from disk (file://) browsers block
     fetch, so the copies metrics.js / status.js (window.DECK_METRICS,
     window.DECK_STATUS) are used. tools/deck_pdf.mjs regenerates the copies. */
  function loadJson(name, fallback) {
    if (location.protocol === 'file:' || !window.fetch) return Promise.resolve(fallback);
    return fetch(name, { cache: 'no-store' })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .catch(function () { return fallback; });
  }
  var status = { works: [], simulated: [] };

  /* ---------------- messaging between the two windows ---------------- */
  var ID = Math.random().toString(36).slice(2);
  var seq = 0;
  var seen = {};
  var popup = null; // presenter window reference (audience side)
  var bc = null;
  try { bc = new BroadcastChannel('asystent-deck'); } catch (e) { bc = null; }
  var handlers = {};

  function send(type, data) {
    var msg = { deck: 'asystent', type: type, src: ID, seq: ++seq, data: data || {} };
    var peer = MODE === 'presenter' ? window.opener : popup;
    try { if (peer && !peer.closed) peer.postMessage(msg, '*'); } catch (e) { /* ignore */ }
    try { if (bc) bc.postMessage(msg); } catch (e) { /* ignore */ }
    try { localStorage.setItem('asystent-deck-msg', JSON.stringify(msg)); } catch (e) { /* ignore */ }
  }
  function receive(msg) {
    if (!msg || msg.deck !== 'asystent' || msg.src === ID) return;
    var key = msg.src + ':' + msg.seq;
    if (seen[key]) return;
    seen[key] = 1;
    if (handlers[msg.type]) handlers[msg.type](msg.data || {});
  }
  window.addEventListener('message', function (ev) { receive(ev.data); });
  if (bc) bc.onmessage = function (ev) { receive(ev.data); };
  window.addEventListener('storage', function (ev) {
    if (ev.key !== 'asystent-deck-msg' || !ev.newValue) return;
    try { receive(JSON.parse(ev.newValue)); } catch (e) { /* ignore */ }
  });

  /* ---------------- building one slide ---------------- */
  // Shrink the big words until they fit: one line if possible, else two lines.
  function fitWords(h) {
    var sizes = [132, 124, 116, 108, 100];
    h.style.whiteSpace = 'nowrap';
    for (var k = 0; k < sizes.length; k++) {
      h.style.fontSize = sizes[k] + 'px';
      if (h.scrollWidth <= h.clientWidth + 1) return;
    }
    h.style.whiteSpace = 'normal';
    for (var s = 112; s >= 64; s -= 4) {
      h.style.fontSize = s + 'px';
      if (h.scrollHeight <= 280 && h.scrollWidth <= h.clientWidth + 1) return;
    }
  }

  /* Timers created by a scene are tracked here and cleared on slide change. */
  function makeCtx(i, opts) {
    var timers = [];
    return {
      index: i, slide: SLIDES[i], metrics: metrics, labels: D.metricLabels || {}, status: status,
      final: !!opts.final, reduced: !!opts.reduced,
      later: function (fn, ms) { timers.push(setTimeout(fn, ms)); },
      every: function (fn, ms) { timers.push(setInterval(fn, ms)); },
      dispose: function () { timers.forEach(function (t) { clearTimeout(t); clearInterval(t); }); timers = []; }
    };
  }

  // Returns {node, dispose}. opts.final: show the last frame without motion.
  function buildStage(i, opts) {
    var s = SLIDES[i];
    var stage = el('section', 'stage');
    stage.setAttribute('aria-label', 'Slajd ' + (i + 1) + ' z ' + N);
    var h = el('h1', 'words', s.screen);
    var scene = el('div', 'scene');
    var sc = window.SCENES[s.scene];
    var ctx = makeCtx(i, opts);
    scene.innerHTML = sc ? sc.svg(ctx) : '';
    scene.style.setProperty('--L', (sc && sc.L ? sc.L : 8) + 's');
    stage.appendChild(h);
    stage.appendChild(scene);
    var cap = el('p', 'caption', s.caption);
    stage.appendChild(cap);
    var foot = el('div', 'foot');
    if (MODE === 'print') {
      foot.appendChild(el('span', '', D.footer));
      foot.appendChild(el('span', '', (i + 1) + ' / ' + N));
    } else {
      foot.appendChild(el('span', '', ''));
      foot.appendChild(el('span', '', (i + 1) + ' / ' + N));
    }
    stage.appendChild(foot);
    return {
      node: stage, words: h,
      start: function () { if (sc && sc.run) sc.run(scene, ctx); },
      dispose: ctx.dispose
    };
  }

  /* ---------------- audience window ---------------- */
  function audience() {
    document.body.className = 'audience';
    var mq = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : { matches: false };
    var motionOff = mq.matches;
    var cur = -1;
    var live = null;
    var jump = el('div', 'jump');
    var flag = el('div', 'motion-flag');
    var holder = el('div');
    app.appendChild(holder);
    app.appendChild(jump);
    app.appendChild(flag);

    function scale() {
      var k = Math.min(window.innerWidth / 1920, window.innerHeight / 1080);
      document.documentElement.style.setProperty('--k', k);
    }
    window.addEventListener('resize', scale);
    scale();

    function render() {
      if (live) live.dispose();
      holder.innerHTML = '';
      document.documentElement.classList.toggle('still', motionOff);
      document.documentElement.classList.toggle('reduced', motionOff);
      live = buildStage(cur, { final: motionOff, reduced: motionOff });
      holder.appendChild(live.node);
      fitWords(live.words);
      live.start();
    }
    function go(i, remote) {
      i = clamp(i);
      if (i === cur) return;
      cur = i;
      setHash(cur);
      render();
      if (!remote) send('goto', { n: cur });
    }
    function toggleMotion(remote) {
      motionOff = !motionOff;
      flag.textContent = motionOff ? 'M' : '';
      render();
      if (!remote) send('motion', { off: motionOff });
    }

    handlers.goto = function (d) { go(d.n, true); };
    handlers.hello = function () { send('state', { n: cur }); };
    handlers.motion = function () { toggleMotion(true); };
    window.addEventListener('hashchange', function () { go(hashIndex()); });

    var buf = '';
    var bufTimer = null;
    function setBuf(v) {
      buf = v; jump.textContent = buf;
      clearTimeout(bufTimer);
      if (buf) bufTimer = setTimeout(function () { setBuf(''); }, 3000);
    }
    document.addEventListener('keydown', function (ev) {
      if (ev.ctrlKey || ev.metaKey || ev.altKey) return;
      var k = ev.key;
      if (/^[0-9]$/.test(k)) { setBuf((buf + k).slice(-2)); ev.preventDefault(); return; }
      if (k === 'Enter' && buf) { go(parseInt(buf, 10) - 1); setBuf(''); ev.preventDefault(); return; }
      if (k === 'Escape') { setBuf(''); return; }
      if (k === 'ArrowRight' || k === ' ' || k === 'PageDown' || k === 'ArrowDown') go(cur + 1);
      else if (k === 'ArrowLeft' || k === 'PageUp' || k === 'ArrowUp') go(cur - 1);
      else if (k === 'Home') go(0);
      else if (k === 'End') go(N - 1);
      else if (k === 'f' || k === 'F') {
        if (document.fullscreenElement) document.exitFullscreen();
        else if (document.documentElement.requestFullscreen) document.documentElement.requestFullscreen();
      } else if (k === 'p' || k === 'P') {
        var url = location.href.split(/[?#]/)[0] + '?presenter=1#' + (cur + 1);
        popup = window.open(url, 'asystent-presenter', 'width=1280,height=860');
      } else if (k === 'm' || k === 'M') toggleMotion();
      else return;
      ev.preventDefault();
    });
    // Clicking the slide advances (left two thirds) or goes back (left third).
    document.addEventListener('click', function (ev) {
      if (ev.clientX < window.innerWidth / 3) go(cur - 1); else go(cur + 1);
    });

    go(hashIndex(), true);
  }

  /* ---------------- presenter window ---------------- */
  function presenter() {
    document.body.className = 'presenter';
    document.title = 'Prelegent — ' + D.title;
    var cur = hashIndex();
    var timerStart = 0;          // 0 = not started yet
    var total = D.durationSec || 300;

    var root = el('div', 'pv');
    var top = el('div', 'pv-top');
    var num = el('span', 'pv-num');
    var timer = el('span', 'pv-timer idle');
    var reset = el('button', '', 'Reset 5:00');
    var next = el('div', 'pv-next');
    top.appendChild(num); top.appendChild(timer); top.appendChild(reset); top.appendChild(next);
    var main = el('div', 'pv-main');
    var say = el('div', 'pv-say');
    say.setAttribute('lang', 'pl');
    var ru = el('div', 'pv-ru');
    ru.setAttribute('lang', 'ru');
    var cue = el('div', 'pv-cue');
    cue.setAttribute('lang', 'ru');
    main.appendChild(say); main.appendChild(ru); main.appendChild(cue);
    var bottom = el('div');
    var grid = el('div', 'pv-answers');
    var help = el('div', 'pv-link', '← → Spacja PageUp/PageDown: slajdy · 1–9, 0: odpowiedzi · Esc: zamknij · M: ruch');
    var phrases = el('div', 'pv-phrases');
    phrases.setAttribute('lang', 'pl');
    (D.phrases || []).forEach(function (p) { phrases.appendChild(el('span', '', '„' + p + '”')); });
    bottom.appendChild(grid); bottom.appendChild(phrases); bottom.appendChild(help);
    root.appendChild(top); root.appendChild(main); root.appendChild(bottom);

    var ans = el('div', 'pv-answer');
    ans.setAttribute('role', 'dialog');
    var ansQ = el('h2'); var ansA = el('p'); ansA.setAttribute('lang', 'pl');
    var ansRu = el('p', 'ru'); ansRu.setAttribute('lang', 'ru');
    var ansClose = el('button', '', 'Zamknij (Esc)');
    ans.appendChild(ansQ); ans.appendChild(ansA); ans.appendChild(ansRu); ans.appendChild(ansClose);
    var ansPhr = el('div', 'pv-phrases');
    ansPhr.setAttribute('lang', 'pl');
    (D.phrases || []).forEach(function (p) { ansPhr.appendChild(el('span', '', '„' + p + '”')); });
    ans.appendChild(ansPhr);
    app.appendChild(root); app.appendChild(ans);

    var lastFocus = null;
    function openAnswer(key) {
      var a = D.answers.filter(function (x) { return x.key === key; })[0];
      if (!a) return;
      lastFocus = document.activeElement;
      ansQ.textContent = a.key + '. ' + a.q;
      ansA.textContent = a.a;
      ansRu.textContent = a.ru;
      ans.classList.add('open');
      ansClose.focus();
    }
    function closeAnswer() {
      if (!ans.classList.contains('open')) return false;
      ans.classList.remove('open');
      if (lastFocus && lastFocus.focus) lastFocus.focus();
      return true;
    }
    ansClose.addEventListener('click', closeAnswer);
    D.answers.forEach(function (a) {
      var b = el('button');
      var kb = el('kbd', '', a.key);
      b.appendChild(kb);
      b.appendChild(document.createTextNode(a.q));
      b.addEventListener('click', function () { openAnswer(a.key); });
      grid.appendChild(b);
    });

    function fmt(sec) {
      var neg = sec < 0; sec = Math.abs(sec);
      var m = Math.floor(sec / 60), s = sec % 60;
      return (neg ? '−' : '') + m + ':' + (s < 10 ? '0' : '') + s;
    }
    function tick() {
      if (!timerStart) { timer.textContent = fmt(total); timer.className = 'pv-timer idle'; return; }
      var elapsed = Math.floor((Date.now() - timerStart) / 1000);
      var left = total - elapsed;
      timer.textContent = fmt(left);
      timer.className = 'pv-timer' + (left < 0 ? ' over' : elapsed >= (D.warnAfterSec || 240) ? ' warn' : '');
    }
    setInterval(tick, 250);
    reset.addEventListener('click', function () { timerStart = 0; tick(); });

    function render() {
      var s = SLIDES[cur];
      num.textContent = (cur + 1) + ' / ' + N;
      // slide 7: "say" if the feature is built, otherwise the fallback wording
      say.textContent = (s.sayFallback && !s.built) ? s.sayFallback : s.say;
      ru.textContent = s.ru;
      cue.textContent = s.cue;
      next.textContent = '';
      next.appendChild(document.createTextNode('Dalej: '));
      next.appendChild(el('b', '', cur + 1 < N ? SLIDES[cur + 1].screen : '— koniec —'));
      setHash(cur);
      tick();
    }
    function set(i, remote) {
      i = clamp(i);
      if (i > cur && !timerStart) timerStart = Date.now(); // timer starts on the first advance
      if (i === cur) return;
      cur = i;
      render();
      if (!remote) send('goto', { n: cur });
    }
    handlers.goto = function (d) { set(d.n, true); };
    handlers.state = function (d) { cur = clamp(d.n); render(); };

    document.addEventListener('keydown', function (ev) {
      if (ev.ctrlKey || ev.metaKey || ev.altKey) return;
      var k = ev.key;
      if (k === 'Escape') { closeAnswer(); return; }
      if (/^[0-9]$/.test(k)) { openAnswer(k); ev.preventDefault(); return; }
      if (k === 'ArrowRight' || k === ' ' || k === 'PageDown' || k === 'ArrowDown') { closeAnswer(); set(cur + 1); }
      else if (k === 'ArrowLeft' || k === 'PageUp' || k === 'ArrowUp') { closeAnswer(); set(cur - 1); }
      else if (k === 'Home') set(0);
      else if (k === 'End') set(N - 1);
      else if (k === 'm' || k === 'M') send('motion', {});
      else return;
      ev.preventDefault();
    });

    render();
    send('hello', {}); // ask the audience window which slide is showing
  }

  /* ---------------- print mode ---------------- */
  function printMode() {
    document.body.className = 'print';
    document.documentElement.classList.add('still');
    for (var i = 0; i < N; i++) {
      var page = el('div', 'page');
      var st = buildStage(i, { final: true, reduced: true });
      page.appendChild(st.node);
      app.appendChild(page);
      fitWords(st.words);
      st.start();
    }
    document.documentElement.setAttribute('data-ready', '1');
  }

  Promise.all([
    loadJson('metrics.json', window.DECK_METRICS || {}),
    loadJson('status.json', window.DECK_STATUS || status)
  ]).then(function (r) {
    metrics = r[0] || {};
    status = r[1] || status;
    if (MODE === 'print') printMode();
    else if (MODE === 'presenter') presenter();
    else audience();
  });
})();
