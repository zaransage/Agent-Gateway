# ADR 0001: GET-Only Transport

## Status
Accepted

## Context
LLM web interfaces (ChatGPT browser, Grok, Claude.ai) accessed via constrained environments
(Bluetooth drive, read-only network proxies) can issue GET requests but not POST.
The gateway must be reachable from these clients without requiring request body support.

## Decision
All gateway endpoints accept GET only. The agent protocol envelope is passed as the `msg`
query parameter, URL-encoded.

## Consequences
- Any LLM that can construct a URL can submit work and poll results.
- Envelope size is constrained by URL length limits (~2KB safe, ~8KB practical).
- Large design documents are passed by reference (`design_ref` URL) not by value.
- No authentication middleware that requires POST (token exchange, OAuth flows) can be used directly.
