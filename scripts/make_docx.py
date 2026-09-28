"""
make_docx.py - wrap a flow-diagram PNG in a one-page JAMA-layout Word file
==========================================================================

    python3 make_docx.py consort_diagram.png consort_diagram.docx \
        --title "Figure 1. Flow of Patients Through the Study" \
        --legend legend.txt

The legend file is plain text; its first paragraph (abbreviations) is set in
italics, each following line is its own paragraph. The page is made as tall
as the figure needs, so type never shrinks below 5 pt. Submit the PDF to the
journal; this .docx is for co-authors.
"""

import argparse

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("png")
ap.add_argument("out")
ap.add_argument("--title", default="Figure 1. Flow of Patients Through the Study")
ap.add_argument("--legend", help="text file with the legend", default=None)
ap.add_argument("--width", type=float, default=6.9, help="printed width, inches")
a = ap.parse_args()

legend = open(a.legend).read().strip() if a.legend else ""
MARGIN = 0.8

with Image.open(a.png) as im:
    aspect = im.height / im.width
img_h = a.width * aspect
page_h = MARGIN * 2 + 0.30 + img_h + 0.15 + 0.2 + 0.25 * max(1, len(legend) // 110)

doc = Document()
s = doc.sections[0]
s.page_width, s.page_height = Inches(8.5), Inches(page_h)
s.top_margin = s.bottom_margin = s.left_margin = s.right_margin = Inches(MARGIN)

normal = doc.styles["Normal"]
normal.font.name = "Arial"
normal.font.size = Pt(9)
normal.font.color.rgb = RGBColor(0, 0, 0)
normal.paragraph_format.space_before = Pt(0)
normal.paragraph_format.space_after = Pt(6)
normal.paragraph_format.line_spacing = 1.0

r = doc.add_paragraph().add_run(a.title)
r.bold = True
r.font.size = Pt(10)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(8)
p.add_run().add_picture(a.png, width=Inches(a.width))

for i, block in enumerate(l for l in legend.split("\n") if l.strip()):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(block)
    r.font.size = Pt(8)
    r.italic = i == 0

doc.save(a.out)
print(f"wrote {a.out}  (page 8.5 x {page_h:.1f} in, figure {a.width:.1f} x {img_h:.1f} in)")
