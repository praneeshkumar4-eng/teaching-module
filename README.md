# LessonForge ⚒️
> **Autonomous AI-Powered Lesson Creation Engine for Teachers**

LessonForge is a local, AI-powered instructional workstation that empowers educators to design comprehensive, verified 45-minute lesson plans for any topic or grade level. 

Unlike generic slide creators or ungrounded chatbots, LessonForge performs **real external research retrieval** across websites, published academic books, and educational YouTube transcripts, strictly enforces grounding on that research with inline citations, and audits the output through two independent automated Quality Control (QC) review layers before presenting the result in an interactive teacher workspace.

---

## 🚀 Key Features

1. **Multi-Source Real Research Retrieval (Zero Hallucinated Links):**
   - **Web Research:** Powered by Tavily Search API with extracted content; automatically falls back to DuckDuckGo Search (`ddgs`) with `trafilatura` for full webpage text extraction.
   - **Academic Books:** Powered by Google Books API (supporting keyed and keyless queries) with fallback to OpenLibrary for academic texts, authors, publication year, and preview links.
   - **Educational Video Media:** Powered by YouTube Data API v3 and DuckDuckGo video search, extracting real spoken captions and transcripts with `youtube-transcript-api`.

2. **Strictly Grounded 45-Minute Lesson Synthesis:**
   - Synthesizes a bell-to-bell 45-minute lesson plan structured with 5-minute increments:
     - `00:00 - 05:00` | Inquiry Hook & Objective Framing
     - `05:00 - 20:00` | Direct Instruction & Teacher Script (addressing anticipated student misconceptions)
     - `20:00 - 35:00` | Guided Practice & Interactive Collaborative Investigation
     - `35:00 - 40:00` | Independent Practice & Student Synthesis
     - `40:00 - 45:00` | Closure, Exit Ticket & Formative Assessment
   - Every factual claim, definition, and empirical assertion strictly cites source references (e.g. `[Web 1]`, `[Book 2]`, `[Video 1]`).

3. **Two-Layer Automated Quality Control (QC) Suite:**
   - **QC Layer 1 (Factual Accuracy & Hallucination Audit):** Cross-examines all claims in the lesson plan against the retrieved research dossier, scoring factual grounding from 0-100% and flagging unsupported or unverified statements.
   - **QC Layer 2 (Instructional Design & Pedagogical Review):** Evaluates lesson alignment against Bloom's Taxonomy learning objectives, 45-minute timing feasibility, active learning ratio, cognitive rigor, and differentiation.
   - **Interactive Recommendation Applier:** Teachers can check recommended improvements and apply them with one click, automatically creating a new version.

4. **Teacher Workspace & Version Control:**
   - Live formatted preview and direct Markdown editor.
   - Immutable version history snapshots (`v1`, `v2`, `v3...`) with one-click rollback.
   - Multi-format exports: standalone `.md`, print-styled `.html` (with `@media print` layout), and complete `.zip` archive containing all artifacts.
   - Local JSON and Markdown persistence under `data/lessons/<lesson_id>/` (zero external database required).

---

## 🛠️ Tech Stack & Requirements

- **Python:** 3.11+
- **UI Framework:** Streamlit
- **AI / LLM:** Google Gemini via the official `google-genai` SDK (`gemini-2.5-flash` default)
- **Web & Content Extraction:** `tavily-python` (optional), `ddgs`, `trafilatura`
- **Books & Video:** Google Books API, OpenLibrary API, YouTube Data API v3, `youtube-transcript-api`
- **Data Validation & Parsing:** `pydantic`
- **Exporting & Rendering:** `markdown`, `jinja2`, `zipfile`

---

## 📦 Installation & Setup

### 1. Clone the repository and navigate to the project root:
```bash
cd kalvium
```

### 2. Create and activate a Python virtual environment:
```bash
python -m venv .venv

# On Windows:
.\.venv\Scripts\activate

# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install dependencies:
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables:
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and configure your keys:
```ini
# Google Gemini API Key (Required for AI generation & QC)
# Obtain from https://aistudio.google.com/
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Tavily API Key (Optional: DuckDuckGo + Trafilatura used if omitted)
TAVILY_API_KEY=

# Google Books API Key (Optional: keyless endpoint works by default)
GOOGLE_BOOKS_API_KEY=

# YouTube Data API Key (Optional: DDG video search used if omitted)
YOUTUBE_API_KEY=
```
*(Note: You can also configure and test API keys directly in the sidebar settings panel within the Streamlit UI).*

---

## 🚀 Running the Application

Launch the Streamlit app:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 📁 Project Architecture

```
kalvium/
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore patterns (.env, data/lessons, etc.)
├── requirements.txt          # Python dependencies with pinned versions
├── README.md                 # Project documentation
├── app.py                    # Main Streamlit application entry point
├── config.py                 # Configuration loader and runtime key manager
├── core/
│   ├── llm.py                # Single LLM wrapper for Google GenAI SDK (with mock fallback)
│   ├── models.py             # Typed Pydantic data schemas for lessons, research & QC
│   ├── storage.py            # Local filesystem persistence and version tracking
│   └── exporter.py           # Multi-format exporter (ZIP, HTML, Markdown)
├── research/
│   ├── web_search.py         # Tavily and DuckDuckGo + Trafilatura web retrieval
│   ├── books_search.py       # Google Books and OpenLibrary retrieval
│   ├── youtube_search.py     # YouTube Data API v3 + transcript extractor
│   └── aggregator.py         # Concurrent multi-source research coordinator
├── generator/
│   ├── lesson_generator.py   # Grounded 45-minute lesson synthesizer
│   └── prompt_templates.py   # Structured system prompts and QC evaluation schemas
├── qc/
│   ├── factual_checker.py    # QC Layer 1: Factual accuracy & hallucination audit
│   └── pedagogical_checker.py# QC Layer 2: Teaching quality & objective alignment
└── ui/
    ├── styles.py             # Custom educator-grade CSS styling
    ├── components.py         # Reusable widgets (score gauges, source badges)
    └── views/
        ├── create_view.py    # Lesson generation input form and progress tracker
        ├── editor_view.py    # Interactive lesson workspace, editor, and versioning
        ├── qc_view.py        # QC Layer 1 & 2 audit reports & recommendation applier
        ├── research_view.py  # Retrieved research explorer and transcript viewer
        └── library_view.py   # Saved lessons catalog and bulk export manager
```

---

## 📄 License

MIT License. Designed and engineered for educators worldwide.
