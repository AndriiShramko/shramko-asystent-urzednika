/*
 * scenes.js — the 8 animated drawings of "Od druku do usługi online"
 * (inline SVG, viewBox 1600x720). Spec: storyboard-formularze.md.
 *
 * Each scene: { L: seconds after which the gentle loop starts,
 *               svg(ctx): markup string,
 *               run(root, ctx): optional small JS timeline }
 * ctx.final === true means "draw the last frame, no motion" (print, key M,
 * prefers-reduced-motion). The natural, un-animated state of every element is
 * its final state; CSS classes in deck.css and scenes.css add the motion:
 *   class="e pop" style="--d:1.2s"   entrance (pop, fade, rise, drop, flip, slideL, slideR, draw, grow, out, fx-from)
 *   class="lp bob" style="--ld:.5s"  loop after the entrance (bob, pulse, glow, flow, spin, tap)
 *   class="lp-only"                  shown only while animating (hidden in print)
 * Rule: never put "e" and "lp" on the same element; nest a <g> instead.
 * Labels inside drawings are Polish and at most three words.
 *
 * Demo videos: put media/demo-1.mp4 (slide 3) and media/demo-2.mp4 (slide 4)
 * next to index.html — each replaces its animated mock automatically
 * (muted, looped). A missing file leaves the mock on screen.
 */
