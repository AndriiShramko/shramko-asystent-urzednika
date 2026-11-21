# Task card digest: "Cyfryzacja formularzy" (Centralny Ośrodek Informatyki)

Source: the two PDFs in the organisers' task folder (full task; task regulations), read 21 November 2026, 11:12. Digest in our words; ids are ours. Prize: 25,000 PLN (one main prize, tax deducted by the partner).

## What they ask for, in one sentence

A service that takes one blank form file and returns a JSON document, in **their** structure, from which an electronic form can be built in their system. The user is the official who digitises forms for e-services, not the resident and not the counter clerk.

## The situation they describe

- Offices publish forms as PDF, DOC, DOCX, ODS, XLSX and as scanned images (JPG, JPEG, PNG). People print, fill in by hand and bring or send them.
- These forms are designed for handwriting: they carry elements that only make sense on paper and lack what a digital form offers.
- Digitising one form takes several steps of analysis: understand the procedure behind it, find the data it needs and how the data depend on each other, decide what to simplify, redesign the content for the screen, plan validation and, where needed, integration.
- It is slow and expensive because forms differ widely and follow no common standard; even forms for the same procedure differ between offices.
- They expect AI to read the document, recognise its structure and fields, and turn it into an ordered data model.
- They state that forms built from such data should **later also be usable by AI agents**, and that the result may serve other AI projects of theirs.

## Materials they prepared (C-MAT)

On Discord, channel of the task, "materiały-dodatkowe":

1. sample form files in several formats and sizes; for some of them the matching JSON files; screenshots of a sample e-service;
2. forms for which our solution must produce JSON files, **these outputs are judged**;
3. rules for designing electronic forms that the JSON must respect (example given: splitting a form into thematic pages) and technical assumptions of the form configuration;
4. a description of dictionaries and of initial data that forms may use;
5. tokens for working on the solution, for the first 20 teams.

## Mandatory minimum (C-MIN)

| Id | Requirement |
|---|---|
| C-MIN-1 | A REST service accepts form files in the listed formats and returns JSON that (a) matches the content of the form, (b) has the structure their application expects (shown by the sample outputs), (c) follows their form-design rules |
| C-MIN-2 | Architecture documentation (see C-TECH-DOC) |

## Optional extensions, scored (C-OPT)

| Id | Extension |
|---|---|
| C-OPT-1 | Use the dictionaries and initial data: link the fitting ones to fields in the JSON |
| C-OPT-2 | Propose a new dictionary where the provided base has none that fits |
| C-OPT-3 | Dependencies between fields, sections and pages; dynamic flows that depend on what the user chooses |
| C-OPT-4 | A simple front end to upload forms and look through the resulting JSON |
| C-OPT-5 | An application that shows the e-service form built from a JSON file |
| C-OPT-6 | Anything that helps verification and validation (data type, field length, phone number, PESEL and so on) and the user's work (batch processing of many documents, interface mock-ups) |

## What the submission must contain (C-SUB)

Title and detailed description; a presentation as PDF, **at most 10 slides**; the resulting JSON files; a film of **at most 3 minutes** in an open repository (link); the code repository. Optional: screenshots, links to a demo, graphics.

## Technical requirements (C-TECH)

| Id | Requirement |
|---|---|
| C-TECH-LANG | Preferred: Java 21 or newer, or Python 3.14 or newer |
| C-TECH-OSS | Only open-source libraries, not under copyleft licences (their examples: AGPL, GNU GPL); no purchase of commercial licences; latest stable versions preferred |
| C-TECH-NOEXT | **No dependencies such as external APIs, MCP, SaaS.** In particular the solution may not use language models that are available only through an API. Such models may be used to write, test and design the code |
| C-TECH-API | REST API to send a single file (a blank form); the answer is the JSON configuration of the form, ready for import into the target system |
| C-TECH-FMT | Inputs: `.pdf`, `.doc`, `.docx`, `.ods`, `.xlsx`, `.jpg`, `.jpeg`, `.png` |
| C-TECH-MIME | Accept only these formats and verify the MIME type so that content matches the extension |
| C-TECH-NAME | File name at most 250 characters and without any of `; : > < / \ | ' * % $` |
| C-TECH-SIZE | Maximum file size configurable through application parameters |
| C-TECH-TEMP | Files are processed only temporarily, in memory or in temporary space, during the request |
| C-TECH-DOCKER | Complete Docker configuration; official base images; light distributions preferred (Alpine named); explicit versions, never `latest`; the process runs as a dedicated user with limited rights; only the needed ports exposed; secrets and sensitive values supplied only at run time |
| C-TECH-CONF | Configurable at least: maximum file size, **JWT authentication parameters**, any integration parameters |
| C-TECH-DOC | `README.md` with: how to build the image, how to run, the configuration, the REST API |

## How it is tested (C-TEST)

Finalists are asked to run the solution on **new files handed over during the defence**.

## Criteria (C-CRIT)

| Weight | Criterion |
|---|---|
| 30 % | Completeness by thresholds: the mandatory minimum, then the extensions named in the criteria list: dictionaries and initial data; new dictionary; dynamic dependencies; front end for import; field validations |
| 20 % | How intuitive the solution is |
| 10 % | Originality |
| 20 % | Code quality |
| 20 % | Deployment potential, including the cost of the solution |

Note: the task lists six extensions, the criteria list five (the viewer of C-OPT-5 is not named there, and validations carry number V). Ask the mentors whether C-OPT-5 is scored.

## Context and contact

- The best solution may be deployed in projects the partner plans for the coming years; the card names "Generator Formularzy", "AI HUB", "Multiportal". The winning team may be invited to cooperate.
- Mentors: at the partner's stand and on Discord.

## Regulations of the task (C-REG)

- Jury of at least three specialists named by the partner; decisions final.
- The winners must sign an agreement transferring the economic copyrights in the works created for the task (template: annex 1 of the regulations); without a signature within 7 days of receiving it the prize is lost. The prize is paid within 7 days of signing. **The owner reads the template before submitting; this file is not legal advice.**
- Each participant declares authorship of their contribution and that the solution infringes nobody's rights.
