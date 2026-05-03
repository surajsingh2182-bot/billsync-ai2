# ⚖️ BillSync AI — Multi-Agent Billing Reconciliation

A multi-agent AI application that reconciles invoices against payment records
using 4 specialised AI agents powered by Google Gemini (free tier).

## 🤖 The 4 Agents

| Agent | Role |
|---|---|
| 🔍 **Data Analyst** | Reads and validates uploaded CSV files |
| 🔗 **Matching Agent** | Pairs each invoice to its payment |
| ⚠️ **Auditor** | Flags risks, duplicates, and anomalies |
| 📝 **Report Writer** | Generates the executive summary |

## 🚀 Deploying on Streamlit Cloud

1. Fork this repo to your GitHub account
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub → New app → select this repo
4. Set main file to `app.py` → Deploy

## 🔑 Getting Your Free Gemini API Key

1. Go to [aistudio.google.com](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **Get API Key** → **Create API key**
4. Copy and paste into the app sidebar — free, no credit card needed

## 📁 Sample Data

Use the included `invoices.csv` and `payments.csv` to test the app instantly.

## 🛠 Built With

- [Streamlit](https://streamlit.io) — web UI
- [Google Gemini](https://aistudio.google.com) — AI agents (free tier)
- [Pandas](https://pandas.pydata.org) — data handling
