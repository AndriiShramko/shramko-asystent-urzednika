#!/usr/bin/env node
/*
 * deck_pdf.mjs — render the deck's print mode (site/deck/index.html?print=1)
 * to site/deck/Asystent-Urzednika.pdf (one 1920x1080 page per slide).
 *
 *   node tools/deck_pdf.mjs
 *
 * 1. Regenerates site/deck/metrics.js and status.js from metrics.json and
 *    status.json (the .js copies are what the deck reads when opened from disk).
 * 2. Uses Playwright if it is installed; otherwise runs the installed Chrome /
 *    Chromium / Edge headless with --print-to-pdf. Set CHROME_PATH to override.
 * 3. Prints the file size; exits with code 1 if it is 10 MB or more.
 */
import { existsSync, readFileSync, writeFileSync, statSync, mkdtempSync, rmSync } from 'node:fs';
import { join, dirname, resolve } from 'node:path';
import { tmpdir, platform } from 'node:os';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { spawnSync, execSync } from 'node:child_process';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const deck = join(root, 'site', 'deck');
const out = join(deck, 'Asystent-Urzednika.pdf');
const url = pathToFileURL(join(deck, 'index.html')).href + '?print=1';

function regen(name, globalName) {
  const data = JSON.parse(readFileSync(join(deck, name + '.json'), 'utf8'));
  const js = `/* GENERATED from ${name}.json by tools/deck_pdf.mjs — do not edit by hand.\n` +
    `   Browsers block reading ${name}.json when the deck is opened from disk\n` +
    `   (file://), so the engine falls back to this copy. */\n` +
    `window.${globalName} = ${JSON.stringify(data)};\n`;
  writeFileSync(join(deck, name + '.js'), js, 'utf8');
}
regen('metrics', 'DECK_METRICS');
regen('status', 'DECK_STATUS');

function findChrome() {
  if (process.env.CHROME_PATH && existsSync(process.env.CHROME_PATH)) return process.env.CHROME_PATH;
  const os = platform();
  const cands = [];
  if (os === 'win32') {
    for (const base of [process.env['PROGRAMFILES'], process.env['PROGRAMFILES(X86)'], process.env.LOCALAPPDATA]) {
      if (!base) continue;
      cands.push(join(base, 'Google', 'Chrome', 'Application', 'chrome.exe'));
      cands.push(join(base, 'Chromium', 'Application', 'chrome.exe'));
      cands.push(join(base, 'Microsoft', 'Edge', 'Application', 'msedge.exe'));
    }
  } else if (os === 'darwin') {
    cands.push('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
      '/Applications/Chromium.app/Contents/MacOS/Chromium',
      '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge');
  } else {
    for (const n of ['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser', 'microsoft-edge']) {
      try { const p = execSync('command -v ' + n, { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim(); if (p) cands.push(p); } catch { /* not found */ }
    }
  }
  return cands.find((p) => existsSync(p));
}

async function withPlaywright() {
  let pw;
  try { pw = await import('playwright'); } catch { return false; }
  const browser = await pw.chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto(url);
  await page.waitForSelector('html[data-ready="1"]');
  await page.pdf({ path: out, preferCSSPageSize: true, printBackground: true });
  await browser.close();
  return true;
}

function withChrome() {
  const chrome = findChrome();
  if (!chrome) throw new Error('Chrome/Chromium not found. Install it or set CHROME_PATH.');
  const profile = mkdtempSync(join(tmpdir(), 'deck-pdf-'));
  const args = ['--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
    '--user-data-dir=' + profile, '--no-pdf-header-footer', '--run-all-compositor-stages-before-draw',
    '--virtual-time-budget=6000', '--print-to-pdf=' + out, url];
  const r = spawnSync(chrome, args, { encoding: 'utf8', timeout: 120000 });
  try { rmSync(profile, { recursive: true, force: true }); } catch { /* profile still locked */ }
  if (!existsSync(out)) throw new Error('Chrome did not write the PDF:\n' + (r.stderr || '').slice(-2000));
  return chrome;
}

if (existsSync(out)) rmSync(out);
const how = (await withPlaywright()) ? 'playwright' : withChrome();
const size = statSync(out).size;
const pages = (readFileSync(out, 'latin1').match(/\/Type\s*\/Page[^s]/g) || []).length;
console.log(`PDF: ${out}\nsize: ${(size / 1048576).toFixed(2)} MB, pages: ${pages}, via: ${how}`);
if (size >= 10 * 1048576) { console.error('PDF is 10 MB or larger'); process.exit(1); }
