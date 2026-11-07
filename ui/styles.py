"""
Premium SaaS styling for LessonForge.
Hides default Streamlit chrome, injects modern Inter typography,
hero gradients (deep indigo -> violet -> teal), progress steppers,
and color-coded severity/access badges.
"""

CUSTOM_CSS = """
<style>
  /* Import Google Font */
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

  /* Global font application */
  html, body, [class*="css"], .stMarkdown, .stButton, .stTextInput, .stTextArea {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
  }

  /* Hide default Streamlit header, footer, and menu */
  #MainMenu {visibility: hidden;}
  footer {visibility: hidden;}
  header {visibility: hidden;}
  .stDeployButton {display:none;}

  /* Main container max width and spacing */
  .main .block-container {
    max-width: 1180px;
    padding-top: 1.5rem;
    padding-bottom: 5rem;
  }

  /* Hero Banner: Deep Indigo -> Violet -> Teal */
  .lf-hero-banner {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 40%, #4338ca 70%, #0d9488 100%);
    color: white;
    padding: 28px 36px;
    border-radius: 16px;
    margin-bottom: 24px;
    box-shadow: 0 10px 25px -5px rgba(49, 46, 129, 0.3), 0 8px 10px -6px rgba(13, 148, 136, 0.2);
    position: relative;
    overflow: hidden;
  }
  .lf-hero-banner::after {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(20, 184, 166, 0.25) 0%, transparent 70%);
    border-radius: 50%;
  }
  .lf-hero-title {
    font-size: 2.1rem;
    font-weight: 800;
    margin: 0;
    letter-spacing: -0.025em;
    color: #ffffff;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .lf-hero-tagline {
    font-size: 1.05rem;
    font-weight: 500;
    color: #cbd5e1;
    margin-top: 6px;
    margin-bottom: 0;
    letter-spacing: 0.05em;
  }
  .lf-hero-tagline span {
    color: #2dd4bf;
    font-weight: 700;
  }

  /* Progress Stepper Bar */
  .lf-stepper-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 12px 20px;
    margin-bottom: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }
  .lf-step-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.85rem;
    font-weight: 600;
    color: #64748b;
  }
  .lf-step-item.active {
    color: #4338ca;
  }
  .lf-step-item.completed {
    color: #059669;
  }
  .lf-step-circle {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: 700;
    background: #f1f5f9;
    color: #64748b;
  }
  .lf-step-item.active .lf-step-circle {
    background: #4338ca;
    color: white;
    box-shadow: 0 0 0 3px rgba(67, 56, 202, 0.2);
  }
  .lf-step-item.completed .lf-step-circle {
    background: #059669;
    color: white;
  }
  .lf-step-divider {
    flex: 1;
    height: 2px;
    background: #e2e8f0;
    margin: 0 8px;
  }
  .lf-step-divider.filled {
    background: #059669;
  }

  /* Source Cards */
  .lf-source-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 14px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
  }
  .lf-source-card:hover {
    border-color: #cbd5e1;
    box-shadow: 0 6px 14px rgba(0,0,0,0.06);
  }

  /* Access Level Badges */
  .lf-access-badge-full {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #dcfce7;
    color: #15803d;
    font-weight: 700;
    font-size: 0.75rem;
    padding: 3px 10px;
    border-radius: 14px;
    letter-spacing: 0.02em;
  }
  .lf-access-badge-desc {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #fef3c7;
    color: #b45309;
    font-weight: 700;
    font-size: 0.75rem;
    padding: 3px 10px;
    border-radius: 14px;
    letter-spacing: 0.02em;
  }

  /* Severity Badges */
  .lf-sev-high {
    background: #fee2e2;
    color: #b91c1c;
    font-weight: 700;
    font-size: 0.75rem;
    padding: 2px 8px;
    border-radius: 12px;
    text-transform: uppercase;
  }
  .lf-sev-medium {
    background: #ffedd5;
    color: #c2410c;
    font-weight: 700;
    font-size: 0.75rem;
    padding: 2px 8px;
    border-radius: 12px;
    text-transform: uppercase;
  }
  .lf-sev-low {
    background: #e0f2fe;
    color: #0369a1;
    font-weight: 700;
    font-size: 0.75rem;
    padding: 2px 8px;
    border-radius: 12px;
    text-transform: uppercase;
  }

  /* Verdict Banners */
  .lf-verdict-banner-warn {
    background: #fffbeb;
    border-left: 5px solid #f59e0b;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 20px;
    color: #92400e;
    font-weight: 600;
  }
  .lf-verdict-banner-pass {
    background: #f0fdf4;
    border-left: 5px solid #10b981;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 20px;
    color: #166534;
    font-weight: 600;
  }

  /* Timing Stacked Bar Badge */
  .lf-timing-badge {
    background: #1e1b4b;
    color: #2dd4bf;
    font-weight: 700;
    font-size: 0.85rem;
    padding: 4px 12px;
    border-radius: 20px;
  }

  /* Diff Viewer Styles */
  .diff-del {
    background-color: #fee2e2;
    color: #991b1b;
    text-decoration: line-through;
    padding: 1px 4px;
    border-radius: 2px;
  }
  .diff-add {
    background-color: #dcfce7;
    color: #166534;
    font-weight: 600;
    padding: 1px 4px;
    border-radius: 2px;
  }

  /* Polished Streamlit Tabs */
  .stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    border-bottom: 2px solid #e2e8f0;
  }
  .stTabs [data-baseweb="tab"] {
    height: 48px;
    font-weight: 600;
    font-size: 0.95rem;
    padding: 0 16px;
    border-radius: 8px 8px 0 0;
  }
  .stTabs [aria-selected="true"] {
    color: #4338ca !important;
    border-bottom: 3px solid #4338ca !important;
  }
</style>
"""


def apply_custom_css() -> str:
    return CUSTOM_CSS
