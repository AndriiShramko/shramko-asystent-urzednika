# Model routing: which work runs where

One table for the lead. Two budgets exist: the owner's subscription (week for all models at 46 %, week for the top model at 56 % on 21 November 2026, 12:30; reset on 26 November, 13:00) and the partner's model credits (100 EUR on a gateway, build-time only, own ledger). Work on the top model counts in both subscription numbers; `opus` and `sonnet` count only in the first; the partner's credits and scripts count in neither.

| Kind of work | Where it runs | Why |
|---|---|---|
| Scope, decisions, contract changes, merges, talking to the owner | the lead session, the session's model | few steps, highest value; nobody else has the whole picture |
| Core stage of a "think" package: field finder, understanding step, composer and section library, conditions, parser isolation, security-sensitive code | `wp-thinker`, session's model (or `think_model: 'opus'` when the top-model week is above 85 %), effort high | the design is the product; a wrong design costs every later stage |
| By-spec packages; the integration and acceptance stages of every package | `wp-builder`, `sonnet`, effort medium, shell and files only | ready specification; the lean tool set keeps every step cheap; spares the top-model week |
| Review of one package before the merge | `wp-reviewer`, `opus`, effort high, read-only | an independent strong check that does not draw on the top-model week; it gets the diff and the acceptance list, not "check everything" |
| Second opinion at a milestone, critique of the seven judged outputs | partner's credits: one call to another model family (`openai/gpt-6.2-astra` or `google/gemini-4-neon`), prompt file with the diff or the JSON | independence of the model family for about 0.30 USD; nothing from the subscription |
| Bulk reading and labelling: silver labels for the judged and reference forms, lexicon mining over the 661 forms of the city's archive | partner's credits through a script: `anthropic/claude-haiku-5-5` or `openai/gpt-6-luna` (0.10 / 0.50 USD per million tokens), a stronger model only for the nine task sets | volume without judgement; results become rules or tests, never run-time dependencies |
| One fact the build needs (a licence, a wheel, a legal rule) | `web-researcher`, `sonnet`, medium; a broad sweep goes to the partner's credits (`perplexityai/sonar-deep-research`, 0.06 to 0.10 USD a report) | a focused question needs the repository's context; a sweep does not |
| Stages without a decision: build the image, run the batch, licence check, link check, metrics, PDF export, the film's screen recording | a shell command with a log; the GitHub Actions workflow for the image | no model is cheaper than any model |
| Looking at the review page or the viewer in a browser | one sub-agent with the browser tools; it reports one sentence per screen | pictures are heavy; the lead opens at most one |
| Short writing that needs what only the lead's conversation holds | a fork of the lead, under about fifteen steps | a fork re-reads the whole conversation on every step: rare, short, never for code |
| Closing notes: changelog, status sync, documentation after a milestone | a fresh `wp-builder` stage from files | mechanical; the lead checks the result with one command |
| The product at run time | no model at all; a switched-off interface for a local open model | the task card forbids hosted models; the default path must work on a plain processor |

Rules that go with the table:

1. Name models by alias (`sonnet`, `opus`, `haiku`, `fable`); the per-call model option takes aliases only (research/08).
2. Do not change the model or the tool set inside a running session without need: it empties the prompt cache.
3. The effort of the owner's own session is his choice. Savings come from the agents of mechanical stages at medium, not from lowering the lead.
4. `haiku` is for selection and labelling, never for judgement.
5. An agent is worth starting for about ten replies of work or a large read; anything smaller the lead does itself. A stage is planned for about thirty replies; longer work is split into stages before it starts, because asking an agent to "fit in thirty replies" does not work.
