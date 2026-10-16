# Manual · sources

The method is cited; course and standard text is not reproduced.

## Courses it comes from

| Course | What it brings to the method |
|---|---|
| **Operations Management** (Gestión de Operaciones) | process analysis: describing a process as a sequence of activities with an owner, inputs and outputs, before improving it |

## What each rule of the format comes from

| Rule | Source |
|---|---|
| SIPOC on top of each page | The SIPOC diagram of the Six Sigma literature (Define phase): suppliers, inputs, process, outputs, customers, to fix the boundaries of a process before detailing it |
| The four source kinds (interview, document, observed, assumption) | Process discovery methods in Dumas et al.: interview-based, evidence-based (document analysis and observation) and workshop-based discovery, each with its known weaknesses. The manual records which one gave each step |
| Exactly one source per step, gaps instead of guesses | The traceability principle of the repo (`CLAUDE.md`, rule 5) applied to process documentation; Dumas et al. on the validation of a discovered model with the domain experts |
| Status, revision, history, approval by a person | ISO 9001:2015, clause 7.5 «documented information»: identification, review and approval for suitability (7.5.2), and control of changes and versions (7.5.3) |
| Letters until approval, `0` on approval, then numbers | The revision convention of engineering document control (issued for review with letters, issued for use from revision 0) |
| Caps on what is loaded, not on what is written | The repo's context contract (`docs/MANUAL-FORMAT.md`): the manual is complete; a model loads the index and one process |

## Bibliography

- Dumas, M.; La Rosa, M.; Mendling, J.; Reijers, H. A. *Fundamentals of Business Process
  Management*. 2nd ed. Springer, 2018. Chapters on process identification, process discovery
  (interviews, document analysis, observation, workshops) and the quality of process models.
- International Organization for Standardization. *ISO 9001:2015 Quality management systems ·
  Requirements*. Clause 7.5 «Documented information» (7.5.1 general, 7.5.2 creating and updating,
  7.5.3 control of documented information).
- Pyzdek, T.; Keller, P. *The Six Sigma Handbook*. 5th ed. McGraw-Hill, 2018. The Define phase and
  the SIPOC diagram.
- George, M. L.; Rowlands, D.; Price, M.; Maxey, J. *The Lean Six Sigma Pocket Toolbook*.
  McGraw-Hill, 2005. SIPOC and process mapping tools.
- Heizer, J.; Render, B.; Munson, C. *Operations Management: Sustainability and Supply Chain
  Management*. 13th ed. Pearson, 2020. Chapter on process strategy and process analysis.

## Where the judgement came from

From the shared contract `docs/MANUAL-FORMAT.md`, written for methodic: the manual is the memory
between sessions, so a line that cannot be traced is worse than a gap. The checks that stop a page
(a step without a source, a guessed logbook line, «Aprobado» typed by hand) are the errors that make
a manual look finished while nobody can say where it came from.
