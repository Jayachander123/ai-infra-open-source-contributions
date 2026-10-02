"""
Cost Governance for Agentic AI
Open-source contributions by Jayachander Reddy Kandakatla.

  pip install -r requirements.txt
  streamlit run app.py
"""
import time
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Cost Governance for Agentic AI",
                   page_icon="◷", layout="wide",
                   initial_sidebar_state="collapsed")

COST_PER_STEP = 0.012       # ~3k in / 500 out, GPT-4-class pricing
STEPS_PER_MIN = 30          # a stuck agent retrying about twice a second
HOURLY = COST_PER_STEP * STEPS_PER_MIN * 60
BUDGET_STEPS = 12

st.markdown("""
<style>
 .big {font-size:60px;font-weight:700;line-height:1;margin:0;}
 .mid {font-size:30px;font-weight:700;line-height:1.1;margin:0;}
 .lbl {font-size:11px;letter-spacing:.15em;text-transform:uppercase;
       color:#8b949e;margin-bottom:3px;}
 .red {color:#c0392b;} .grn {color:#1f6f43;} .amb {color:#9a6700;}
 .step{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;
       padding:1px 0;color:#555;}
 .card{border:1px solid #e1e4e8;border-radius:8px;padding:16px 20px;background:#fafbfc;}
 .verify{border:2px solid #1f6f43;border-radius:8px;padding:18px 22px;
         background:#f2f9f5;}
 .quiet{color:#6a737d;font-size:14px;}
 .fn{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:13px;
     font-weight:600;color:#1b1a18;}
</style>""", unsafe_allow_html=True)

st.title("Cost Governance for Agentic AI")
st.markdown('<p class="quiet">Four merged open-source contributions that let teams bound, '
            'observe and price what AI agents consume in production.<br>'
            'Jayachander Reddy Kandakatla</p>', unsafe_allow_html=True)

t0, t1, t2 = st.tabs(["  The contributions  ",
                      "  See it work  ",
                      "  ✓  Verify it yourself  "])

STEPS = [
    "query ledger.variance(period=2026-09)",
    "-> 14 line items returned",
    "query costs.basis(item=*)",
    "-> WARN malformed record ITEM-88213 (null unit_cost)",
    "retry costs.basis(item=ITEM-88213)",
    "-> WARN malformed record ITEM-88213 (null unit_cost)",
    "reasoning: cost basis incomplete, reconciling",
    "query ledger.invoice(item=ITEM-88213)",
    "-> no matching invoice",
    "retry costs.basis(item=ITEM-88213)",
    "-> WARN malformed record ITEM-88213 (null unit_cost)",
    "reasoning: retry with widened window",
]


