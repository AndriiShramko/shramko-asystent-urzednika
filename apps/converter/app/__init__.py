"""The forms converter: a blank official form in, the form JSON of the e-services generator out.

Rules and a library of standard sections only: no language model runs here and nothing calls out of the
process. Module layout: docs/02-architecture/converter-design.md, section 2. One work package owns one
sub-package (docs/03-plan/ownership.md); shared models live in app.model.
"""

__version__ = "0.1.0"
