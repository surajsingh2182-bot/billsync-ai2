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
    .demo-banner {
        background: #fffbeb;
        border: 1.5px solid #f59e0b;
        border-radius: 10px;
        padding: 0.8rem 1.2rem;
        margin-bottom: 1.2rem;
        font-size: 0.88rem;
        color: #92400e;
    }
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
    st.markdown("### ⚙️ Mode")
    mode = st.radio(
        "Select mode",
        ["🎭 Demo Mode (no API key needed)", "🤖 Live Mode (Gemini API)"],
        index=0
    )
    is_demo = mode.startswith("🎭")

    st.markdown("---")

    if not is_demo:
        st.markdown("### 🔑 Gemini API Key")
        api_key = st.text_input(
            "API Key",
            type="password",
            placeholder="AIza...",
            help="Get your free key at aistudio.google.com"
        )
        st.markdown("[👉 Get a free key](https://aistudio.google.com/app/apikey)")
    else:
        api_key = None
        st.info("🎭 Demo Mode uses pre-built realistic responses — no API key needed.")

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


# ── Mock responses ────────────────────────────────────────────────────────────
MOCK_AGENT_1 = """
INVOICE SUMMARY
- Total invoices: 10
- Total value: ₹15,70,500
- Status breakdown: Paid (6), Overdue (2), Sent (2)
- Date range: 05 Jan 2024 – 28 Jan 2024
- Data quality issues: All fields present. INV-006 and INV-010 marked Sent with no payment received yet.

PAYMENT SUMMARY
- Total transactions: 10
- Total value: ₹15,09,000
- Payment modes used: NEFT (5), RTGS (2), UPI (3)
- Date range: 19 Jan 2024 – 10 Feb 2024
- Data quality issues: TXN-8826 and TXN-8830 have no reference number. TXN-8830 payer listed as "Unknown Payer".

DATA READINESS
- Ready for reconciliation: Yes
- Notes: Minor issues with missing references on 2 transactions. These will require fuzzy/semantic matching. Overall data quality is acceptable for reconciliation.
"""

MOCK_AGENT_2 = """
MATCHED PAIRS
| Invoice ID | Customer | Invoice Amount | Transaction ID | Paid Amount | Match Type | Difference |
|------------|----------|---------------|----------------|-------------|------------|------------|
| INV-001 | Tata Consultancy Services | ₹1,25,000 | TXN-8821 | ₹1,25,000 | Exact match | ₹0 |
| INV-002 | Infosys Ltd | ₹87,500 | TXN-8822 | ₹87,500 | Exact match | ₹0 |
| INV-003 | Wipro Technologies | ₹2,10,000 | TXN-8827 | ₹2,10,000 | Exact match | ₹0 |
| INV-004 | HCL Technologies | ₹45,000 | TXN-8823 | ₹45,000 | Exact match | ₹0 |
| INV-005 | Tech Mahindra | ₹95,000 | TXN-8824 | ₹95,000 | Fuzzy match (ref: "inv 005") | ₹0 |
| INV-007 | Bajaj Auto | ₹62,000 | TXN-8825 | ₹61,500 | Exact match | -₹500 (short payment) |
| INV-008 | Mahindra & Mahindra | ₹1,78,000 | TXN-8829 | ₹1,78,000 | Fuzzy match (ref: "INVOICE008") | ₹0 |
| INV-009 | Asian Paints | ₹33,000 | TXN-8826 | ₹33,000 | Semantic match (amount + payer name) | ₹0 |

UNMATCHED INVOICES
| Invoice ID | Customer | Amount | Reason |
|------------|----------|--------|--------|
| INV-006 | Reliance Industries | ₹3,20,000 | No payment transaction found |
| INV-010 | Larsen & Toubro | ₹4,15,000 | No payment transaction found |

UNMATCHED PAYMENTS
| Transaction ID | Payer | Amount | Reason |
|----------------|-------|--------|--------|
| TXN-8828 | TCS Mumbai | ₹1,25,000 | Possible duplicate — INV-001 already matched to TXN-8821 |
| TXN-8830 | Unknown Payer | ₹50,000 | No reference, unknown payer, no matching invoice found |

MATCHING SUMMARY
- Total matched: 8
- Total unmatched invoices: 2
- Total unmatched payments: 2
"""

