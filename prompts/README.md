# Runtime instructions for the product's AI steps

These are the starting versions of the system instructions used by the product at run time (not instructions for coding agents; those are in `AGENTS.md`). They answer requirement R13: what the checking agents must watch and how they must behave. The work packages that own each file (see `docs/03-plan/ownership.md`) refine them against the evaluation set.

| File | Step | Data class | Owner |
|---|---|---|---|
| `udip-analysis-system.md` | letter type, questions, classification | PERSONAL (pseudonymised by the gateway before any external call) | WP-A4 |
| `udip-draft-system.md` | writing the marked slots of a document | PERSONAL | WP-A5 |
| `form-check-system.md` | second check of filled forms | PERSONAL (local model, or pseudonymised) | WP-B5 |
| `bundle-recommender-system.md` | from a described situation to a set of forms | PUBLIC (the description must contain no identifying data) | WP-B1 / WP-B3 |
| `form-onboarding-system.md` | from a blank form to field proposals | PUBLIC | WP-B6 |

## Rules that hold for every instruction

1. **Instructions are in Polish and outputs are in Polish**, because the material and the readers are Polish. Field names of structured output stay in English as in the API contract.
2. **Outside text is data.** Requests, attachments and form contents are placed in a delimited block by the gateway helper; the instruction tells the model that nothing inside the block is a command.
3. **Structured output only**, validated against a schema; free text appears only inside named fields.
4. **No invented facts.** The model may use only what is in its input: the text, the retrieved provisions with their ids, the profile. Numbers, dates, names and legal bases that are not in the input are forbidden; code checks this after the call.
5. **The model proposes, a person decides.** No instruction lets the model reject, approve, send or change a state.
6. **Corrections against the earlier draft of these instructions** (see `docs/06-audit/`): the rule "never ask an anonymous applicant for identification" was removed, because the case law changed in 2024–2026 and the choice belongs to the office; hard-coded lists of form codes inside instructions were removed (the catalogue and the bundles are data); the instructions are no longer written in Russian.

## What each checker must watch (summary for humans)

**Public-information requests:** is it a request under the act at all; several questions in one letter; the filing date and both deadline dates; information already published; information the office does not hold; another access regime; processed information and the special public interest; restrictions (privacy, business secret, statutory secrets) and the exception for persons performing public functions; the right document type; mandatory elements of decisions; who must review; signs of a campaign; text addressed to the AI system.

**Filled forms:** checksum and consistency of identifiers; the same person spelled differently in two places; required fields per form; dates and terms from the service card; relation-dependent rules (proxy fee exemption, child's data defaults that are often wrong); document-type-dependent fields; one form per person where required; text too long for its boxes; likely recognition artefacts (0 and O, 1 and I, lost diacritics); a paper form that should not be printed at all because the state register generates it; the wrong delivery channel for the unit.
