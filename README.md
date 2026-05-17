# 💰 FinanceIQ — Personal Finance Manager

> A full-featured personal finance management web app built with **Python + Streamlit**.  
> Track your net worth, set financial goals, forecast your future wealth, and generate actionable insights — all in a beautiful dark-themed UI.

---

## 📸 Features at a Glance

| Module | What it does |
|---|---|
| 🏦 Net Worth Calculator | Add, edit, delete assets & liabilities with real-time net worth |
| 🗺️ Financial Roadmap | Set goals with month/year targets, milestones, and AI insights |
| 📈 Forecast & Projections | Compound growth model + ML regression on your history |
| 📊 Reports & Insights | Health score, monthly summaries, charts, and CSV exports |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Streamlit |
| **Backend** | Python 3.10+ |
| **Database** | SQLite (via `sqlite3`) |
| **Data** | Pandas, NumPy |
| **ML / Forecasting** | Scikit-learn (LinearRegression, PolynomialFeatures) |
| **Charts** | Plotly |
| **Fonts** | Syne + DM Sans (Google Fonts) |

---

## 📁 Project Structure

```
financial_manager/
│
├── app.py                  # Main entry point — page routing + global CSS
│
├── modules/
│   ├── __init__.py         # Makes modules a Python package
│   ├── database.py         # SQLite setup, all CRUD helpers, seed data
│   ├── net_worth.py        # Net Worth Calculator page
│   ├── roadmap.py          # Financial Roadmap + goal insights page
│   ├── forecast.py         # Forecast & Projections page
│   └── reports.py          # Reports, health score, exports page
│
├── finance.db              # Auto-created SQLite database (gitignore this)
├── requirements.txt        # Python dependencies
└── README.md               # You are here
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.10 or higher
- pip

### 1. Clone or download the project

```bash
git clone https://github.com/yourusername/financeiq.git
cd financeiq
```

Or simply download and unzip the project folder.

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install streamlit pandas numpy scikit-learn plotly
```

### 3. Run the app

```bash
streamlit run app.py
```

The app will open automatically at `http://localhost:8501`

---

## 🧪 Load Example Data

When you first open the app:

1. Go to **📊 Reports & Insights** in the sidebar
2. Expand the **🧪 Demo / Testing** section
3. Click **🚀 Load Example Dataset**

This seeds the database with:
- 6 sample assets (savings, stocks, mutual funds, property, etc.)
- 4 sample liabilities (mortgage, car loan, credit cards)
- 4 financial goals (emergency fund, house, retirement, travel)
- 12 months of net worth snapshot history

---

## 📖 Module Guide

### 🏦 Net Worth Calculator (`net_worth.py`)
- Add assets across categories: **Cash, Investments, Property, Other**
- Add liabilities: **Loans, Credit Cards, Mortgage, Other**
- **Inline edit** any entry with ✏️ — change name, category, or amount
- **Delete** entries with 🗑️
- **Save snapshots** with a custom name (e.g. "May 2026") for trend tracking
- Charts: donut breakdown, assets vs liabilities bar, category breakdown

### 🗺️ Financial Roadmap (`roadmap.py`)
- Add goals with **target month + year** for precise deadlines
- Priority levels: 🔴 High · 🟡 Medium · 🟢 Low
- **Milestone tracking**: 25% → 50% → 75% → 100% with estimated dates
- **Rule-based AI insights** per goal — tells you if you're on track, what to do, and by when
- **Edit goals inline** — update any field and save instantly
- Timeline chart and progress overview chart

### 📈 Forecast & Projections (`forecast.py`)
- **Compound growth model**: input monthly savings + expected return rate
- **Inflation adjustment**: see real vs nominal projected net worth
- **ML trend**: polynomial regression on your snapshot history (needs 3+ snapshots)
- **Scenario comparison**: Conservative (6%) vs Moderate (10%) vs Aggressive (15%)
- Projection summary table at 5, 10, 15, 20, 25, 30 year marks

