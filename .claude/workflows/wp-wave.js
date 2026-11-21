export const meta = {
  name: 'wp-wave',
  description: 'Run a wave of work packages: one builder per package in its own worktree, three at a time, then one independent review per finished package',
  whenToUse: 'The lead starts several ready work packages of one milestone. Pass args: { packages: [{ id, slug, file, kind, read }], width }',
  phases: [
    { title: 'Build', detail: 'one builder sub-agent per work package, own worktree and branch' },
    { title: 'Review', detail: 'one independent reviewer per package that reported ready' },
  ],
}

// args example:
// { "packages": [
//     { "id": "A1", "slug": "case-store", "file": "docs/03-plan/work-packages/WP-A1-case-store.md", "kind": "spec" },
//     { "id": "A2", "slug": "gateway-pii", "file": "docs/03-plan/work-packages/WP-A2-model-gateway-pii.md", "kind": "think" }
//   ], "width": 3 }
// kind "spec"  -> middle model tier, medium effort (implementation from a ready specification)
// kind "think" -> top model tier, high effort (security, legal form, design); always reviewed
// width: at most 3 unless the owner has raised the limit (see docs/04-orchestration/lead-agent-playbook.md)

const input = args || {}
const packages = Array.isArray(input.packages) ? input.packages : []
if (packages.length === 0) {
  throw new Error('wp-wave: pass args.packages = [{ id, slug, file, kind }]')
}
const width = Math.max(1, Math.min(Number(input.width) || 3, 3))

const BUILD_REPORT = {
  type: 'object',
  properties: {
    status: { type: 'string', description: 'ready | blocked | out_of_budget' },
    branch: { type: 'string' },
    commits: { type: 'array', items: { type: 'string' } },
    proven: { type: 'array', items: { type: 'string' }, description: 'acceptance items that pass, with numbers' },
    not_verified: { type: 'array', items: { type: 'string' } },
    requests_to_lead: { type: 'array', items: { type: 'string' } },
    next_step: { type: 'string' },
  },
  required: ['status', 'branch', 'commits', 'proven', 'not_verified', 'requests_to_lead', 'next_step'],
}

const REVIEW_REPORT = {
  type: 'object',
  properties: {
    verdict: { type: 'string', description: 'merge | fix_first' },
    blocking: { type: 'array', items: { type: 'string' } },
    non_blocking: { type: 'array', items: { type: 'string' } },
    checked: { type: 'array', items: { type: 'string' }, description: 'what was actually run or read' },
  },
  required: ['verdict', 'blocking', 'non_blocking', 'checked'],
}

function buildBrief(p) {
  const branch = 'wp/' + p.id + '-' + p.slug
  const extra = Array.isArray(p.read) && p.read.length ? p.read.map((x, i) => (i + 3) + '. ' + x).join('\n') + '\n' : ''
  return [
    'You are the builder of work package WP-' + p.id + ' in this repository. You work in your own git worktree.',
    'First command: `git branch -m ' + branch + '` (if the branch is not already named so). Work only inside this worktree.',
    '',
    'RESUME-FIRST: before anything run `git log main..HEAD --oneline`, `git status --short` and read',
    '"## Status" in docs/03-plan/wip/WP-' + p.id + '.status.md. If work exists, you are continuing it: never redo',
    'committed steps or re-run checks that passed for unchanged inputs; uncommitted files are your',
    'predecessor\'s work in progress: inspect the diff, finish or revert it, commit first.',
    'CHECKPOINTS: commit after every finished step and update the Status checklist in the same commit;',
    'commit before any run longer than 2 minutes.',
    '',
    'READ (in this order, only these):',
    '1. AGENTS.md',
    '2. ' + p.file,
    extra,
    'DO: exactly what the work package says. Edit only the paths it owns (docs/03-plan/ownership.md).',
    'If you need a change elsewhere (API contract, shared schema, a dependency, another module), do not make it:',
    'write it under "## Requests to lead" in your status file and continue against a mock.',
    '',
    'DONE means: every acceptance item passes, shown by command output; `tools/gate.sh fast` passes;',
    'one negative control is recorded in the status file.',
    '',
    'COST: every reply re-reads your whole context. Read a file by the needed part, once. Batch independent',
    'reads and commands. Keep command output under 3,000 tokens (tail, counts, logs to a file). Write files',
    'with the file-writing tool, never a shell heredoc. Synthetic test data only. Before returning add one',
    'line to "## Cost notes" in the status file: what took the most turns and what would make it cheaper.',
    '',
    'Your final answer is the structured report: status ready, blocked or out_of_budget; the branch name;',
    'commit hashes; what is proven with numbers; what is not verified; requests to lead; the next step.',
  ].join('\n')
}

