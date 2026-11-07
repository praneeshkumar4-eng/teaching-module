"""
Custom styling and theme definitions for LessonForge.
Ensures an elegant, focused, educator-first visual experience.
"""

CUSTOM_CSS = """
<style>
  /* Base typography and clean layout */
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

  html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, sans-serif;
  }

  /* Main container max width and spacing */
  .main .block-container {
    max-width: 1140px;
    padding-top: 2rem;
    padding-bottom: 4rem;
  }

  /* App Header banner */
  .lf-header-card {
    background: linear-gradient(135deg, #1e3a8a 0%, #1e1b4b 100%);
    color: white;
    padding: 24px 32px;
    border-radius: 14px;
    margin-bottom: 24px;
    box-shadow: 0 4px 14px rgba(30, 58, 138, 0.15);
  }
  .lf-header-title {
    font-size: 1.85rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: -0.02em;
    color: #ffffff;
  }
  .lf-header-sub {
    font-size: 0.95rem;
    color: #cbd5e1;
    margin-top: 6px;
    margin-bottom: 0;
  }

  /* Metric cards */
  .lf-metric-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    text-align: center;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
  }
  .lf-metric-card:hover {
    box-shadow: 0 4px 10px rgba(0,0,0,0.06);
  }
  .lf-metric-score {
    font-size: 2.2rem;
    font-weight: 800;
    line-height: 1.1;
  }
  .lf-metric-label {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600;
    color: #64748b;
    margin-top: 4px;
  }

  /* Source badges */
  .lf-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 9px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  .lf-badge-web {
    background-color: #dbeafe;
    color: #1d4ed8;
  }
  .lf-badge-book {
    background-color: #fef3c7;
    color: #b45309;
  }
  .lf-badge-video {
    background-color: #fee2e2;
    color: #b91c1c;
  }
  .lf-badge-pass {
    background-color: #dcfce7;
    color: #15803d;
  }
  .lf-badge-warn {
    background-color: #fef3c7;
    color: #b45309;
  }

  /* QC Finding Card */
  .lf-finding-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-left: 4px solid #3b82f6;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 12px;
  }
  .lf-finding-card.verified {
    border-left-color: #10b981;
  }
  .lf-finding-card.unsupported {
    border-left-color: #f59e0b;
  }
  .lf-finding-card.contradicted {
    border-left-color: #ef4444;
  }

  /* Recommendation Card */
  .lf-rec-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 14px;
  }

  /* Library lesson card */
  .lf-library-item {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 18px 22px;
    margin-bottom: 14px;
    transition: all 0.2s ease;
  }
  .lf-library-item:hover {
    border-color: #93c5fd;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.08);
  }

  /* Streamlit Tabs Polish */
  .stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    border-bottom: 2px solid #e2e8f0;
  }
  .stTabs [data-baseweb="tab"] {
    height: 48px;
    font-weight: 600;
    font-size: 0.95rem;
    padding: 0 16px;
    border-radius: 6px 6px 0 0;
  }
  .stTabs [aria-selected="true"] {
    color: #1e3a8a !important;
    border-bottom: 3px solid #1e3a8a !important;
  }
</style>
"""


def apply_custom_css():
    """Returns markdown string injecting custom CSS."""
    return CUSTOM_CSS
