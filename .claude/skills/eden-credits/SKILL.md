---
name: eden-credits
description: When and how to spend the partner's model credits (the Eden AI gateway, 100 EUR for the team, build-time only) - the tool tools/eden/eden.py, models and prices seen on 21 November 2026, key handling, the spending cap, what may be sent. Use before any bulk reading, silver labelling, lexicon mining, second-opinion review or web research that would otherwise burn the subscription.
---

# The partner's model credits

The partner gave the team one key to a gateway with every frontier model, capped at 100 EUR, **only for solving this task**. The product may not use it: nothing in the product calls out of the container. The credits are for building.

## Key handling (the partner's own conditions)

- The key lives in the user-level environment variable `EDENAI_API_KEY` on the owner's laptop. `tools/eden/eden.py` reads it; nothing else does.
- Never print it, echo it, pass it on a command line, put it into a prompt, a brief, a file, a log, a commit, front-end code or a chat message. A sub-agent that needs the gateway calls the tool; it never sees the key.
- If the tool says the key is missing, ask the owner. Do not look for it.

## The tool

```
python tools/eden/eden.py models --grep gemini          # catalogue with prices, no key needed
python tools/eden/eden.py budget                        # what the ledger says was spent
python tools/eden/eden.py chat --model <id> --prompt-file q.md --out research/eden/<name>.md --purpose research
```

Options: `--system`, `--image <path>` (repeatable), `--max-tokens`, `--json`, `--extra '<JSON merged into the request>'`, `--raw <file>`, `--timeout`. Every call lands in `.eden/ledger.jsonl` (git-ignored). The tool refuses to call once the ledger reaches `EDEN_BUDGET_USD` (default 115, the whole grant of 100 EUR; the owner lifted the earlier 60 USD cap on 21 November 16:45). Run long calls in the background with a log file; read the last line.

## What it costs (measured today)

| Use | Model | Seen cost |
|---|---|---|
| Web research with citations, 3 to 6 minutes | `perplexityai/sonar-deep-research` | 0.06 to 0.10 USD a report |
| Search-grounded answer, long | `google/gemini-4-neon` with `--extra '{"web_search_options":{"search_context_size":"high"}}'` | about 0.30 USD |
| Long design or critique answer | `openai/gpt-6.2-astra`, `anthropic/claude-opus-5-5` | 0.30 to 0.40 USD |
| Bulk reading, labelling, extraction | `anthropic/claude-haiku-5-5`, `openai/gpt-6-luna` | 0.10 / 0.50 USD per million tokens in / out |
| Middle tier with images or PDF | `anthropic/claude-sonnet-5-5`, `google/gemini-4-carbon` | 2 / 10 USD per million tokens |

Traps seen: the Google "deep-research" models answer HTTP 400 on this endpoint; a reasoning model can spend the whole `--max-tokens` on thinking and return an empty text with `finish=length` (give it room, or add `"reasoning_effort":"low"` through `--extra`): **check that the output file is not empty**. Prices change: `models --grep` before a large run.

## Spend it on

1. **Silver labels.** For each judged form and each reference form, an independent reading by a strong model (title, addressee, who may apply, fields of the matter with types, choices, attachments, declarations, fee) as JSON. They are a second opinion for our rules, never the truth and never shipped as output.
2. **Lexicon mining.** Bulk model over the text of the city's archive (661 forms): label to field type, validator, concept, dictionary candidate. A human-readable table is committed; a rule or a test must back every entry the product uses.
3. **Second-opinion review** by another model family before a milestone: the diff and the acceptance list in one prompt file, findings as a list. One call, not a panel.
4. **Research** the build needs: licences, wheels, a legal rule. One focused question a call.
5. **Critique of our outputs** for the judged forms before submission.

## Do not spend it on

- Anything at run time of the product, or anything the demo depends on.
- Work a script can do; work that needs the repository's tools (that is a sub-agent's job).
- Personal data of any kind. Blank forms, our code and our documents are public material and may be sent.

## Rules for what comes back

Model reports go to `research/eden/` with the model name in the file name; they are raw material, labelled unverified. A claim enters a document of ours only with its source checked or with the label "unverified". A label enters the product only as a rule or a test that passes without the model.

## Budget

Plan: research and ideas up to 10 USD, silver labels and lexicon up to 15, reviews and critique up to 15, reserve the rest. Write the `budget` line into `docs/03-plan/STATUS.md` at every milestone.
