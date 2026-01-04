# engine.py
import os
from datetime import date
from textwrap import wrap

import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors

# ---------- DATA LOADING (GLOBAL) ----------

# Adjust paths as needed
DEMO_CSV_PATH = os.path.join(os.path.dirname(__file__), "demo.csv")
EMR_CSV_PATH = os.path.join(os.path.dirname(__file__), "emr.csv")

demo = pd.read_csv(DEMO_CSV_PATH)
emr = pd.read_csv(EMR_CSV_PATH)


# ---------- SMALL HELPERS ----------

def _get_demo_row(patient_id: str):
    row = demo.loc[demo["Patient_ID"] == patient_id]
    return row.iloc[0] if not row.empty else None


def _safe_get(d, key, default=""):
    try:
        return d.get(key, default)
    except Exception:
        return d[key] if key in d else default


def _draw_footer(c: canvas.Canvas,
                 page_num: int,
                 width: float,
                 bottom_margin: float,
                 logo_path: str | None = None) -> None:
    """Footer with note (left), small logo (center), and page number (right)."""
    note_y = bottom_margin - 25
    note_x = 72  # 1 inch

    c.setFont("Helvetica", 7)
    c.setFillColor(colors.gray)
    c.drawString(
        note_x,
        note_y,
        "Note: Fictious report for illustration only"
    )

    # small logo in the middle
    if logo_path:
        small_logo_w = 0.9 * inch
        small_logo_h = 0.45 * inch
        logo_x = width / 2 - small_logo_w / 2
        logo_y = bottom_margin - 35
        c.drawImage(
            logo_path,
            logo_x,
            logo_y,
            width=small_logo_w,
            height=small_logo_h,
            preserveAspectRatio=True,
            mask="auto",
        )

    # page number on the right
    page_text = f"{page_num} | Page"
    c.drawRightString(width - 72, note_y, page_text)


def _draw_wrapped_text(c: canvas.Canvas,
                       text: str,
                       x: float,
                       y: float,
                       max_chars: int,
                       line_height: float) -> float:
    """Draw wrapped text and return the new y position."""
    for line in wrap(text, max_chars):
        c.drawString(x, y, line)
        y -= line_height
    return y


# ---------- MAIN PDF BUILDER ----------