# ============================================================ CONTRIBUTIONS
with t0:
    st.markdown("""
Production AI agents fail quietly. A malformed record or an ambiguous question sends an
agent into a retry loop: no exception, no alert, the run simply never finishes — while
consuming model capacity the whole time. The cost surfaces on an invoice, by which point
it has been multiplied by every deployment running the same agent.

These four contributions address that at the framework layer, where agents actually run.
""")
    st.dataframe(pd.DataFrame([
        {"Project": "LlamaIndex", "Contribution": "Token-budget enforcement in TokenCountingHandler",
         "PR": "#20546", "Shipped in": "v0.14.14"},
        {"Project": "LlamaIndex", "Contribution": "Google GenAI cleanup and error handling",
         "PR": "#20607", "Shipped in": "v0.14.14"},
        {"Project": "SkyPilot", "Contribution": "Real-time cluster burn-rate metric",
         "PR": "#8683", "Shipped in": "v0.12.0"},
        {"Project": "LiteLLM", "Contribution": "Official model-pricing source metadata",
         "PR": "#20181", "Shipped in": "v1.83.3-stable"},
    ]), hide_index=True, use_container_width=True)

    st.markdown("### What each one does")

    st.markdown('<p class="fn">TokenCountingHandler(tokenizer=..., token_budget=50_000)</p>',
                unsafe_allow_html=True)
    st.markdown("""
Sets a hard token ceiling on an agent run. The handler tracks usage as the agent works,
and the moment cumulative usage passes the ceiling it raises, naming the limit and the
usage that breached it. The run ends there instead of continuing. It is one argument on a
handler most LlamaIndex applications already register, so adding it changes no agent logic.
""")

    st.markdown('<p class="fn">sky_apiserver_total_burn_rate_dollars</p>',
                unsafe_allow_html=True)
    st.markdown("""
A Prometheus gauge on the SkyPilot API server that reports the combined hourly spend rate,
in dollars, of every active cluster. It refreshes every 30 seconds and is scraped like any
other metric, so existing dashboards and alert rules can act on it. It answers *what are we
burning right now* rather than *what did we spend last month*.
""")

    st.markdown('<p class="fn">Google GenAI client cleanup and error handling</p>',
                unsafe_allow_html=True)
    st.markdown("""
Makes failed provider calls terminate cleanly rather than leaving resources open or
cascading into repeated retries — the condition that turns one bad request into a storm
of them.
""")

    st.markdown('<p class="fn">source field on model pricing entries</p>',
                unsafe_allow_html=True)
    st.markdown("""
Attaches a verifiable origin to model cost entries in LiteLLM's pricing registry, linking
each price to the provider's own published announcement. Routing and chargeback are only
as trustworthy as the price data behind them.
""")

    st.markdown('<div class="card">All four were reviewed by each project\'s own maintainers, '
                'merged into the core repositories, and named in official release notes. None is '
                'a product, a wrapper or a licence — any team already running these frameworks '
                'has them.</div>', unsafe_allow_html=True)


