"""
flowlib.py - JAMA-format study flow diagrams (CONSORT / STROBE) in matplotlib
============================================================================

Reusable engine for CONSORT / STROBE participant-flow figures.
A study script supplies only the counts dict and the sequence of steps:

    import sys; sys.path.insert(0, "<skill>/scripts")
    from flowlib import Flow

    N = {"screened": 1000, "ex_age": 50, "enrolled": 950, ...}
    fl = Flow(N, height_in=12.0)
    fl.step(f"Patients screened (No. = {fl.f('screened')})",
            None,
            f"Excluded (No. = {fl.tot('ex_age', 'ex_other')})",
            f"Age <18 y: {fl.f('ex_age')}\\nOther: {fl.f('ex_other')}")
    last = fl.step("Analytic cohort ...", "...", last=True)
    fl.branches(last, [("Head 1", "body"), ("Head 2", "body"), ("Head 3", "body")],
                label="Analysis populations")
    fl.footnote("Abbreviations: ...")
    fl.save("consort_diagram")          # .pdf .svg .png (600 dpi)

    fl.chk("screened - excluded = enrolled",
           N["screened"] - N["ex_age"] - N["ex_other"], N["enrolled"])
    fl.report()

JAMA figure rules this enforces:
  * sans-serif (Arial/Helvetica), >= 6 pt at printed size; TrueType embedded
  * plain black rules, white boxes, no colour, shadows or 3-D
  * vector output (PDF/SVG); commas in 4+ digit numbers; "No." not "n"
Counts left as None print as an em-dash rule so gaps stay visible.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrow, Rectangle

BLANK = "————"       # em-dash rule: a count still to be supplied

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "Helvetica Neue", "DejaVu Sans"],
    "pdf.fonttype": 42,      # TrueType, required for JAMA submission
    "ps.fonttype": 42,
})


class Flow:
    def __init__(self, N, width_in=7.0, height_in=12.0, fs=7.4, spc=1.5,
                 lw=0.7, pad=1.15, hgap=0.55, gap=3.8,
                 spine_x=3, spine_w=48, excl_x=54, excl_w=43):
        self.N = N
        self.FS, self.SPC, self.LW = fs, spc, lw
        self.PAD, self.HGAP, self.GAP = pad, hgap, gap
        self.SX, self.SW, self.EX, self.EW = spine_x, spine_w, excl_x, excl_w
        # one text line, in axis units (axes span 0-100 over height_in inches)
        self.LH = (fs * spc) / (height_in * 72 / 100)

        self.fig = plt.figure(figsize=(width_in, height_in))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, 100)
        self.ax.set_ylim(0, 100)
        self.ax.axis("off")

        self.spine = 98.5
        # the exclusion column has its own cursor, so a tall exclusion box
        # never pushes the spine down
        self.excl_floor = 98.5
        self.bottom = self.spine
        self._checks = []

    # ---- number formatting -------------------------------------------------
    def f(self, key):
        v = self.N.get(key)
        return f"{v:,}" if v is not None else BLANK

    def tot(self, *keys):
        vals = [self.N.get(k) for k in keys]
        return f"{sum(vals):,}" if all(v is not None for v in vals) else BLANK

    def diff(self, a, b):
        x, y = self.N.get(a), self.N.get(b)
        return f"{x - y:,}" if x is not None and y is not None else BLANK

    # ---- primitives --------------------------------------------------------
    @staticmethod
    def _nlines(s):
        return len(s.split("\n")) if s else 0

    def height(self, head, body=None):
        n = self._nlines(head) + (self.HGAP + self._nlines(body) if body else 0)
        return 2 * self.PAD + n * self.LH

    def box(self, x, top, w, head, body=None):
        h = self.height(head, body)
        ax = self.ax
        ax.add_patch(Rectangle((x, top - h), w, h, facecolor="white",
                               edgecolor="black", linewidth=self.LW, zorder=2))
        ax.text(x + 1.8, top - self.PAD, head, fontsize=self.FS, weight="bold",
                ha="left", va="top", zorder=3, linespacing=self.SPC)
        if body:
            ax.text(x + 1.8, top - self.PAD - (self._nlines(head) + self.HGAP) * self.LH,
                    body, fontsize=self.FS, ha="left", va="top", zorder=3,
                    linespacing=self.SPC)
        self.bottom = min(self.bottom, top - h)
        return {"cx": x + w / 2, "top": top, "bottom": top - h,
                "left": x, "right": x + w, "h": h}

    def v_arrow(self, x, y0, y1, head=True):
        self.ax.add_patch(FancyArrow(x, y0, 0, y1 - y0, width=0.001,
                                     head_width=1.0 if head else 0,
                                     head_length=0.9 if head else 0,
                                     length_includes_head=True, color="black",
                                     linewidth=self.LW, zorder=1))

    def elbow(self, x_from, y, x_to):
        self.ax.plot([x_from, x_to - 1.6], [y, y], color="black", lw=self.LW, zorder=1)
        self.ax.add_patch(FancyArrow(x_to - 2.0, y, 2.0, 0, width=0.001,
                                     head_width=1.0, head_length=0.9,
                                     length_includes_head=True, color="black",
                                     linewidth=self.LW, zorder=1))

    # ---- layout ------------------------------------------------------------
    def step(self, head, body=None, ex_head=None, ex_body=None, last=False):
        """One spine box, with an optional exclusion box off to the right."""
        b = self.box(self.SX, self.spine, self.SW, head, body)
        self.spine = b["bottom"]
        if last:
            return b
        y_elbow = self.spine - self.GAP / 2
        if ex_head:
            eh = self.height(ex_head, ex_body)
            e_top = min(y_elbow + eh / 2, self.excl_floor - 1.5)
            self.box(self.EX, e_top, self.EW, ex_head, ex_body)
            self.excl_floor = e_top - eh
            self.elbow(b["cx"], y_elbow, self.EX)
        self.v_arrow(b["cx"], self.spine, self.spine - self.GAP)
        self.spine -= self.GAP
        return b

    def branches(self, parent, boxes, label=None, margin=2.0, sep=2.1):
        """Split `parent` into len(boxes) side-by-side boxes via a rail.
        boxes: list of (head, body) tuples. Returns the list of box dicts."""
        k = len(boxes)
        bw = (100 - 2 * margin - (k - 1) * sep) / k
        cols = [margin + i * (bw + sep) for i in range(k)]
        centers = [c + bw / 2 for c in cols]
        rail = parent["bottom"] - 4.2
        top = rail - 3.8
        self.v_arrow(parent["cx"], parent["bottom"], rail, head=False)
        self.ax.plot([min(centers), max(centers)], [rail, rail],
                     color="black", lw=self.LW, zorder=1)
        for c in centers:
            self.v_arrow(c, rail, top)
        if label:
            self.ax.text(parent["cx"] + 1.8, rail + 0.7, label, fontsize=self.FS,
                         style="italic", ha="left", va="bottom")
        return [self.box(c, top, bw, h, b) for c, (h, b) in zip(cols, boxes)]

    def footnote(self, text, fs=6.3):
        top = self.bottom - 2.6
        self.ax.text(3, top, text, fontsize=fs, ha="left",
                     va="top", linespacing=1.6)
        lh = (fs * 1.6) / (self.fig.get_figheight() * 72 / 100)
        self.bottom = top - self._nlines(text) * lh

    def save(self, stem="consort_diagram"):
        # crop unused space below the content while keeping the scale
        if self.bottom > 1.5:
            lo = self.bottom - 1.5
            w, h = self.fig.get_size_inches()
            self.fig.set_size_inches(w, h * (100 - lo) / 100)
            self.ax.set_ylim(lo, 100)
        for ext, kw in (("pdf", {}), ("svg", {}), ("png", {"dpi": 600})):
            self.fig.savefig(f"{stem}.{ext}", bbox_inches="tight",
                             pad_inches=0.12, **kw)
        if self.bottom < 0:
            print(f"WARNING: content runs off the page (bottom = {self.bottom:.1f}); "
                  f"increase height_in")
        print(f"wrote {stem}.pdf, .svg and .png")

    # ---- arithmetic check --------------------------------------------------
    def chk(self, label, lhs, rhs):
        self._checks.append((label, lhs, rhs))

    def report(self):
        ok = True
        print("\nflow arithmetic")
        for label, lhs, rhs in self._checks:
            good = lhs == rhs
            ok &= good
            print(f"  [{'ok ' if good else 'OFF'}] {label}: {lhs:,} vs {rhs:,}"
                  + ("" if good else f"   difference {lhs - rhs:+,}"))
        return ok
