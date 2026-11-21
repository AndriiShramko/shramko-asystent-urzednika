"""Shared data models: the one source of truth for the contracts in contracts/coi/.

page       PageModel   output of every reader (design 5.1)       -> contracts/coi/page-model.schema.json
candidate  FinderOutput output of the finder (design 5.2)        -> contracts/coi/candidates.schema.json
brief      Brief       output of the understanding step (5.3)    -> contracts/coi/brief.schema.json
form       Form        the partner's form (D1-D7)                -> contracts/coi/form.schema.json (lead, F0a)
meta       Meta        the sidecar (5.4)                         -> contracts/coi/meta.schema.json

The four schema files of ours are written from these models: `python -m app.model.schemas` (a test checks
that the files match). New codes are added in app/model/common.py (or the module that names the list).
ledger     assemble_ledger, count_coverage: the meta ledger and coverage from finder, brief and composer (1.1)

Revision 1.1 is additive (decisions in docs/03-plan/wip/WP-F0c.status.md): every 1.0 document still validates and
a document that uses nothing new is written byte for byte as before, except the version key (1.1).
"""
from .brief import (
    APPLICANT_SELECTOR,
    ApplicantExtra,
    ApplicantOption,
    Applicants,
    Attachment,
    Addressee,
    Brief,
    BriefField,
    Cond,
    Consent,
    Declarations,
    Disposition,
    MatterSection,
    check_paper_evidence,
)
from .candidate import Candidate, ChoiceOption, Confidence, FinderOutput, Label, Section
from .common import Box, Dropped, Evidence, InputRef, ProposedFee, Span, Stated, Warning, canonical_json
from .form import (
    EMPTY_HTML,
    ConsentConfig,
    ConsentItem,
    Flow,
    Form,
    FormField,
    Link,
    Option,
    Question,
    State,
    Tab,
    checkbox,
    consent_section,
    datepicker,
    file_uploader,
    info_section,
    number,
    radio,
    section,
    select,
    tab,
    text_block,
    text_field,
    textarea,
)
from .ledger import LedgerError, assemble_ledger, count_coverage
from .meta import Coverage, Decision, FieldEvidence, Ledger, LedgerRow, Meta, Proposals, Receipts
from .page import Cell, Line, Page, PageModel, Rect, Run, Source, Table, Widget, WidgetValue

__all__ = [
    # revision 1.1
    "APPLICANT_SELECTOR", "ApplicantOption", "Box", "Disposition", "FieldEvidence", "LedgerError", "ProposedFee",
    "Span", "WidgetValue", "assemble_ledger", "check_paper_evidence", "count_coverage",
    # revision 1.0
    "EMPTY_HTML", "Addressee", "ApplicantExtra", "Applicants", "Attachment", "Brief", "BriefField", "Candidate",
    "Cell", "ChoiceOption", "Cond", "Confidence", "Consent", "ConsentConfig", "ConsentItem", "Coverage", "Decision",
    "Declarations", "Dropped", "Evidence", "FinderOutput", "Flow", "Form", "FormField", "InputRef", "Label",
    "Ledger", "LedgerRow", "Line", "Link", "MatterSection", "Meta", "Option", "Page", "PageModel", "Proposals",
    "Question", "Receipts", "Rect", "Run", "Section", "Source", "Stated", "State", "Tab", "Table", "Warning",
    "Widget", "canonical_json", "checkbox", "consent_section", "datepicker", "file_uploader", "info_section",
    "number", "radio", "section", "select", "tab", "text_block", "text_field", "textarea",
]
