---
name: flow-diagram-yw
description: |
  Build a publication-ready study flow diagram (CONSORT for trials, STROBE for observational /
  target-trial-emulation cohorts) in JAMA figure format: matplotlib → PDF/SVG/600-dpi PNG, plus a
  one-page Word figure sheet with title and legend. Counts live in one dict, derived counts are
  checked arithmetically, missing counts print as visible em-dash rules.
  Use when the user asks for a CONSORT diagram, STROBE flow diagram, patient flow / cohort
  selection figure, participant flowchart, or "Figure 1" for a manuscript, or wants to update
  the counts in an existing one.
---

# JAMA study flow diagram

Engine: `scripts/flowlib.py` (class `Flow`). Word wrapper: `scripts/make_docx.py`.
Full worked example (exclusion boxes, 3 analysis branches, an em-dash placeholder, arithmetic checks):
`examples/example_cohort.py` — **read it before writing a new figure** and copy its
structure.

## Workflow

1. **Collect counts first, draw second.** Get every box's No. from the cohort SQL output
   (row counts / `count(distinct PatientDurableKey)`) or the manuscript. Put them in one `N`
   dict at the top of the study script, one key per number, with a comment naming the source
   table. Mark anything computed by subtraction `# DERIVED: a - b`.
2. **Unknown counts stay `None`.** They render as `————` so the figure can circulate to
   co-authors with gaps visibly flagged. Never invent or back-fill a number to make boxes add up.
3. **Write the study script** in the user's project folder (not in the skill folder):
   ```python
   import os, sys
   sys.path.insert(0, os.path.expanduser("~/.claude/skills/flow-diagram-yw/scripts"))
   from flowlib import Flow
   fl = Flow(N, height_in=12.0)
   fl.step(head, body, ex_head, ex_body)     # spine box + optional exclusion box
   last = fl.step(head, body, last=True)     # final spine box, no arrow below
   fl.branches(last, [(head, body), ...], label="Analysis populations")
   fl.footnote("Abbreviations: ...")
   fl.save("consort_diagram")                # .pdf .svg .png
   fl.chk("a - b = c", N["a"] - N["b"], N["c"]); fl.report()
   ```
   Use `fl.f(key)`, `fl.tot(k1, k2)`, `fl.diff(a, b)` in text — they add thousands commas and
   fall back to the em-dash when any input is `None`.
4. **Run with `/usr/bin/python3`** (has matplotlib, python-docx, PIL). Every `chk` must print
   `[ok ]`. For an `OFF` line, report the difference to the user and ask; do not adjust counts.
   Anything that cannot be reconciled goes in an "unreconciled – needs a decision" printout and,
   if drawn, an exclusion box headed "Excluded (reason to be confirmed)".
5. **Look at the PNG** (Read it). Check for text overflowing box edges, overlapping exclusion
   boxes, content running off the bottom (`save` warns). Fix by raising `height_in`, breaking
   lines with `\n` + 3-space hanging indent, or widening `spine_w`/`excl_w`.
6. **Word file for co-authors:**
   `python3 make_docx.py consort_diagram.png consort_diagram.docx --title "Figure 1. ..." --legend legend.txt`
   Submit the PDF to the journal; the .docx is for circulation. To hand-edit in Word:
   Insert > Pictures > the .svg, right-click > Convert to Shape (quick fixes only).

## JAMA figure conventions (enforced or to follow in text)

- Sans-serif (Arial/Helvetica), ≥6 pt printed; TrueType embedded (`pdf.fonttype 42`).
- Black rules, white boxes, no colour, shading, shadows or 3-D.
- Vector submission (PDF/EPS). Commas in numbers ≥1,000. "No. =" not "n =".
- Title: "Figure 1. Flow of Patients Through the Study" (title case, above the figure).
  Legend starts with abbreviations ("GLP-1 indicates …; HbA1c, …").
- Spell out drug classes in boxes ("GLP-1 receptor agonist", not "GLP-1RA"); "y", "mo", "d".
- Observational cohort = STROBE diagram, not CONSORT; say so if the user calls it CONSORT.

## Content lessons

- Exclusion box header gives the total; list each reason with its count. When reasons are applied
  as one union, list components, then "Total, after removing overlap:"; state when categories are
  not mutually exclusive.
- Don't draw an exclusion box for a step that defines groups rather than excludes (e.g. drug
  initiation); state instead that arms overlap at that stage and are not additive.
- When the SQL runs several filters without saving intermediate counts, report the net removal
  per arm rather than inventing intermediate boxes.
- Keep counts for undrawn steps in `N` anyway so the `chk` lines still validate the data.
- Report analysis populations (primary, sensitivity subsets, PS trimming, matched pairs, IPTW ESS)
  as side-by-side branches below the analytic cohort.
