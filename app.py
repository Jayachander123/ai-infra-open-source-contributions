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

st.markdown("""
<style>
 .big {font-size:76px;font-weight:700;line-height:1;margin:0;}
 .mid {font-size:34px;font-weight:700;line-height:1.1;margin:0;}
 .lbl {font-size:11px;letter-spacing:.15em;text-transform:uppercase;
       color:#8b949e;margin-bottom:4px;}
 .red {color:#c0392b;} .grn {color:#1f6f43;} .amb {color:#9a6700;}
 .step{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px;
       padding:1px 0;color:#555;}
 .card{border:1px solid #e1e4e8;border-radius:8px;padding:16px 20px;background:#fafbfc;}
 .quiet{color:#6a737d;font-size:14px;}
</style>""", unsafe_allow_html=True)

st.title("Cost Governance for Agentic AI")
st.markdown('<p class="quiet">Four merged open-source contributions that let teams bound, '
            'observe and price what AI agents consume in production.<br>'
            'Jayachander Reddy Kandakatla</p>', unsafe_allow_html=True)

t0, t1, t2, t3, t4 = st.tabs([
    "  The contributions  ", "  1 · Unbounded  ", "  2 · With a ceiling  ",
    "  3 · Across a fleet  ", "  4 · Verify it  "])

SCENARIO = ("A document-reconciliation agent is asked to explain a cost variance. "
            "It queries a ledger, meets a record with a null unit cost, and retries.")
STEPS = [
    "query ledger.variance(period=2026-09)",
    "-> 14 line items returned",
    "query costs.basis(item=*)",
    "-> WARN malformed record ITEM-88213 (null unit_cost)",
    "retry costs.basis(item=ITEM-88213)",
    "-> WARN malformed record ITEM-88213 (null unit_cost)",
    "reasoning: cost basis incomplete, attempting reconciliation",
    "query ledger.invoice(item=ITEM-88213)",
    "-> no matching invoice",
    "retry costs.basis(item=ITEM-88213)",
    "-> WARN malformed record ITEM-88213 (null unit_cost)",
    "reasoning: retry with widened window",
]


def readout(col_cost, col_steps, col_log, i, cost, log, cls, rate=True):
    col_cost.markdown(
        f'<p class="lbl">{"Burn rate" if rate else "Cost"}</p>'
        f'<p class="big {cls}">${HOURLY*min(1,(i)/16):,.0f}'
        f'<span style="font-size:24px">/hr</span></p>', unsafe_allow_html=True)
    col_steps.markdown(
        f'<p class="lbl">Steps</p><p class="mid {cls}">{i}</p>'
        f'<p class="lbl" style="margin-top:12px">Spent</p>'
        f'<p class="mid {cls}">${cost:,.2f}</p>', unsafe_allow_html=True)
    col_log.markdown('<p class="lbl">Agent trace</p>' +
                     "".join(f'<div class="step">{s}</div>' for s in log[-9:]),
                     unsafe_allow_html=True)


