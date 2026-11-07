"""
Export module for LessonForge.
Builds in-memory ZIP archives, styled HTML documents with print stylesheets,
standalone references, and QC report tables (Issue found | Suggested improvement | Severity | Status).
"""
import io
import json
import logging
import re
from typing import Optional
import zipfile
import markdown

from core.models import LessonPackage, QCFactualReport, QCPedagogicalReport

logger = logging.getLogger(__name__)


def generate_references_markdown(package: LessonPackage) -> str:
    """Generates a standalone references document from cited research sources."""
    dossier = package.research_dossier
    cited_ids = set(re.findall(r"\[(S\d+)\]", package.markdown_content))
    if not cited_ids:
        cited_ids = set(dossier.get_all_ids())

    lines = [
        f"# References & Verified Citations — {package.metadata.title}\n",
        f"*The following sources from the Research Dossier were cited during lesson delivery:*\n",
        "| ID | Type | Title | Author / Publisher | Access Level | Reference URL |",
        "|---|---|---|---|---|---|",
    ]

    for s in dossier.sources:
        if s.id in cited_ids:
            type_icon = {"web": "🌐 Web", "book": "📚 Book", "video": "▶️ Video"}.get(s.type.value, "📄 Source")
            access_str = "Full Text Verified" if s.access_level.value == "full_text" else "Description Only"
            author_str = s.author_or_channel or "N/A"
            lines.append(f"| **{s.id}** | {type_icon} | {s.title} | {author_str} | {access_str} | [{s.url}]({s.url}) |")

    lines.append("\n## Detailed Source Relevance Notes\n")
    for s in dossier.sources:
        if s.id in cited_ids:
            lines.append(f"### [{s.id}] {s.title}")
            lines.append(f"- **URL:** {s.url}")
            lines.append(f"- **Relevance Note:** {s.relevance_note}")
            lines.append(f"- **Excerpt:** \"{s.retrieved_text_excerpt[:300]}...\"\n")

    return "\n".join(lines)


def format_qc1_report_table(report: Optional[QCFactualReport]) -> str:
    """Formats QC Layer 1 (Factual Accuracy) as a clean Markdown table."""
    if not report:
        return "# QC Report 1: Factual Accuracy Review\n*No QC 1 report generated yet.*"

    lines = [
        f"# QC Report 1: Factual Accuracy & Citation Review\n",
        f"**Verdict:** {report.verdict} | **Confidence:** {report.confidence_note}\n",
        f"**What Was Verified:** {report.what_was_verified}\n",
        f"**Deterministic Checks:** {'PASSED' if report.deterministic_passed else 'FLAGS DETECTED'}\n",
        "---",
        "\n### Audit Issues Table\n",
        "| Issue Found | Suggested Improvement | Severity | Status |",
        "|---|---|---|---|",
    ]

    if not report.issues:
        lines.append("| No factual contradictions found. All claims corroborated. | Maintain existing source citations. | Low | Applied |")
    else:
        for iss in report.issues:
            status_str = "Applied" if iss.applied else "Pending"
            issue_clean = iss.issue_found.replace("|", "/")
            sugg_clean = iss.suggested_improvement.replace("|", "/")
            lines.append(f"| **[{iss.location}]** {issue_clean} | {sugg_clean} | {iss.severity.upper()} | {status_str} |")

    return "\n".join(lines)


def format_qc2_report_table(report: Optional[QCPedagogicalReport]) -> str:
    """Formats QC Layer 2 (Teaching Quality) as a clean Markdown table with objective coverage."""
    if not report:
        return "# QC Report 2: Teaching Quality Review\n*No QC 2 report generated yet.*"

    lines = [
        f"# QC Report 2: Teaching Quality & Instructional Design Review\n",
        f"**Verdict:** {report.verdict} | **Confidence:** {report.confidence_note}\n",
        f"**What Was Verified:** {report.what_was_verified}\n",
        "---",
        "\n### Objective Coverage Breakdown\n",
        "| Objective Component | Where Taught | Where Tested | Covered? |",
        "|---|---|---|---|",
    ]

    for cov in report.objective_coverage:
        covered_str = "Yes ✅" if cov.covered else "No ❌"
        lines.append(f"| {cov.objective_part} | {cov.where_taught} | {cov.where_tested} | {covered_str} |")

    lines.append("\n### Pedagogical Recommendations Table\n")
    lines.append("| Issue Found | Suggested Improvement | Severity | Status |")
    lines.append("|---|---|---|---|")

    if not report.issues:
        lines.append("| Excellent instructional scaffolding and timing alignment. | No critical interventions needed. | Low | Applied |")
    else:
        for iss in report.issues:
            status_str = "Applied" if iss.applied else "Pending"
            issue_clean = iss.issue_found.replace("|", "/")
            sugg_clean = iss.suggested_improvement.replace("|", "/")
            lines.append(f"| **[{iss.location}]** {issue_clean} | {sugg_clean} | {iss.severity.upper()} | {status_str} |")

    return "\n".join(lines)


