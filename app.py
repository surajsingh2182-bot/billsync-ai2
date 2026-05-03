import streamlit as st
import google.generativeai as genai
import pandas as pd
import time

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BillSync AI — Reconciliation",
    page_icon="⚖️",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #f8f9fb; }
    .agent-card {
        background: white;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        border: 1px solid #e8eaf0;
        margin-bottom: 1rem;
    }
    .agent-header {
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #6b7280;
        margin-bottom: 0.3rem;
    }
    .agent-output {
        font-size: 0.9rem;
        color: #374151;
        line-height: 1.7;
        white-space: pre-wrap;
    }
    .app-header {
        background: linear-gradient(135deg, #0f172a 0%, #1a3a5c 100%);
        border-radius: 14px;
        padding: 2rem 2.5rem;
        margin-bottom: 2rem;
        color: white;
    }
    .app-title { font-size: 1.8rem; font-weight: 700; margin: 0; }
    .app-sub   { font-size: 0.95rem; opacity: 0.7; margin-top: 4px; }
    hr { border: none; border-top: 1px solid #e8eaf0; margin: 1.5rem 0; }
    #MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <div class="app-title">⚖️ BillSync AI</div>
    <div class="app-sub">Multi-Agent Billing & Payment Reconciliation · Powered by Google Gemini</div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔑 Configuration")
    api_key = st.text_input(
        "Google Gemini API Key",
        type="password",
        placeholder="AIza...",
        help="Get your free key at aistudio.google.com"
    )
    st.markdown("[👉 Get a free Gemini API key](https://aistudio.google.com/app/apikey)")
    st.markdown("---")
    st.markdown("### 📋 How it works")
    st.markdown("""
1. Upload your **Invoice CSV**
2. Upload your **Payments CSV**
3. Click **Run Reconciliation**
4. Watch 4 AI agents work in sequence
5. Download the final report
    """)
    st.markdown("---")
    st.markdown("### 🤖 The 4 Agents")
    st.markdown("""
- 🔍 **Data Analyst** — reads & validates data
- 🔗 **Matching Agent** — pairs invoices to payments
- ⚠️ **Auditor** — flags risks & anomalies
- 📝 **Report Writer** — executive summary
    """)

# ── File Upload ───────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 🧾 Invoice File")
    invoice_file = st.file_uploader(
        "Upload invoices CSV",
        type=["csv"],
        key="invoices",
        label_visibility="collapsed"
    )
    if invoice_file:
        inv_df = pd.read_csv(invoice_file)
        st.success(f"✅ {len(inv_df)} invoices loaded")
        with st.expander("Preview invoices"):
            st.dataframe(inv_df, use_container_width=True)

with col2:
    st.markdown("#### 💳 Payments File")
    payment_file = st.file_uploader(
        "Upload payments CSV",
        type=["csv"],
        key="payments",
        label_visibility="collapsed"
    )
    if payment_file:
        pay_df = pd.read_csv(payment_file)
        st.success(f"✅ {len(pay_df)} payments loaded")
        with st.expander("Preview payments"):
            st.dataframe(pay_df, use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)


# ── Agent functions ───────────────────────────────────────────────────────────
def call_gemini(api_key, system_prompt, user_message):
    """Single Gemini API call — one agent."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=system_prompt
    )
    response = model.generate_content(user_message)
    return response.text


def run_agent_1(api_key, inv_csv, pay_csv):
    system = """You are a Data Analyst Agent specialising in financial data.
Your job is to read the invoice and payment datasets and produce a clear structured summary.

Return your response in this exact structure:

INVOICE SUMMARY
- Total invoices: X
- Total value: ₹X
- Status breakdown (Paid/Overdue/Sent): ...
- Date range: ...
- Any data quality issues: ...

PAYMENT SUMMARY
- Total transactions: X
- Total value: ₹X
- Payment modes used: ...
- Date range: ...
- Any data quality issues: ...

DATA READINESS
- Ready for reconciliation: Yes/No
- Notes: ...
"""
    user_msg = f"""Here are the two datasets:

INVOICES CSV:
{inv_csv}

PAYMENTS CSV:
{pay_csv}

Please analyse both datasets and provide your structured summary."""
    return call_gemini(api_key, system, user_msg)


def run_agent_2(api_key, inv_csv, pay_csv, agent1_output):
    system = """You are a Matching Agent specialising in payment reconciliation.
Match each invoice to its corresponding payment using these rules in order:
1. Exact match: invoice_id equals reference field
2. Fuzzy match: reference contains invoice number in a different format (e.g. INVOICE008 = INV-008)
3. Amount + payer name similarity when reference is missing
4. If no match found, mark as UNMATCHED

Return your response in this exact structure:

MATCHED PAIRS
| Invoice ID | Customer | Invoice Amount | Transaction ID | Paid Amount | Match Type | Difference |
(one row per matched pair)

UNMATCHED INVOICES
| Invoice ID | Customer | Amount | Reason |

UNMATCHED PAYMENTS
| Transaction ID | Payer | Amount | Reason |

MATCHING SUMMARY
- Total matched: X
- Total unmatched invoices: X
- Total unmatched payments: X
"""
    user_msg = f"""INVOICES:
{inv_csv}

PAYMENTS:
{pay_csv}

CONTEXT FROM DATA ANALYST:
{agent1_output}

Please match invoices to payments and return results in the specified format."""
    return call_gemini(api_key, system, user_msg)


def run_agent_3(api_key, agent2_output):
    system = """You are an Auditor Agent specialising in financial risk and compliance.
Analyse the matching results and flag all anomalies and risks.

Look for:
- Short payments (paid less than invoiced)
- Overpayments (paid more than invoiced)
- Possible duplicate payments (same invoice paid twice)
- Unknown payments (no reference or unknown payer)
- Long overdue unpaid invoices
- Suspicious patterns

Return your response in this exact structure:

🚨 HIGH RISK ITEMS
| Issue Type | Invoice/Txn ID | Details | Recommended Action |

⚠️ MEDIUM RISK ITEMS
| Issue Type | Invoice/Txn ID | Details | Recommended Action |

✅ LOW RISK / INFORMATIONAL
| Issue Type | Details |

RISK SUMMARY
- High risk items: X
- Medium risk items: X
- Total financial exposure: ₹X
- Overall reconciliation health: Good / Fair / Poor
"""
    user_msg = f"""Here are the matching results from the Matching Agent:

{agent2_output}

Please audit these results and flag all risks."""
    return call_gemini(api_key, system, user_msg)


def run_agent_4(api_key, agent1_output, agent2_output, agent3_output):
    system = """You are a Report Writer Agent specialising in executive financial summaries.
Synthesise all findings into a clear professional executive summary a finance manager
can act on immediately. Write in plain business English. Be direct and actionable.

Structure your report exactly like this:

EXECUTIVE SUMMARY
(2-3 sentence overview)

KEY METRICS
(bullet points of the most important numbers)

WHAT NEEDS IMMEDIATE ATTENTION
(numbered list of actions required today)

WHAT IS RECONCILED AND CLOSED
(brief confirmation of what is clean)

RECOMMENDED NEXT STEPS
(numbered list of follow-up actions this week)

Keep the total report under 400 words. Use ₹ for all currency amounts.
"""
    user_msg = f"""AGENT 1 — DATA ANALYST:
{agent1_output}

AGENT 2 — MATCHING AGENT:
{agent2_output}

AGENT 3 — AUDITOR:
{agent3_output}

Please write the final executive reconciliation report."""
    return call_gemini(api_key, system, user_msg)


# ── Run button ────────────────────────────────────────────────────────────────
can_run = invoice_file and payment_file and api_key

if not api_key:
    st.info("👈 Enter your free Gemini API key in the sidebar. [Get one here](https://aistudio.google.com/app/apikey)")
elif not invoice_file or not payment_file:
    st.info("⬆️ Upload both the Invoice CSV and Payments CSV above to continue.")

if can_run:
    if st.button("⚡ Run Reconciliation", type="primary", use_container_width=True):

        invoice_file.seek(0)
        payment_file.seek(0)
        inv_csv = invoice_file.read().decode("utf-8")
        pay_csv = payment_file.read().decode("utf-8")

        st.markdown("## 🤖 Agent Pipeline Running")
        st.markdown("Each agent completes its task and hands off to the next.")
        st.markdown("<hr>", unsafe_allow_html=True)

        results = {}

        # ── Agent 1 ──────────────────────────────────────────────────────────
        with st.status("🔍 Agent 1: Data Analyst — reading and validating your data...", expanded=True) as status:
            st.write("Analysing invoice structure and payment records...")
            time.sleep(0.5)
            try:
                agent1_result = run_agent_1(api_key, inv_csv, pay_csv)
                results["agent1"] = agent1_result
                status.update(label="✅ Agent 1: Data Analyst — complete", state="complete")
            except Exception as e:
                status.update(label="❌ Agent 1 failed", state="error")
                st.error(f"Error: {e}")
                st.stop()

        with st.expander("📊 Agent 1 Output — Data Summary", expanded=False):
            st.markdown(agent1_result)

        # ── Agent 2 ──────────────────────────────────────────────────────────
        with st.status("🔗 Agent 2: Matching Agent — pairing invoices to payments...", expanded=True) as status:
            st.write("Running exact match → fuzzy match → semantic match...")
            time.sleep(0.5)
            try:
                agent2_result = run_agent_2(api_key, inv_csv, pay_csv, agent1_result)
                results["agent2"] = agent2_result
                status.update(label="✅ Agent 2: Matching Agent — complete", state="complete")
            except Exception as e:
                status.update(label="❌ Agent 2 failed", state="error")
                st.error(f"Error: {e}")
                st.stop()

        with st.expander("🔗 Agent 2 Output — Match Results", expanded=False):
            st.markdown(agent2_result)

        # ── Agent 3 ──────────────────────────────────────────────────────────
        with st.status("⚠️ Agent 3: Auditor — flagging risks and anomalies...", expanded=True) as status:
            st.write("Scanning for duplicates, short payments, unknown transactions...")
            time.sleep(0.5)
            try:
                agent3_result = run_agent_3(api_key, agent2_result)
                results["agent3"] = agent3_result
                status.update(label="✅ Agent 3: Auditor — complete", state="complete")
            except Exception as e:
                status.update(label="❌ Agent 3 failed", state="error")
                st.error(f"Error: {e}")
                st.stop()

        with st.expander("⚠️ Agent 3 Output — Audit & Risk Report", expanded=False):
            st.markdown(agent3_result)

        # ── Agent 4 ──────────────────────────────────────────────────────────
        with st.status("📝 Agent 4: Report Writer — generating executive summary...", expanded=True) as status:
            st.write("Synthesising all findings into the final report...")
            time.sleep(0.5)
            try:
                agent4_result = run_agent_4(api_key, agent1_result, agent2_result, agent3_result)
                results["agent4"] = agent4_result
                status.update(label="✅ Agent 4: Report Writer — complete", state="complete")
            except Exception as e:
                status.update(label="❌ Agent 4 failed", state="error")
                st.error(f"Error: {e}")
                st.stop()

        # ── Final report ──────────────────────────────────────────────────────
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("## 📋 Final Reconciliation Report")
        st.markdown(
            f"""<div class="agent-card">
                <div class="agent-header">Agent 4 · Report Writer · Executive Summary</div>
                <div class="agent-output">{agent4_result}</div>
            </div>""",
            unsafe_allow_html=True
        )

        # ── Download button ───────────────────────────────────────────────────
        st.markdown("<hr>", unsafe_allow_html=True)
        full_report = f"""BILLSYNC AI — RECONCILIATION REPORT
Generated by Multi-Agent Pipeline (Google Gemini)
{'='*60}

AGENT 1 — DATA ANALYST
{'-'*40}
{results['agent1']}

AGENT 2 — MATCHING AGENT
{'-'*40}
{results['agent2']}

AGENT 3 — AUDITOR
{'-'*40}
{results['agent3']}

AGENT 4 — EXECUTIVE SUMMARY
{'-'*40}
{results['agent4']}
"""
        st.download_button(
            label="⬇️ Download Full Report",
            data=full_report,
            file_name="reconciliation_report.txt",
            mime="text/plain",
            use_container_width=True
        )

        st.success("🎉 Reconciliation complete! All 4 agents finished successfully.")
