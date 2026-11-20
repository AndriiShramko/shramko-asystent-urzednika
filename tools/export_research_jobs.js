// Export the research job prompts from an orchestration script into research/_jobs/*.md
// Usage: node tools/export_research_jobs.js <workflow-script.js> <out-dir>
// The script file is expected to define COMMON (string) and JOBS (array of {key, prompt}) before
// a line that starts with "const SUMMARY_SCHEMA".
const fs = require('fs')
const path = require('path')

const [, , scriptPath, outDir] = process.argv
if (!scriptPath || !outDir) {
  console.error('usage: node export_research_jobs.js <workflow-script.js> <out-dir>')
  process.exit(2)
}
let src = fs.readFileSync(scriptPath, 'utf8')
const cut = src.indexOf('const SUMMARY_SCHEMA')
if (cut < 0) throw new Error('marker "const SUMMARY_SCHEMA" not found')
src = src.slice(0, cut).replace('export const meta', 'const meta')

const TAIL = [
  '',
  'FINAL ANSWER FORMAT: after writing the files, reply with at most 25 lines:',
  'FILES: list of files written;',
  'KEY FINDINGS: up to 10 one-sentence bullets;',
  'VERDICTS: one line per claim id (CONFIRMED / PARTLY / WRONG / UNVERIFIABLE, with the correction);',
  'SURPRISES: findings that change the plan;',
  'NOT DONE: what is missing and why.',
  '',
].join('\n')

const run = new Function('fs', 'path', 'outDir', 'TAIL', src + `
fs.mkdirSync(outDir, { recursive: true })
for (const j of JOBS) {
  fs.writeFileSync(path.join(outDir, j.key + '.md'), COMMON + '\\n' + j.prompt + '\\n' + TAIL)
  console.log(j.key, (COMMON + j.prompt).length)
}
`)
run(fs, path, outDir, TAIL)
