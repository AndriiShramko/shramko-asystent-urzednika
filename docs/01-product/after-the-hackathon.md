# After the hackathon

Winning does not mean deployment: the organisers say winning teams may continue with the institution, and projects then pass verification, tests and adaptation to organisational, legal and technological requirements. This page is the owner's plan for that conversation, whatever the result.

## What to offer the city on Monday

1. A two-week test on exported historical requests inside the office, on the office's hardware, with a local model, with no connection to other systems. Deliverable: measured accuracy and time, and a list of differences between our templates and the office's own letters.
2. A pilot in one unit for four to eight weeks next to the current process. Deliverable: handling time before and after, and the clerks' verdict.
3. The online request form with the "already published" hint as a separate small step: it needs no access to internal systems at all.

Details, exit conditions and what the office must provide: [`../02-architecture/ai-layer.md`](../02-architecture/ai-layer.md) §5–§6.

## What must be true before real data

Security review, impact assessment and sign-off by the office's data protection officer, a processing agreement, an accessibility audit, staff training, a lawyer's review of every template. The list with legal sources: [`research/05`](../../research/05-rodo-ai-act-security-requirements.md) §6.

## Ownership and licence

The event rules expect that economic rights to a winning project pass to the institution, or that the project is published under an open licence; the exact clause comes with the task card. This repository is already open (MIT for code, CC BY 4.0 for documents), which satisfies the open-licence variant and does not prevent a transfer of the code written at the event. Third-party components keep their own licences; the dependency list is kept by the build.

## The wider plan

| Step | What | With whom |
|---|---|---|
| Open registry of form descriptions | Describe the most used forms once, share them between offices; detect changed templates by hash | other city halls; the organisations that maintain service catalogues |
| "Fill the form from the wallet" | The resident shares only the fields a form needs by scanning a QR code; the flow exists in the government app for selected partners and the EU wallet sandbox is open; an agreement is required | the ministry and the institution that builds the government app |
| Counter module pilot | Data once, forms filled on the approved templates, a second check before printing | a unit with many repeated paper forms; the 2022 Opole experience as the reference |
| Document reader | The owner's reader was donated for refugee registration; any product use needs the manufacturer's consent and current licences | the manufacturer, as a possible partner |

## Costs to expect

One server for the office (with a GPU if the local model is chosen), integration work per office system, a security and accessibility audit, maintenance of templates and rules as the law changes. No per-seat licence.

## What not to promise

A date for integration with a state system; savings in hours or money before they are measured in the office; that a printed form is "legally identical" to a statutory template (say: printed on the original template file, without re-typesetting).