# ============================================================ SEE IT WORK
with t1:
    st.markdown("A document-reconciliation agent is asked to explain a cost variance. "
                "It queries a ledger, meets a record with a null unit cost, and retries. "
                "**The same agent, run twice — the only difference is one argument.**")

    go = st.button("Run both", type="primary", key="krun")

    cL, cR = st.columns(2)
    cL.markdown("#### No ceiling")
    cL.caption("TokenCountingHandler(tokenizer=tok)")
    cR.markdown("#### With a ceiling")
    cR.caption("TokenCountingHandler(tokenizer=tok, token_budget=50_000)")

    lA, lB = cL.empty(), cR.empty()
    tA, tB = cL.empty(), cR.empty()
    nA, nB = cL.empty(), cR.empty()

    def panel(slot, rate, steps, spent, cls):
        slot.markdown(
            f'<p class="lbl">Burn rate</p><p class="big {cls}">${rate:,.0f}'
            f'<span style="font-size:22px">/hr</span></p>'
            f'<p class="lbl" style="margin-top:12px">Steps / spent</p>'
            f'<p class="mid {cls}">{steps} &nbsp;·&nbsp; ${spent:,.2f}</p>',
            unsafe_allow_html=True)

    def trace(slot, log, stop=False):
        html = "".join(f'<div class="step">{s}</div>' for s in log[-8:])
        if stop:
            html += ('<div class="step" style="color:#c0392b;font-weight:600">'
                     'ValueError: Token budget exceeded! Limit: 50000, Current: 50412</div>')
        slot.markdown('<p class="lbl">Agent trace</p>' + html, unsafe_allow_html=True)

    if go:
        logA, logB = [], []
        for i in range(1, 61):
            logA.append(STEPS[i-1] if i <= 12 else STEPS[3 + (i % 9)])
            panel(lA, HOURLY*min(1, i/16), i, i*COST_PER_STEP, "red")
            trace(tA, logA)
            if i <= BUDGET_STEPS:
                logB.append(STEPS[i-1])
                panel(lB, HOURLY*min(1, i/16), i, i*COST_PER_STEP, "grn")
                trace(tB, logB, stop=(i == BUDGET_STEPS))
                if i == BUDGET_STEPS:
                    nB.success("**Stopped itself** and reported the limit it hit.")
            time.sleep(0.07)
        nA.error("**Nothing stopped it.** Halted by hand after 60 steps.")
        st.markdown(
            f'<div class="card">Unbounded: <b style="color:#c0392b">${HOURLY:,.0f}/hour</b>, '
            f'continuing. &nbsp;Bounded: stopped at '
            f'<b style="color:#1f6f43">${BUDGET_STEPS*COST_PER_STEP:,.2f}</b>. '
            f'Same agent, same bad record, one argument.</div>', unsafe_allow_html=True)
    else:
        panel(lA, 0, 0, 0, "red"); panel(lB, 0, 0, 0, "grn")
        trace(tA, STEPS[:8]); trace(tB, STEPS[:8])

    st.divider()

    # ---------------- fleet ----------------
    st.markdown("### Across a fleet")
    st.markdown('<p class="quiet">Per-run ceilings bound one agent. '
                '<code>sky_apiserver_total_burn_rate_dollars</code> shows the whole estate: '
                'what is burning now, and what the ceilings are keeping off the invoice.</p>',
                unsafe_allow_html=True)

    n = st.slider("Deployments running agents", 50, 2000, 420, step=10)
    stuck_n = max(1, n // 140)
    window = 60                                     # hours, Friday night to Monday

    unbounded_cost = stuck_n * HOURLY * window
    bounded_cost = stuck_n * BUDGET_STEPS * COST_PER_STEP
    baseline = n * 1.2

    f1, f2, f3, f4 = st.columns(4)
    f1.markdown(f'<p class="lbl">Fleet burn rate, healthy</p>'
                f'<p class="mid">${baseline:,.0f}<span style="font-size:16px">/hr</span></p>',
                unsafe_allow_html=True)
    f2.markdown(f'<p class="lbl">Agents stuck at any time</p>'
                f'<p class="mid amb">{stuck_n}</p>', unsafe_allow_html=True)
    f3.markdown(f'<p class="lbl">Their cost, no ceiling (60h)</p>'
                f'<p class="mid red">${unbounded_cost:,.0f}</p>', unsafe_allow_html=True)
    f4.markdown(f'<p class="lbl">Their cost, with ceiling</p>'
                f'<p class="mid grn">${bounded_cost:,.2f}</p>', unsafe_allow_html=True)

    st.markdown(f'<div class="card">Across <b>{n:,}</b> deployments, a ceiling keeps roughly '
                f'<b style="color:#1f6f43">${unbounded_cost - bounded_cost:,.0f}</b> off a single '
                f'weekend\'s invoice — and the gauge is what tells you it happened at all, '
                f'rather than finding out a month later.</div>', unsafe_allow_html=True)

    chart = pd.DataFrame({
        "No ceiling": [stuck_n * HOURLY * h for h in range(0, window + 1, 5)],
        "With ceiling": [bounded_cost] * len(range(0, window + 1, 5)),
    }, index=[f"{h}h" for h in range(0, window + 1, 5)])
    st.line_chart(chart, height=220)

    with st.expander("Cost assumptions"):
        st.markdown(f"""
| Assumption | Value |
|---|---|
| Cost per agent reasoning step | ${COST_PER_STEP:.3f} (~3k in / 500 out, GPT-4-class) |
| Steps per minute, stuck agent | {STEPS_PER_MIN} |
| Ceiling halts the run at | {BUDGET_STEPS} steps |
| Window | {window} hours |
| Agents stuck at any time | 1 per 140 deployments |

Substitute your own model mix, rates and failure frequency. The shape does not change.
""")


# ============================================================ VERIFY
with t2:
    st.markdown('<div class="verify"><b style="font-size:17px">This tab is not a simulation.</b>'
                '<br><span class="quiet">The other tabs model costs from published pricing. '
                'Everything below runs against the <code>llama-index-core</code> package '
                'installed on this machine, from public PyPI. Press the button and watch the '
                'contributed control refuse a run.</span></div>', unsafe_allow_html=True)
    st.markdown("")

    import inspect as _i
    from unittest.mock import Mock as _M
    import llama_index.core as _core
    from llama_index.core.callbacks.schema import CBEventType, EventPayload
    from llama_index.core.callbacks.token_counting import TokenCountingHandler
    from llama_index.core.llms import CompletionResponse

    params = list(_i.signature(TokenCountingHandler.__init__).parameters)
    v1, v2, v3 = st.columns(3)
    v1.markdown(f'<p class="lbl">Package</p><p class="step" style="font-size:15px">'
                f'llama-index-core <b>{_core.__version__}</b></p>', unsafe_allow_html=True)
    v2.markdown('<p class="lbl">Source</p><p class="step" style="font-size:15px">'
                'public PyPI, not vendored</p>', unsafe_allow_html=True)
    v3.markdown(f'<p class="lbl">token_budget in signature</p>'
                f'<p class="step" style="font-size:15px"><b>'
                f'{"yes" if "token_budget" in params else "NO"}</b></p>', unsafe_allow_html=True)
    st.caption(f"TokenCountingHandler.__init__{tuple(params)}")

    st.markdown("")
    run = st.button("Run both versions against the installed library",
                    type="primary", key="kver")

    BOX = ("<div style='background:#0d1117;border-radius:8px;padding:14px 16px;"
           "font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px;"
           "line-height:1.6;color:#c9d1d9;min-height:235px'>{}</div>")
    wA, wB = st.columns(2)
    wA.markdown("##### Without the contribution")
    wA.caption("TokenCountingHandler(tokenizer=tok)")
    wB.markdown("##### With the contribution")
    wB.caption("TokenCountingHandler(tokenizer=tok, token_budget=15)")
    oA, oB = wA.empty(), wB.empty()
    rA, rB = wA.empty(), wB.empty()

    def exchange(h):
        h.on_event_end(event_type=CBEventType.LLM,
                       payload={EventPayload.PROMPT: "input prompt",
                                EventPayload.COMPLETION: CompletionResponse(text="generated")})

    if run:
        tok = _M(return_value=[1, 2, 3, 4, 5])
        hA = TokenCountingHandler(tokenizer=tok)
        hB = TokenCountingHandler(tokenizer=tok, token_budget=15)
        la = ["<span style='color:#8b949e'>budget: none</span>"]
        lb = ["<span style='color:#8b949e'>budget: 15 tokens</span>"]
        halted = False
        for k in range(1, 7):
            exchange(hA)
            la.append(f"exchange {k} &rarr; total "
                      f"<b style='color:#f0883e'>{hA.total_llm_token_count}</b> tokens")
            oA.markdown(BOX.format("<br>".join(la)), unsafe_allow_html=True)
            if not halted:
                try:
                    exchange(hB)
                    lb.append(f"exchange {k} &rarr; total "
                              f"<b style='color:#3fb950'>{hB.total_llm_token_count}</b> tokens")
                except ValueError as e:
                    halted = True
                    lb.append(f"exchange {k} &rarr; <b style='color:#ff7b72'>REFUSED</b>")
                    lb.append(f"<span style='color:#ff7b72'>ValueError: {e}</span>")
                    lb.append("<span style='color:#8b949e'>run halted by the framework</span>")
            oB.markdown(BOX.format("<br>".join(lb)), unsafe_allow_html=True)
            time.sleep(0.45)
        rA.error(f"Never stopped — {hA.total_llm_token_count} tokens and counting.")
        rB.success("Stopped itself at the ceiling, and said why.")
        st.markdown('<div class="verify" style="margin-top:14px">Same library, same class, same '
                    'tokenizer. The only difference is <code>token_budget</code> — contributed in '
                    '<b>run-llama/llama_index #20546</b>, merged by <b>logan-markewich</b> '
                    '(LlamaIndex co-founder), shipped in <b>v0.14.14</b> on 10 February 2026.'
                    '</div>', unsafe_allow_html=True)
    else:
        oA.markdown(BOX.format("<span style='color:#8b949e'>press the button above</span>"),
                    unsafe_allow_html=True)
        oB.markdown(BOX.format("<span style='color:#8b949e'>press the button above</span>"),
                    unsafe_allow_html=True)

    st.markdown("")
    st.caption("Reproduce without Streamlit:  `pip install llama-index-core && python proof.py`")
