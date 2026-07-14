# AI Business Analytics Copilot

An intelligent, enterprise-grade Business Intelligence (BI) and analytics platform built with Django, Pandas, Plotly, and the Mistral AI API. The application operates like an AI Business Analyst, automatically parsing uploads, rendering interactive KPI metric charts, and writing strategic executive recommendations.

---

## Key Features

1. **Secure Session Authentication:** User Registration, Login, Logout (with unsaved changes validation), and Password Reset.
2. **Repository File Manager:** Drag-and-drop styled interface accepting CSV and Excel (.xlsx) spreadsheets, calculating rows/columns, duplicates, null counts, schemas, and generating interactive data tables.
3. **Interactive Plotly Canvas:** Slice and filter active datasets by categorical columns, select customized X/Y axes, toggle visual outputs (Bar, Line, Pie, Donut, Histogram, Scatter), and save dashboard preferences.
4. **AI Business Advisor (Mistral AI):** Connects to Mistral chat APIs to compile rich, structured Markdown insights (Executive Summaries, Highlights, Risks, Opportunities, Actionable Recommendations) dynamically sized for your variables.
5. **Multi-Format Exporting:**
   - Client-side capture of Plotly charts into landscape PDFs.
   - Excel and CSV downloads of parsed dataset grids.
   - Dynamic memory-compiled ZIP archives bundling dataset records, AI reports, and dashboard metric sheets.
6. **Unified Theme Engine:** Sleek enterprise layout with variables support for Light/Dark themes.

---

## Tech Stack

- **Backend:** Django 4.x, Python 3.x
- **Data Pipelines:** Pandas, NumPy, OpenPyXL
- **Visualization:** Plotly.js (Plotly Python wrapper)
- **AI Engine:** Mistral AI API (via python requests)
- **PDF Compiler:** xhtml2pdf (ReportLab subset)
- **Database:** SQLite3

---

## Installation & Setup

1. **Clone or unzip this project** into your active workspace directory.
2. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Execute database migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
4. **Start the local server:**
   ```bash
   python manage.py runserver
   ```
5. **Open the application:**
   Navigate to [http://localhost:8000/](http://localhost:8000/) in your web browser.

---

## AI Advisor Setup

To enable the AI Business Advisor:
1. Register a new account and log in.
2. Go to **Settings** in the sidebar.
3. Select **AI Configuration** and paste your **Mistral API Key**.
4. Click **Test API Connection** to verify validity, then click **Save Configuration**.
5. Once saved, navigate back to the Dashboard or AI Advisor page to generate audits.
