🎵 Music Store Executive Dashboard

An interactive executive analytics dashboard built with Streamlit, dbt, and DuckDB, delivering country-level revenue intelligence, customer value insights, and genre performance analytics with real-time data refresh capability.

This project simulates an enterprise-grade analytics workflow using the Chinook dataset, modeled in dbt and visualized through a modern executive dashboard.

🚀 Overview

The Music Store Executive Dashboard provides:

Country revenue performance monitoring

Year-over-Year (YoY) growth analysis

Top genre revenue tracking

Customer Lifetime Value (LTV) insights

Revenue concentration analysis

Monthly & YTD revenue trends

One-click dbt model refresh from the UI

Designed as a portfolio-ready data engineering + analytics showcase.

🏗️ Tech Stack

Streamlit – Interactive dashboard application

dbt – Data transformation & modeling

DuckDB – Embedded analytical database

Plotly – Executive-grade visualizations

Python (Pandas) – Data manipulation

📊 Key Features
1️⃣ Executive KPIs

Country Revenue (scaled to executive-level display)

Top Genre Revenue

Top Customer Lifetime Value

Top Customer Revenue Contribution %

Country YoY Growth %

Revenue values are scaled for executive visualization purposes.

2️⃣ Executive Summary Generator

Automatically generates narrative insights based on:

Revenue levels

YoY performance

Genre dominance

Revenue concentration risk

This simulates AI-style automated business reporting.

3️⃣ Revenue Trend Analysis

Monthly revenue trend

Month-over-Month growth %

Year-to-Date (YTD) revenue overlay

Dynamic country filtering

4️⃣ Interactive Filters

Top N countries selection

Country-level drilldown

Genre selection

5️⃣ One-Click dbt Refresh

Users can:

Run dbt run

Rebuild transformation models

Clear Streamlit cache

Reload fresh DuckDB data

All directly from the dashboard UI.

🧠 Data Architecture

Raw Chinook data →
dbt transformations →
Fact table: fct_music_kpi →
DuckDB →
Streamlit dashboard

The dashboard reads from the transformed fact model, not raw tables.

⚙️ Installation & Setup
1️⃣ Clone the repository
git clone <your-repo-url>
cd <repo-name>

2️⃣ Install dependencies
pip install -r requirements.txt

3️⃣ Run dbt models

Navigate to your dbt project root:

dbt run

4️⃣ Launch Streamlit app
streamlit run app.py

🔄 Refreshing Data

Inside the dashboard:

Click "🔄 Refresh Data (Run dbt)"

This will:

Execute dbt run

Clear cached data

Reload fresh results

Update KPIs and charts live

📁 Project Structure (Example)
├── app.py
├── dev.duckdb
├── models/
│   ├── staging/
│   ├── marts/
│   │   └── fct_music_kpi.sql
├── dbt_project.yml
├── requirements.txt
└── README.md