# ============================================================ CONTRIBUTIONS
with t0:
    st.markdown("""
Production AI agents fail quietly. A malformed record or an ambiguous question sends an
agent into a retry loop: no exception, no alert, the run simply never finishes — while
consuming model capacity the whole time. The cost surfaces on an invoice, by which point
it has been multiplied by every deployment running the same agent.

These four contributions address that at the framework layer, where agents actually run.
""")
    st.markdown("")
    st.dataframe(pd.DataFrame([
        {"Project": "LlamaIndex", "Contribution": "Token-budget enforcement in TokenCountingHandler",
         "PR": "#20546", "Shipped": "v0.14.14", "What it does": "Halts a run that exceeds a token ceiling and reports the limit it hit"},
        {"Project": "LlamaIndex", "Contribution": "Google GenAI cleanup and error handling",
         "PR": "#20607", "Shipped": "v0.14.14", "What it does": "Prevents retry storms from failed provider calls"},
        {"Project": "SkyPilot", "Contribution": "Real-time cluster burn-rate metric",
         "PR": "#8683", "Shipped": "v0.12.0", "What it does": "Prometheus gauge reporting live USD/hour across active clusters"},
        {"Project": "LiteLLM", "Contribution": "Official model-pricing source metadata",
         "PR": "#20181", "Shipped": "stable", "What it does": "Attaches verifiable pricing provenance to model entries"},
    ]), hide_index=True, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.markdown('<p class="lbl">Ceiling</p><p class="quiet">Stop a single run before it '
                'runs away. <code>token_budget</code> in llama-index-core.</p>', unsafe_allow_html=True)
    c2.markdown('<p class="lbl">Gauge</p><p class="quiet">See spend rate across every cluster '
                'as it happens. <code>sky_apiserver_total_burn_rate_dollars</code> in SkyPilot.</p>',
                unsafe_allow_html=True)
    c3.markdown('<p class="lbl">Provenance</p><p class="quiet">Know what each model actually '
                'costs, from an official source. LiteLLM pricing metadata.</p>', unsafe_allow_html=True)

    st.markdown("")
    st.markdown('<div class="card">All four were reviewed by each project\'s own maintainers, '
                'merged into the core repositories, and named in official release notes. None is '
                'a product, a wrapper or a licence — any team already running these frameworks '
                'has them.</div>', unsafe_allow_html=True)

    with st.expander("Scope, stated plainly"):
        st.markdown("""
The token-budget work is **18 lines across one file**: a constructor parameter, a
`_check_budget()` method that raises, and two call sites. `TokenCountingHandler` itself
predates the contribution — what was added is the enforcement inside it.

**Known limits.** Enforcement fires at event boundaries, so it stops the *next* call rather
than one already in flight, and budget state lives in the process. For ceilings that
survive restarts, pair it with the fleet gauge.
""")


# ============================================================ UNBOUNDED
with t1:
    st.markdown(SCENARIO)
    st.caption("No budget configured. This is the default behaviour of most agent deployments.")
    a, b, c = st.columns([1.1, 1, 2.4])
    pa, pb, pc = a.empty(), b.empty(), c.empty()
    chart = st.empty()
    if st.button("Run the agent", type="primary", key="k1"):
        hist, log = [], []
        for i in range(1, 61):
            hist.append(i * COST_PER_STEP)
            log.append(STEPS[i-1] if i <= 12 else STEPS[3 + (i % 9)])
            readout(pa, pb, pc, i, i*COST_PER_STEP, log, "red")
            chart.line_chart(pd.DataFrame({"USD": hist}), height=170)
            time.sleep(0.07)
        st.error("**Nothing stopped it.** The run was halted by hand after 60 steps.")
        st.markdown(f'<div class="card">One agent, one task: <b>${HOURLY:,.0f}/hour</b>. '
                    f'Across 100 deployments doing the same thing: <b>${HOURLY*100:,.0f}/hour</b>. '
                    f'Unnoticed over a 60-hour weekend: <b style="color:#c0392b">'
                    f'${HOURLY*100*60:,.0f}</b>.</div>', unsafe_allow_html=True)


# ============================================================ BOUNDED
with t2:
    st.markdown(SCENARIO)
    st.markdown("Same agent, same record. One argument added to a handler already in use.")
    st.code("""from llama_index.core.callbacks import CallbackManager
from llama_index.core.callbacks.token_counting import TokenCountingHandler

Settings.callback_manager = CallbackManager([
    TokenCountingHandler(tokenizer=tok, token_budget=50_000)   # <-- the contribution
])""", language="python")
    a, b, c = st.columns([1.1, 1, 2.4])
    qa, qb, qc = a.empty(), b.empty(), c.empty()
    chart2 = st.empty()
    if st.button("Run the agent", type="primary", key="k2"):
        hist, log = [], []
        for i in range(1, 13):
            hist.append(i * COST_PER_STEP)
            log.append(STEPS[i-1])
            readout(qa, qb, qc, i, i*COST_PER_STEP, log, "grn")
            chart2.line_chart(pd.DataFrame({"USD": hist}), height=170)
            time.sleep(0.14)
        qc.markdown('<p class="lbl">Agent trace</p>' +
                    "".join(f'<div class="step">{s}</div>' for s in log[-8:]) +
                    '<div class="step" style="color:#c0392b;font-weight:600">'
                    'ValueError: Token budget exceeded! Limit: 50000, Current: 50412</div>',
                    unsafe_allow_html=True)
        st.success("**The agent stopped itself** and reported the limit it hit.")
        st.markdown(f'<div class="card">Halted at <b>${12*COST_PER_STEP:,.2f}</b>. '
                    f'The operator hears it from the agent rather than from an invoice.</div>',
                    unsafe_allow_html=True)


# ============================================================ FLEET
with t3:
    st.markdown("Per-run budgets bound one agent. This is the reading across a fleet.")
    st.markdown('<p class="quiet">Pattern of <code>sky_apiserver_total_burn_rate_dollars</code>, '
                'a Prometheus gauge contributed to SkyPilot (PR #8683, v0.12.0) that reports live '
                'spend rate across all active clusters.</p>', unsafe_allow_html=True)
    n = st.slider("Deployments running agents", 50, 2000, 420, step=10)
    f1, f2, f3 = st.columns(3)
    g1, g2, g3 = f1.empty(), f2.empty(), f3.empty()
    bars = st.empty()
    if st.button("Show live fleet rate", type="primary", key="k3"):
        base = [0.6 + ((i*37) % 120)/100 for i in range(n)]
        stuck = [i for i in (88, 214, 377) if i < n] or [n//3]
        for t in range(1, 24):
            rates = list(base)
            for s in stuck:
                rates[s] = 1.5 + t*2.4
            total = sum(rates)
            g1.markdown(f'<p class="lbl">Fleet burn rate</p><p class="mid">${total:,.0f}'
                        f'<span style="font-size:17px">/hr</span></p>', unsafe_allow_html=True)
            g2.markdown(f'<p class="lbl">Above threshold</p>'
                        f'<p class="mid amb">{len(stuck)}</p>', unsafe_allow_html=True)
            g3.markdown(f'<p class="lbl">If unnoticed for 60h</p>'
                        f'<p class="mid red">${total*60:,.0f}</p>', unsafe_allow_html=True)
            top = sorted(range(n), key=lambda i: -rates[i])[:18]
            bars.bar_chart(pd.DataFrame({"USD/hr": [rates[i] for i in top]},
                                        index=[f"node-{i:04d}" for i in top]), height=230)
            time.sleep(0.11)
        st.warning(f"**{len(stuck)} nodes burning at many times the fleet median.** "
                   "Visible in seconds rather than on next month's invoice.")
        st.markdown('<div class="card">The per-run budget is the circuit breaker. '
                    'The burn-rate gauge is the fuel gauge. Agentic AI at scale needs both.</div>',
                    unsafe_allow_html=True)
    with st.expander("Cost assumptions"):
        st.markdown(f"""
| Assumption | Value |
|---|---|
| Cost per agent reasoning step | ${COST_PER_STEP:.3f} (~3k in / 500 out, GPT-4-class) |
| Steps per minute, stuck agent | {STEPS_PER_MIN} |
| Weekend window | 60 hours |

Substitute your own model mix and rates. The shape of the problem is unchanged.
""")


# ============================================================ VERIFY
with t4:
    st.markdown("Tabs 1 to 3 are a simulation with a published cost model. "
                "**This one is not.** It runs against the library installed on this machine.")

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
    go = st.button("Run both versions against the installed library", type="primary", key="k4")

    BOX = ("<div style='background:#0d1117;border-radius:8px;padding:14px 16px;"
           "font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px;"
           "line-height:1.6;color:#c9d1d9;min-height:235px'>{}</div>")
    cA, cB = st.columns(2)
    cA.markdown("##### Without the contribution")
    cA.caption("TokenCountingHandler(tokenizer=tok)")
    cB.markdown("##### With the contribution")
    cB.caption("TokenCountingHandler(tokenizer=tok, token_budget=15)")
    lA, lB = cA.empty(), cB.empty()
    oA, oB = cA.empty(), cB.empty()

    def exchange(h):
        h.on_event_end(event_type=CBEventType.LLM,
                       payload={EventPayload.PROMPT: "input prompt",
                                EventPayload.COMPLETION: CompletionResponse(text="generated")})

    if go:
        tok = _M(return_value=[1, 2, 3, 4, 5])
        hA = TokenCountingHandler(tokenizer=tok)
        hB = TokenCountingHandler(tokenizer=tok, token_budget=15)
        la = ["<span style='color:#8b949e'>budget: none</span>"]
        lb = ["<span style='color:#8b949e'>budget: 15 tokens</span>"]
        halted = False
        for n_ in range(1, 7):
            exchange(hA)
            la.append(f"exchange {n_} &rarr; total "
                      f"<b style='color:#f0883e'>{hA.total_llm_token_count}</b> tokens")
            lA.markdown(BOX.format("<br>".join(la)), unsafe_allow_html=True)
            if not halted:
                try:
                    exchange(hB)
                    lb.append(f"exchange {n_} &rarr; total "
                              f"<b style='color:#3fb950'>{hB.total_llm_token_count}</b> tokens")
                except ValueError as e:
                    halted = True
                    lb.append(f"exchange {n_} &rarr; <b style='color:#ff7b72'>REFUSED</b>")
                    lb.append(f"<span style='color:#ff7b72'>ValueError: {e}</span>")
                    lb.append("<span style='color:#8b949e'>run halted by the framework</span>")
            lB.markdown(BOX.format("<br>".join(lb)), unsafe_allow_html=True)
            time.sleep(0.45)
        oA.error(f"Never stopped — {hA.total_llm_token_count} tokens and counting.")
        oB.success("Stopped itself at the ceiling, and said why.")
        st.markdown('<div class="card" style="margin-top:14px">Same library, same class, same '
                    'tokenizer. The only difference is <code>token_budget</code> — contributed in '
                    '<b>run-llama/llama_index #20546</b>, merged by <b>logan-markewich</b> '
                    '(LlamaIndex co-founder), shipped in <b>v0.14.14</b> on 10 February 2026.'
                    '</div>', unsafe_allow_html=True)

    st.markdown("")
    st.caption("Reproduce without Streamlit:  `pip install llama-index-core && python proof.py`")