function reviewBrief(p, build) {
  return [
    'Independent review of work package WP-' + p.id + '. You did not write this code. Do not edit files.',
    'Read: AGENTS.md (hard rules), ' + p.file + ' (acceptance list and owned paths).',
    'Inspect: `git diff main...' + build.branch + ' --stat`, then the diff of the files that matter;',
    'run the tests of the package and `tools/gate.sh fast` on that branch (check it out in a temporary worktree,',
    'remove it afterwards).',
    'Check, in this order: (1) every acceptance item really passes; (2) nothing outside the owned paths was',
    'changed; (3) the hard rules: no real personal data, no secrets, outside text treated as data, personal',
    'data never sent to an external model unmasked, no silent changes without a clerk; (4) the negative control',
    'in the status file is real. First try to prove each of your findings wrong; report only what survives.',
    'Verdict "merge" or "fix_first". Blocking findings: one sentence each with file and line.',
    'The builder reported: ' + JSON.stringify({ proven: build.proven, not_verified: build.not_verified }).slice(0, 1500),
  ].join('\n')
}

async function pool(jobs, w, fn) {
  const out = new Array(jobs.length)
  let next = 0
  async function worker() {
    while (next < jobs.length) {
      const i = next
      next = next + 1
      try {
        out[i] = await fn(jobs[i])
      } catch (e) {
        out[i] = { id: jobs[i].id, error: String(e && e.message ? e.message : e) }
        log('WP-' + jobs[i].id + ' failed: ' + out[i].error)
      }
    }
  }
  const workers = []
  for (let k = 0; k < Math.min(w, jobs.length); k++) workers.push(worker())
  await Promise.all(workers)
  return out
}

log('wp-wave: ' + packages.map(p => 'WP-' + p.id).join(', ') + ' (width ' + width + ')')

const results = await pool(packages, width, async (p) => {
  const think = p.kind === 'think'
  const build = await agent(buildBrief(p), {
    label: 'build WP-' + p.id,
    phase: 'Build',
    schema: BUILD_REPORT,
    agentType: 'wp-builder',
    isolation: 'worktree',
    model: think ? 'opus' : 'sonnet',
    effort: think ? 'high' : 'medium',
  })
  if (!build) return { id: p.id, build: null, review: null }
  log('WP-' + p.id + ': ' + build.status + ' on ' + build.branch)
  if (build.status !== 'ready') return { id: p.id, build, review: null }
  const review = await agent(reviewBrief(p, build), {
    label: 'review WP-' + p.id,
    phase: 'Review',
    schema: REVIEW_REPORT,
    agentType: 'wp-reviewer',
    model: 'opus',
    effort: 'high',
  })
  if (review) log('WP-' + p.id + ' review: ' + review.verdict)
  return { id: p.id, build, review }
})

return {
  ready_to_merge: results.filter(r => r && r.review && r.review.verdict === 'merge').map(r => r.id),
  fix_first: results.filter(r => r && r.review && r.review.verdict !== 'merge').map(r => ({ id: r.id, blocking: r.review.blocking })),
  not_ready: results.filter(r => r && r.build && r.build.status !== 'ready').map(r => ({ id: r.id, status: r.build.status, next: r.build.next_step, requests: r.build.requests_to_lead })),
  failed: results.filter(r => !r || r.error || r.build === null).map(r => (r ? r.id : null)),
  results,
}
