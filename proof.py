"""
PROOF SCRIPT -- run this live if anyone asks "is this really in the library?"

Installs nothing special. Uses llama-index-core straight from PyPI.
Shows that the token_budget control contributed by Jayachander Reddy Kandakatla
(PR #20546, shipped in llama-index-core v0.14.14) is present and enforcing.
"""
import inspect
from unittest.mock import Mock

import llama_index.core as core
from llama_index.core.callbacks.schema import CBEventType, EventPayload
from llama_index.core.callbacks.token_counting import TokenCountingHandler
from llama_index.core.llms import CompletionResponse

LINE = "=" * 74


def banner(t):
    print(f"\n{LINE}\n{t}\n{LINE}")


banner("1. WHICH LIBRARY IS THIS?")
print(f"   llama-index-core version : {core.__version__}")
print(f"   installed from           : {core.__file__}")
print("   (public PyPI package -- nothing vendored, nothing patched)")

banner("2. IS THE CONTRIBUTED CONTROL ACTUALLY IN IT?")
params = list(inspect.signature(TokenCountingHandler.__init__).parameters)
print(f"   TokenCountingHandler accepts : {params}")
print(f"   'token_budget' present       : {'token_budget' in params}")

src = inspect.getsource(TokenCountingHandler)
print(f"   enforcement method present   : {'_check_budget' in src}")

banner("3. DOES IT ACTUALLY STOP ANYTHING?")
tokenizer = Mock(return_value=[1, 2, 3, 4, 5])          # every call = 5 tokens
handler = TokenCountingHandler(tokenizer=tokenizer, token_budget=15)
response = CompletionResponse(text="generated text")

print("   Budget set to 15 tokens. Each exchange costs 10 (5 prompt + 5 completion).\n")

print("   -> Exchange 1 (running total 10 of 15) ...", end=" ")
handler.on_event_end(
    event_type=CBEventType.LLM,
    payload={EventPayload.PROMPT: "input prompt",
             EventPayload.COMPLETION: response},
)
print(f"allowed.  total={handler.total_llm_token_count}")

print("   -> Exchange 2 (would reach 20 of 15) .....", end=" ")
try:
    handler.on_event_end(
        event_type=CBEventType.LLM,
        payload={EventPayload.PROMPT: "input prompt",
                 EventPayload.COMPLETION: response},
    )
    print("NOT STOPPED  <-- unexpected")
except ValueError as e:
    print("BLOCKED")
    print(f"\n      raised -> ValueError: {e}")

banner("4. WHAT THIS MEANS")
print("""   The agent stopped itself. No wrapper, no middleware, no vendor product.
   One constructor argument, inside the framework, enforced by the framework.

   Contributed by : Jayachander Reddy Kandakatla
   Pull request   : run-llama/llama_index #20546
   Merged by      : logan-markewich (LlamaIndex co-founder)
   Shipped in     : llama-index-core v0.14.14, 10 Feb 2026
   Release notes  : "feat(callbacks): add TokenBudgetHandler for cost governance (#20546)"
""")
