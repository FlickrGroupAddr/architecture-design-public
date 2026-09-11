# Clean-room architecture comparison provenance

On 2026-08-23, Terry disclosed that the FGA architecture work begun in this
repository on 2026-08-20 was intentionally developed as an independent design
track after he became frustrated with a separate design discussion with Claude
Opus 5. The separate design had not been shown to Sol during this repository's
initial architecture and phase-by-phase review work.

At disclosure, the independent track comprised 96 commits from root commit
`449490b` (`2026-08-20T11:12:04-04:00`) through commit `887b6c4`. Treat that
history as the pre-disclosure comparison baseline. Later discussion may compare
it with the Claude Opus 5 proposal, but must distinguish independently derived
convergence or divergence from changes made after the other proposal became
available.

This records process provenance, not a conclusion that either design is better
and not a legal characterization of a formal clean-room implementation process.

## Comparison purpose and success criterion

Terry intentionally restarted from himself as the only expected customer and
from the desired Lightroom Classic customer experience. The independent track
was allowed to defer backend architecture until the FGA LrC plug-in workflow
needed it. The prior Claude-era material was withheld until the independent
track could produce its own reviewed architecture and a high-level diagram.

After disclosure, the purpose is to decide which earlier elements, if any, are
worth adding to, changing in, or removing from the independent baseline. The
goal is not to merge the designs, maximize reuse, validate either agent, or make
the tracks converge. Selective reuse is a successful result; rejecting every
earlier element is also a successful result when the customer-centered baseline
and repository evidence support that outcome. The value of the exercise is the
independent comparison itself and the ability to identify convergence,
divergence, and obsolete scope without hindsight contaminating the initial
customer-experience design.
