"""
RiderEx — Band.ai Hackathon Presentation Generator
Run: .venv/bin/python make_pptx.py
Output: RiderEx_Presentation.pptx
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import copy

# ── Palette ───────────────────────────────────────────────────────────
BG        = RGBColor(0x0B, 0x10, 0x18)   # deep navy-black
SURFACE   = RGBColor(0x13, 0x1A, 0x26)   # card surface
TEAL      = RGBColor(0x00, 0xE5, 0xC8)   # primary teal
GREEN     = RGBColor(0x63, 0xFF, 0xB4)   # go-green
AMBER     = RGBColor(0xFB, 0xBF, 0x24)   # warning amber
RED       = RGBColor(0xEF, 0x44, 0x44)   # danger red
PURPLE    = RGBColor(0x81, 0x8C, 0xF8)   # accent purple
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
MUTED     = RGBColor(0x94, 0xA3, 0xB8)
SLIDE_W   = Inches(13.33)
SLIDE_H   = Inches(7.5)

prs = Presentation()
prs.slide_width  = SLIDE_W
prs.slide_height = SLIDE_H
blank_layout = prs.slide_layouts[6]  # completely blank


# ── Helpers ───────────────────────────────────────────────────────────

def add_slide():
    slide = prs.slides.add_slide(blank_layout)
    # Full background rectangle
    bg = slide.shapes.add_shape(1, 0, 0, SLIDE_W, SLIDE_H)
    bg.fill.solid()
    bg.fill.fore_color.rgb = BG
    bg.line.fill.background()
    return slide


def txb(slide, text, l, t, w, h,
        size=20, bold=False, color=WHITE, align=PP_ALIGN.LEFT,
        italic=False, wrap=True):
    box = slide.shapes.add_textbox(l, t, w, h)
    tf  = box.text_frame
    tf.word_wrap = wrap
    p   = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size   = Pt(size)
    run.font.bold   = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return box


def rect(slide, l, t, w, h, fill=SURFACE, line_color=None, line_width=Pt(1)):
    shape = slide.shapes.add_shape(1, l, t, w, h)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    if line_color:
        shape.line.color.rgb = line_color
        shape.line.width = line_width
    else:
        shape.line.fill.background()
    return shape


def accent_bar(slide, color=TEAL, height=Inches(0.04)):
    """Top accent strip."""
    r = slide.shapes.add_shape(1, 0, 0, SLIDE_W, height)
    r.fill.solid()
    r.fill.fore_color.rgb = color
    r.line.fill.background()


def pill(slide, text, l, t, w=Inches(1.6), h=Inches(0.32),
         fill=TEAL, text_color=BG, size=10):
    r = rect(slide, l, t, w, h, fill=fill)
    txb(slide, text, l, t, w, h, size=size, bold=True,
        color=text_color, align=PP_ALIGN.CENTER)


def section_label(slide, text, t=Inches(0.55), color=TEAL):
    txb(slide, text.upper(), Inches(0.55), t, Inches(5), Inches(0.3),
        size=9, bold=True, color=color)


def divider(slide, t, color=TEAL, opacity_rect=False):
    r = slide.shapes.add_shape(1, Inches(0.55), t, Inches(12.23), Inches(0.015))
    r.fill.solid()
    r.fill.fore_color.rgb = color
    r.line.fill.background()


def add_multiline(slide, lines, l, t, w, h, default_size=14,
                  default_color=WHITE, line_spacing=None):
    """lines = list of (text, size, bold, color) or just str."""
    box = slide.shapes.add_textbox(l, t, w, h)
    tf  = box.text_frame
    tf.word_wrap = True
    first = True
    for item in lines:
        if isinstance(item, str):
            item = (item, default_size, False, default_color)
        text, size, bold, color = item
        if first:
            p = tf.paragraphs[0]
            first = False
        else:
            p = tf.add_paragraph()
        run = p.add_run()
        run.text = text
        run.font.size  = Pt(size)
        run.font.bold  = bold
        run.font.color.rgb = color
    return box


def agent_card(slide, l, t, w, h, number, name, role, msg_type,
               num_color=TEAL):
    r = rect(slide, l, t, w, h, fill=SURFACE,
             line_color=RGBColor(0x1E, 0x30, 0x45))
    # Number badge
    badge = rect(slide, l + Inches(0.1), t + Inches(0.1),
                 Inches(0.3), Inches(0.3), fill=num_color)
    txb(slide, str(number),
        l + Inches(0.1), t + Inches(0.1),
        Inches(0.3), Inches(0.3),
        size=11, bold=True, color=BG, align=PP_ALIGN.CENTER)
    # Agent name
    txb(slide, name, l + Inches(0.5), t + Inches(0.1),
        w - Inches(0.6), Inches(0.3),
        size=12, bold=True, color=WHITE)
    # Role
    txb(slide, role, l + Inches(0.12), t + Inches(0.46),
        w - Inches(0.2), Inches(0.55),
        size=10, color=MUTED)
    # Band message tag
    pill(slide, msg_type,
         l + Inches(0.1), t + h - Inches(0.38),
         w - Inches(0.2), Inches(0.28),
         fill=RGBColor(0x00, 0x23, 0x1E), text_color=TEAL, size=8)


def kpi_card(slide, l, t, w, h, value, label, color=TEAL):
    r = rect(slide, l, t, w, h, fill=RGBColor(0x0F, 0x18, 0x24),
             line_color=RGBColor(0x1E, 0x30, 0x45))
    txb(slide, value, l, t + Inches(0.12), w, Inches(0.4),
        size=22, bold=True, color=color, align=PP_ALIGN.CENTER)
    txb(slide, label, l, t + Inches(0.52), w, Inches(0.28),
        size=9, color=MUTED, align=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════
# SLIDE 1 — Title
# ══════════════════════════════════════════════════════════════════════
slide = add_slide()
accent_bar(slide, color=TEAL)

# Large background watermark text
txb(slide, "RIDEREX", Inches(1.2), Inches(1.2), Inches(11), Inches(4.5),
    size=140, bold=True,
    color=RGBColor(0x0D, 0x1A, 0x26), align=PP_ALIGN.CENTER)

txb(slide, "RiderEx", Inches(0.8), Inches(1.5), Inches(11.7), Inches(1.8),
    size=72, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

txb(slide, "AV Customer Experience Multi-Agent Pipeline",
    Inches(0.8), Inches(3.2), Inches(11.7), Inches(0.7),
    size=24, color=TEAL, align=PP_ALIGN.CENTER)

divider(slide, Inches(4.1))

txb(slide, "Powered by Band.ai  ·  Track 1: Internal Enterprise Workflows",
    Inches(0.8), Inches(4.3), Inches(11.7), Inches(0.5),
    size=14, color=MUTED, align=PP_ALIGN.CENTER)

pill(slide, "5 AGENTS",   Inches(3.7), Inches(5.1),
     Inches(1.7), Inches(0.38), fill=TEAL, text_color=BG, size=11)
pill(slide, "BAND NATIVE", Inches(5.6), Inches(5.1),
     Inches(1.9), Inches(0.38), fill=GREEN, text_color=BG, size=11)
pill(slide, "ENTERPRISE READY", Inches(7.7), Inches(5.1),
     Inches(2.2), Inches(0.38), fill=PURPLE, text_color=WHITE, size=11)

txb(slide, "Band.ai Hackathon 2025",
    Inches(0.8), Inches(6.6), Inches(11.7), Inches(0.4),
    size=11, color=MUTED, align=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════
# SLIDE 2 — The Problem
# ══════════════════════════════════════════════════════════════════════
slide = add_slide()
accent_bar(slide)
section_label(slide, "The Problem")

txb(slide, "AV Customer Support Is Broken",
    Inches(0.55), Inches(0.8), Inches(12), Inches(0.7),
    size=36, bold=True, color=WHITE)

divider(slide, Inches(1.6))

problems = [
    ("⚠️  Safety incidents buried in generic support queues — NHTSA reportability missed",
     AMBER),
    ("🔄  Manual triage: one agent classifies, another drafts, a third reviews — siloed and slow",
     RED),
    ("📋  No structured handoff from customer feedback to engineering JIRA ticket",
     RED),
    ("🚫  No automated Go / No-Go signal for software releases based on real field data",
     AMBER),
    ("📊  Fleet teams and engineering teams operating on completely different data views",
     MUTED),
]

for i, (text, color) in enumerate(problems):
    t = Inches(1.85) + i * Inches(0.85)
    r = rect(slide, Inches(0.55), t, Inches(12.23), Inches(0.72),
             fill=RGBColor(0x0F, 0x18, 0x24),
             line_color=RGBColor(0x1E, 0x30, 0x45))
    txb(slide, text, Inches(0.75), t + Inches(0.12),
        Inches(12), Inches(0.5), size=14, color=color)


# ══════════════════════════════════════════════════════════════════════
# SLIDE 3 — Solution Overview
# ══════════════════════════════════════════════════════════════════════
slide = add_slide()
accent_bar(slide, color=GREEN)
section_label(slide, "Solution", color=GREEN)

txb(slide, "RiderEx — End-to-End AV Feedback Pipeline",
    Inches(0.55), Inches(0.8), Inches(12), Inches(0.7),
    size=34, bold=True, color=WHITE)

divider(slide, Inches(1.6), color=GREEN)

# Flow boxes
steps = [
    ("01", "Passenger\nSubmits Feedback", TEAL),
    ("02", "5 Agents\nCollaborate via Band", GREEN),
    ("03", "Auto-Draft\nCustomer Response", PURPLE),
    ("04", "Release Report\nGo / No-Go", AMBER),
    ("05", "JIRA Ticket\nCreated", RED),
]
box_w  = Inches(2.1)
box_h  = Inches(1.5)
gap    = Inches(0.22)
start_l = Inches(0.55)

for i, (num, label, color) in enumerate(steps):
    l = start_l + i * (box_w + gap)
    r = rect(slide, l, Inches(1.85), box_w, box_h,
             fill=RGBColor(0x0F, 0x18, 0x24),
             line_color=color, line_width=Pt(1.5))
    txb(slide, num, l, Inches(1.9), box_w, Inches(0.4),
        size=28, bold=True, color=color, align=PP_ALIGN.CENTER)
    txb(slide, label, l, Inches(2.45), box_w, Inches(0.8),
        size=12, color=WHITE, align=PP_ALIGN.CENTER)
    # Arrow
    if i < len(steps) - 1:
        arrow_l = l + box_w + Inches(0.04)
        txb(slide, "→", arrow_l, Inches(2.35), Inches(0.14), Inches(0.4),
            size=16, color=MUTED, align=PP_ALIGN.CENTER)

# Outcome boxes
outcomes = [
    ("250,400 rides\nseeded across\n200 vehicles", TEAL),
    ("Supabase stores\nevery real run\nfor persistence", GREEN),
    ("Fleet + Dashboard +\nSoftware tabs stay\nin sync automatically", PURPLE),
]
ow = Inches(3.9)
for i, (text, color) in enumerate(outcomes):
    l = Inches(0.55) + i * (ow + Inches(0.24))
    r = rect(slide, l, Inches(3.7), ow, Inches(1.25),
             fill=RGBColor(0x0A, 0x12, 0x1E),
             line_color=color, line_width=Pt(1))
    txb(slide, text, l + Inches(0.15), Inches(3.8),
        ow - Inches(0.3), Inches(1.05),
        size=13, color=WHITE)

txb(slide, "All 4 tabs share a single getMetrics() data source — one submission updates everything.",
    Inches(0.55), Inches(5.2), Inches(12.23), Inches(0.45),
    size=12, color=MUTED, italic=True)

txb(slide, "TRACK 1  ·  Customer Support Escalation Workflow",
    Inches(0.55), Inches(5.85), Inches(12.23), Inches(0.4),
    size=11, bold=True, color=GREEN)
txb(slide, "RiderEx automates the journey from raw passenger complaint → classified ticket → safety triage → drafted response → quality review → engineering handoff. Each step is a distinct agent. Band is the collaboration layer.",
    Inches(0.55), Inches(6.2), Inches(12.23), Inches(0.9),
    size=11, color=MUTED)


# ══════════════════════════════════════════════════════════════════════
# SLIDE 4 — The 5 Agents
# ══════════════════════════════════════════════════════════════════════
slide = add_slide()
accent_bar(slide, color=PURPLE)
section_label(slide, "Multi-Agent Architecture", color=PURPLE)

txb(slide, "5 Agents Collaborating Through Band",
    Inches(0.55), Inches(0.8), Inches(12), Inches(0.65),
    size=34, bold=True, color=WHITE)

divider(slide, Inches(1.55), color=PURPLE)

agents = [
    (1, "Intake & Classification", "Parses raw feedback · assigns category (SAFETY / COMFORT / ROUTE / SOFTWARE / COMPLIMENT) · priority P1–P4 · sentiment · churn risk · key phrases", "TICKET_CREATED", TEAL),
    (2, "Safety Triage",           "Reads TICKET_CREATED from Band · assesses NHTSA reportability · identifies AV failure mode · recommends vehicle action (GROUND / INSPECT / CONTINUE)", "SAFETY_ASSESSMENT", RED),
    (3, "Resolution",              "Reads Ticket + Safety from Band · drafts warm customer response · computes refund / credit per policy · generates action item list", "RESOLUTION_DRAFT", PURPLE),
    (4, "Quality Review",          "Reads entire Band thread · scores tone, empathy, policy compliance (0–100) · detects recurring patterns · approves or requests revision", "REVIEW_COMPLETE", AMBER),
    (5, "Engineering Handoff",     "Reads all 4 prior messages from Band · creates JIRA ticket · assigns team · sets SLA target · closes the case", "CASE_CLOSED", GREEN),
]

card_w = Inches(2.38)
card_h = Inches(1.72)
gap    = Inches(0.15)
start_l = Inches(0.55)

for i, (num, name, role, msg, color) in enumerate(agents):
    l = start_l + i * (card_w + gap)
    agent_card(slide, l, Inches(1.75), card_w, card_h,
               num, name, role, msg, num_color=color)
    # Arrow between cards
    if i < 4:
        txb(slide, "↓", l + card_w + Inches(0.02), Inches(2.25),
            Inches(0.13), Inches(0.5), size=14, color=MUTED, align=PP_ALIGN.CENTER)

# Band message chain visual
txb(slide, "Band Message Chain",
    Inches(0.55), Inches(3.65), Inches(4), Inches(0.3),
    size=10, bold=True, color=MUTED)

chain_msgs = ["TICKET_CREATED", "SAFETY_ASSESSMENT", "RESOLUTION_DRAFT", "REVIEW_COMPLETE", "CASE_CLOSED"]
chain_colors = [TEAL, RED, PURPLE, AMBER, GREEN]
for i, (msg, color) in enumerate(zip(chain_msgs, chain_colors)):
    l = Inches(0.55) + i * Inches(2.53)
    pill(slide, msg, l, Inches(3.95), Inches(2.35), Inches(0.3),
         fill=RGBColor(0x0A, 0x12, 0x1E), text_color=color, size=8)
    if i < 4:
        txb(slide, "→", l + Inches(2.37), Inches(3.95),
            Inches(0.16), Inches(0.3), size=11, color=MUTED, align=PP_ALIGN.CENTER)

# Key point
rect(slide, Inches(0.55), Inches(4.5), Inches(12.23), Inches(0.72),
     fill=RGBColor(0x0A, 0x17, 0x12),
     line_color=GREEN, line_width=Pt(1))
txb(slide, "✅  Every agent reads prior agent outputs from Band before acting — context is never passed directly between agents. Band IS the shared memory and coordination layer.",
    Inches(0.75), Inches(4.6), Inches(11.8), Inches(0.55),
    size=12, color=GREEN)

# Requirement callouts
cols = [
    ("Minimum: 3 agents",     "RiderEx has 5",             TEAL),
    ("Meaningful Band usage", "Band = shared context store", GREEN),
    ("Agent collaboration",   "Each agent reads Band before acting", PURPLE),
]
cw = Inches(3.9)
for i, (req, ans, color) in enumerate(cols):
    l = Inches(0.55) + i * (cw + Inches(0.24))
    r = rect(slide, l, Inches(5.42), cw, Inches(0.82),
             fill=RGBColor(0x0A, 0x12, 0x1E),
             line_color=color)
    txb(slide, req, l + Inches(0.12), Inches(5.48), cw - Inches(0.2), Inches(0.3),
        size=9, color=MUTED, bold=True)
    txb(slide, ans, l + Inches(0.12), Inches(5.75), cw - Inches(0.2), Inches(0.38),
        size=12, color=color, bold=True)


# ══════════════════════════════════════════════════════════════════════
# SLIDE 5 — Band as Core Collaboration Layer
# ══════════════════════════════════════════════════════════════════════
slide = add_slide()
accent_bar(slide, color=GREEN)
section_label(slide, "How Band Powers the Collaboration", color=GREEN)

txb(slide, "Band Is the Collaboration Layer — Not a Wrapper",
    Inches(0.55), Inches(0.8), Inches(12), Inches(0.65),
    size=32, bold=True, color=WHITE)
divider(slide, Inches(1.55), color=GREEN)

# Left: what Band does in RiderEx
left_items = [
    ("Band as shared context store", GREEN, True),
    ("Each agent posts its structured JSON output to a Band room as a typed message.", MUTED, False),
    ("Every downstream agent reads the Band channel before generating its response,", MUTED, False),
    ("so it has full visibility of all prior agent decisions.", MUTED, False),
    ("", MUTED, False),
    ("Agent-to-agent delegation", GREEN, True),
    ("Safety agent only runs after reading Intake's TICKET_CREATED from Band.", MUTED, False),
    ("Resolution agent reads both Ticket AND Safety before drafting a response.", MUTED, False),
    ("Review agent reads the full 3-message thread before scoring quality.", MUTED, False),
    ("Engineering agent reads all 4 prior messages before closing the case.", MUTED, False),
    ("", MUTED, False),
    ("Not a thin wrapper", GREEN, True),
    ("Removing Band would break the pipeline — agents have no other way", MUTED, False),
    ("to receive structured context from prior agents.", MUTED, False),
]

box = slide.shapes.add_textbox(Inches(0.55), Inches(1.7), Inches(5.8), Inches(5.2))
tf = box.text_frame
tf.word_wrap = True
first = True
for text, color, bold in left_items:
    if first:
        p = tf.paragraphs[0]
        first = False
    else:
        p = tf.add_paragraph()
    run = p.add_run()
    run.text = text
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.size = Pt(13 if bold else 11)

# Right: code snippet
rect(slide, Inches(6.6), Inches(1.7), Inches(6.18), Inches(5.3),
     fill=RGBColor(0x08, 0x0E, 0x18),
     line_color=RGBColor(0x1E, 0x30, 0x45))

txb(slide, "agents.py — Band message passing",
    Inches(6.75), Inches(1.78), Inches(5.8), Inches(0.28),
    size=9, color=MUTED, italic=True)

code = (
    "# Agent 1 posts to Band\n"
    "band_post('intake_agent',\n"
    "  'TICKET_CREATED', intake_result)\n"
    "\n"
    "# Agent 2 reads Band before acting\n"
    "def agent_safety():\n"
    "  ticket = band_read_latest(\n"
    "    'TICKET_CREATED'\n"
    "  )['content']\n"
    "  result = call_claude(\n"
    "    SAFETY_SYSTEM,\n"
    "    f'Ticket from Band:\\n'\n"
    "    f'{json.dumps(ticket)}'\n"
    "  )\n"
    "  band_post('safety_agent',\n"
    "    'SAFETY_ASSESSMENT', result)\n"
    "\n"
    "# Agent 5 reads ALL Band messages\n"
    "def agent_engineering():\n"
    "  all_msgs = band_read_all()\n"
    "  result = call_claude(\n"
    "    ENGINEERING_SYSTEM,\n"
    "    f'Full Band thread:\\n'\n"
    "    f'{json.dumps(all_msgs)}'\n"
    "  )\n"
)
txb(slide, code, Inches(6.75), Inches(2.1), Inches(5.8), Inches(4.7),
    size=10, color=GREEN)


# ══════════════════════════════════════════════════════════════════════
# SLIDE 6 — Pipeline Tab
# ══════════════════════════════════════════════════════════════════════
slide = add_slide()
accent_bar(slide, color=TEAL)
section_label(slide, "Tab Walkthrough — Pipeline")

txb(slide, "🚀  Pipeline Tab",
    Inches(0.55), Inches(0.8), Inches(9), Inches(0.65),
    size=36, bold=True, color=WHITE)
pill(slide, "LIVE DEMO", Inches(10.2), Inches(0.87),
     Inches(1.5), Inches(0.38), fill=TEAL, text_color=BG, size=10)
divider(slide, Inches(1.6))

# Left: input description
txb(slide, "Submit passenger feedback",
    Inches(0.55), Inches(1.75), Inches(5.5), Inches(0.4),
    size=15, bold=True, color=TEAL)

inputs = [
    "• Free-text complaint or compliment",
    "• Vehicle ID  (auto-generated WM-001 to WM-200)",
    "• 1–5 star rating from the passenger",
    "",
    "The form POSTs to /run-pipeline → 5 Band agents run",
    "sequentially → result is saved to localStorage and",
    "Supabase → Dashboard, Fleet, and Software tabs update.",
]
for i, line in enumerate(inputs):
    txb(slide, line, Inches(0.55), Inches(2.22) + i * Inches(0.37),
        Inches(5.5), Inches(0.35),
        size=12, color=WHITE if not line.startswith("The") else MUTED)

# Right: result sub-tabs
txb(slide, "6 result sub-tabs after pipeline runs",
    Inches(6.4), Inches(1.75), Inches(6.4), Inches(0.4),
    size=15, bold=True, color=TEAL)

sub_tabs = [
    ("📋 Ticket",         "Category · Priority · Sentiment · Churn Risk · Key Phrases",             TEAL),
    ("🚨 Safety",         "Safety Level · NHTSA Flag · AV Failure Mode · Vehicle Action",           RED),
    ("💬 Response",       "Customer-facing response · Refund / Credit amounts · Action items",      PURPLE),
    ("🚦 Release Report", "Go / Conditional / No-Go checklist for the software branch",             GREEN),
    ("🔧 JIRA",           "Engineering ticket · Team assignment · Acceptance criteria · SLA",       AMBER),
    ("📡 Band Log",       "Live agent collaboration thread — every message exchanged through Band", MUTED),
]
for i, (name, desc, color) in enumerate(sub_tabs):
    t = Inches(2.18) + i * Inches(0.73)
    r = rect(slide, Inches(6.4), t, Inches(6.4), Inches(0.65),
             fill=RGBColor(0x0F, 0x18, 0x24),
             line_color=color, line_width=Pt(1))
    txb(slide, name, Inches(6.55), t + Inches(0.06),
        Inches(2.1), Inches(0.3), size=11, bold=True, color=color)
    txb(slide, desc, Inches(8.7), t + Inches(0.06),
        Inches(4), Inches(0.55), size=10, color=MUTED)

# Road animation note
rect(slide, Inches(0.55), Inches(5.55), Inches(5.5), Inches(0.55),
     fill=RGBColor(0x0A, 0x12, 0x1E), line_color=TEAL)
txb(slide, "✨  Animated perspective road runs in the background — lane markings scroll toward the viewer with a scan line and HUD corner brackets",
    Inches(0.7), Inches(5.62), Inches(5.2), Inches(0.45),
    size=9, color=TEAL)


# ══════════════════════════════════════════════════════════════════════
# SLIDE 7 — Dashboard Tab
# ══════════════════════════════════════════════════════════════════════
slide = add_slide()
accent_bar(slide, color=PURPLE)
section_label(slide, "Tab Walkthrough — Dashboard", color=PURPLE)

txb(slide, "📊  Dashboard Tab",
    Inches(0.55), Inches(0.8), Inches(12), Inches(0.65),
    size=36, bold=True, color=WHITE)
divider(slide, Inches(1.6), color=PURPLE)

txb(slide, "250,400 seeded rides  +  every real pipeline submission, fully filterable",
    Inches(0.55), Inches(1.72), Inches(12.23), Inches(0.38),
    size=13, color=MUTED)

# KPI grid
kpis = [
    ("250,400",  "Total Rides",       TEAL),
    ("4.4 ★",    "Avg CSAT",          AMBER),
    ("~73%",     "Good Ride Rate",    GREEN),
    ("~7%",      "Safety Rate",       RED),
    ("0",        "NHTSA Flags",       GREEN),
    ("87/100",   "Avg Quality",       PURPLE),
    ("~18%",     "Escalation Rate",   AMBER),
    ("$3 avg",   "Refund / Credit",   TEAL),
    ("8 msg",    "Band Messages",     PURPLE),
    ("< 1%",     "P1 Incidents",      RED),
]
kw = Inches(1.18)
kh = Inches(0.85)
kgap = Inches(0.09)
for i, (val, lbl, color) in enumerate(kpis):
    col = i % 5
    row = i // 5
    l = Inches(0.55) + col * (kw + kgap)
    t = Inches(2.22) + row * (kh + kgap)
    kpi_card(slide, l, t, kw, kh, val, lbl, color)

# Features below
features = [
    ("Filters", "Category · Priority · Safety Level · Time Range · Software Version — combinable; counter shows N of M when active"),
    ("All Rides Table", "Every ride, no row cap, sorted by most recent. Click any row → ticket modal with full breakdown + original customer feedback"),
    ("Scroll Animation", "Pod, SUV, and Shuttle images swoosh in from alternating sides as you scroll — fixed-position, scoped to Dashboard tab only"),
]
fw = Inches(3.9)
for i, (title, desc) in enumerate(features):
    l = Inches(0.55) + i * (fw + Inches(0.24))
    r = rect(slide, l, Inches(4.35), fw, Inches(1.05),
             fill=RGBColor(0x0A, 0x12, 0x1E),
             line_color=PURPLE)
    txb(slide, title, l + Inches(0.12), Inches(4.42), fw - Inches(0.2), Inches(0.3),
        size=11, bold=True, color=PURPLE)
    txb(slide, desc, l + Inches(0.12), Inches(4.72), fw - Inches(0.2), Inches(0.62),
        size=10, color=MUTED)

txb(slide, "Data source: getMetrics() = seededRecords (in-memory) + localStorage real runs + Supabase cross-device runs",
    Inches(0.55), Inches(5.55), Inches(12.23), Inches(0.35),
    size=10, color=MUTED, italic=True)


# ══════════════════════════════════════════════════════════════════════
# SLIDE 8 — Fleet Tab
# ══════════════════════════════════════════════════════════════════════
slide = add_slide()
accent_bar(slide, color=TEAL)
section_label(slide, "Tab Walkthrough — Fleet")

txb(slide, "🚗  Fleet Tab",
    Inches(0.55), Inches(0.8), Inches(12), Inches(0.65),
    size=36, bold=True, color=WHITE)
divider(slide, Inches(1.6))

txb(slide, "HUD-style real-time registry of all 200 Weimo vehicles — WM-001 to WM-200",
    Inches(0.55), Inches(1.72), Inches(12.23), Inches(0.38),
    size=13, color=MUTED)

# Two columns
# Left
txb(slide, "Vehicle Card (front)",
    Inches(0.55), Inches(2.2), Inches(5.8), Inches(0.35),
    size=14, bold=True, color=TEAL)
front_items = [
    "• Vehicle ID + live status (ACTIVE / MAINTENANCE / GROUNDED)",
    "• Model image: Pod Gen2 · Shuttle Gen3 · SUV Gen4",
    "• Safety score bar, color-coded 0–100",
    "• Open vs. resolved ticket counts",
    "• Avg passenger rating",
]
for i, line in enumerate(front_items):
    txb(slide, line, Inches(0.55), Inches(2.62) + i * Inches(0.38),
        Inches(5.8), Inches(0.36), size=11, color=WHITE)

txb(slide, "Flip → Vehicle Card (back)",
    Inches(0.55), Inches(4.65), Inches(5.8), Inches(0.35),
    size=14, bold=True, color=TEAL)
back_items = [
    "• Fleet zone · Software version · Total mileage",
    "• Rides processed (synced with Dashboard / Software)",
    "• Last incident type · Pipeline run count · Open tickets",
    "• VIEW DETAILS → full modal with pipeline run history",
]
for i, line in enumerate(back_items):
    txb(slide, line, Inches(0.55), Inches(5.07) + i * Inches(0.38),
        Inches(5.8), Inches(0.36), size=11, color=WHITE)

# Right: smart ticket tracking
rect(slide, Inches(6.6), Inches(2.1), Inches(6.18), Inches(3.35),
     fill=RGBColor(0x0A, 0x12, 0x1E),
     line_color=TEAL)
txb(slide, "Smart Ticket Tracking",
    Inches(6.75), Inches(2.18), Inches(5.8), Inches(0.35),
    size=14, bold=True, color=TEAL)
txb(slide, "netOpen  =  original_open  +  new_incidents  −  resolved",
    Inches(6.75), Inches(2.6), Inches(5.8), Inches(0.35),
    size=11, color=GREEN, bold=True)

tracking = [
    ("Pipeline run — LOW / NONE safety", "→  ticket resolved, OPEN drops", GREEN),
    ("Pipeline run — HIGH / CRITICAL",   "→  new incident logged, OPEN rises", RED),
    ("CRITICAL safety level",            "→  vehicle status → GROUNDED", RED),
    ("HIGH safety level",                "→  vehicle status → MAINTENANCE", AMBER),
    ("Score delta: CRITICAL −25,",       "   HIGH −12, MEDIUM −4, NONE +5", MUTED),
]
for i, (left, right, color) in enumerate(tracking):
    t = Inches(3.02) + i * Inches(0.38)
    txb(slide, left, Inches(6.75), t, Inches(3.1), Inches(0.35), size=10, color=MUTED)
    txb(slide, right, Inches(9.9), t, Inches(2.8), Inches(0.35), size=10, color=color)

# Live sync
rect(slide, Inches(6.6), Inches(5.65), Inches(6.18), Inches(0.62),
     fill=RGBColor(0x0A, 0x17, 0x12), line_color=GREEN)
txb(slide, "⚡  Live sync — every pipeline submission instantly updates the vehicle card (score, status, ticket counts, ride total) without a page reload. Run Pipeline button pre-fills the vehicle ID.",
    Inches(6.75), Inches(5.72), Inches(5.9), Inches(0.5),
    size=10, color=GREEN)


# ══════════════════════════════════════════════════════════════════════
# SLIDE 9 — Software Branch Tab
# ══════════════════════════════════════════════════════════════════════
slide = add_slide()
accent_bar(slide, color=AMBER)
section_label(slide, "Tab Walkthrough — Software Branches", color=AMBER)

txb(slide, "🔀  Software Branch Tab",
    Inches(0.55), Inches(0.8), Inches(12), Inches(0.65),
    size=36, bold=True, color=WHITE)
divider(slide, Inches(1.6), color=AMBER)

txb(slide, "Software release tracker — Go / Conditional / No-Go readiness per branch, driven by real field data",
    Inches(0.55), Inches(1.72), Inches(12.23), Inches(0.38),
    size=13, color=MUTED)

# Branch cards
branches = [
    ("weimo-av-4.2.1",    "RELEASED", "Mar 15, 2024",  "Initial stable release",             GREEN,  "✅ GO",    GREEN),
    ("weimo-av-4.3.0",    "RELEASED", "Sep 1, 2024",   "Route optimization & comfort",        TEAL,   "✅ GO",    GREEN),
    ("weimo-av-4.3.1",    "RELEASED", "Jan 20, 2025",  "Safety patch — AEB false trigger fix",PURPLE, "✅ GO",    GREEN),
    ("weimo-av-4.4.0-beta","BETA",    "Pending",       "Next-gen perception stack",           AMBER,  "⚠️ COND.", AMBER),
]
bw = Inches(2.95)
bg = Inches(0.12)
for i, (name, status, date, note, bcolor, readiness, rcolor) in enumerate(branches):
    l = Inches(0.55) + i * (bw + bg)
    t = Inches(2.15)
    h = Inches(2.2)
    r = rect(slide, l, t, bw, h, fill=RGBColor(0x0F, 0x18, 0x24),
             line_color=bcolor, line_width=Pt(1.5))
    pill(slide, status, l + Inches(0.1), t + Inches(0.1),
         Inches(1.15), Inches(0.28), fill=bcolor, text_color=BG if bcolor != AMBER else BG, size=8)
    pill(slide, readiness, l + bw - Inches(1.2), t + Inches(0.1),
         Inches(1.05), Inches(0.28),
         fill=RGBColor(0x08, 0x1A, 0x10) if rcolor == GREEN else RGBColor(0x1A, 0x12, 0x08),
         text_color=rcolor, size=8)
    txb(slide, name, l + Inches(0.12), t + Inches(0.48), bw - Inches(0.2), Inches(0.35),
        size=11, bold=True, color=bcolor)
    txb(slide, date, l + Inches(0.12), t + Inches(0.85), bw - Inches(0.2), Inches(0.28),
        size=9, color=MUTED)
    txb(slide, note, l + Inches(0.12), t + Inches(1.12), bw - Inches(0.2), Inches(0.55),
        size=10, color=WHITE)

# Metrics row explanation
txb(slide, "Per-branch metrics",
    Inches(0.55), Inches(4.52), Inches(12), Inches(0.35),
    size=13, bold=True, color=AMBER)

metrics = [
    ("Rides", "Total seeded + real rides\non this branch"),
    ("Safety Rate", "% of rides categorized\nas SAFETY incidents"),
    ("NHTSA Flags", "Count of federally\nreportable incidents"),
    ("Avg Quality", "Mean AI response\nquality score 0–100"),
    ("Vehicles", "Fleet vehicles currently\nrunning this branch"),
    ("Pipeline Runs", "Real feedback submissions\non this branch"),
]
mw = Inches(1.98)
mg = Inches(0.09)
for i, (name, desc) in enumerate(metrics):
    l = Inches(0.55) + i * (mw + mg)
    r = rect(slide, l, Inches(4.95), mw, Inches(0.9),
             fill=RGBColor(0x0A, 0x12, 0x1E),
             line_color=RGBColor(0x1E, 0x30, 0x45))
    txb(slide, name, l + Inches(0.1), Inches(5.0), mw - Inches(0.15), Inches(0.28),
        size=10, bold=True, color=AMBER)
    txb(slide, desc, l + Inches(0.1), Inches(5.28), mw - Inches(0.15), Inches(0.52),
        size=9, color=MUTED)

# Key insight
rect(slide, Inches(0.55), Inches(6.05), Inches(12.23), Inches(0.65),
     fill=RGBColor(0x0A, 0x17, 0x12), line_color=GREEN)
txb(slide, "Released branches (4.2.1 / 4.3.0 / 4.3.1) show ✅ GO — they already passed signoff, so seeded data uses clean safety distribution (no CRITICAL/HIGH).  Beta branch retains full incident distribution reflecting a pre-release build.  Pipeline Release Reports inside each card show a checklist for every real submission on that branch.",
    Inches(0.72), Inches(6.12), Inches(11.9), Inches(0.55),
    size=10, color=GREEN)


# ══════════════════════════════════════════════════════════════════════
# SLIDE 10 — Tech Stack & Data Flow
# ══════════════════════════════════════════════════════════════════════
slide = add_slide()
accent_bar(slide, color=TEAL)
section_label(slide, "Tech Stack & Data Architecture")

txb(slide, "Tech Stack & Data Flow",
    Inches(0.55), Inches(0.8), Inches(12), Inches(0.65),
    size=34, bold=True, color=WHITE)
divider(slide, Inches(1.6))

# Left: tech stack table
stack = [
    ("Agent Framework",  "Band.ai (band-sdk)",                                  TEAL),
    ("AI Model",         "claude-sonnet-4-5  via AI/ML API (OpenAI-compatible)", PURPLE),
    ("Backend",          "FastAPI + Uvicorn (Python)",                           TEAL),
    ("Database",         "Supabase (PostgreSQL) — gracefully optional",          GREEN),
    ("Frontend",         "Vanilla HTML / CSS / JS — dark space HUD aesthetic",   PURPLE),
    ("Deployment",       "Vercel (serverless Python)",                           TEAL),
    ("Fleet Dataset",    "200 vehicles · riderex_vehicles.json / .csv",          AMBER),
]
for i, (layer, tech, color) in enumerate(stack):
    t = Inches(1.85) + i * Inches(0.6)
    r = rect(slide, Inches(0.55), t, Inches(6.0), Inches(0.52),
             fill=RGBColor(0x0F, 0x18, 0x24),
             line_color=RGBColor(0x1E, 0x30, 0x45))
    txb(slide, layer, Inches(0.7), t + Inches(0.08), Inches(1.8), Inches(0.36),
        size=10, bold=True, color=color)
    txb(slide, tech, Inches(2.55), t + Inches(0.08), Inches(3.9), Inches(0.36),
        size=10, color=WHITE)

# Right: data flow diagram
rect(slide, Inches(6.85), Inches(1.72), Inches(6.0), Inches(5.6),
     fill=RGBColor(0x08, 0x0E, 0x18),
     line_color=RGBColor(0x1E, 0x30, 0x45))

txb(slide, "Data Flow",
    Inches(7.0), Inches(1.82), Inches(5.5), Inches(0.35),
    size=13, bold=True, color=TEAL)

flow_items = [
    ("seededRecords",                    "250,400 rides in memory (200 veh × 1,252)", TEAL),
    ("  +  localStorage real runs",      "from this device's pipeline submissions",   GREEN),
    ("  +  Supabase real runs",          "from other devices / sessions",             PURPLE),
    ("           ↓",                     "",                                          MUTED),
    ("  getMetrics()",                   "single shared data function",               WHITE),
    ("           ↓",                     "",                                          MUTED),
    ("  Dashboard · Fleet · Software",   "all 3 tabs read same source",               TEAL),
]
for i, (line, sub, color) in enumerate(flow_items):
    t = Inches(2.28) + i * Inches(0.56)
    txb(slide, line, Inches(7.0), t, Inches(3.5), Inches(0.35),
        size=11, bold=(color == WHITE), color=color)
    if sub:
        txb(slide, sub, Inches(7.0), t + Inches(0.25), Inches(5.6), Inches(0.28),
            size=9, color=MUTED, italic=True)

rect(slide, Inches(6.85), Inches(6.1), Inches(6.0), Inches(0.75),
     fill=RGBColor(0x0A, 0x17, 0x12), line_color=GREEN)
txb(slide, "One pipeline submission → localStorage write → Supabase write → Dashboard rerenders → Fleet card updates in memory → Software tab refreshes on next visit",
    Inches(7.0), Inches(6.17), Inches(5.7), Inches(0.62),
    size=10, color=GREEN)


# ══════════════════════════════════════════════════════════════════════
# SLIDE 11 — Why RiderEx Wins
# ══════════════════════════════════════════════════════════════════════
slide = add_slide()
accent_bar(slide, color=GREEN)
section_label(slide, "Why RiderEx", color=GREEN)

txb(slide, "Why RiderEx Satisfies Every Requirement",
    Inches(0.55), Inches(0.8), Inches(12), Inches(0.65),
    size=32, bold=True, color=WHITE)
divider(slide, Inches(1.6), color=GREEN)

requirements = [
    (
        "✅  3+ agents collaborating through Band",
        "RiderEx has 5 agents. Each one reads prior agent outputs from the Band channel before generating its own output. Band is the only mechanism for inter-agent context transfer.",
        GREEN,
    ),
    (
        "✅  Meaningful Band usage — not a wrapper",
        "Safety Agent reads TICKET_CREATED from Band. Resolution Agent reads Ticket + Safety. Review reads all 3. Engineering reads all 4. Agents have zero direct access to prior outputs — Band is the protocol.",
        GREEN,
    ),
    (
        "✅  Agent collaboration: planning → execution → review → handoff",
        "Intake (plan) → Safety (triage) → Resolution (execute) → Quality Review (review) → Engineering (handoff). This is a textbook multi-agent workflow with every required collaboration pattern.",
        GREEN,
    ),
    (
        "✅  Track 1: Internal Enterprise Workflow",
        "Customer support escalation workflow. A passenger complaint becomes a classified ticket → safety report → drafted response → quality-reviewed response → JIRA engineering ticket. Fully automated, fully traceable.",
        TEAL,
    ),
    (
        "✅  Real enterprise scope",
        "250,400 ride dataset, 200 vehicle fleet registry, 4 software branches with Go/No-Go logic, Supabase persistence, NHTSA compliance tracking, and a full fleet operations dashboard.",
        TEAL,
    ),
]

for i, (title, desc, color) in enumerate(requirements):
    t = Inches(1.78) + i * Inches(0.98)
    r = rect(slide, Inches(0.55), t, Inches(12.23), Inches(0.88),
             fill=RGBColor(0x0A, 0x12, 0x1E),
             line_color=color, line_width=Pt(1.5))
    txb(slide, title, Inches(0.72), t + Inches(0.06), Inches(12), Inches(0.3),
        size=12, bold=True, color=color)
    txb(slide, desc, Inches(0.72), t + Inches(0.37), Inches(12), Inches(0.45),
        size=10, color=MUTED)


# ══════════════════════════════════════════════════════════════════════
# SLIDE 12 — Closing / Demo
# ══════════════════════════════════════════════════════════════════════
slide = add_slide()
accent_bar(slide, color=TEAL)

txb(slide, "RIDEREX", Inches(0.8), Inches(0.9), Inches(11.7), Inches(2.5),
    size=100, bold=True, color=RGBColor(0x0D, 0x1A, 0x26),
    align=PP_ALIGN.CENTER)

txb(slide, "RiderEx", Inches(0.8), Inches(1.2), Inches(11.7), Inches(1.5),
    size=60, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

txb(slide, "5 agents · Band collaboration · Track 1 Enterprise Workflow",
    Inches(0.8), Inches(2.75), Inches(11.7), Inches(0.6),
    size=20, color=TEAL, align=PP_ALIGN.CENTER)

divider(slide, Inches(3.5))

summary_cols = [
    ("🚀\nPipeline", "5-agent Band\ncollaboration\nwith real AI",       TEAL),
    ("📊\nDashboard", "250,400 rides\n10 KPIs\nreal-time filters",      PURPLE),
    ("🚗\nFleet",     "200 vehicles\nLive sync\nSmart tickets",         TEAL),
    ("🔀\nSoftware",  "4 branches\nGo / No-Go\nRelease reports",       AMBER),
    ("🗄️\nSupabase",  "Every real run\npersisted and\ncross-device",    GREEN),
]
cw = Inches(2.35)
cg = Inches(0.15)
for i, (icon_lbl, desc, color) in enumerate(summary_cols):
    l = Inches(0.55) + i * (cw + cg)
    r = rect(slide, l, Inches(3.72), cw, Inches(1.8),
             fill=RGBColor(0x0F, 0x18, 0x24),
             line_color=color)
    txb(slide, icon_lbl, l, Inches(3.78), cw, Inches(0.55),
        size=16, bold=True, color=color, align=PP_ALIGN.CENTER)
    txb(slide, desc, l, Inches(4.35), cw, Inches(1.1),
        size=11, color=WHITE, align=PP_ALIGN.CENTER)

txb(slide, "Live demo  →  riderex.vercel.app",
    Inches(0.8), Inches(5.75), Inches(11.7), Inches(0.55),
    size=18, bold=True, color=TEAL, align=PP_ALIGN.CENTER)

txb(slide, "Built for Band.ai Hackathon 2025  ·  Track 1: Internal Enterprise Workflows",
    Inches(0.8), Inches(6.4), Inches(11.7), Inches(0.4),
    size=12, color=MUTED, align=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════
# Save
# ══════════════════════════════════════════════════════════════════════
out_path = "/Users/jasminewong/Desktop/RiderEx/RiderEx_Presentation.pptx"
prs.save(out_path)
print(f"Saved: {out_path}")
print(f"Slides: {len(prs.slides)}")
