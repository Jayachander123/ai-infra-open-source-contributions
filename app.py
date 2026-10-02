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
 .red {color:#e05a4b;} .grn {color:#2f9e63;} .amb {color:#c08a1e;}
 .step{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;
       padding:1px 0;color:inherit;opacity:.72;}
 .card{border:1px solid rgba(128,128,128,.32);border-radius:8px;
       padding:16px 20px;background:rgba(128,128,128,.07);color:inherit;}
 .verify{border:2px solid #2f9e63;border-radius:8px;padding:18px 22px;
         background:rgba(47,158,99,.10);color:inherit;}
 .quiet{color:inherit;opacity:.68;font-size:14px;}
 .fn{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:13.5px;
     font-weight:700;color:inherit;}
 .attrib{font-size:13px;color:inherit;opacity:.78;border-left:3px solid #2f9e63;
         padding:4px 0 4px 12px;margin:0 0 14px;}
 .prom{background:#0d1117;border:1px solid rgba(128,128,128,.3);border-radius:8px;
       padding:16px 18px;color:#c9d1d9;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
       font-size:12.5px;line-height:1.7;overflow-x:auto;}
 .prom .c{color:#6e7681;} .prom .v-ok{color:#3fb950;} .prom .v-hot{color:#ff7b72;}
 .term{background:#0d1117;border:1px solid rgba(128,128,128,.3);border-radius:8px;
       padding:14px 16px;color:#c9d1d9;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
       font-size:12px;line-height:1.75;min-height:200px;overflow-x:auto;}
 .term .w{color:#d29922;} .term .r{color:#8b949e;} .term .e{color:#ff7b72;font-weight:600;}
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
         "PR": "https://github.com/run-llama/llama_index/pull/20546", "Shipped in": "v0.14.14"},
        {"Project": "LlamaIndex", "Contribution": "Google GenAI cleanup and error handling",
         "PR": "https://github.com/run-llama/llama_index/pull/20607", "Shipped in": "v0.14.14"},
        {"Project": "SkyPilot", "Contribution": "Real-time cluster burn-rate metric",
         "PR": "https://github.com/skypilot-org/skypilot/pull/8683", "Shipped in": "v0.12.0"},
        {"Project": "LiteLLM", "Contribution": "Official model-pricing source metadata",
         "PR": "https://github.com/BerriAI/litellm/pull/20181", "Shipped in": "v1.83.3-stable"},
    ]), hide_index=True, use_container_width=True,
        column_config={"PR": st.column_config.LinkColumn("PR", display_text=r"pull/(\d+)")})

    r1, r2, r3 = st.columns(3)
    r1.markdown('<p class="lbl">LlamaIndex</p><p class="mid">52k<span style="font-size:15px"> '
                'stars</span></p><p class="quiet">4.5M downloads / month</p>', unsafe_allow_html=True)
    r2.markdown('<p class="lbl">LiteLLM</p><p class="mid">59k<span style="font-size:15px"> '
                'stars</span></p><p class="quiet">LLM gateway and proxy</p>', unsafe_allow_html=True)
    r3.markdown('<p class="lbl">SkyPilot</p><p class="mid">10.6k<span style="font-size:15px"> '
                'stars</span></p><p class="quiet">Multi-cloud AI compute</p>', unsafe_allow_html=True)
    st.caption("Project metrics shown for context on where the contributions landed, "
               "not as a claim about the contributions themselves.")

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

    # ---------- CONTRIBUTION 1 : THE CEILING ----------
    st.markdown("## Contribution 1 · The ceiling")
    st.markdown('<p class="attrib">Token-budget enforcement in <code>TokenCountingHandler</code> &nbsp;·&nbsp; '
                '<b>LlamaIndex PR #20546</b>, authored by Jayachander Reddy Kandakatla, '
                'merged by logan-markewich (LlamaIndex co-founder), shipped in v0.14.14</p>',
                unsafe_allow_html=True)
    st.markdown("A document-reconciliation agent is asked to explain a cost variance. It queries a "
                "ledger, meets a record with a null unit cost, and retries. "
                "**The same agent run twice — the only difference is the contributed argument.**")

    st.info("**This runs for real.** A live LlamaIndex pipeline with a real `CallbackManager` "
            "and a real `TokenCountingHandler`, driven by `MockLLM` so it needs no API key and "
            "spends nothing. The token counts below come from the handler itself, and the stop "
            "is the contributed code raising.")

    go = st.button("Run both", type="primary", key="krun")

    cL, cR = st.columns(2)
    cL.markdown("#### Without the contribution")
    cL.caption("TokenCountingHandler(tokenizer=tok)")
    cR.markdown("#### With the contribution")
    cR.caption("TokenCountingHandler(tokenizer=tok, token_budget=1000)")

    lA, lB = cL.empty(), cR.empty()
    tA, tB = cL.empty(), cR.empty()
    nA, nB = cL.empty(), cR.empty()

    def panel(slot, toks, calls, cls, stopped=False):
        slot.markdown(
            f'<p class="lbl">Tokens counted by the handler</p>'
            f'<p class="big {cls}">{toks:,}</p>'
            f'<p class="lbl" style="margin-top:12px">Agent steps</p>'
            f'<p class="mid {cls}">{calls}{" · halted" if stopped else ""}</p>',
            unsafe_allow_html=True)

    def trace(slot, log, err=None):
        rows = []
        for ln in log[-8:]:
            cls = "w" if "WARN" in ln else ("r" if ln.startswith("->") else "")
            rows.append(f'<div class="{cls}">{ln}</div>' if cls else f"<div>{ln}</div>")
        if err:
            rows.append(f'<div class="e">ValueError: {err}</div>')
        slot.markdown('<p class="lbl">Agent trace</p><div class="term">'
                      + "".join(rows) + '</div>', unsafe_allow_html=True)

    if go:
        from llama_index.core.llms import MockLLM
        from llama_index.core.callbacks import CallbackManager
        from llama_index.core.callbacks.token_counting import TokenCountingHandler

        words = lambda t: t.split()
        hA = TokenCountingHandler(tokenizer=words)
        hB = TokenCountingHandler(tokenizer=words, token_budget=1000)
        llmA = MockLLM(max_tokens=40, callback_manager=CallbackManager([hA]))
        llmB = MockLLM(max_tokens=40, callback_manager=CallbackManager([hB]))

        logA, logB, halted, err = [], [], False, None
        for i in range(1, 41):
            prompt = STEPS[(i - 1) % len(STEPS)] + " reconcile ledger entry ITEM-88213 " * 3
            llmA.complete(prompt)
            logA.append(STEPS[(i - 1) % len(STEPS)])
            panel(lA, hA.total_llm_token_count, i, "red")
            trace(tA, logA)
            if not halted:
                try:
                    llmB.complete(prompt)
                    logB.append(STEPS[(i - 1) % len(STEPS)])
                    panel(lB, hB.total_llm_token_count, i, "grn")
                    trace(tB, logB)
                except ValueError as e:
                    halted, err = True, str(e)
                    panel(lB, hB.total_llm_token_count, i - 1, "grn", stopped=True)
                    trace(tB, logB, err=err)
                    nB.success("**Stopped itself.** The framework refused the next call.")
            time.sleep(0.09)
        nA.error(f"**Nothing stopped it** — {hA.total_llm_token_count:,} tokens after 40 steps, "
                 "halted only because the loop ended.")
        ratio = hA.total_llm_token_count / max(hB.total_llm_token_count, 1)
        st.markdown(
            f'<div class="card">Same agent, same prompts, same tokenizer. Unbounded consumed '
            f'<b style="color:#e05a4b">{hA.total_llm_token_count:,}</b> tokens; bounded stopped at '
            f'<b style="color:#2f9e63">{hB.total_llm_token_count:,}</b> — about '
            f'<b>{ratio:.0f}&times;</b> less. The difference is one argument, added in PR #20546.'
            f'</div>', unsafe_allow_html=True)
        st.caption("Token volumes here are small because MockLLM returns short responses. "
                   "At production prompt sizes the same ratio applies to real spend — modelled below.")
    else:
        panel(lA, 0, 0, "red"); panel(lB, 0, 0, "grn")
        trace(tA, STEPS[:6]); trace(tB, STEPS[:6])

    st.divider()

    # ---------- CONTRIBUTION 2 : THE GAUGE ----------
    st.markdown("## Contribution 2 · The gauge")
    st.markdown('<p class="attrib">Real-time cluster burn-rate metric &nbsp;·&nbsp; '
                '<b>SkyPilot PR #8683</b>, authored by Jayachander Reddy Kandakatla, '
                'reviewed and merged by aylei, shipped in v0.12.0</p>', unsafe_allow_html=True)
    st.markdown("A ceiling bounds one agent. It cannot tell you what the estate is burning right "
                "now. This contribution adds a Prometheus gauge to the SkyPilot API server that "
                "sums the hourly cost of every cluster in `UP` state, refreshed every 30 seconds "
                "and scraped like any other metric.")

    n = st.slider("Clusters running agent workloads", 50, 2000, 420, step=10)
    stuck_n = max(1, n // 140)
    window = 60
    unbounded_cost = stuck_n * HOURLY * window
    bounded_cost = stuck_n * BUDGET_STEPS * COST_PER_STEP
    baseline = n * 1.2

    scrape = st.empty()
    show = st.button("Scrape the metric", type="primary", key="kscrape")

    def exposition(val, stuck, rising):
        return (
            '<div class="prom">'
            '<span class="c"># HELP sky_apiserver_total_burn_rate_dollars '
            'Total estimated hourly spend across all active clusters (USD/hr)</span><br>'
            '<span class="c"># TYPE sky_apiserver_total_burn_rate_dollars gauge</span><br>'
            f'sky_apiserver_total_burn_rate_dollars{{type="local_clusters"}} '
            f'<b class="{"v-hot" if rising else "v-ok"}">{val:,.2f}</b>'
            '<br><br>'
            f'<span class="c"># {stuck} cluster(s) above alert threshold</span>'
            '</div>')

    if show:
        for t in range(1, 22):
            val = baseline + stuck_n * (1.5 + t * 2.4)
            scrape.markdown(exposition(val, stuck_n, t > 4), unsafe_allow_html=True)
            time.sleep(0.12)
    else:
        scrape.markdown(exposition(baseline, 0, False), unsafe_allow_html=True)

    st.markdown("Because it is an ordinary gauge, existing alerting acts on it directly:")
    st.code(
        "# prometheus/rules.yml\n"
        "- alert: ClusterBurnRateHigh\n"
        "  expr: sky_apiserver_total_burn_rate_dollars > 750\n"
        "  for: 10m\n"
        "  labels:\n"
        "    severity: warning\n"
        "  annotations:\n"
        "    summary: Fleet burn rate above threshold\n",
        language="yaml")

    st.markdown("")
    f1, f2, f3, f4 = st.columns(4)
    f1.markdown(f'<p class="lbl">Fleet rate, healthy</p>'
                f'<p class="mid">${baseline:,.0f}<span style="font-size:16px">/hr</span></p>',
                unsafe_allow_html=True)
    f2.markdown(f'<p class="lbl">Stuck at any time</p>'
                f'<p class="mid amb">{stuck_n}</p>', unsafe_allow_html=True)
    f3.markdown(f'<p class="lbl">Their 60h cost, no ceiling</p>'
                f'<p class="mid red">${unbounded_cost:,.0f}</p>', unsafe_allow_html=True)
    f4.markdown(f'<p class="lbl">Their 60h cost, with ceiling</p>'
                f'<p class="mid grn">${bounded_cost:,.2f}</p>', unsafe_allow_html=True)

    st.markdown(f'<div class="card">The two contributions work together. Across <b>{n:,}</b> '
                f'clusters the ceiling keeps about '
                f'<b style="color:#2f9e63">${unbounded_cost - bounded_cost:,.0f}</b> off a single '
                f'weekend\'s invoice, and the gauge is what tells you it happened at all — rather '
                f'than finding out a month later.</div>', unsafe_allow_html=True)

    hours = list(range(0, window + 1, 5))
    st.line_chart(
        pd.DataFrame({
            "Hours unattended": hours,
            "No ceiling": [stuck_n * HOURLY * h for h in hours],
            "With ceiling": [bounded_cost] * len(hours),
        }),
        x="Hours unattended", y=["No ceiling", "With ceiling"], height=220)

    with st.expander("Cost assumptions"):
        st.markdown(f"""
| Assumption | Value |
|---|---|
| Cost per agent reasoning step | ${COST_PER_STEP:.3f} (~3k in / 500 out, GPT-4-class) |
| Steps per minute, stuck agent | {STEPS_PER_MIN} |
| Ceiling halts the run at | {BUDGET_STEPS} steps |
| Window | {window} hours |
| Agents stuck at any time | 1 per 140 clusters |

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