(function () {
  'use strict';

  /* ---------------- small drawing kit (same as the first deck) ---------------- */
  function svg(label, inner) {
    return '<svg viewBox="0 0 1600 720" role="img" aria-label="' + label + '" xmlns="http://www.w3.org/2000/svg">' + inner + '</svg>';
  }
  function d(sec) { return 'style="--d:' + sec + 's"'; }
  function t(x, y, s, size, cls, anchor) {
    return '<text x="' + x + '" y="' + y + '" font-size="' + (size || 44) + '" text-anchor="' + (anchor || 'middle') + '"' +
      (cls ? ' class="' + cls + '"' : '') + '>' + s + '</text>';
  }
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
  function qrIcon() {
    var s = '<rect width="110" height="110" rx="10" class="fi"/>';
    [[10, 10], [64, 10], [10, 64]].forEach(function (c) {
      s += '<rect x="' + c[0] + '" y="' + c[1] + '" width="36" height="36" rx="4" class="fbg"/><rect x="' + (c[0] + 11) + '" y="' + (c[1] + 11) + '" width="14" height="14" class="fi"/>';
    });
    return s + '<rect x="66" y="66" width="14" height="14" class="fbg"/><rect x="86" y="86" width="14" height="14" class="fbg"/><rect x="66" y="88" width="10" height="10" class="fbg"/>';
  }
  // a small paper sheet with a coloured type band (PDF / DOC / RTF)
  function sheet(x, y, w, h, type) {
    var band = type === 'PDF' ? 'fr' : type === 'DOC' ? 'fb' : 'fm';
    return '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="8" class="fi"/>' +
      '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + Math.round(h * 0.28) + '" rx="8" class="' + band + '"/>' +
      t(x + w / 2, y + h * 0.22, type, Math.round(w * 0.3), 'fbg') +
      '<rect x="' + (x + w * 0.16) + '" y="' + (y + h * 0.45) + '" width="' + (w * 0.68) + '" height="' + Math.max(5, h * 0.08) + '" rx="3" class="fl"/>' +
      '<rect x="' + (x + w * 0.16) + '" y="' + (y + h * 0.66) + '" width="' + (w * 0.5) + '" height="' + Math.max(5, h * 0.08) + '" rx="3" class="fl"/>';
  }
  // measured numbers (metrics.json) over a demo slide, HTML overlay; nothing when all are null
  function metricsHtml(ctx, keys) {
    var html = '';
    keys.forEach(function (k) {
      var v = ctx.metrics[k], lab = ctx.labels[k];
      if (v === null || v === undefined || !lab) return;
      html += '<div><b>' + v + lab.suffix + '</b><span>' + lab.label + '</span></div>';
    });
    return html ? '<div class="demo-metrics">' + html + '</div>' : '';
  }
  // labels that type themselves: <text data-type="1" data-at="1.6">imię</text>
  function typeLabels(root, ctx) {
    Array.prototype.forEach.call(root.querySelectorAll('[data-type]'), function (n) {
      var full = n.textContent, at = parseFloat(n.getAttribute('data-at')) * 1000;
      n.textContent = '';
      ctx.later(function () {
        var i = 0;
        ctx.every(function () { if (i <= full.length) n.textContent = full.slice(0, i++); }, 85);
      }, at);
    });
  }
  // numbers that count up: <text data-count="275" data-at="0.8">275</text>
  function countUp(root, ctx, ms) {
    Array.prototype.forEach.call(root.querySelectorAll('[data-count]'), function (n) {
      var target = parseFloat(n.getAttribute('data-count')), at = parseFloat(n.getAttribute('data-at') || 0) * 1000;
      n.textContent = '0';
      ctx.later(function () {
        var t0 = Date.now();
        ctx.every(function () {
          var p = Math.min(1, (Date.now() - t0) / ms);
          n.textContent = String(Math.round(target * (1 - Math.pow(1 - p, 2))));
        }, 40);
      }, at);
    });
  }
  // demo slide: the video if the file exists, else the animated mock
  function demoRun(file) {
    return function (root, ctx) {
      if (ctx.final) return;
      typeLabels(root, ctx);
      var wrap = root.querySelector('.demo-wrap');
      var v = root.querySelector('video');
      v.addEventListener('loadeddata', function () { wrap.classList.add('has-video'); v.play().catch(function () {}); });
      v.addEventListener('error', function () { wrap.classList.remove('has-video'); });
      v.src = file; // missing file => error event => the mock stays
    };
  }
  function demoWrap(mock, ctx, keys) {
    return '<div class="demo-wrap"><video muted loop playsinline preload="auto" aria-label="Nagranie demo"></video>' + mock + metricsHtml(ctx, keys) + '</div>';
  }
  function windowFrame() {
    return '<rect x="40" y="10" width="1520" height="700" rx="30" class="fp sl" stroke-width="5"/>' +
      '<circle cx="90" cy="50" r="12" class="fr"/><circle cx="130" cy="50" r="12" class="fa"/><circle cx="170" cy="50" r="12" class="fg"/>' +
      '<line x1="40" y1="90" x2="1560" y2="90" class="sl" stroke-width="4"/>';
  }

  /* QR code for https://formularze.flyreelstudio.eu (version 3, ECC M, 29x29).
     Generated with the Python "qrcode" package; decoded back with OpenCV, both
     from the module matrix and from the screenshot of slide 8 (tools/deck_smoke.py). */
  var QR_N = 29;
  var QR_PATH = 'M0 0h7v1h-7zM9 0h1v1h-1zM14 0h1v1h-1zM19 0h1v1h-1zM22 0h7v1h-7zM0 1h1v1h-1zM6 1h1v1h-1zM16 1h1v1h-1zM20 1h1v1h-1zM22 1h1v1h-1zM28 1h1v1h-1zM0 2h1v1h-1zM2 2h3v1h-3zM6 2h1v1h-1zM9 2h2v1h-2zM12 2h1v1h-1zM14 2h2v1h-2zM17 2h2v1h-2zM22 2h1v1h-1zM24 2h3v1h-3zM28 2h1v1h-1zM0 3h1v1h-1zM2 3h3v1h-3zM6 3h1v1h-1zM10 3h4v1h-4zM18 3h1v1h-1zM20 3h1v1h-1zM22 3h1v1h-1zM24 3h3v1h-3zM28 3h1v1h-1zM0 4h1v1h-1zM2 4h3v1h-3zM6 4h1v1h-1zM10 4h2v1h-2zM18 4h1v1h-1zM22 4h1v1h-1zM24 4h3v1h-3zM28 4h1v1h-1zM0 5h1v1h-1zM6 5h1v1h-1zM8 5h1v1h-1zM10 5h1v1h-1zM12 5h1v1h-1zM15 5h2v1h-2zM18 5h3v1h-3zM22 5h1v1h-1zM28 5h1v1h-1zM0 6h7v1h-7zM8 6h1v1h-1zM10 6h1v1h-1zM12 6h1v1h-1zM14 6h1v1h-1zM16 6h1v1h-1zM18 6h1v1h-1zM20 6h1v1h-1zM22 6h7v1h-7zM11 7h1v1h-1zM13 7h1v1h-1zM15 7h1v1h-1zM17 7h2v1h-2zM20 7h1v1h-1zM0 8h1v1h-1zM3 8h1v1h-1zM5 8h2v1h-2zM8 8h2v1h-2zM11 8h1v1h-1zM14 8h1v1h-1zM19 8h1v1h-1zM21 8h1v1h-1zM23 8h1v1h-1zM1 9h3v1h-3zM11 9h3v1h-3zM16 9h2v1h-2zM20 9h1v1h-1zM22 9h1v1h-1zM25 9h1v1h-1zM28 9h1v1h-1zM0 10h3v1h-3zM5 10h2v1h-2zM8 10h1v1h-1zM11 10h4v1h-4zM16 10h1v1h-1zM19 10h3v1h-3zM23 10h5v1h-5zM3 11h2v1h-2zM9 11h1v1h-1zM12 11h2v1h-2zM15 11h2v1h-2zM18 11h1v1h-1zM23 11h2v1h-2zM26 11h2v1h-2zM1 12h6v1h-6zM8 12h2v1h-2zM11 12h1v1h-1zM14 12h1v1h-1zM16 12h2v1h-2zM20 12h3v1h-3zM25 12h1v1h-1zM27 12h2v1h-2zM1 13h1v1h-1zM3 13h1v1h-1zM5 13h1v1h-1zM7 13h2v1h-2zM10 13h1v1h-1zM13 13h2v1h-2zM19 13h3v1h-3zM0 14h5v1h-5zM6 14h4v1h-4zM11 14h1v1h-1zM13 14h2v1h-2zM16 14h2v1h-2zM21 14h1v1h-1zM23 14h1v1h-1zM25 14h4v1h-4zM0 15h1v1h-1zM3 15h3v1h-3zM8 15h3v1h-3zM12 15h1v1h-1zM16 15h2v1h-2zM20 15h2v1h-2zM23 15h1v1h-1zM25 15h1v1h-1zM27 15h1v1h-1zM2 16h1v1h-1zM4 16h4v1h-4zM9 16h1v1h-1zM11 16h3v1h-3zM15 16h1v1h-1zM17 16h1v1h-1zM20 16h2v1h-2zM23 16h1v1h-1zM27 16h1v1h-1zM3 17h1v1h-1zM7 17h3v1h-3zM13 17h2v1h-2zM18 17h1v1h-1zM20 17h4v1h-4zM25 17h1v1h-1zM28 17h1v1h-1zM0 18h1v1h-1zM2 18h1v1h-1zM5 18h5v1h-5zM12 18h1v1h-1zM14 18h1v1h-1zM17 18h2v1h-2zM22 18h2v1h-2zM27 18h2v1h-2zM4 19h1v1h-1zM7 19h3v1h-3zM12 19h1v1h-1zM14 19h1v1h-1zM17 19h2v1h-2zM20 19h1v1h-1zM22 19h1v1h-1zM24 19h1v1h-1zM27 19h2v1h-2zM0 20h1v1h-1zM3 20h4v1h-4zM8 20h1v1h-1zM10 20h1v1h-1zM15 20h2v1h-2zM20 20h5v1h-5zM26 20h1v1h-1zM8 21h1v1h-1zM11 21h2v1h-2zM14 21h1v1h-1zM16 21h5v1h-5zM24 21h1v1h-1zM26 21h3v1h-3zM0 22h7v1h-7zM9 22h1v1h-1zM16 22h1v1h-1zM20 22h1v1h-1zM22 22h1v1h-1zM24 22h1v1h-1zM27 22h1v1h-1zM0 23h1v1h-1zM6 23h1v1h-1zM8 23h4v1h-4zM14 23h2v1h-2zM20 23h1v1h-1zM24 23h3v1h-3zM28 23h1v1h-1zM0 24h1v1h-1zM2 24h3v1h-3zM6 24h1v1h-1zM9 24h1v1h-1zM15 24h3v1h-3zM20 24h5v1h-5zM28 24h1v1h-1zM0 25h1v1h-1zM2 25h3v1h-3zM6 25h1v1h-1zM8 25h1v1h-1zM10 25h1v1h-1zM12 25h1v1h-1zM17 25h2v1h-2zM20 25h1v1h-1zM22 25h6v1h-6zM0 26h1v1h-1zM2 26h3v1h-3zM6 26h1v1h-1zM10 26h1v1h-1zM13 26h1v1h-1zM16 26h2v1h-2zM20 26h2v1h-2zM24 26h3v1h-3zM28 26h1v1h-1zM0 27h1v1h-1zM6 27h1v1h-1zM12 27h1v1h-1zM15 27h4v1h-4zM20 27h2v1h-2zM23 27h2v1h-2zM27 27h1v1h-1zM0 28h7v1h-7zM8 28h1v1h-1zM10 28h1v1h-1zM12 28h1v1h-1zM17 28h1v1h-1zM20 28h1v1h-1zM22 28h4v1h-4zM27 28h1v1h-1z';

  /* the wall of paper (slide 1) and its return (slide 8) share the type pattern */
  function wallType(k) { var r = (k * 7 + 3) % 10; return r < 6 ? 'PDF' : r < 9 ? 'DOC' : 'RTF'; }

  var S = {};

  /* 1. The size of the problem — a pin pours out a wall of forms; one is fillable */
  S.scale = {
    L: 7.5,
    svg: function () {
      var s = '';
      // the city pin
      s += '<g class="e drop" ' + d(0.2) + '><g class="lp bob" style="--lt:3s">' +
        '<path d="M190 340 C150 280 100 230 100 170 A90 90 0 0 1 280 170 C280 230 230 280 190 340 Z" class="fr"/>' +
        '<circle cx="190" cy="170" r="34" class="fbg"/></g></g>' +
        '<g class="e fade" ' + d(0.5) + '>' + t(190, 410, 'Bydgoszcz', 46) + '</g>';
      // the wall: 9 x 6 sheets pour out of the pin, bottom row first
      var cols = 9, rows = 6, x0 = 400, y0 = 30, gx = 80, gy = 96, w = 64, h = 84;
      var green = { c: 6, r: 5 };
      for (var r = 0; r < rows; r++) {
        for (var c = 0; c < cols; c++) {
          var x = x0 + c * gx, y = y0 + r * gy;
          var order = (rows - 1 - r) * cols + c;
          var dl = (0.6 + order * 0.065).toFixed(2);
          s += '<g class="e fx-from" style="--d:' + dl + 's;--t:.75s;--dx:' + (190 - x - w / 2) + 'px;--dy:' + (180 - y - h / 2) + 'px;--s:.3">' +
            sheet(x, y, w, h, wallType(r * cols + c)) + '</g>';
        }
      }
      // the one fillable form lights up green
      var gxp = x0 + green.c * gx, gyp = y0 + green.r * gy;
      s += '<g class="e pop" ' + d(6.0) + '><rect x="' + gxp + '" y="' + gyp + '" width="' + w + '" height="' + h + '" rx="8" class="fg"/>' +
        tick(gxp + w / 2 - 2, gyp + h / 2 + 4, 14, 'sbg') + '</g>' +
        '<g class="e fade" ' + d(6.0) + '><g class="lp glow" style="--lt:2.4s"><rect x="' + (gxp - 10) + '" y="' + (gyp - 10) + '" width="' + (w + 20) + '" height="' + (h + 20) + '" rx="14" class="fn sg" stroke-width="7"/></g></g>';
      s += '<g class="e rise" ' + d(6.5) + '>' + '<rect x="' + (gxp + w / 2 - 230) + '" y="628" width="460" height="76" rx="38" class="fp2 sg" stroke-width="6"/>' +
        t(gxp + w / 2, 680, '1 z 32 z polami', 44, 'fg') + '</g>';
      // two counters
      s += '<g class="e fade" ' + d(0.8) + '>' +
        '<text x="1390" y="190" font-size="140" text-anchor="middle" class="fa" data-count="275" data-at="0.8">275</text>' + t(1390, 260, 'kart usług', 48) +
        '<text x="1390" y="450" font-size="140" text-anchor="middle" class="fa" data-count="710" data-at="0.8">710</text>' + t(1390, 520, 'plików', 48) + '</g>';
      return svg('Mapa z pinezką Bydgoszcz, z której wysypuje się ściana druków; 275 kart usług, 710 plików, 1 z 32 z polami', s);
    },
    run: function (root, ctx) { if (!ctx.final) countUp(root, ctx, 3600); }
  };

  /* 2. The solution in one picture — scan, approve, three results */
  S.solution = {
    L: 7,
    svg: function () {
      var s = '';
      var fy = [200, 270, 340, 410, 480], boxCls = ['sa', 'sb', 'sg', 'sr', 'sa'];
      // the paper form
      s += '<g class="e slideL" ' + d(0.2) + '><rect x="80" y="90" width="300" height="480" rx="18" class="fi"/>' +
        '<rect x="110" y="122" width="180" height="22" rx="11" class="fl"/>';
      fy.forEach(function (y) {
        s += '<rect x="110" y="' + (y + 12) + '" width="66" height="14" rx="7" class="fl"/>' +
          '<rect x="190" y="' + y + '" width="160" height="40" rx="8" class="fn sl" stroke-width="5"/>';
      });
      s += '</g>';
      // the boxes the AI draws on the fields
      fy.forEach(function (y, k) {
        s += '<g class="e pop" ' + d((1.6 + k * 0.35).toFixed(2)) + '><g class="lp glow" style="--ld:' + (k * 0.3).toFixed(1) + 's;--lt:3s">' +
          '<rect x="183" y="' + (y - 7) + '" width="174" height="54" rx="12" class="fn ' + boxCls[k] + '" stroke-width="7"/></g></g>';
      });
      // scanning line: once, then gently in the loop
      s += '<g class="lp-only"><g class="s2-scan" opacity="0"><rect x="66" y="176" width="328" height="10" rx="5" class="fa"/></g>' +
        '<g class="lp s2-scanl" style="--lt:4.5s" opacity="0"><rect x="66" y="176" width="328" height="10" rx="5" class="fa"/></g></g>';
      // the person who approves
      s += '<g class="e fade" ' + d(0.5) + '>' + person(560, 160, 1.35, 'fb') + '</g>';
      s += '<g class="e pop" ' + d(3.4) + '><g class="e press" style="--d:4.1s;--t:.5s">' +
        chip(440, 400, 240, 76, 'zatwierdź', 40, 'fg', 'fbg') + '</g></g>';
      // three branches to the results
      var ys = [130, 340, 550];
      ys.forEach(function (y, i) {
        var p = 'M690 438 C760 438 750 ' + y + ' 812 ' + y;
        s += '<g class="e draw" style="--d:' + (4.5 + i * 0.15).toFixed(2) + 's;--t:.6s"><path d="' + p + '" pathLength="1" class="fn sl" stroke-width="8"/></g>' +
          '<g class="e fade" ' + d(5.2) + '><path d="' + p + '" class="fn sa lp flow" stroke-width="8" style="--lt:2s"/></g>';
      });
      // copies of the form fly to the results
      ys.forEach(function (y, i) {
        s += '<g class="lp-only"><g class="fx-fly" style="--d:' + (4.6 + i * 0.2).toFixed(1) + 's;--t:1s;--dx:660px;--dy:' + (y - 330) + 'px;--s:.6">' +
          '<rect x="180" y="270" width="100" height="120" rx="10" class="fi" opacity=".9"/></g></g>';
      });
      // the three results
      var icons = [
        '<rect x="845" y="40" width="100" height="180" rx="20" class="fp sl" stroke-width="7"/>' +
          '<rect x="862" y="72" width="66" height="20" rx="6" class="fa"/><rect x="862" y="106" width="66" height="20" rx="6" class="fa"/><rect x="862" y="140" width="66" height="20" rx="6" class="fa"/>' +
          '<rect x="872" y="182" width="46" height="18" rx="9" class="fg"/>',
        doc(830, 255, 130, 170) + '<path d="M860 404 h70" class="fn sm" stroke-width="4" stroke-dasharray="2 10"/>',
        '<rect x="830" y="465" width="130" height="170" rx="16" class="fp2 sl" stroke-width="6"/>' +
          tick(860, 510, 12, 'sg') + '<rect x="888" y="500" width="54" height="12" rx="6" class="fl"/>' +
          tick(860, 554, 12, 'sg') + '<rect x="888" y="544" width="54" height="12" rx="6" class="fl"/>' +
          tick(860, 598, 12, 'sg') + '<rect x="888" y="588" width="40" height="12" rx="6" class="fl"/>'
      ];
      var labels = ['formularz online', 'wydruk na wzorze', 'reguły kontroli'];
      ys.forEach(function (y, i) {
        s += '<g class="e slideR" ' + d((5.0 + i * 0.4).toFixed(1)) + '><g class="lp bob" style="--ld:' + (i * 0.5) + 's;--lt:3.5s">' +
          icons[i] + t(1000, y + 17, labels[i], 52, '', 'start') + '</g></g>';
      });
      return svg('Druk skanowany przez AI, człowiek zatwierdza; powstają formularz online, wydruk na wzorze i reguły kontroli', s);
    }
  };

  /* 3. Demo 1 — a PDF becomes an online form (video media/demo-1.mp4 if present) */
  S.demo1 = {
    L: 9,
    svg: function (ctx) {
      var s = windowFrame();
      // drop zone and the dropped PDF
      s += '<rect x="100" y="115" width="520" height="580" rx="22" class="fn sl" stroke-width="5" stroke-dasharray="16 16"/>';
      s += '<g class="e drop" style="--d:.3s;--t:1s"><rect x="130" y="130" width="460" height="550" rx="16" class="fi"/>' +
        chip(150, 150, 110, 50, 'PDF', 32, 'fr', 'fbg') + '<rect x="280" y="166" width="200" height="18" rx="9" class="fl"/>';
      var fy = [240, 330, 420, 510, 600];
      fy.forEach(function (y) {
        s += '<rect x="160" y="' + (y - 24) + '" width="90" height="12" rx="6" class="fl"/>' +
          '<rect x="160" y="' + y + '" width="400" height="48" rx="8" class="fn sl" stroke-width="4"/>';
      });
      s += '</g>';
      // AI boxes: three right away, two misplaced and dragged into place by a cursor
      var cls = ['sa', 'sa', 'sa', 'sb', 'sb'], drag = [null, null, null, [70, 30, 4.0], [-56, 36, 5.2]];
      fy.forEach(function (y, k) {
        var box = '<rect x="152" y="' + (y - 8) + '" width="416" height="64" rx="12" class="fn ' + cls[k] + '" stroke-width="7"/>';
        if (drag[k]) {
          var g = drag[k];
          box = '<g class="s3-drag" style="--d:' + g[2] + 's;--dx:' + g[0] + 'px;--dy:' + g[1] + 'px">' + box +
            '<g class="lp-only"><g class="s3-cur" style="--d:' + g[2] + 's"><path d="M548 ' + (y + 44) + ' l0 52 l14 -14 l12 26 l12 -6 l-12 -25 l20 0 z" class="fi sbg" stroke-width="4"/></g></g></g>';
        }
        s += '<g class="e pop" ' + d((1.4 + k * 0.5).toFixed(1)) + '>' + box + '</g>';
      });
      // labels type themselves next to the first three boxes
      [['imię', 1.6], ['PESEL', 2.1], ['adres', 2.6]].forEach(function (l, k) {
        var y = fy[k] + 24;
        s += '<g class="e fade" ' + d(l[1]) + '><line x1="568" y1="' + y + '" x2="640" y2="' + y + '" class="sa" stroke-width="6"/>' +
          '<rect x="640" y="' + (y - 32) + '" width="240" height="64" rx="32" class="fp2 sa" stroke-width="5"/>' +
          '<text x="760" y="' + (y + 14) + '" font-size="40" text-anchor="middle" class="fa" data-type="1" data-at="' + (l[1] + 0.2) + '">' + l[0] + '</text></g>';
      });
      // field list fills in step by step
      s += '<g class="e fade" ' + d(0.8) + '><rect x="940" y="130" width="320" height="400" rx="22" class="fp2 sl" stroke-width="5"/></g>';
      fy.forEach(function (y, k) {
        var ry = 170 + k * 72;
        s += '<g class="e grow" style="--d:' + (1.5 + k * 0.5).toFixed(1) + 's;--t:.45s"><circle cx="980" cy="' + ry + '" r="16" class="' + (k < 3 ? 'fa' : 'fb') + '"/>' +
          '<rect x="1010" y="' + (ry - 10) + '" width="' + [210, 170, 200, 150, 190][k] + '" height="20" rx="10" class="fl"/></g>';
      });
      // publish, and the phone form pops up
      s += '<g class="e pop" ' + d(6.0) + '><g class="e press" style="--d:6.8s;--t:.5s">' +
        chip(950, 570, 300, 80, 'Opublikuj', 42, 'fg', 'fbg') + '</g></g>';
      s += '<g class="e pop" ' + d(7.4) + '><g class="lp bob" style="--lt:3.5s">' +
        '<rect x="1320" y="140" width="200" height="420" rx="36" class="fp sl" stroke-width="8"/>' +
        '<rect x="1346" y="186" width="148" height="22" rx="8" class="fa"/>';
      for (var k = 0; k < 4; k++) {
        s += '<rect x="1346" y="' + (232 + k * 62) + '" width="60" height="10" rx="5" class="fl"/>' +
          '<rect x="1346" y="' + (248 + k * 62) + '" width="148" height="30" rx="8" class="fbg sl" stroke-width="3"/>';
      }
      s += '<rect x="1370" y="500" width="100" height="36" rx="18" class="fg"/></g></g>';
      var mock = svg('Pokaz: druk PDF zamienia się w formularz online', s);
      return demoWrap(mock, ctx, ['digitise_seconds', 'fields_detected_pct', 'forms_digitised']);
    },
    run: demoRun('media/demo-1.mp4')
  };

  /* 4. Demo 2 — visitor's phone and clerk's screen (video media/demo-2.mp4 if present) */
  S.demo2 = {
    L: 9,
    svg: function (ctx) {
      var s = '<rect x="40" y="10" width="740" height="700" rx="30" class="fp sl" stroke-width="5"/>' +
        '<rect x="820" y="10" width="740" height="700" rx="30" class="fp sl" stroke-width="5"/>';
      // visitor: QR code on the desk, phone scans it
      s += '<g class="e fade" ' + d(0.2) + '><g transform="translate(92,250) scale(1.5)">' + qrIcon() + '</g></g>';
      s += '<g class="e fade" ' + d(0.9) + '><path d="M372 270 L262 244 L262 420 L372 392 Z" class="fa" opacity=".22"/></g>';
      s += '<g class="e slideL" ' + d(0.4) + '><rect x="372" y="60" width="250" height="600" rx="40" class="fp2 sl" stroke-width="8"/>';
      var fy = [170, 270, 370];
      fy.forEach(function (y) {
        s += '<rect x="402" y="' + (y - 28) + '" width="80" height="12" rx="6" class="fl"/>' +
          '<rect x="402" y="' + y + '" width="190" height="56" rx="10" class="fbg sl" stroke-width="4"/>';
      });
      s += '</g>';
      fy.forEach(function (y, k) {
        s += '<g class="e grow" style="--d:' + (1.5 + k * 0.4).toFixed(1) + 's;--t:.5s"><rect x="418" y="' + (y + 19) + '" width="' + [150, 120, 140][k] + '" height="18" rx="9" class="fa"/></g>';
      });
      s += '<g class="e pop" ' + d(2.7) + '>' + '<rect x="432" y="520" width="130" height="56" rx="28" class="fa"/>' + tick(494, 550, 12, 'sbg') + '</g>';
      // the locked packet crosses to the clerk
      s += '<g class="e pop" ' + d(3.0) + '><g class="lp pulse" style="--lt:2.6s"><circle cx="800" cy="360" r="46" class="fp2 sa" stroke-width="6"/>' + lock(800, 360, 1.05, 'fa') + '</g></g>';
      s += '<g class="lp-only"><g class="fx-fly" style="--d:2.9s;--t:1.3s;--dx:520px;--dy:-220px;--s:.8">' +
        '<rect x="440" y="500" width="110" height="80" rx="14" class="fa"/>' + lock(495, 540, .8, 'fbg') + '</g></g>';
      // clerk's screen with the data in very large type
      s += '<g class="e rise" ' + d(0.6) + '><rect x="850" y="44" width="680" height="400" rx="22" class="fbg sl" stroke-width="7"/>' +
        '<path d="M1190 444 v34 m-80 0 h160" class="fn sl" stroke-width="9"/></g>';
      var rows = [['Anna Nowak', 135], ['31.02.1990', 255], ['ul. Polna 7', 375]];
      rows.forEach(function (r, k) {
        s += '<g class="e fade" ' + d((3.6 + k * 0.3).toFixed(1)) + '>' + t(885, r[1], r[0], 58, '', 'start') + '</g>';
        if (k === 1) {
          s += '<g class="e pop" ' + d(4.7) + '><circle cx="1485" cy="' + (r[1] - 20) + '" r="26" class="fa"/>' + t(1485, r[1] - 4, '!', 42, 'fbg') + '</g>';
        } else {
          s += '<g class="e pop" ' + d((4.4 + k * 0.3).toFixed(1)) + '><circle cx="1485" cy="' + (r[1] - 20) + '" r="26" class="fg"/>' + tick(1483, r[1] - 18, 12, 'sbg') + '</g>';
        }
      });
      // the date turns amber with a note
      s += '<g class="e fade" ' + d(5.2) + '><g class="lp glow" style="--lt:2.4s"><rect x="868" y="190" width="644" height="92" rx="16" class="fn sa" stroke-width="7"/></g></g>';
      s += '<g class="e pop" ' + d(5.6) + '>' + chip(1212, 210, 230, 52, 'sprawdź datę', 30, 'fa', 'fbg') + '</g>';
      // print: the filled sheet slides out with a dotted signature line
      s += '<g class="e pop" ' + d(6.2) + '><g class="e press" style="--d:6.9s;--t:.5s">' + chip(870, 520, 240, 80, 'Drukuj', 44, 'fg', 'fbg') + '</g></g>';
      s += '<rect x="1160" y="500" width="320" height="30" rx="12" class="fl"/>';
      s += '<clipPath id="s4clip"><rect x="1150" y="528" width="340" height="182"/></clipPath>' +
        '<g clip-path="url(#s4clip)"><g class="s4-out" ' + d(7.2) + '><rect x="1190" y="520" width="260" height="176" rx="6" class="fi"/>' +
        '<rect x="1215" y="552" width="170" height="14" rx="7" class="fl"/><rect x="1215" y="584" width="200" height="14" rx="7" class="fl"/>' +
        '<rect x="1215" y="616" width="140" height="14" rx="7" class="fl"/>' +
        '<path d="M1300 670 h126" class="fn sm" stroke-width="5" stroke-dasharray="2 11"/></g></g>';
      var mock = svg('Pokaz: interesant skanuje kod i podaje dane, urzędnik widzi je i drukuje wniosek', s);
      return demoWrap(mock, ctx, ['fill_seconds']);
    },
    run: demoRun('media/demo-2.mp4')
  };

  /* 5. Proven in a real queue — Opole 2022 */
  S.queue = {
    L: 7,
    svg: function () {
      var s = '';
      s += '<line x1="60" y1="606" x2="1540" y2="606" class="sl" stroke-width="8"/>';
      // badge
      s += '<g class="e pop" ' + d(0.3) + '><g class="lp pulse" style="--lt:3s">' + chip(320, 50, 760, 88, 'punkt pomocy uchodźcom', 50, 'fp2 sa', 'fa') + '</g></g>';
      // printer (paper in the loop comes out of its top)
      s += '<g class="lp-only"><g class="lp s5-print" style="--lt:2.6s" opacity="0">' + doc(1320, 196, 160, 120) + '</g></g>';
      s += '<g class="e rise" ' + d(0.5) + '><rect x="1250" y="300" width="300" height="170" rx="26" class="fp sb" stroke-width="8"/>' +
        '<rect x="1300" y="290" width="200" height="22" rx="8" class="fl"/><circle cx="1500" cy="350" r="12" class="fg"/></g>';
      // printed forms land on the pile
      [3.6, 4.6, 5.6].forEach(function (dl, k) {
        s += '<g class="e fx-from" style="--d:' + dl + 's;--t:.8s;--dx:0px;--dy:-90px">' + doc(1300 + k * 8, 486 - k * 14, 200, 110) + '</g>';
      });
      // one person (phone glowing as they type) at the head of the queue, then the rest
      function guest(cx, i) {
        return person(cx, 330, 1.7, 'fb') +
          '<rect x="' + (cx + 40) + '" y="' + 440 + '" width="34" height="56" rx="8" class="fp sl" stroke-width="4"/>' +
          '<g class="e fade" style="--d:' + (1.6 + i * 0.2).toFixed(1) + 's"><g class="lp glow" style="--ld:' + (i * 0.35).toFixed(2) + 's;--lt:1.8s">' +
          '<rect x="' + (cx + 45) + '" y="' + 446 + '" width="24" height="40" rx="4" class="fa"/></g></g>';
      }
      s += '<g class="e out" style="--d:3.9s;--t:.6s" opacity="0"><g class="e pop" ' + d(0.4) + '>' + guest(1030, 0) + '</g></g>';
      s += '<g class="s5-q">';
      s += '<g class="e out" style="--d:5s;--t:.6s" opacity="0"><g class="e pop" ' + d(0.6) + '>' + guest(1190, 1) + '</g></g>';
      [1030, 870, 710, 550, 390].forEach(function (cx, j) {
        s += '<g class="e pop" ' + d((0.8 + j * 0.2).toFixed(1)) + '>' + guest(cx, j + 2) + '</g>';
      });
      s += '</g>';
      return svg('Kolejka ludzi z telefonami, drukarka wydaje gotowe wnioski, kolejka się skraca', s);
    }
  };

  /* 6. Data once, without a shared database */
  S.once = {
    L: 9,
    svg: function () {
      var s = '';
      // the phone with the profile and a padlock
      s += '<g class="e slideL" ' + d(0.2) + '><rect x="80" y="30" width="250" height="410" rx="40" class="fp sl" stroke-width="8"/></g>';
      s += '<g class="e pop" ' + d(0.5) + '><g class="lp pulse" style="--lt:3s">' + lock(205, 96, 1.2, 'fg') + '</g></g>';
      var rows = [150, 190, 230, 270, 310, 350, 390], lit = [1, 3, 5];
      rows.forEach(function (y, k) {
        s += '<g class="e fade" ' + d((0.5 + k * 0.08).toFixed(2)) + '><rect x="115" y="' + (y - 11) + '" width="180" height="22" rx="11" class="fl"/></g>';
      });
      lit.forEach(function (k, i) {
        s += '<g class="e grow" style="--d:' + (1.0 + i * 0.3).toFixed(1) + 's;--t:.4s"><rect x="115" y="' + (rows[k] - 11) + '" width="180" height="22" rx="11" class="fa"/></g>';
      });
      // path phone -> QR -> office
      s += '<line x1="340" y1="240" x2="530" y2="240" class="sl" stroke-width="7" stroke-dasharray="4 18"/>' +
        '<line x1="692" y1="240" x2="836" y2="240" class="sl" stroke-width="7" stroke-dasharray="4 18"/>' +
        '<line x1="340" y1="240" x2="530" y2="240" class="sa lp flow" stroke-width="7" style="--lt:1.6s"/>' +
        '<line x1="692" y1="240" x2="836" y2="240" class="sa lp flow" stroke-width="7" style="--lt:1.6s"/>';
      s += '<g class="e pop" ' + d(0.9) + '><g transform="translate(541,170) scale(1.27)">' + qrIcon() + '</g></g>';
      s += '<g class="e fade" ' + d(0.6) + '>' + building(960, 110, 220, 230, 'sb') + '</g>';
      // three locked fields fly through the QR code to the office
      lit.forEach(function (k, i) {
        var cy = rows[k];
        s += '<g class="lp-only"><g class="s6-hop" style="--d:' + (2.0 + i * 0.2).toFixed(1) + 's;--qx:' + (610 - 205) + 'px;--qy:' + (240 - cy) + 'px;--dx:' + (960 - 205) + 'px;--dy:' + (300 - cy) + 'px">' +
          '<rect x="115" y="' + (cy - 14) + '" width="180" height="28" rx="14" class="fa"/>' + lock(140, cy - 2, .5, 'fbg') + '</g></g>';
      });
      // the packet at the office dissolves; the timer above it runs out
      s += '<g class="lp-only"><g class="s6-pkt"><rect x="900" y="270" width="120" height="76" rx="14" class="fa"/>' + lock(960, 300, .8, 'fbg') + '</g></g>';
      s += '<g class="e fade" ' + d(3.4) + '><circle cx="760" cy="120" r="38" class="fn sl" stroke-width="10"/>' +
        '<circle cx="760" cy="120" r="38" pathLength="1" class="fn sa s6-drain" stroke-width="10" stroke-dasharray="1" style="stroke-dashoffset:1" transform="rotate(-90 760 120)"/>' +
        '<path d="M760 98 V120 H776" class="fn sm" stroke-width="7"/></g>';
      // the big database of people that we do not build
      s += '<g class="e pop" ' + d(7.0) + '><path d="M1250 80 v230 a120 36 0 0 0 240 0 v-230" class="fp sm" stroke-width="7"/>' +
        '<ellipse cx="1370" cy="80" rx="120" ry="36" class="fp2 sm" stroke-width="7"/>' +
        person(1320, 150, 0.75, 'fm') + person(1420, 150, 0.75, 'fm') + person(1370, 230, 0.75, 'fm') + '</g>' +
        '<g class="e draw" style="--d:7.6s;--t:.4s"><path d="M1215 40 L1525 390" pathLength="1" class="fn sr" stroke-width="18"/></g>' +
        '<g class="e draw" style="--d:7.9s;--t:.4s"><path d="M1525 40 L1215 390" pathLength="1" class="fn sr" stroke-width="18"/></g>';
      // the shelf of form descriptions shared by offices
      s += '<g class="e fade" ' + d(5.4) + '><line x1="200" y1="600" x2="770" y2="600" class="sb" stroke-width="14"/>' + t(485, 668, 'katalog opisów', 48) + '</g>';
      for (var k = 0; k < 6; k++) {
        s += '<g class="e pop" ' + d((5.6 + k * 0.15).toFixed(2)) + '><rect x="' + (232 + k * 88) + '" y="' + (512 + (k % 2) * 8) + '" width="56" height="' + (82 - (k % 2) * 8) + '" rx="8" class="' + (k % 2 ? 'fa' : 'fi') + '"/></g>';
      }
      [1000, 1200, 1400].forEach(function (cx, i) {
        var p = 'M778 600 C840 600 850 690 920 690 H' + cx + ' V664';
        s += '<g class="e draw" style="--d:' + (6.3 + i * 0.25).toFixed(2) + 's;--t:.5s"><path d="' + p + '" pathLength="1" class="fn sl" stroke-width="7"/></g>' +
          '<g class="e fade" ' + d(7.2) + '><path d="' + p + '" class="fn sb lp flow" stroke-width="7" style="--lt:2s"/></g>' +
          '<g class="e fade" ' + d((6.5 + i * 0.25).toFixed(2)) + '>' + building(cx, 520, 120, 100, 'sb') + '</g>';
      });
      return svg('Dane zostają na telefonie; tylko trzy pola trafiają do urzędu na kilka minut; wspólny katalog opisów zamiast bazy danych o ludziach', s);
    }
  };

  /* 7. What works, what is simulated — lists from status.json (from the first deck) */
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

  /* 8. Close — the wall of paper turns into phones, QR code */
  S.offer = {
    L: 6,
    svg: function () {
      var s = '', cols = 8, rows = 5, x0 = 60, y0 = 20, gx = 108, gy = 104, w = 80, h = 92;
      for (var r = 0; r < rows; r++) {
        for (var c = 0; c < cols; c++) {
          var x = x0 + c * gx, y = y0 + r * gy, wave = c + r;
          var dl = 0.6 + wave * 0.2;
          s += '<g class="e out" style="--d:' + dl.toFixed(1) + 's;--t:.35s" opacity="0">' + sheet(x, y, w, h, wallType(r * cols + c)) + '</g>';
          s += '<g class="e pop" style="--d:' + (dl + 0.15).toFixed(2) + 's;--t:.5s"><g class="lp glow" style="--ld:' + (wave * 0.15).toFixed(2) + 's;--lt:3s">' +
            '<rect x="' + (x + 14) + '" y="' + y + '" width="52" height="' + h + '" rx="12" class="fp sl" stroke-width="4"/>' +
            '<rect x="' + (x + 20) + '" y="' + (y + 10) + '" width="40" height="62" rx="5" class="fa"/>' +
            '<rect x="' + (x + 26) + '" y="' + (y + 20) + '" width="28" height="8" rx="4" class="fbg"/>' +
            '<rect x="' + (x + 26) + '" y="' + (y + 36) + '" width="28" height="8" rx="4" class="fbg"/>' +
            '<rect x="' + (x + 26) + '" y="' + (y + 52) + '" width="18" height="8" rx="4" class="fbg"/></g></g>';
        }
      }
      var size = 440, unit = size / (QR_N + 8);
      s += '<g class="e fade" style="--d:3.6s;--t:1s"><rect x="1090" y="20" width="' + size + '" height="' + size + '" rx="18" fill="#ffffff"/>' +
        '<g transform="translate(' + (1090 + 4 * unit) + ',' + (20 + 4 * unit) + ') scale(' + unit + ')"><path d="' + QR_PATH + '" fill="#000000" shape-rendering="crispEdges"/></g></g>';
      s += '<g class="e fade" ' + d(4.2) + '>' + t(800, 612, 'formularze.flyreelstudio.eu', 54, 'fa') +
        t(800, 682, 'github.com/AndriiShramko/shramko-asystent-urzednika', 34, 'fm') + '</g>';
      return svg('Ściana druków zamienia się w telefony; kod QR do formularze.flyreelstudio.eu', s);
    }
  };

  window.SCENES = S;
})();
