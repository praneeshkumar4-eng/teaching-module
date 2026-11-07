"""
Export module for LessonForge.
Builds in-memory ZIP bundles, styled HTML documents with print stylesheets,
and standalone Markdown files for teachers.
"""
import io
import json
import logging
from typing import Optional
import zipfile
import markdown

from core.models import LessonPackage
from qc.factual_checker import factual_report_to_markdown
from qc.pedagogical_checker import pedagogical_report_to_markdown

logger = logging.getLogger(__name__)


def generate_styled_html(lesson_markdown: str, title: str, subtitle: str = "") -> str:
    """
    Renders lesson markdown into an elegant, print-ready HTML document
    with typography optimized for teachers and students.
    """
    html_body = markdown.markdown(
        lesson_markdown,
        extensions=["extra", "tables", "nl2br", "sane_lists"]
    )

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} - LessonForge</title>
<style>
  :root {{
    --primary: #1e3a8a;
    --primary-light: #eff6ff;
    --text: #1f2937;
    --text-muted: #4b5563;
    --border: #e5e7eb;
    --accent: #0284c7;
    --bg-card: #f9fafb;
  }}
  * {{
    box-sizing: border-box;
  }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    line-height: 1.65;
    color: var(--text);
    background-color: #ffffff;
    max-width: 900px;
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
    color: var(--accent);
    margin-bottom: 8px;
  }}
  h1 {{
    font-size: 2.2rem;
    color: var(--primary);
    margin: 0 0 8px 0;
    line-height: 1.25;
  }}
  .subtitle {{
    font-size: 1.1rem;
    color: var(--text-muted);
    margin: 0;
  }}
  h2 {{
    font-size: 1.45rem;
    color: var(--primary);
    border-bottom: 1px solid var(--border);
    padding-bottom: 8px;
    margin-top: 36px;
    margin-bottom: 16px;
  }}
  h3 {{
    font-size: 1.18rem;
    color: #1e293b;
    margin-top: 24px;
    margin-bottom: 12px;
  }}
  p, li {{
    font-size: 1.02rem;
  }}
  ul, ol {{
    padding-left: 24px;
    margin-bottom: 16px;
  }}
  li {{
    margin-bottom: 6px;
  }}
  blockquote {{
    border-left: 4px solid var(--accent);
    background-color: var(--primary-light);
    margin: 20px 0;
    padding: 12px 20px;
    font-style: italic;
    color: #1e3a8a;
    border-radius: 0 8px 8px 0;
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
    color: var(--primary);
    font-weight: 600;
  }}
  code {{
    background-color: #f3f4f6;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.9em;
    color: #b91c1c;
  }}
  .footer {{
    margin-top: 50px;
    padding-top: 20px;
    border-top: 1px solid var(--border);
    font-size: 0.85rem;
    color: var(--text-muted);
    text-align: center;
  }}
  @media print {{
    body {{
      max-width: 100%;
      padding: 0;
      color: #000;
    }}
    .header {{
      border-bottom-color: #000;
    }}
    a {{
      color: #000;
      text-decoration: underline;
    }}
    blockquote {{
      background: none;
      border-left-color: #000;
    }}
    h1, h2, h3 {{
      page-break-after: avoid;
    }}
    table, blockquote, pre {{
      page-break-inside: avoid;
    }}
  }}
</style>
</head>
<body>
  <div class="header">
    <div class="brand">LessonForge Educator Suite • Verified Lesson Plan</div>
    <h1>{title}</h1>
    {f'<p class="subtitle">{subtitle}</p>' if subtitle else ''}
  </div>

  <div class="content">
    {html_body}
  </div>

  <div class="footer">
    Generated with LessonForge • Grounded on Verified External Research • 45-Minute Classroom Guide
  </div>
</body>
</html>"""
    return html_template


def build_lesson_zip_bundle(package: LessonPackage) -> bytes:
    """
    Creates an in-memory ZIP archive containing the complete lesson package:
    - lesson.md
    - lesson.html (styled printable)
    - metadata.json
    - research.json
    - research_summary.md
    - qc_factual.json & qc_factual.md
    - qc_pedagogical.json & qc_pedagogical.md
    """
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # 1. Main lesson in Markdown
        zip_file.writestr("lesson.md", package.markdown_content)

        # 2. Main lesson in styled HTML
        html_content = generate_styled_html(
            lesson_markdown=package.markdown_content,
            title=package.metadata.title,
            subtitle=f"{package.metadata.grade_level} • {package.metadata.subject} • {package.metadata.duration_minutes} Mins",
        )
        zip_file.writestr("lesson.html", html_content)

        # 3. Metadata
        zip_file.writestr(
            "metadata.json",
            json.dumps(package.metadata.model_dump(), indent=2, ensure_ascii=False),
        )

        # 4. Research dossier
        zip_file.writestr(
            "research.json",
            json.dumps(package.research_dossier.model_dump(), indent=2, ensure_ascii=False),
        )
        zip_file.writestr("research_summary.md", package.research_dossier.get_citation_summary())

        # 5. QC Factual Report
        if package.qc_factual:
            zip_file.writestr(
                "qc_factual_report.json",
                json.dumps(package.qc_factual.model_dump(), indent=2, ensure_ascii=False),
            )
            zip_file.writestr(
                "qc_factual_report.md",
                factual_report_to_markdown(package.qc_factual),
            )

        # 6. QC Pedagogical Report
        if package.qc_pedagogical:
            zip_file.writestr(
                "qc_pedagogical_report.json",
                json.dumps(package.qc_pedagogical.model_dump(), indent=2, ensure_ascii=False),
            )
            zip_file.writestr(
                "qc_pedagogical_report.md",
                pedagogical_report_to_markdown(package.qc_pedagogical),
            )

    buffer.seek(0)
    return buffer.getvalue()