MOCK_AGENT_3 = """
🚨 HIGH RISK ITEMS
| Issue Type | Invoice/Txn ID | Details | Recommended Action |
|------------|----------------|---------|-------------------|
| Possible Duplicate Payment | TXN-8828 | ₹1,25,000 received from TCS Mumbai — INV-001 was already paid via TXN-8821 on 19 Jan. Same amount, same payer, different date. | Contact TCS Mumbai immediately to confirm. If duplicate, initiate refund of ₹1,25,000. |
| Unknown Transaction | TXN-8830 | ₹50,000 received from "Unknown Payer" with no reference. Cannot be linked to any invoice. | Investigate bank records for sender details. Do not recognise as revenue until source confirmed. |
| Large Unpaid Invoice | INV-010 | ₹4,15,000 due from Larsen & Toubro — no payment received. Due date was 12 Feb 2024. | Escalate to accounts team. Send payment reminder immediately. |

⚠️ MEDIUM RISK ITEMS
| Issue Type | Invoice/Txn ID | Details | Recommended Action |
|------------|----------------|---------|-------------------|
| Short Payment | INV-007 / TXN-8825 | Bajaj Auto paid ₹61,500 against invoice of ₹62,000. Shortfall of ₹500. | Raise a follow-up invoice or debit note for ₹500. |
| Unpaid Invoice | INV-006 | ₹3,20,000 due from Reliance Industries. No payment found. Due date was 02 Feb 2024. | Send payment reminder. Check if PO or approval is pending on their side. |

✅ LOW RISK / INFORMATIONAL
| Issue Type | Details |
|------------|---------|
| Fuzzy matches accepted | INV-005 matched via "inv 005" reference and INV-008 via "INVOICE008" — both amounts agree exactly, low risk. |
| Semantic match used | INV-009 matched to TXN-8826 via amount and payer name — no reference provided but match is confident. |

RISK SUMMARY
- High risk items: 3
- Medium risk items: 2
- Total financial exposure: ₹7,40,000 (unreconciled + duplicate risk)
- Overall reconciliation health: Fair
"""

MOCK_AGENT_4 = """
EXECUTIVE SUMMARY
BillSync AI completed reconciliation of 10 invoices (₹15,70,500) against 10 payment transactions (₹15,09,000). 8 of 10 invoices were successfully matched, but 3 high-risk items require immediate attention — including a likely duplicate payment of ₹1,25,000 and two large unpaid invoices totalling ₹7,35,000.

KEY METRICS
- Invoices reconciled: 8 of 10 (80%)
- Total invoiced: ₹15,70,500
- Total received: ₹15,09,000
- Net shortfall: ₹61,500 (excluding unmatched invoices)
- Unmatched invoice value: ₹7,35,000
- Duplicate payment risk: ₹1,25,000
- Unknown incoming payment: ₹50,000

WHAT NEEDS IMMEDIATE ATTENTION
1. Investigate TXN-8828 (₹1,25,000 from TCS Mumbai) — likely duplicate of TXN-8821. Contact TCS and initiate refund if confirmed.
2. Trace TXN-8830 (₹50,000 from Unknown Payer) — identify sender via bank before booking as income.
3. Chase INV-010 (₹4,15,000 from Larsen & Toubro) — overdue, largest outstanding invoice.
4. Follow up INV-006 (₹3,20,000 from Reliance Industries) — no payment received, past due date.

WHAT IS RECONCILED AND CLOSED
- INV-001, INV-002, INV-003, INV-004, INV-005, INV-007, INV-008, INV-009 are all matched and closed. Total settled: ₹8,35,500.

RECOMMENDED NEXT STEPS
1. Send payment reminders to Reliance Industries and Larsen & Toubro today.
2. Raise a ₹500 debit note to Bajaj Auto for the short payment on INV-007.
3. Resolve the duplicate payment query with TCS within 48 hours.
4. Escalate the unknown ₹50,000 transaction to the finance manager for investigation.
5. Schedule next reconciliation run after all outstanding items are resolved.
"""


# ── Gemini agent functions ────────────────────────────────────────────────────
def call_gemini(api_key, system_prompt, user_message):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=system_prompt
    )
    response = model.generate_content(user_message)
    return response.text


def run_agent_1_live(api_key, inv_csv, pay_csv):
    system = """You are a Data Analyst Agent specialising in financial data.
Analyse the invoice and payment datasets and return a structured summary.

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
    return call_gemini(api_key, system, f"INVOICES:\n{inv_csv}\n\nPAYMENTS:\n{pay_csv}")


def run_agent_2_live(api_key, inv_csv, pay_csv, agent1_output):
    system = """You are a Matching Agent. Match each invoice to its payment using:
1. Exact reference match
2. Fuzzy reference match (e.g. INVOICE008 = INV-008)
3. Amount + payer name similarity
4. UNMATCHED if no match found

Return tables for: MATCHED PAIRS, UNMATCHED INVOICES, UNMATCHED PAYMENTS, MATCHING SUMMARY."""
    return call_gemini(api_key, system, f"INVOICES:\n{inv_csv}\n\nPAYMENTS:\n{pay_csv}\n\nAGENT 1:\n{agent1_output}")


def run_agent_3_live(api_key, agent2_output):
    system = """You are an Auditor Agent. Flag all risks: duplicates, short payments,
