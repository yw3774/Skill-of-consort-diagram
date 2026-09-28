"""
Worked example: new-user cohort, drug A vs drug B, STROBE flow diagram in JAMA
format. All counts are made-up placeholders. Copy this file next to the study,
then edit N and the steps.

Run:  python3 example_cohort.py
Out:  consort_diagram.pdf / .svg / .png
"""
import os, sys
sys.path.insert(0, os.path.expanduser("~/.claude/skills/flow-diagram-yw/scripts"))
from flowlib import Flow

# ===========================================================================
# COUNTS - one key per number; comment the source table; None = still missing
# ===========================================================================
N = {
    # --- 1. condition identified -----------------------------------------
    "identified":       10000,   # #pts_condition
    "ex_history":         600,   # #exclude_history
    "ex_pregnancy":       400,   # #exclude_pregnancy
    "ex_union":          1000,   # #all_exclusions (after removing overlap)

    # --- 2. eligible adults ----------------------------------------------
    "confirmed":         9000,   # #pts_confirmed
    "ex_age":             500,   # DERIVED: confirmed - age18
    "ex_prior_tx":        500,   # #exclude_prior_treatment
    "eligible":          8000,   # DERIVED: confirmed - ex_age - ex_prior_tx

    # --- 3. initiators ---------------------------------------------------
    "init_a":            4000,   # #drug_a_after_index
    "init_b":            4000,   # #drug_b_after_index
    "ex_death":           300,   # death before index date
    "ex_no_followup":     700,   # last encounter on or before index date

    # --- 4. analytic cohort ----------------------------------------------
    "cohort_a":          3500,
    "cohort_b":          3500,

    # --- 5. analysis populations -----------------------------------------
    "ps_a":              3500,
    "ps_b":              3500,
    "match_pairs":       3000,
    "lab_a":             3000,
    "lab_b":             3000,
    "disp_a":            2500,
    "disp_b":            2500,
    "disp_pairs":        None,   # not yet available -> prints as an em-dash rule
}

fl = Flow(N, width_in=7.0, height_in=7.6)

# ---- 1. condition identified ----------------------------------------------
fl.step(f"Patients with the condition identified\n"
        f"(No. = {fl.f('identified')})",
        "≥2 qualifying records ≥30 d apart; the earlier record\n"
        "defined the index condition date",
        f"Excluded (No. = {fl.f('ex_union')})",
        f"Exclusionary history before the condition date: {fl.f('ex_history')}\n"
        f"Pregnancy within 9 mo before or after: {fl.f('ex_pregnancy')}")

# ---- 2. age and prior treatment -------------------------------------------
fl.step(f"Patients with confirmed condition\n"
        f"(No. = {fl.f('confirmed')})",
        None,
        f"Excluded (No. = {fl.tot('ex_age', 'ex_prior_tx')})",
        f"Age <18 y at the condition date: {fl.f('ex_age')}\n"
        f"Any study drug before the condition date: {fl.f('ex_prior_tx')}")

# ---- 3. initiators ----------------------------------------------------------
fl.step(f"Initiated drug A or drug B\n"
        f"(No. = {fl.tot('init_a', 'init_b')})",
        f"Drug A: {fl.f('init_a')}\n"
        f"Drug B: {fl.f('init_b')}",
        f"Excluded (No. = {fl.tot('ex_death', 'ex_no_followup')})",
        f"Death recorded before the index date: {fl.f('ex_death')}\n"
        f"Last recorded encounter on or before the index\n"
        f"   date: {fl.f('ex_no_followup')}")

# ---- 4. analytic cohort -----------------------------------------------------
last = fl.step(f"Analytic cohort (No. = {fl.tot('cohort_a', 'cohort_b')})",
               f"Drug A initiators: {fl.f('cohort_a')}\n"
               f"Drug B initiators: {fl.f('cohort_b')}\n"
               "No patient contributed to both treatment groups",
               last=True)

# ---- 5. analysis populations ------------------------------------------------
fl.branches(last, [
    (f"Primary analysis\n(No. = {fl.tot('ps_a', 'ps_b')})",
     f"Drug A: {fl.f('ps_a')}\n"
     f"Drug B: {fl.f('ps_b')}\n"
     f"Matched pairs: {fl.f('match_pairs')}"),
    (f"Baseline laboratory value\n(No. = {fl.tot('lab_a', 'lab_b')})",
     f"Drug A: {fl.f('lab_a')}\n"
     f"Drug B: {fl.f('lab_b')}"),
    (f"Pharmacy dispensing data\n(No. = {fl.tot('disp_a', 'disp_b')})",
     f"Drug A: {fl.f('disp_a')}\n"
     f"Drug B: {fl.f('disp_b')}\n"
     f"Matched pairs: {fl.f('disp_pairs')}"),
], label="Analysis populations")

fl.footnote(
    "The index date was the first order or dispense of drug A or drug B on or after "
    "the condition date. Follow-up ran from the index date\n"
    "to the outcome, death, the last recorded encounter, or the end of the data, "
    "whichever came first.")

fl.save("consort_diagram")

# ---- arithmetic check: every DERIVED count must reconcile ------------------
fl.chk("identified - exclusions = confirmed",
       N["identified"] - N["ex_union"], N["confirmed"])
fl.chk("union = its named components",
       N["ex_history"] + N["ex_pregnancy"], N["ex_union"])
fl.chk("confirmed - age - prior tx = eligible",
       N["confirmed"] - N["ex_age"] - N["ex_prior_tx"], N["eligible"])
fl.chk("initiators - exclusions = analytic cohort",
       N["init_a"] + N["init_b"] - N["ex_death"] - N["ex_no_followup"],
       N["cohort_a"] + N["cohort_b"])
fl.report()