def generate_transition_report_pdf(patient_id: str,
                                   pdf_path: str,
                                   logo_path: str = "favicon.png") -> None:
    """
    Generate a 4-page, designed transition report PDF for the given patient.

      Page 1: Cover
      Page 2: About CHAH AI Care + patient-specific setup + disclaimer
      Page 3: Clinical overview + risk summary + interRAI snapshot table
      Page 4: Detailed transition summary (clinical summary, sessions, progress, next steps)
    """
    d = _get_demo_row(patient_id)
    if d is None:
        raise ValueError(f"No demographics found for Patient_ID = {patient_id}")

    name = str(d["Name"])
    dob = _safe_get(d, "DOB", "Unknown")
    sex = _safe_get(d, "Sex", "")
    race = _safe_get(d, "Race_Ethnicity", "")
    address = _safe_get(d, "Address", "")
    city = _safe_get(d, "City", "")
    state = _safe_get(d, "State", "")
    zip_code = _safe_get(d, "ZIP", "")
    guardian = _safe_get(d, "Guardian_Name", "")
    insurance = _safe_get(d, "Insurance_Type", "")

    # EMR-derived fields for pages 2 & 4
    emr_rows = emr.loc[emr["Patient_ID"] == patient_id]

    # Enrollment (used on page 2)
    enrolled_since = None
    if not emr_rows.empty and "Care_Plan_Start" in emr_rows.columns:
        enrolled_since = emr_rows["Care_Plan_Start"].min()
    enrolled_str = (
        str(enrolled_since) if enrolled_since is not None else "[Enrollment date unavailable]"
    )

    # Care-plan details for page 4
    if emr_rows.empty:
        diagnosis_str = "N/A"
        goals_str = "N/A"
        care_plan_start = "N/A"
        last_session_date = "N/A"
        providers_str = "N/A"
        recent_sessions = emr_rows  # empty
        last_progress = "N/A"
    else:
        diagnosis_list = (
            emr_rows["Diagnosis"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )
        diagnosis_str = ", ".join(diagnosis_list) if diagnosis_list else "N/A"

        goals_list = (
            emr_rows["Care_Plan_Goals"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )
        goals_str = "; ".join(goals_list) if goals_list else "N/A"

        care_plan_start = emr_rows["Care_Plan_Start"].min()
        last_session_date = emr_rows["Session_Date"].max()

        providers = (
            emr_rows["Provider"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )
        providers_str = ", ".join(providers) if providers else "N/A"

        try:
            most_recent_idx = emr_rows["Session_Date"].idxmax()
            last_progress = emr_rows.loc[most_recent_idx, "Progress_Score"]
        except Exception:
            last_progress = "N/A"

        recent_sessions = (
            emr_rows.sort_values("Session_Date", ascending=False)
            .head(3)
        )

    today_str = date.today().strftime("%B %d, %Y")
    health_card = "##########"  # placeholder – replace if you have a real field

    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    left_margin = 72
    top_margin = 72
    bottom_margin = 72
    brand_green = colors.HexColor("#6BA539")

    # ---------- PAGE 1: COVER ----------
    logo_width = 4 * inch
    logo_height = 2 * inch
    logo_x = (width - logo_width) / 2
    logo_y = height - 3.5 * inch

    c.drawImage(
        logo_path,
        logo_x,
        logo_y,
        width=logo_width,
        height=logo_height,
        preserveAspectRatio=True,
        mask="auto",
    )

    c.setFillColor(brand_green)
    c.setFont("Helvetica-Bold", 24)
    title_text = f"Transition Report: {name}"
    c.drawString(left_margin, logo_y - 1.0 * inch, title_text)

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Oblique", 11)
    subtitle = (
        "A clinical summary of recent health trends, functional status, and care history "
        "to support safe and informed transitions between care settings."
    )
    y = logo_y - 1.3 * inch
    y = _draw_wrapped_text(
        c, subtitle, left_margin, y, max_chars=95, line_height=14
    )

    _draw_footer(c, page_num=1, width=width, bottom_margin=bottom_margin, logo_path=logo_path)
    c.showPage()

    # ---------- PAGE 2: ABOUT CHAH AI CARE ----------
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.black)
    y = height - 1.25 * inch
    c.drawString(left_margin, y, "About CHAH AI Care")

    y -= 22
    c.setFont("Helvetica", 10)
    about_text = (
        "CHAH (Comprehensive Healthcare at Home) AI Care is an advanced, continuous monitoring "
        "platform that supports older adults living at home through 24/7 sensor integration, "
        "real-time health analytics, and coordinated clinical intervention."
    )
    y = _draw_wrapped_text(c, about_text, left_margin, y, max_chars=95, line_height=14)

    y -= 8
    c.drawString(left_margin, y, "It combines:")
    y -= 18

    bullet_indent = left_margin + 14
    c.setFont("Helvetica-Bold", 10)
    c.drawString(left_margin, y, "•")
    c.drawString(bullet_indent, y, "Vision AI:")
    c.setFont("Helvetica", 10)
    c.drawString(bullet_indent + 52, y,
                 "monitors movement, falls, gait stability, and safety risks like elopement.")
    y -= 16

    c.setFont("Helvetica-Bold", 10)
    c.drawString(left_margin, y, "•")
    c.drawString(bullet_indent, y, "Audio AI:")
    c.setFont("Helvetica", 10)
    c.drawString(
        bullet_indent + 52,
        y,
        "detects respiratory changes, distress cries, and conversational markers of cognitive or emotional decline.",
    )
    y -= 16

    c.setFont("Helvetica-Bold", 10)
    c.drawString(left_margin, y, "•")
    c.drawString(bullet_indent, y, "Biometric Mattress Sensor:")
    c.setFont("Helvetica", 10)
    c.drawString(
        bullet_indent + 130,
        y,
        "captures real-time vitals and sleep-related metrics for early risk detection.",
    )
    y -= 24

    system_text = (
        "This system works in tandem with scheduled clinical visits and a 24/7 Care Response "
        "infrastructure to enable early detection, rapid response, and reduced risk of hospitalization."
    )
    y = _draw_wrapped_text(c, system_text, left_margin, y, max_chars=95, line_height=14)

    # Patient-specific setup
    y -= 24
    c.setFont("Helvetica-Bold", 12)
    c.drawString(left_margin, y, f"Patient-Specific Setup: {name}")
    y -= 18

    c.setFont("Helvetica", 10)
    c.drawString(left_margin, y, "• Continuous monitoring through CHAH Support Hub:")
    y -= 16
    c.drawString(left_margin + 20, y, "o Vision AI (installed in key living areas).")
    y -= 14
    c.drawString(left_margin + 20, y, "o Audio AI (24/7 ambient audio monitoring, non-recording).")
    y -= 14
    c.drawString(left_margin + 20, y, "o Biometric Mattress Sensor (sleep and vital trends).")
    y -= 16

    c.drawString(
        left_margin,
        y,
        "• 1× daily clinical visit by a designated Personal Support Worker."
    )
    y -= 16
    c.drawString(
        left_margin,
        y,
        "• Supervision by an RPN Care Designer, overseeing personalized care planning and escalation."
    )
    y -= 16
    c.drawString(
        left_margin,
        y,
        "• 24/7 Care Response Services engaged in the event of any AI-detected concern."
    )
    y -= 16
    c.drawString(
        left_margin,
        y,
        f"• Enrolled since: {enrolled_str}"
    )

    # Disclaimer section
    y -= 28
    c.setFont("Helvetica-Bold", 11)
    c.drawString(left_margin, y, "Disclaimer")
    y -= 18

    c.setFont("Helvetica", 10)
    disclaimer_text = (
        "This report summarizes data and observations collected in the course of CHAH AI Care services. "
        "While every effort has been made to ensure accuracy, this document is not a substitute for a full "
        "clinical assessment by a physician or regulated healthcare provider."
    )
    y = _draw_wrapped_text(c, disclaimer_text, left_margin, y, max_chars=95, line_height=14)
    y -= 8

    c.drawString(left_margin, y, "• CHAH AI Care reports are designed to support care transitions by offering a longitudinal view")
    y -= 14
    c.drawString(left_margin + 14, y, "of the patient's status based on sensor data, clinical notes, and predictive AI scoring.")
    y -= 14
    c.drawString(left_margin, y, "• Data is current as of the report generation date and may reflect trends or AI-predicted risks.")
    y -= 14
    c.drawString(left_margin, y, "• This report should be interpreted by trained clinicians with corroborating assessments.")
    y -= 14
    c.drawString(left_margin, y, "• CHAH Technology and Stay at Home Nursing assume no liability for decisions made solely")
    y -= 14
    c.drawString(left_margin + 14, y, "on the basis of this report.")

    # Privacy & consent
    y -= 24
    c.setFont("Helvetica-Bold", 11)
    c.drawString(left_margin, y, "Privacy & Consent")
    y -= 18

    c.setFont("Helvetica", 10)
    privacy_text = (
        "All monitoring was conducted with informed consent in accordance with PHIPA and PIPEDA. "
        "All data has been handled following CHAH’s internal security protocols and privacy standards."
    )
    y = _draw_wrapped_text(c, privacy_text, left_margin, y, max_chars=95, line_height=14)

    # Highlighted fictional-note bar
    y -= 16
    highlight_text = (
        "Please note: This report is fictional and does not include real data or real patient information. "
        "All information here is fabricated for illustrative purposes only."
    )
    c.setFillColorRGB(1, 1, 0.8)  # pale yellow
    rect_height = 32
    c.rect(left_margin - 4, y - rect_height + 6, width - 2 * left_margin + 8, rect_height, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 9)
    y = _draw_wrapped_text(c, highlight_text, left_margin, y, max_chars=95, line_height=12)

    _draw_footer(c, page_num=2, width=width, bottom_margin=bottom_margin, logo_path=logo_path)
    c.showPage()

    # ---------- PAGE 3: CLINICAL OVERVIEW ----------
    y = height - 1.25 * inch
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.black)

    c.drawString(left_margin, y, "Patient Name: ")
    c.setFont("Helvetica", 11)
    c.drawString(left_margin + 90, y, name)

    y -= 16
    c.setFont("Helvetica-Bold", 11)
    c.drawString(left_margin, y, "Date of Birth: ")
    c.setFont("Helvetica", 11)
    c.drawString(left_margin + 90, y, str(dob))

    y -= 16
    c.setFont("Helvetica-Bold", 11)
    c.drawString(left_margin, y, "Health Card #: ")
    c.setFont("Helvetica", 11)
    c.drawString(left_margin + 90, y, health_card)

    y -= 16
    c.setFont("Helvetica-Bold", 11)
    c.drawString(left_margin, y, "Date of Report: ")
    c.setFont("Helvetica", 11)
    c.drawString(left_margin + 90, y, today_str)

    y -= 16
    c.setFont("Helvetica-Bold", 11)
    c.drawString(left_margin, y, "Prepared by: ")
    c.setFont("Helvetica", 11)
    c.drawString(left_margin + 90, y, "Stay at Home Nursing / CHAH Technology")

    y -= 20
    c.setLineWidth(0.7)
    c.setStrokeColor(colors.grey)
    c.line(left_margin, y, width - left_margin, y)
    y -= 24

    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(colors.black)
    c.drawString(left_margin, y, "Clinical Overview")
    y -= 22

    # Baseline Summary
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(brand_green)
    c.drawString(left_margin, y, "Baseline Summary")
    y -= 18

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    baseline_text = (
        f"{name} is an older adult with complex medical needs receiving coordinated home-based care "
        "through CHAH AI Care. They live in the community with support from scheduled clinical "
        "visits and continuous AI-enabled monitoring. Family and caregivers are engaged in ongoing "
        "care planning and decision-making."
    )
    y = _draw_wrapped_text(c, baseline_text, left_margin, y, max_chars=95, line_height=14)
    y -= 10

    baseline_text2 = (
        "This baseline profile reflects functional limitations, fall risk, and evolving medical "
        "conditions that require close observation, proactive intervention, and clear communication "
        "between home-care, virtual, and in-person providers."
    )
    y = _draw_wrapped_text(c, baseline_text2, left_margin, y, max_chars=95, line_height=14)

    # Current Risk Summary
    y -= 20
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(brand_green)
    c.drawString(left_margin, y, "Current Risk Summary")
    y -= 18
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)

    risks = [
        ("Fall Risk", "Moderate to High"),
        ("Cognitive Impairment", "Mild, stable"),
        ("Infection Risk", "Elevated; recent infections and respiratory pattern changes flagged"),
        ("Hospitalization Risk", "Moderate; requires early response to clinical changes"),
        ("Sleep Quality", "Mild deterioration in the past 30 days"),
        ("Social Engagement", "Low but stable"),
    ]
    for label, value in risks:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(left_margin, y, "• " + label + ":")
        c.setFont("Helvetica", 10)
        c.drawString(left_margin + 130, y, value)
        y -= 14

    # Divider line before interRAI section
    y -= 14
    c.setLineWidth(0.7)
    c.setStrokeColor(colors.grey)
    c.line(left_margin, y, width - left_margin, y)
    y -= 24

    # interRAI Assessment Snapshot heading
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.black)
    c.drawString(left_margin, y, "interRAI Assessment Snapshot with CHAH AI Trends")
    y -= 18

    c.setFont("Helvetica", 10)
    recent_assess_text = "Most recent interRAI-HC assessment: April 14, 2025"
    c.drawString(left_margin, y, recent_assess_text)
    y -= 24

    # Simple interRAI table
    table_top = y
    col_widths = [2.0 * inch, 1.2 * inch, 1.8 * inch, 2.5 * inch]
    row_height = 22

    x_positions = [left_margin]
    for wcol in col_widths[:-1]:
        x_positions.append(x_positions[-1] + wcol)

    table_height = row_height * 2
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.rect(left_margin, table_top - table_height, sum(col_widths), table_height, fill=0)

    c.line(left_margin, table_top - row_height,
           left_margin + sum(col_widths), table_top - row_height)

    x_cursor = left_margin
    for wcol in col_widths[:-1]:
        x_cursor += wcol
        c.line(x_cursor, table_top, x_cursor, table_top - table_height)

    headers = ["Domain", "interRAI Score", "CHAH Trendline", "Summary (AI Generated)"]
    c.setFont("Helvetica-Bold", 9)
    text_y = table_top - 15
    for i, header in enumerate(headers):
        c.drawString(x_positions[i] + 4, text_y, header)

    c.setFont("Helvetica", 9)
    data_y = table_top - row_height - 15
    c.drawString(x_positions[0] + 4, data_y, "ADL Hierarchy")
    c.drawString(x_positions[1] + 4, data_y, "4")
    c.drawString(x_positions[2] + 4, data_y, "[Graph]")
    summary_text = "Requires assistance with most ADLs. Trend appears stable over recent weeks."
    _ = _draw_wrapped_text(
        c, summary_text, x_positions[3] + 4, data_y, max_chars=50, line_height=11
    )

    _draw_footer(c, page_num=3, width=width, bottom_margin=bottom_margin, logo_path=logo_path)
    c.showPage()

    # ---------- PAGE 4: DETAILED TRANSITION SUMMARY ----------
    y = height - 1.25 * inch
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(brand_green)
    c.drawString(left_margin, y, "Transition Summary – Care Plan Details")
    y -= 24

    # Demographic snippet (optional)
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawString(left_margin, y, f"Patient ID: {patient_id}")
    y -= 14
    c.drawString(left_margin, y, f"Name: {name}")
    y -= 14
    c.drawString(left_margin, y, f"DOB: {dob}")
    y -= 14
    if sex:
        c.drawString(left_margin, y, f"Sex: {sex}")
        y -= 14
    if race:
        c.drawString(left_margin, y, f"Race/Ethnicity: {race}")
        y -= 14
    if address:
        c.drawString(left_margin, y, f"Address: {address}, {city}, {state} {zip_code}")
        y -= 14
    if guardian:
        c.drawString(left_margin, y, f"Primary Guardian: {guardian}")
        y -= 14
    if insurance:
        c.drawString(left_margin, y, f"Insurance: {insurance}")
        y -= 18

    # CLINICAL SUMMARY
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(brand_green)
    c.drawString(left_margin, y, "CLINICAL SUMMARY")
    y -= 16
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10)
    y = _draw_wrapped_text(
        c,
        f"Primary diagnosis/diagnoses: {diagnosis_str}",
        left_margin,
        y,
        max_chars=95,
        line_height=14,
    )
    y = _draw_wrapped_text(
        c,
        f"Care plan start date: {care_plan_start}",
        left_margin,
        y,
        max_chars=95,
        line_height=14,
    )
    y = _draw_wrapped_text(
        c,
        f"Care plan goals: {goals_str}",
        left_margin,
        y,
        max_chars=95,
        line_height=14,
    )
    y = _draw_wrapped_text(
        c,
        f"Primary providers involved: {providers_str}",
        left_margin,
        y,
        max_chars=95,
        line_height=14,
    )

    # RECENT CARE PLAN SESSIONS
    y -= 18
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(brand_green)
    c.drawString(left_margin, y, "RECENT CARE PLAN SESSIONS")
    y -= 16
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10)

    if recent_sessions.empty:
        y = _draw_wrapped_text(
            c,
            "No recorded sessions.",
            left_margin,
            y,
            max_chars=95,
            line_height=14,
        )
    else:
        for _, row in recent_sessions.iterrows():
            session_date = row["Session_Date"]
            provider = row["Provider"]
            notes = row["Session_Notes"]
            progress = row["Progress_Score"]
            bullet = f"- {session_date} with {provider}: {notes} (Progress score: {progress})"
            y = _draw_wrapped_text(
                c,
                bullet,
                left_margin,
                y,
                max_chars=95,
                line_height=14,
            )

    # OVERALL PROGRESS
    y -= 18
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(brand_green)
    c.drawString(left_margin, y, "OVERALL PROGRESS")
    y -= 16
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10)
    y = _draw_wrapped_text(
        c,
        f"Most recent progress score: {last_progress} (0–10 scale, higher = better).",
        left_margin,
        y,
        max_chars=95,
        line_height=14,
    )

    # TRANSITION CONSIDERATIONS / NEXT STEPS
    y -= 18
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(brand_green)
    c.drawString(left_margin, y, "TRANSITION CONSIDERATIONS / NEXT STEPS")
    y -= 16
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10)

    bullets_next = [
        "Ensure transfer of care plan and recent session notes to the receiving team.",
        "Review medications, follow-up appointments, and safety/monitoring needs.",
        "Confirm contact information for guardians and providers.",
    ]
    for text in bullets_next:
        y = _draw_wrapped_text(
            c,
            f"- {text}",
            left_margin,
            y,
            max_chars=95,
            line_height=14,
        )

    _draw_footer(c, page_num=4, width=width, bottom_margin=bottom_margin, logo_path=logo_path)
    c.save()


if __name__ == "__main__":
    pid = input("Enter Patient_ID (e.g., P001): ").strip()
    default_filename = f"transition_report_{pid}.pdf"
    filename = input(f"Enter output PDF filename [{default_filename}]: ").strip()
    if not filename:
        filename = default_filename

    generate_transition_report_pdf(pid, filename)
    print(f"Report for {pid} saved as {filename}")