### 📊 Reports & Insights (`reports.py`)
- **Net worth history chart** with assets, liabilities, and net worth over time
- **Monthly Summary table** — fully editable (name, amounts) with ✏️ and 🗑️ per row
- **Asset & Liability breakdown** pie charts
- **Goals summary** table + progress bar chart
- **Financial Health Score** (0–100) across 5 pillars:
  - 🏦 Debt Control (25 pts)
  - 📈 Net Worth (20 pts)
  - 🎯 Goal Funding (20 pts)
  - 🌐 Diversification (20 pts)
  - 📊 Tracking Consistency (15 pts)
- Per-pillar action cards — exactly what to do to earn more points
- **Quick Wins** section — 5-minute, this-week, this-month actions
- **CSV exports** for Assets, Liabilities, Goals, and History

---

## 🗄️ Database Schema

All data is stored in `finance.db` (SQLite). Tables are auto-created on first run.

```sql
-- Assets
CREATE TABLE assets (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    category   TEXT NOT NULL,
    name       TEXT NOT NULL,
    amount     REAL NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT (date('now'))
);

-- Liabilities
CREATE TABLE liabilities (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    category   TEXT NOT NULL,
    name       TEXT NOT NULL,
    amount     REAL NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT (date('now'))
);

-- Goals
CREATE TABLE goals (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_name      TEXT NOT NULL,
    target_amount  REAL NOT NULL,
    current_saved  REAL DEFAULT 0,
    target_month   INTEGER DEFAULT 1,
    target_year    INTEGER,
    priority       TEXT DEFAULT 'medium',
    created_at     TEXT DEFAULT (date('now'))
);

-- Snapshots (net worth history)
CREATE TABLE snapshots (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    snap_name         TEXT NOT NULL DEFAULT '',
    snap_date         TEXT NOT NULL,
    total_assets      REAL,
    total_liabilities REAL,
    net_worth         REAL
);
```

---

## 🚀 Deploy to Streamlit Cloud (Free)

1. Push your project to a **public GitHub repository**

2. Make sure you have a `requirements.txt`:
   ```
   streamlit
   pandas
   numpy
   scikit-learn
   plotly
   ```

3. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub

4. Click **New app** → select your repo → set main file to `app.py` → **Deploy**

> ⚠️ **Note:** Streamlit Cloud uses an ephemeral filesystem. The SQLite `finance.db` will reset on each redeploy. For persistent storage on the cloud, consider replacing SQLite with **Supabase** (free PostgreSQL) or **TinyDB with file storage**.

---

## 🖥️ Run in Google Colab

```python
# Install dependencies
!pip install streamlit pandas numpy scikit-learn plotly pyngrok -q

# Upload your project files, then:
from pyngrok import ngrok
import subprocess

# Start Streamlit in background
proc = subprocess.Popen(["streamlit", "run", "app.py", "--server.port", "8501"])

# Create public tunnel
public_url = ngrok.connect(8501)
print("FinanceIQ is live at:", public_url)
```

---

## 🔧 Common Issues

| Error | Fix |
|---|---|
| `ModuleNotFoundError: modules` | Run `streamlit run app.py` from inside the `financial_manager/` folder |
| `sqlite3.OperationalError: no such column` | Run the migration: `python -c "import sqlite3; conn=sqlite3.connect('finance.db'); conn.execute('ALTER TABLE goals ADD COLUMN target_month INTEGER DEFAULT 12'); conn.commit()"` |
| Port already in use | Run with `streamlit run app.py --server.port 8502` |
| Blank white/black screen | Check for duplicate CSS in `app.py` — there should be only one `st.markdown("""<style>...""")` block |
| `ImportError: cannot import name X` | Replace `modules/database.py` with the latest version which includes all functions |

---

## 📦 requirements.txt

```
streamlit>=1.32.0
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
plotly>=5.18.0
```

---

## 👤 Contributor

<table>
  <tr>
    <td align="center">
      <b>Yashraj Tarte</b><br>
      <sub>Developer & Designer</sub>
    </td>
  </tr>
</table>

---

## 📄 License

This project is open-source and free to use for personal and educational purposes.

---

<div align="center">
  <sub>Built with ❤️ using Streamlit · SQLite · Scikit-learn · Plotly</sub><br>
  <sub>© 2026 FinanceIQ · All rights reserved</sub>
</div>