overpayments, unknown transactions, overdue invoices.
Return: 🚨 HIGH RISK, ⚠️ MEDIUM RISK, ✅ LOW RISK tables, and RISK SUMMARY."""
    return call_gemini(api_key, system, f"MATCHING RESULTS:\n{agent2_output}")


def run_agent_4_live(api_key, a1, a2, a3):
    system = """You are a Report Writer. Write a concise executive summary under 400 words.
Sections: EXECUTIVE SUMMARY, KEY METRICS, WHAT NEEDS IMMEDIATE ATTENTION,
WHAT IS RECONCILED AND CLOSED, RECOMMENDED NEXT STEPS. Use ₹ for currency."""
    return call_gemini(api_key, system, f"AGENT 1:\n{a1}\n\nAGENT 2:\n{a2}\n\nAGENT 3:\n{a3}")


# ── Run button ────────────────────────────────────────────────────────────────
can_run = invoice_file and payment_file and (is_demo or api_key)

if not invoice_file or not payment_file:
    st.info("⬆️ Upload both the Invoice CSV and Payments CSV above to continue.")
elif not is_demo and not api_key:
    st.info("👈 Enter your Gemini API key in the sidebar, or switch to Demo Mode.")

if can_run:
    if st.button("⚡ Run Reconciliation", type="primary", use_container_width=True):

        if is_demo:
            st.markdown("""
<div class="demo-banner">
🎭 <strong>Demo Mode</strong> — Showing pre-built realistic agent responses based on the sample dataset.
Switch to Live Mode in the sidebar to use real AI with a Gemini API key.
</div>""", unsafe_allow_html=True)

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
            if is_demo:
                time.sleep(2)
                agent1_result = MOCK_AGENT_1
            else:
                try:
                    agent1_result = run_agent_1_live(api_key, inv_csv, pay_csv)
                except Exception as e:
                    status.update(label="❌ Agent 1 failed", state="error")
                    st.error(f"Error: {e}")
                    st.stop()
            results["agent1"] = agent1_result
            status.update(label="✅ Agent 1: Data Analyst — complete", state="complete")

        with st.expander("📊 Agent 1 Output — Data Summary", expanded=False):
            st.markdown(agent1_result)

        # ── Agent 2 ──────────────────────────────────────────────────────────
        with st.status("🔗 Agent 2: Matching Agent — pairing invoices to payments...", expanded=True) as status:
            st.write("Running exact match → fuzzy match → semantic match...")
            if is_demo:
                time.sleep(2.5)
                agent2_result = MOCK_AGENT_2
            else:
                try:
                    time.sleep(15)
                    agent2_result = run_agent_2_live(api_key, inv_csv, pay_csv, agent1_result)
                except Exception as e:
                    status.update(label="❌ Agent 2 failed", state="error")
                    st.error(f"Error: {e}")
                    st.stop()
            results["agent2"] = agent2_result
            status.update(label="✅ Agent 2: Matching Agent — complete", state="complete")

        with st.expander("🔗 Agent 2 Output — Match Results", expanded=False):
            st.markdown(agent2_result)

        # ── Agent 3 ──────────────────────────────────────────────────────────
        with st.status("⚠️ Agent 3: Auditor — flagging risks and anomalies...", expanded=True) as status:
            st.write("Scanning for duplicates, short payments, unknown transactions...")
            if is_demo:
                time.sleep(2)
                agent3_result = MOCK_AGENT_3
            else:
                try:
                    time.sleep(15)
                    agent3_result = run_agent_3_live(api_key, agent2_result)
                except Exception as e:
                    status.update(label="❌ Agent 3 failed", state="error")
                    st.error(f"Error: {e}")
                    st.stop()
            results["agent3"] = agent3_result
            status.update(label="✅ Agent 3: Auditor — complete", state="complete")

        with st.expander("⚠️ Agent 3 Output — Audit & Risk Report", expanded=False):
            st.markdown(agent3_result)

        # ── Agent 4 ──────────────────────────────────────────────────────────
        with st.status("📝 Agent 4: Report Writer — generating executive summary...", expanded=True) as status:
            st.write("Synthesising all findings into the final report...")
            if is_demo:
                time.sleep(2)
                agent4_result = MOCK_AGENT_4
            else:
                try:
                    time.sleep(15)
                    agent4_result = run_agent_4_live(api_key, agent1_result, agent2_result, agent3_result)
                except Exception as e:
                    status.update(label="❌ Agent 4 failed", state="error")
                    st.error(f"Error: {e}")
                    st.stop()
            results["agent4"] = agent4_result
            status.update(label="✅ Agent 4: Report Writer — complete", state="complete")

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

        # ── Download ──────────────────────────────────────────────────────────
        st.markdown("<hr>", unsafe_allow_html=True)
        full_report = f"""BILLSYNC AI — RECONCILIATION REPORT
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