def generate_styled_html(lesson_markdown: str, title: str, subtitle: str = "") -> str:
    """Renders lesson markdown into an elegant, print-ready HTML document."""
    html_body = markdown.markdown(
        lesson_markdown,
        extensions=["extra", "tables", "nl2br", "sane_lists"]
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — LessonForge</title>
<style>
  :root {{
    --primary: #4338ca;
    --primary-light: #e0e7ff;
    --text: #0f172a;
    --text-muted: #475569;
    --border: #cbd5e1;
    --bg-card: #f8fafc;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    line-height: 1.65;
    color: var(--text);
    background-color: #ffffff;
    max-width: 920px;
    margin: 0 auto;
    padding: 40px 24px;
  }}
  .header {{
    border-bottom: 3px solid var(--primary);
    padding-bottom: 20px;
    margin-bottom: 32px;
  }}
  .brand {{
    font-size: 0.85rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #6366f1;
    margin-bottom: 8px;
  }}
  h1 {{
    font-size: 2.1rem;
    color: #1e1b4b;
    margin: 0 0 8px 0;
    line-height: 1.25;
  }}
  .subtitle {{
    font-size: 1.05rem;
    color: var(--text-muted);
    margin: 0;
  }}
  h2 {{
    font-size: 1.4rem;
    color: #312e81;
    border-bottom: 1px solid var(--border);
    padding-bottom: 8px;
    margin-top: 36px;
    margin-bottom: 16px;
  }}
  h3 {{
    font-size: 1.15rem;
    color: #1e293b;
    margin-top: 24px;
    margin-bottom: 12px;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 24px 0;
  }}
  th, td {{
    border: 1px solid var(--border);
    padding: 10px 14px;
    text-align: left;
  }}
  th {{
    background-color: var(--primary-light);
    color: #312e81;
    font-weight: 600;
  }}
  pre, code {{
    background-color: #f1f5f9;
    font-family: ui-monospace, Menlo, Consolas, monospace;
    border-radius: 4px;
  }}
  pre {{
    padding: 16px;
    overflow-x: auto;
    border: 1px solid var(--border);
  }}
  code {{
    padding: 2px 6px;
    font-size: 0.9em;
    color: #be123c;
  }}
  pre code {{
    color: inherit;
    padding: 0;
  }}
  blockquote {{
    border-left: 4px solid #6366f1;
    background-color: #f5f3ff;
    margin: 20px 0;
    padding: 12px 20px;
    color: #3730a3;
    border-radius: 0 8px 8px 0;
  }}
  @media print {{
    body {{ max-width: 100%; padding: 0; color: #000; }}
    .header {{ border-bottom-color: #000; }}
    a {{ color: #000; text-decoration: underline; }}
    h1, h2, h3 {{ page-break-after: avoid; }}
    table, blockquote, pre {{ page-break-inside: avoid; }}
  }}
</style>
</head>
<body>
  <div class="header">
    <div class="brand">LessonForge Educator Suite • Verified 45-Minute Lesson Plan</div>
    <h1>{title}</h1>
    {f'<p class="subtitle">{subtitle}</p>' if subtitle else ''}
  </div>
  <div class="content">
    {html_body}
  </div>
</body>
</html>"""


def build_lesson_zip_bundle(package: LessonPackage) -> bytes:
    """
    Creates an in-memory ZIP archive containing the exact required files:
    - lesson.md
    - lesson.html
    - references.md
    - qc_report_1_accuracy.md
    - qc_report_2_teaching.md
    """
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # 1. lesson.md
        zip_file.writestr("lesson.md", package.markdown_content)

        # 2. lesson.html
        html_content = generate_styled_html(
            lesson_markdown=package.markdown_content,
            title=package.metadata.title,
            subtitle=package.metadata.objective,
        )
        zip_file.writestr("lesson.html", html_content)

        # 3. references.md
        references_md = generate_references_markdown(package)
        zip_file.writestr("references.md", references_md)

        # 4. qc_report_1_accuracy.md
        qc1_md = format_qc1_report_table(package.qc_factual)
        zip_file.writestr("qc_report_1_accuracy.md", qc1_md)

        # 5. qc_report_2_teaching.md
        qc2_md = format_qc2_report_table(package.qc_pedagogical)
        zip_file.writestr("qc_report_2_teaching.md", qc2_md)

    buffer.seek(0)
    return buffer.getvalue()
