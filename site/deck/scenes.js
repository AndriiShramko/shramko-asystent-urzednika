/*
 * scenes.js — the 11 animated drawings (inline SVG, viewBox 1600x720).
 *
 * Each scene: { L: seconds after which the gentle loop starts,
 *               svg(ctx): markup string,
 *               run(root, ctx): optional small JS timeline }
 * ctx.final === true means "draw the last frame, no motion" (print, key M,
 * prefers-reduced-motion). The natural, un-animated state of every element is
 * its final state; CSS classes in deck.css add the motion:
 *   class="e pop" style="--d:1.2s"   entrance (pop, fade, rise, drop, flip, slideL, slideR, draw, grow, out)
 *   class="lp bob" style="--ld:.5s"  loop after the entrance (bob, pulse, glow, flow, spin, tap)
 *   class="lp-only"                  shown only while animating (hidden in print)
 *   class="print-only"               shown only in the final frame
 * Rule: never put "e" and "lp" on the same element; nest a <g> instead.
 * Labels inside drawings are Polish and at most three words.
 *
 * Demo video for slide 4: put a file at site/deck/media/demo.mp4 — it then
 * replaces the animated mock automatically (muted, looped).
 */
(function () {
  'use strict';

  /* ---------------- small drawing kit ---------------- */
  function svg(label, inner) {
    return '<svg viewBox="0 0 1600 720" role="img" aria-label="' + label + '" xmlns="http://www.w3.org/2000/svg">' + inner + '</svg>';
  }
  function d(sec) { return 'style="--d:' + sec + 's"'; }
  // text: x, y, string, size, extra class, anchor
  function t(x, y, s, size, cls, anchor) {
    return '<text x="' + x + '" y="' + y + '" font-size="' + (size || 44) + '" text-anchor="' + (anchor || 'middle') + '"' +
      (cls ? ' class="' + cls + '"' : '') + '>' + s + '</text>';
  }
  // envelope with top-left corner at x,y
  function env(x, y, w) {
    var h = Math.round(w * 0.66);
    return '<g transform="translate(' + x + ',' + y + ')"><rect width="' + w + '" height="' + h + '" rx="' + Math.round(w / 10) + '" class="fa"/>' +
      '<path d="M' + (w * 0.08) + ' ' + (h * 0.12) + ' L' + (w / 2) + ' ' + (h * 0.58) + ' L' + (w * 0.92) + ' ' + (h * 0.12) + '" class="fn sbg" stroke-width="' + Math.max(4, w / 18) + '"/></g>';
  }
  // sheet of paper with lines
  function doc(x, y, w, h, lineCls) {
    var s = '<g transform="translate(' + x + ',' + y + ')"><rect width="' + w + '" height="' + h + '" rx="14" class="fi"/>';
    for (var k = 0; k < 4; k++) {
      var ly = h * 0.22 + k * h * 0.17;
      s += '<line x1="' + w * 0.16 + '" y1="' + ly + '" x2="' + w * (k === 3 ? 0.6 : 0.84) + '" y2="' + ly + '" class="' + (lineCls || 'sl') + '" stroke-width="' + Math.max(5, w / 16) + '"/>';
    }
    return s + '</g>';
  }
  function tick(x, y, s, cls) {
    return '<path d="M' + (x - s) + ' ' + y + ' l' + (s * 0.7) + ' ' + (s * 0.7) + ' l' + (s * 1.3) + ' ' + (-s * 1.4) + '" class="fn ' + (cls || 'sg') + '" stroke-width="' + Math.max(8, s / 3) + '"/>';
  }
  function person(cx, top, s, cls) {
    cls = cls || 'fb';
    return '<circle cx="' + cx + '" cy="' + (top + 26 * s) + '" r="' + 26 * s + '" class="' + cls + '"/>' +
      '<path d="M' + (cx - 46 * s) + ' ' + (top + 130 * s) + ' a' + 46 * s + ' ' + 52 * s + ' 0 0 1 ' + 92 * s + ' 0 z" class="' + cls + '"/>';
  }
  function lock(cx, cy, s, cls) {
    return '<g transform="translate(' + cx + ',' + cy + ') scale(' + s + ')"><path d="M-14 -6 v-12 a14 14 0 0 1 28 0 v12" class="fn ' + (cls ? 's' + cls.slice(1) : 'sg') + '" stroke-width="7"/>' +
      '<rect x="-22" y="-8" width="44" height="34" rx="8" class="' + (cls || 'fg') + '"/></g>';
  }
  function building(cx, y, w, h, strokeCls) {
    var x = cx - w / 2;
    var s = '<path d="M' + (x - 14) + ' ' + (y + 40) + ' L' + cx + ' ' + (y - 20) + ' L' + (x + w + 14) + ' ' + (y + 40) + ' Z" class="fp ' + strokeCls + '" stroke-width="8"/>' +
      '<rect x="' + x + '" y="' + (y + 40) + '" width="' + w + '" height="' + h + '" class="fp ' + strokeCls + '" stroke-width="8"/>';
    for (var k = 1; k <= 3; k++) {
      var cx2 = x + (w * k) / 4;
      s += '<line x1="' + cx2 + '" y1="' + (y + 62) + '" x2="' + cx2 + '" y2="' + (y + 40 + h - 18) + '" class="' + strokeCls + '" stroke-width="8"/>';
    }
    return s;
  }
  function chip(x, y, w, h, text, size, fillCls, textCls) {
    return '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="' + h / 2 + '" class="' + fillCls + '"/>' +
      t(x + w / 2, y + h / 2 + size * 0.36, text, size, textCls);
  }

  /* QR code for https://urzad.flyreelstudio.eu (version 3, ECC M, 29x29).
     Generated with the Python "qrcode" package; decoded back with OpenCV. */
  var QR_N = 29;
  var QR_PATH = 'M0 0h7v1h-7zM9 0h1v1h-1zM13 0h1v1h-1zM16 0h1v1h-1zM19 0h1v1h-1zM22 0h7v1h-7zM0 1h1v1h-1zM6 1h1v1h-1zM9 1h3v1h-3zM13 1h3v1h-3zM17 1h2v1h-2zM20 1h1v1h-1zM22 1h1v1h-1zM28 1h1v1h-1zM0 2h1v1h-1zM2 2h3v1h-3zM6 2h1v1h-1zM13 2h1v1h-1zM16 2h4v1h-4zM22 2h1v1h-1zM24 2h3v1h-3zM28 2h1v1h-1zM0 3h1v1h-1zM2 3h3v1h-3zM6 3h1v1h-1zM9 3h3v1h-3zM13 3h3v1h-3zM18 3h3v1h-3zM22 3h1v1h-1zM24 3h3v1h-3zM28 3h1v1h-1zM0 4h1v1h-1zM2 4h3v1h-3zM6 4h1v1h-1zM13 4h2v1h-2zM16 4h1v1h-1zM22 4h1v1h-1zM24 4h3v1h-3zM28 4h1v1h-1zM0 5h1v1h-1zM6 5h1v1h-1zM8 5h7v1h-7zM18 5h3v1h-3zM22 5h1v1h-1zM28 5h1v1h-1zM0 6h7v1h-7zM8 6h1v1h-1zM10 6h1v1h-1zM12 6h1v1h-1zM14 6h1v1h-1zM16 6h1v1h-1zM18 6h1v1h-1zM20 6h1v1h-1zM22 6h7v1h-7zM9 7h2v1h-2zM12 7h1v1h-1zM14 7h1v1h-1zM17 7h2v1h-2zM20 7h1v1h-1zM0 8h1v1h-1zM3 8h1v1h-1zM5 8h2v1h-2zM8 8h3v1h-3zM12 8h1v1h-1zM15 8h1v1h-1zM19 8h1v1h-1zM21 8h1v1h-1zM23 8h1v1h-1zM0 9h2v1h-2zM5 9h1v1h-1zM7 9h2v1h-2zM10 9h2v1h-2zM14 9h2v1h-2zM17 9h1v1h-1zM20 9h3v1h-3zM25 9h1v1h-1zM28 9h1v1h-1zM0 10h7v1h-7zM10 10h3v1h-3zM16 10h1v1h-1zM19 10h1v1h-1zM21 10h1v1h-1zM23 10h5v1h-5zM5 11h1v1h-1zM8 11h3v1h-3zM14 11h2v1h-2zM19 11h1v1h-1zM21 11h1v1h-1zM26 11h2v1h-2zM1 12h2v1h-2zM4 12h4v1h-4zM9 12h1v1h-1zM11 12h2v1h-2zM16 12h2v1h-2zM20 12h1v1h-1zM22 12h1v1h-1zM25 12h1v1h-1zM27 12h2v1h-2zM0 13h1v1h-1zM2 13h1v1h-1zM7 13h2v1h-2zM11 13h1v1h-1zM15 13h1v1h-1zM19 13h3v1h-3zM0 14h3v1h-3zM6 14h1v1h-1zM10 14h3v1h-3zM15 14h4v1h-4zM20 14h2v1h-2zM23 14h1v1h-1zM25 14h4v1h-4zM1 15h1v1h-1zM4 15h1v1h-1zM10 15h1v1h-1zM12 15h3v1h-3zM16 15h10v1h-10zM27 15h1v1h-1zM1 16h2v1h-2zM4 16h1v1h-1zM6 16h2v1h-2zM13 16h5v1h-5zM19 16h3v1h-3zM23 16h1v1h-1zM27 16h1v1h-1zM1 17h3v1h-3zM10 17h1v1h-1zM12 17h1v1h-1zM15 17h1v1h-1zM17 17h1v1h-1zM21 17h3v1h-3zM25 17h1v1h-1zM28 17h1v1h-1zM0 18h1v1h-1zM2 18h2v1h-2zM5 18h2v1h-2zM8 18h2v1h-2zM13 18h1v1h-1zM17 18h1v1h-1zM20 18h3v1h-3zM27 18h2v1h-2zM3 19h3v1h-3zM7 19h1v1h-1zM11 19h1v1h-1zM13 19h1v1h-1zM15 19h5v1h-5zM21 19h1v1h-1zM23 19h1v1h-1zM27 19h2v1h-2zM0 20h1v1h-1zM2 20h3v1h-3zM6 20h3v1h-3zM10 20h1v1h-1zM14 20h1v1h-1zM16 20h1v1h-1zM18 20h1v1h-1zM20 20h5v1h-5zM26 20h1v1h-1zM8 21h1v1h-1zM12 21h2v1h-2zM15 21h2v1h-2zM20 21h1v1h-1zM24 21h1v1h-1zM26 21h3v1h-3zM0 22h7v1h-7zM9 22h1v1h-1zM11 22h1v1h-1zM13 22h3v1h-3zM17 22h1v1h-1zM20 22h1v1h-1zM22 22h1v1h-1zM24 22h1v1h-1zM27 22h1v1h-1zM0 23h1v1h-1zM6 23h1v1h-1zM8 23h2v1h-2zM11 23h3v1h-3zM16 23h1v1h-1zM20 23h1v1h-1zM24 23h5v1h-5zM0 24h1v1h-1zM2 24h3v1h-3zM6 24h1v1h-1zM9 24h1v1h-1zM12 24h1v1h-1zM14 24h4v1h-4zM20 24h5v1h-5zM27 24h1v1h-1zM0 25h1v1h-1zM2 25h3v1h-3zM6 25h1v1h-1zM8 25h1v1h-1zM10 25h2v1h-2zM14 25h4v1h-4zM19 25h1v1h-1zM22 25h1v1h-1zM24 25h3v1h-3zM28 25h1v1h-1zM0 26h1v1h-1zM2 26h3v1h-3zM6 26h1v1h-1zM10 26h3v1h-3zM14 26h1v1h-1zM17 26h1v1h-1zM20 26h1v1h-1zM24 26h3v1h-3zM28 26h1v1h-1zM0 27h1v1h-1zM6 27h1v1h-1zM10 27h3v1h-3zM15 27h4v1h-4zM20 27h1v1h-1zM22 27h1v1h-1zM27 27h1v1h-1zM0 28h7v1h-7zM8 28h3v1h-3zM12 28h1v1h-1zM16 28h2v1h-2zM20 28h1v1h-1zM23 28h2v1h-2zM27 28h1v1h-1z';

  var S = {};

  /* 1. Problem — 14 days run out, envelopes come in faster than they leave */
  S.problem = {
    L: 6.5,
    svg: function () {
      var s = '';
      for (var i = 0; i < 14; i++) {
        var x = 106 + i * 100, late = i >= 11;
        s += '<rect x="' + x + '" y="30" width="88" height="120" rx="16" class="' + (late ? 'fr' : 'fl') + ' s1-day" ' + d((0.4 + i * 0.43).toFixed(2)) + '/>';
        s += t(x + 44, 108, 14 - i, 50, (late ? 'fbg' : 'fm') + ' s1-num', 'middle').replace('<text ', '<text ' + d((0.4 + i * 0.43).toFixed(2)) + ' ');
      }
      // the last days keep pulsing red
      s += '<g class="lp glow" style="--lt:1.6s">';
      for (var j = 11; j < 14; j++) s += '<rect x="' + (106 + j * 100 - 6) + '" y="24" width="100" height="132" rx="20" class="fn sr" stroke-width="6"/>';
      s += '</g>';
      // "today" marker walking across the calendar
      s += '<g class="s1-mark"><rect x="1394" y="18" width="112" height="144" rx="22" class="fn sa" stroke-width="10"/></g>';
      // inbox tray with a growing pile
      s += '<path d="M500 500 v150 h340 v-150" class="fn si" stroke-width="12"/>';
      for (var k = 0; k < 8; k++) {
        s += '<g class="e drop" ' + d((1 + k * 0.6).toFixed(1)) + '>' +
          '<rect x="520" y="' + (612 - k * 32) + '" width="300" height="26" rx="8" class="fa"/></g>';
      }
      s += t(470, 330, 'wpływa', 46, 'fm', 'end');
      // incoming envelopes (fast) and outgoing answers (slow)
      s += '<g class="lp-only">' +
        '<g class="s1-in" ' + d(0) + '>' + env(625, 380, 90) + '</g>' +
        '<g class="s1-in" ' + d(0.37) + '>' + env(625, 380, 90) + '</g>' +
        '<g class="s1-in" ' + d(0.73) + '>' + env(625, 380, 90) + '</g>' +
        '<g class="s1-out" ' + d(1.5) + '>' + env(860, 560, 90) + '</g></g>';
      s += '<g class="print-only">' + env(625, 190, 90) + env(625, 290, 90) + env(1180, 560, 90) + '</g>';
      s += '<path d="M870 650 H1290" class="fn sl" stroke-width="6" stroke-dasharray="4 18"/>';
      s += t(1080, 540, 'wychodzi', 46, 'fm');
      // source of the yearly number (storyboard label)
      s += '<g class="e fade" ' + d(6) + '>' + chip(1020, 250, 520, 76, 'Bydgoszcz 2022: 501–1200', 38, 'fp2', 'fa') + '</g>';
      return svg('Kalendarz 14 dni i rosnący stos wniosków', s);
    }
  };

  /* 2. Why it is hard — three question cards and a gavel */
  S.hard = {
    L: 6,
    svg: function () {
      var cards = [
        { l1: '„Jakie', l2: 'pismo?”', icon: function (cx) {
          return '<rect x="' + (cx - 60) + '" y="90" width="120" height="156" rx="14" class="fn si" stroke-width="9"/>' +
            t(cx, 210, '?', 110, 'fa'); } },
        { l1: '„Pismo czy', l2: 'decyzja?”', icon: function (cx) {
          return '<rect x="' + (cx - 118) + '" y="100" width="96" height="128" rx="12" class="fn si" stroke-width="9"/>' +
            '<rect x="' + (cx + 22) + '" y="100" width="96" height="128" rx="12" class="fn si" stroke-width="9"/>' +
            '<circle cx="' + (cx + 70) + '" cy="196" r="20" class="fa"/>' + t(cx, 186, '/', 64, 'fm'); } },
        { l1: '„Dane', l2: 'osobowe?”', icon: function (cx) {
          return person(cx - 40, 92, 1.05, 'fb') + lock(cx + 64, 190, 1.5, 'fa'); } }
      ];
      var s = '';
      // gavel (behind the cards, appears at the end)
      s += '<g class="e rise" ' + d(5) + '><g class="lp tap" style="--lt:3s;transform-origin:800px 640px;transform-box:view-box">' +
        '<rect x="700" y="520" width="200" height="74" rx="20" class="fr"/>' +
        '<rect x="788" y="590" width="24" height="120" rx="10" class="fr"/></g>' +
        '<rect x="660" y="690" width="280" height="24" rx="12" class="fl"/></g>';
      cards.forEach(function (c, i) {
        var x = 100 + i * 490, cx = x + 210;
        s += '<g class="e flip" ' + d((0.6 + i * 1.4).toFixed(1)) + ' style="--d:' + (0.6 + i * 1.4).toFixed(1) + 's;--t:.9s">' +
          '<g class="lp bob" style="--ld:' + i * 0.6 + 's">' +
          '<rect x="' + x + '" y="40" width="420" height="440" rx="36" class="fp2 sl" stroke-width="5"/>' +
          c.icon(cx) + t(cx, 350, c.l1, 54) + t(cx, 420, c.l2, 54) + '</g></g>';
      });
      return svg('Trzy pytania urzędnika i młotek sędziowski', s);
    }
  };

  /* 3. The solution — the envelope passes four stations, a person approves */
  var STATIONS = ['Analiza', 'Terminy', 'Projekt pisma', 'Zatwierdzenie'];
  function stationIcon(k, cx, cy) {
    if (k === 0) return '<circle cx="' + (cx - 8) + '" cy="' + (cy - 8) + '" r="24" class="fn si" stroke-width="9"/><line x1="' + (cx + 10) + '" y1="' + (cy + 10) + '" x2="' + (cx + 30) + '" y2="' + (cy + 30) + '" class="si" stroke-width="11"/>';
    if (k === 1) return '<circle cx="' + cx + '" cy="' + cy + '" r="32" class="fn si" stroke-width="8"/><path d="M' + cx + ' ' + (cy - 18) + ' V' + cy + ' H' + (cx + 16) + '" class="fn si" stroke-width="8"/>';
    if (k === 2) return '<rect x="' + (cx - 26) + '" y="' + (cy - 34) + '" width="52" height="68" rx="8" class="fn si" stroke-width="7"/><path d="M' + (cx - 12) + ' ' + (cy - 12) + ' h24 M' + (cx - 12) + ' ' + cy + ' h24 M' + (cx - 12) + ' ' + (cy + 12) + ' h14" class="fn si" stroke-width="6"/>';
    return tick(cx - 6, cy + 2, 26, 'si');
  }
  S.solution = {
    L: 8,
    svg: function () {
      var xs = [220, 560, 900, 1240], lit = [1.2, 2.8, 4.2, 5.7];
      var s = '<line x1="120" y1="300" x2="1240" y2="300" class="sl" stroke-width="12"/>' +
        '<line x1="120" y1="300" x2="1240" y2="300" class="lp flow sa" stroke-width="12" style="--lt:2s"/>';
      xs.forEach(function (x, k) {
        s += '<circle cx="' + x + '" cy="300" r="74" class="fp sl" stroke-width="8"/>' +
          '<g class="e fade" ' + d(lit[k]) + '><circle cx="' + x + '" cy="300" r="74" class="fp2 sa" stroke-width="10"/></g>' +
          stationIcon(k, x, 300) + t(x, 440, STATIONS[k], 46);
      });
      // the clerk who decides
      s += '<g class="e fade" ' + d(0.2) + '>' + person(1450, 150, 1.6, 'fb') + '</g>' +
        '<g class="s3-arm"><line x1="1405" y1="262" x2="1322" y2="296" class="sb" stroke-width="24"/></g>';
      // approved document comes out
      s += '<g class="e rise" ' + d(6.6) + '><g class="lp pulse" style="--lt:3s">' +
        doc(1176, 490, 128, 164) + '<circle cx="1296" cy="642" r="38" class="fg"/>' + tick(1294, 644, 18, 'sbg') + '</g></g>';
      // the travelling envelope (ends hidden at the last station)
      s += '<g class="s3-env" style="opacity:0">' + env(1185, 263, 110) + '</g>';
      return svg('Wniosek przechodzi przez cztery etapy, urzędnik zatwierdza', s);
    }
  };

  /* 4. Demo — video if media/demo.mp4 exists, else the animated desk */
  S.demo = {
    L: 10,
    svg: function () {
      var s = '<rect x="40" y="10" width="1520" height="700" rx="30" class="fp sl" stroke-width="5"/>' +
        '<circle cx="90" cy="50" r="12" class="fr"/><circle cx="130" cy="50" r="12" class="fa"/><circle cx="170" cy="50" r="12" class="fg"/>' +
        '<line x1="40" y1="90" x2="1560" y2="90" class="sl" stroke-width="4"/>';
      // the e-mail
      s += '<g class="e slideL" ' + d(0.3) + '>' + env(90, 120, 84) +
        '<rect x="200" y="128" width="380" height="22" rx="11" class="fl"/><rect x="200" y="166" width="260" height="22" rx="11" class="fl"/>' +
        '<rect x="90" y="220" width="600" height="18" rx="9" class="fl"/><rect x="90" y="252" width="520" height="18" rx="9" class="fl"/></g>';
      var qs = [{ y: 330, c: 'fg', label: '„już w BIP”', lc: 'fg' }, { y: 450, c: 'fb', label: '„dane z wydziału”', lc: 'fb' }, { y: 570, c: 'fr', label: '„dane osobowe”', lc: 'fr' }];
      qs.forEach(function (q, k) {
        s += '<g class="e fade" ' + d(0.6) + '><rect x="150" y="' + (q.y - 14) + '" width="' + (520 - k * 60) + '" height="28" rx="14" class="fl"/></g>' +
          '<g class="e grow" ' + d((1.6 + k * 0.6).toFixed(1)) + '><rect x="140" y="' + (q.y - 26) + '" width="' + (540 - k * 60) + '" height="52" rx="26" class="' + q.c + '" opacity=".35"/></g>' +
          '<g class="e pop" ' + d((1.6 + k * 0.6).toFixed(1)) + '><circle cx="100" cy="' + q.y + '" r="30" class="' + q.c + '"/>' + t(100, q.y + 14, k + 1, 40, 'fbg') + '</g>' +
          '<g class="e slideR" ' + d((3.4 + k * 0.6).toFixed(1)) + '><g class="lp glow" style="--ld:' + k * 0.7 + 's;--lt:3s">' +
          '<line x1="' + (700 - k * 60) + '" y1="' + q.y + '" x2="740" y2="' + q.y + '" class="sl" stroke-width="6"/>' +
          '<rect x="745" y="' + (q.y - 36) + '" width="330" height="72" rx="36" class="fp2 s' + q.c.slice(1) + '" stroke-width="6"/>' +
          t(910, q.y + 13, q.label, 36, q.lc) + '</g></g>';
      });
      // deadline badge with two dates
      s += '<g class="e pop" ' + d(5.2) + '><rect x="1120" y="120" width="400" height="150" rx="24" class="fp2 sa" stroke-width="6"/>' +
        '<circle cx="1180" cy="195" r="34" class="fn sa" stroke-width="8"/><path d="M1180 175 V195 H1196" class="fn sa" stroke-width="7"/>' +
        t(1236, 182, '14 dni · 05.12', 36, '', 'start') + t(1236, 236, '2 mies. · 21.01', 36, 'fm', 'start') + '</g>';
      // the draft fills in
      s += '<g class="e fade" ' + d(5.8) + '><rect x="1120" y="300" width="400" height="290" rx="20" class="fi"/></g>';
      for (var k = 0; k < 6; k++) {
        s += '<g class="e grow" ' + d((6.0 + k * 0.3).toFixed(1)) + ' style="--d:' + (6.0 + k * 0.3).toFixed(1) + 's;--t:.4s"><rect x="1150" y="' + (330 + k * 40) + '" width="' + [330, 300, 340, 280, 320, 200][k] + '" height="18" rx="9" class="fl"/></g>';
      }
      s += '<g class="lp glow" style="--lt:1s"><rect x="1358" y="526" width="8" height="30" class="fa"/></g>';
      // the approve button
      s += '<g class="e pop" ' + d(7.6) + '><g class="e press" style="--d:8.6s;--t:.5s">' +
        '<rect x="1150" y="610" width="270" height="76" rx="38" class="fg"/>' + t(1285, 661, 'Zatwierdź', 40, 'fbg') + '</g></g>' +
        '<g class="e pop" ' + d(9.1) + '><circle cx="1470" cy="648" r="34" class="fg"/>' + tick(1468, 650, 16, 'sbg') + '</g>';
      var mock = svg('Pokaz: e-mail z trzema pytaniami i projekt odpowiedzi', s);
      return '<div class="demo-wrap"><video muted loop playsinline preload="auto" aria-label="Nagranie demo"></video>' + mock + '</div>';
    },
    run: function (root, ctx) {
      if (ctx.final) return;
      var wrap = root.querySelector('.demo-wrap');
      var v = root.querySelector('video');
      v.addEventListener('loadeddata', function () { wrap.classList.add('has-video'); v.play().catch(function () {}); });
      v.addEventListener('error', function () { wrap.classList.remove('has-video'); });
      v.src = 'media/demo.mp4'; // missing file => error event => the mock stays
    }
  };

  /* 5. Secure — name becomes a token, only tokens leave the office */
  var ORIG = 'Jan Kowalski, ul. Długa 5';
  var MASK = '[OSOBA_1], [ADRES_1]';
  S.secure = {
    L: 7.5,
    svg: function () {
      var s = '';
      s += '<path d="M60 200 L480 50 L900 200 Z" class="fp sb" stroke-width="10"/>' +
        '<rect x="80" y="200" width="800" height="480" rx="10" class="fn sb" stroke-width="10"/>' + t(480, 170, 'urząd', 50, 'fb');
      s += '<g class="e fade" ' + d(0.3) + '>' + t(440, 320, ORIG, 40, 'mono') + '</g>';
      s += '<g class="e fade" ' + d(1.2) + '><path d="M440 350 v60 m-22 -22 l22 22 l22 -22" class="fn sm" stroke-width="8"/></g>';
      s += '<g class="e fade" ' + d(1.2) + '>' + '<text x="440" y="480" font-size="40" text-anchor="middle" class="mono fa" data-morph="1">' + MASK + '</text></g>';
      // the shield in the wall: originals stay inside
      s += '<g class="e pop" ' + d(0.8) + '><g class="lp pulse" style="--lt:2.6s"><path d="M880 250 l70 26 v58 c0 46 -30 74 -70 92 c-40 -18 -70 -46 -70 -92 v-58 z" class="fg"/>' +
        tick(880, 336, 22, 'sbg') + '</g></g>';
      // path to the model
      s += '<line x1="890" y1="520" x2="1170" y2="520" class="sl" stroke-width="8"/>' +
        '<line x1="890" y1="520" x2="1170" y2="520" class="lp flow sa" stroke-width="8" style="--lt:1.6s"/>' +
        '<path d="M1150 500 l22 20 l-22 20" class="fn sl" stroke-width="8"/>';
      // the model box
      s += '<rect x="1180" y="380" width="360" height="270" rx="34" class="fp2 sa" stroke-width="8"/>' + t(1360, 620, 'model', 50, 'fa');
      [['[OSOBA_1]', 410, 5.0, -880, 50], ['[ADRES_1]', 490, 5.5, -650, -30]].forEach(function (c) {
        s += '<g class="e s5-fly" style="--d:' + c[2] + 's;--dx:' + c[3] + 'px;--dy:' + c[4] + 'px">' +
          chip(1225, c[1], 270, 58, c[0], 34, 'fa', 'mono fbg') + '</g>';
      });
      return svg('Dane osobowe zastąpione znacznikami zanim tekst trafi do modelu', s);
    },
    // letter-by-letter morph of the name into tokens
    run: function (root, ctx) {
      var node = root.querySelector('[data-morph]');
      if (!node || ctx.final) return;
      var i = 0, n = Math.max(ORIG.length, MASK.length);
      node.textContent = ORIG;
      node.setAttribute('class', 'mono');
      ctx.later(function () {
        ctx.every(function () {
          if (i > n) return;
          node.textContent = MASK.slice(0, i) + ORIG.slice(i, Math.max(i, ORIG.length - (ORIG.length - MASK.length) * (i / n | 0)));
          if (i === n) { node.textContent = MASK; node.setAttribute('class', 'mono fa'); }
          i++;
        }, 95);
      }, 2000);
    }
  };

  /* 6. Legal safety — citations checked in the statute, a fake one is blocked */
  S.legal = {
    L: 8,
    svg: function (ctx) {
      var s = '<rect x="80" y="20" width="700" height="540" rx="24" class="fp sl" stroke-width="5"/>';
      [70, 110, 210, 250, 350, 390, 490].forEach(function (y, k) {
        s += '<rect x="130" y="' + (y + 60) + '" width="' + [560, 480, 560, 420, 500, 380, 300][k] + '" height="16" rx="8" class="fl"/>';
      });
      // book with the statute
      s += '<g class="lp glow" style="--lt:3s"><rect x="1120" y="110" width="320" height="400" rx="22" class="fb"/>' +
        '<rect x="1150" y="110" width="22" height="400" class="fbg" opacity=".35"/>' +
        '<rect x="1200" y="180" width="190" height="16" rx="8" class="fbg" opacity=".5"/><rect x="1200" y="216" width="150" height="16" rx="8" class="fbg" opacity=".5"/></g>' +
        t(1280, 580, 'tekst ustawy', 48);
      var chips = [
        { txt: 'art. 13 ust. 2', y: 140, w: 330, dl: 1.0, ok: true },
        { txt: 'art. 16 ust. 1', y: 280, w: 330, dl: 2.4, ok: true },
        { txt: 'art. 99', y: 420, w: 200, dl: 3.8, ok: false }
      ];
      chips.forEach(function (c) {
        var cx = 130 + c.w / 2, cy = c.y + 32;
        var dx = 1280 - cx, dy = 300 - cy;
        s += '<g class="e fade" ' + d(0.4) + '>' + chip(130, c.y, c.w, 64, c.txt, 38, 'fp2', '') + '</g>';
        if (c.ok) {
          s += '<g class="e pop" ' + d((c.dl + 1.8).toFixed(1)) + '><circle cx="' + (130 + c.w + 50) + '" cy="' + cy + '" r="32" class="fg"/>' + tick(130 + c.w + 48, cy + 2, 15, 'sbg') + '</g>';
        } else {
          s += '<g class="e fade" ' + d(c.dl + 0.9) + '>' + chip(130, c.y, c.w, 64, c.txt, 38, 'fr', 'fbg') + '</g>';
        }
        s += '<g class="lp-only"><g class="' + (c.ok ? 's6-fly' : 's6-bounce') + '" style="--d:' + c.dl + 's;--dx:' + dx + 'px;--dy:' + dy + 'px">' +
          chip(130, c.y, c.w, 64, c.txt, 38, 'fa', 'fbg') + '</g></g>';
      });
      // "zablokowano" stamp
      s += '<g transform="rotate(-10 590 470)"><g class="stamp" ' + d(5.9) + '>' +
        '<rect x="420" y="424" width="340" height="90" rx="16" class="fbg sr" stroke-width="9"/>' + t(590, 486, 'zablokowano', 50, 'fr') + '</g></g>';
      // measured counters (only values present in metrics.json)
      var keys = Object.keys(ctx.labels).filter(function (k) { return ctx.metrics[k] !== null && ctx.metrics[k] !== undefined; });
      keys.forEach(function (k, i) {
        var cx = 800 + (i - (keys.length - 1) / 2) * 300;
        s += '<g class="e rise" ' + d(6.5) + '><text x="' + cx + '" y="660" font-size="64" text-anchor="middle" class="fa" data-count="' + ctx.metrics[k] + '" data-suffix="' + ctx.labels[k].suffix + '">' + ctx.metrics[k] + ctx.labels[k].suffix + '</text>' +
          t(cx, 708, ctx.labels[k].label, 30, 'fm') + '</g>';
      });
      return svg('Podstawy prawne sprawdzane w tekście ustawy, zmyślony przepis zablokowany', s);
    },
    run: function (root, ctx) {
      if (ctx.final) return;
      var nodes = root.querySelectorAll('[data-count]');
      Array.prototype.forEach.call(nodes, function (n) {
        var target = parseFloat(n.getAttribute('data-count')), suf = n.getAttribute('data-suffix');
        var dec = String(n.getAttribute('data-count')).indexOf('.') >= 0 ? 1 : 0;
        n.textContent = (0).toFixed(dec) + suf;
        ctx.later(function () {
          var t0 = Date.now();
          ctx.every(function () {
            var p = Math.min(1, (Date.now() - t0) / 1500);
            n.textContent = (target * (1 - Math.pow(1 - p, 3))).toFixed(dec) + suf;
          }, 40);
        }, 6500);
      });
    }
  };

  /* 7. Less work at the source — PDF becomes an online form, a hint saves a request */
  S.source = {
    L: 9.5,
    svg: function () {
      var s = '';
      // PDF that turns into a phone with a form
      s += '<g class="e out" ' + d(1.0) + ' opacity="0"><rect x="160" y="120" width="240" height="320" rx="18" class="fi"/>' + t(280, 310, 'PDF', 84, 'fr') + '</g>';
      s += '<g class="e pop" ' + d(1.3) + '><rect x="140" y="60" width="280" height="560" rx="44" class="fp sl" stroke-width="9"/>' +
        '<rect x="180" y="130" width="200" height="40" rx="10" class="fbg sl" stroke-width="4"/>' +
        '<rect x="180" y="190" width="200" height="40" rx="10" class="fbg sl" stroke-width="4"/>' +
        '<rect x="180" y="260" width="200" height="130" rx="12" class="fbg sa" stroke-width="5"/>' +
        '<rect x="200" y="530" width="160" height="52" rx="26" class="fa"/></g>';
      for (var k = 0; k < 3; k++) {
        s += '<g class="e grow" style="--d:' + (2.0 + k * 0.35).toFixed(2) + 's;--t:.35s"><rect x="198" y="' + (282 + k * 32) + '" width="' + [160, 140, 90][k] + '" height="14" rx="7" class="fi"/></g>';
      }
      s += t(280, 690, 'PDF → formularz', 40, 'fm');
      // the hint
      s += '<g class="e slideL" ' + d(3.2) + '><g class="lp pulse" style="--lt:3s">' +
        '<path d="M470 260 h420 a24 24 0 0 1 24 24 v80 a24 24 0 0 1 -24 24 h-420 a24 24 0 0 1 -24 -24 v-24 l-24 -14 l24 -14 v-28 a24 24 0 0 1 24 -24 z" class="fg"/>' +
        t(640, 340, '„Już w BIP”', 44, 'fbg') +
        '<path d="M846 312 l20 -20 m-18 0 h18 v18 M836 300 h-14 v40 h40 v-14" class="fn sbg" stroke-width="6"/></g></g>';
      // envelope that is not sent, then the one that is
      s += '<g class="lp-only"><g class="s7-unsent">' + env(470, 440, 110) + '</g><g class="s7-sent">' + env(470, 470, 110) + '</g></g>';
      s += '<line x1="470" y1="560" x2="1150" y2="560" class="sl" stroke-width="6" stroke-dasharray="4 20"/>';
      // the office receives a tidy card
      s += building(1350, 220, 340, 440, 'sb') + t(1350, 245, 'urząd', 34, 'fb');
      s += '<g class="e pop" ' + d(8.0) + '><g class="lp bob" style="--lt:3.5s"><rect x="1210" y="300" width="280" height="320" rx="20" class="fp2 sa" stroke-width="7"/>';
      for (var q = 0; q < 3; q++) {
        s += '<circle cx="1256" cy="' + (360 + q * 90) + '" r="26" class="fa"/>' + t(1256, 360 + q * 90 + 12, q + 1, 34, 'fbg') +
          '<rect x="1300" y="' + (350 + q * 90) + '" width="' + [160, 130, 150][q] + '" height="20" rx="10" class="fl"/>';
      }
      s += '</g></g>';
      return svg('Wzór PDF staje się formularzem online, wniosek trafia do urzędu uporządkowany', s);
    }
  };

  /* 8. The same core, a bigger picture — data once fills three forms; the forms
     go to a shared register of templates; no central database of people */
  S.counter = {
    L: 9.5,
    svg: function () {
      var s = '';
      // phone with the resident's profile
      s += '<g class="e slideL" ' + d(0.3) + '><rect x="50" y="30" width="200" height="390" rx="32" class="fp sl" stroke-width="7"/>' +
        '<circle cx="150" cy="110" r="36" class="fb"/><rect x="95" y="166" width="110" height="16" rx="8" class="fi"/><rect x="95" y="196" width="80" height="16" rx="8" class="fl"/>' +
        '<g transform="translate(105,250) scale(.82)">' + qrIcon() + '</g></g>';
      // clerk's screen
      s += '<g class="e rise" ' + d(0.7) + '><rect x="330" y="60" width="270" height="200" rx="18" class="fp sl" stroke-width="7"/>' +
        '<path d="M465 260 v40 m-60 0 h120" class="fn sl" stroke-width="9"/>' +
        '<rect x="360" y="90" width="210" height="30" rx="8" class="fl"/><rect x="360" y="135" width="210" height="30" rx="8" class="fl"/><rect x="360" y="180" width="210" height="30" rx="8" class="fl"/></g>' +
        '<g class="e fade" ' + d(1.9) + '><rect x="354" y="129" width="222" height="42" rx="12" class="fn sa" stroke-width="6"/></g>';
      // QR handshake
      s += '<g class="e fade" ' + d(1.3) + '><path d="M250 300 C 300 300, 280 160, 326 160" class="fn sa s8-beam" stroke-width="7"/></g>';
      // three different forms, the same fields fill at once
      var forms = [{ x: 670, rows: [1, 0, 1, 1] }, { x: 830, rows: [0, 1, 1, 0] }, { x: 990, rows: [1, 1, 0, 1] }];
      forms.forEach(function (f, i) {
        s += '<g class="e slideR" ' + d((2.2 + i * 0.3).toFixed(1)) + '><rect x="' + f.x + '" y="30" width="140" height="330" rx="14" class="fi"/>' +
          '<rect x="' + (f.x + 18) + '" y="50" width="' + (60 + i * 18) + '" height="16" rx="6" class="fl"/>';
        f.rows.forEach(function (lit, r) {
          s += '<rect x="' + (f.x + 18) + '" y="' + (90 + r * 64) + '" width="104" height="38" rx="8" class="fn sl" stroke-width="4"/>';
        });
        s += '</g>';
        f.rows.forEach(function (lit, r) {
          if (lit) s += '<g class="e grow" style="--d:3.6s;--t:.9s"><rect x="' + (f.x + 18) + '" y="' + (90 + r * 64) + '" width="104" height="38" rx="8" class="fa"/></g>';
        });
        // a copy of each form flies to the shelf
        s += '<g class="lp-only"><g class="s8-fly" style="--d:' + (4.8 + i * 0.25).toFixed(2) + 's;--dx:' + (652 + i * 66 - f.x) + 'px;--dy:320px">' +
          '<rect x="' + f.x + '" y="30" width="140" height="330" rx="14" class="fa" opacity=".8"/></g></g>';
      });
      s += '<line x1="610" y1="180" x2="660" y2="180" class="lp flow sa" stroke-width="7" style="--lt:1.2s"/>';
      // the shelf "rejestr wzorów"
      s += '<g class="e fade" ' + d(4.4) + '><line x1="540" y1="566" x2="900" y2="566" class="sb" stroke-width="14"/>' + t(720, 626, 'rejestr wzorów', 44) + '</g>';
      for (var k = 0; k < 5; k++) {
        s += '<g class="e pop" ' + d(k < 2 ? 4.4 : (5.6 + (k - 2) * 0.25).toFixed(2)) + '><rect x="' + (566 + k * 66) + '" y="' + (476 + (k % 2) * 8) + '" width="48" height="' + (82 - (k % 2) * 8) + '" rx="8" class="' + (k < 2 ? 'fi' : 'fa') + '"/></g>';
      }
      // offices connected to the shelf
      [1080, 1260, 1440].forEach(function (cx, i) {
        s += '<g class="e draw" style="--d:' + (6.3 + i * 0.3).toFixed(1) + 's;--t:.5s"><path d="M905 566 L940 660 H' + cx + ' V634" pathLength="1" class="fn sl" stroke-width="6"/></g>' +
          '<g class="e fade" ' + d((6.5 + i * 0.3).toFixed(1)) + '>' + building(cx, 480, 130, 110, 'sb') + '</g>';
      });
      // the central database of people that we do NOT build
      s += '<g class="e pop" ' + d(7.3) + '><path d="M1250 100 v240 a120 36 0 0 0 240 0 v-240" class="fp sm" stroke-width="7"/>' +
        '<ellipse cx="1370" cy="100" rx="120" ry="36" class="fp2 sm" stroke-width="7"/>' +
        person(1320, 170, 0.75, 'fm') + person(1420, 170, 0.75, 'fm') + person(1370, 250, 0.75, 'fm') + '</g>' +
        '<g class="e draw" style="--d:8s;--t:.4s"><path d="M1220 60 L1520 410" pathLength="1" class="fn sr" stroke-width="18"/></g>' +
        '<g class="e draw" style="--d:8.3s;--t:.4s"><path d="M1520 60 L1220 410" pathLength="1" class="fn sr" stroke-width="18"/></g>';
      // Opole 2022
      s += '<g class="e pop" ' + d(8.8) + '><g class="lp pulse" style="--lt:2.4s"><rect x="40" y="540" width="270" height="76" rx="38" class="fp2 sa" stroke-width="6"/>' +
        t(175, 591, 'Opole 2022', 40, 'fa') + '</g></g>';
      return svg('Dane podane raz wypełniają formularze; wspólny rejestr wzorów; bez centralnej bazy danych osobowych', s);
    }
  };

  /* 9. What works, what is simulated — lists from status.json */
  S.status = {
    L: 7,
    svg: function (ctx) {
      var works = (ctx.status && ctx.status.works) || [], sim = (ctx.status && ctx.status.simulated) || [];
      var step = Math.min(78, 470 / Math.max(1, works.length));
      var s = '<line x1="860" y1="40" x2="860" y2="520" class="sl" stroke-width="6"/>';
      works.forEach(function (w, k) {
        var y = 70 + k * step;
        s += '<g class="s9-item" ' + d((0.6 + k * 0.5).toFixed(1)) + '><g class="lp glow" style="--ld:' + (k * 0.4).toFixed(1) + 's;--lt:4s">' +
          '<circle cx="190" cy="' + y + '" r="28" class="fg"/>' + tick(188, y + 2, 13, 'sbg') + '</g>' + t(240, y + 18, w, 50, '', 'start') + '</g>';
      });
      sim.forEach(function (w, k) {
        var y = 70 + k * 78;
        var dl = (0.9 + works.length * 0.5 + k * 0.6).toFixed(1);
        s += '<g class="s9-item" ' + d(dl) + '><g class="lp pulse" style="--ld:' + k * 0.6 + 's;--lt:2.6s"><circle cx="950" cy="' + y + '" r="20" class="fa"/></g>' +
          t(990, y + 18, w, 50, '', 'start') + '</g>';
      });
      var last = (1.6 + works.length * 0.5 + sim.length * 0.6).toFixed(1);
      s += '<g class="e fade" ' + d(last) + '><rect x="530" y="590" width="540" height="90" rx="45" class="fp2 sm" stroke-width="5"/>' +
        t(800, 650, 'dane syntetyczne', 46, 'fm') + '</g>';
      return svg('Co działa w prototypie, a co jest symulowane', s);
    }
  };
  function qrIcon() {
    var s = '<rect width="110" height="110" rx="10" class="fi"/>';
    var cells = [[10, 10], [64, 10], [10, 64]];
    cells.forEach(function (c) { s += '<rect x="' + c[0] + '" y="' + c[1] + '" width="36" height="36" rx="4" class="fbg"/><rect x="' + (c[0] + 11) + '" y="' + (c[1] + 11) + '" width="14" height="14" class="fi"/>'; });
    s += '<rect x="66" y="66" width="14" height="14" class="fbg"/><rect x="86" y="86" width="14" height="14" class="fbg"/><rect x="66" y="88" width="10" height="10" class="fbg"/>';
    return s;
  }

  /* 10. Ready for a pilot — timeline and three badges */
  S.pilot = {
    L: 6,
    svg: function () {
      var xs = [170, 590, 1010, 1430];
      var top = ['Dziś:', 'Grudzień:', 'Styczeń:', 'Dalej:'];
      var bot = ['prototyp', 'test', 'pilotaż', 'EZD'];
      var s = '<g class="e draw" style="--d:.3s;--t:2.6s"><path d="M120 300 H1480" pathLength="1" class="fn sl" stroke-width="12"/></g>';
      xs.forEach(function (x, k) {
        var dl = (0.6 + k * 0.7).toFixed(1);
        s += '<g class="e pop" ' + d(dl) + '><circle cx="' + x + '" cy="300" r="30" class="' + (k === 0 ? 'fa' : 'fp2 sa') + '" stroke-width="8"/></g>' +
          '<g class="e rise" ' + d(dl) + '>' + t(x, 230, top[k], 54, 'fa') + t(x, 396, bot[k], 48) + '</g>';
      });
      s += '<g class="lp pulse" style="--lt:2s"><circle cx="170" cy="300" r="46" class="fn sa" stroke-width="5"/></g>';
      s += '<circle cx="170" cy="300" r="12" class="fi lp-only s10-dot"/>';
      var badges = ['otwarty kod', 'obok EZD', 'model lokalny'];
      badges.forEach(function (b, i) {
        var cx = 320 + i * 480;
        s += '<g class="e drop" ' + d((3.8 + i * 0.4).toFixed(1)) + '><g class="lp bob" style="--ld:' + i * 0.5 + 's">' +
          '<rect x="' + (cx - 220) + '" y="520" width="440" height="96" rx="48" class="fp2 sg" stroke-width="7"/>' +
          tick(cx - 168, 568, 16, 'sg') + t(cx + 28, 582, b, 42, '') + '</g></g>';
      });
      return svg('Plan: prototyp, test, pilotaż, integracja z EZD', s);
    }
  };

  /* 11. Close — the envelope does the loop once more, QR code */
  S.close = {
    L: 6,
    svg: function () {
      var s = '<circle cx="420" cy="300" r="220" class="fn sl" stroke-width="12"/>';
      var pts = [[420, 80], [640, 300], [420, 520], [200, 300]];
      pts.forEach(function (p, k) {
        s += '<circle cx="' + p[0] + '" cy="' + p[1] + '" r="22" class="fp2 sl" stroke-width="6"/>' +
          '<g class="e fade" style="--d:' + (0.6 + 0.8 * (k + 1)).toFixed(1) + 's;--t:.3s"><circle cx="' + p[0] + '" cy="' + p[1] + '" r="22" class="fa"/></g>';
      });
      s += '<g class="lp-only s11-dot"><circle cx="420" cy="80" r="12" class="fi"/></g>';
      s += '<g class="e out" style="--d:3.9s;--t:.4s" opacity="0"><g class="s11-orbit"><g class="s11-orbit-up">' + env(365, 44, 110) + '</g></g></g>';
      s += '<g class="e pop" ' + d(4.1) + '><g class="lp pulse" style="--lt:3s">' + doc(345, 205, 150, 190) +
        '<circle cx="482" cy="380" r="44" class="fg"/>' + tick(480, 382, 20, 'sbg') + '</g></g>';
      var size = 460, unit = size / (QR_N + 8);
      s += '<g class="e fade" style="--d:4.4s;--t:1s"><rect x="1050" y="20" width="' + size + '" height="' + size + '" rx="18" fill="#ffffff"/>' +
        '<g transform="translate(' + (1050 + 4 * unit) + ',' + (20 + 4 * unit) + ') scale(' + unit + ')"><path d="' + QR_PATH + '" fill="#000000" shape-rendering="crispEdges"/></g></g>';
      s += '<g class="e fade" ' + d(4.8) + '>' + t(800, 612, 'urzad.flyreelstudio.eu', 54, 'fa') +
        t(800, 682, 'github.com/AndriiShramko/shramko-asystent-urzednika', 34, 'fm') + '</g>';
      return svg('Od wniosku do odpowiedzi, kod QR do urzad.flyreelstudio.eu', s);
    }
  };

  window.SCENES = S;
})();
