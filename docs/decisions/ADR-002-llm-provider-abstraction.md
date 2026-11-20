# ADR-002 — LLM Provider Abstraction

**Date:** 2026-11-20
**Status:** Accepted

## Context

v0.1 uses local Ollama with a Qwen agentic model. Anthropic (Claude) will be added in a later iteration. If graph nodes import `ChatOllama` directly, swapping the provider requires touching every node.

## Decision

All LLM access goes through a single factory function in `src/mentoros/infrastructure/llm/provider.py`. Nodes receive a `BaseChatModel` instance; they never import a provider-specific class.

```
infrastructure/
  llm/
    provider.py     ← get_chat_model() factory, reads LLM_PROVIDER env var
    base.py         ← shared retry + timeout wrapper
```

`get_chat_model()` reads `LLM_PROVIDER` from config:
- `"ollama"` → returns `ChatOllama(model=LLM_MODEL, ...)`
- `"anthropic"` → returns `ChatAnthropic(model=LLM_MODEL, ...)` (added in later iteration)

The wrapper in `base.py` enforces a timeout and bounded retries on every call regardless of provider.

## Consequences

- Swapping provider requires one env var change, no node code changes.
- Tests mock `get_chat_model()` at the factory, not at provider-specific call sites.
- Adding Anthropic requires installing `langchain-anthropic` and one `elif` branch.

## Alternatives rejected

- Injecting provider via LangChain callbacks: more indirection, harder to test.
- LiteLLM as a universal proxy: adds an external dependency and network hop without benefit at this scale.
