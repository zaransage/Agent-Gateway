# AGENTS.md

Extends the [Agentic-Code-Genotype](https://github.com/zaransage/Agentic-Code-Genotype)
baseline contract. Read that repo's `AGENTS.md` and `AI_CONTRACT.md` first.

## What this service does

`agent-gateway` is a GET-only FastAPI service that bridges LLM web interfaces to the
agent-tasks coordinator fleet. Any LLM that can construct a URL can submit work,
poll status, and read results — no POST, no auth flow, no platform lock-in.

## Protocol

All messages use the [Agent Protocol v1](protocol/v1.md). Learn the envelope format
before making any changes — it is the wire contract between agents.

## Hexagonal layout

```
domain/agent_gateway/core/adaptors/   ← inbound: how callers reach the core (parser, HTTP)
domain/agent_gateway/core/ports/      ← outbound: how core reaches agent-tasks queue
gateway.py                            ← composition root only
```

## Before writing code

1. Read `protocol/v1.md` — understand the envelope format
2. Check `fixtures/raw/agent_protocol/v1/` — real envelope examples
3. Check `fixtures/expected/agent_protocol/v1/` — canonical parsed forms
4. Run tests: `python3 -m unittest discover -s tests -v`
5. Add fixture pair before adding a new envelope variant

## Adding a new verb

1. Add fixture files in `fixtures/raw/` and `fixtures/expected/`
2. Add the verb to `Envelope.SUPPORTED_VERBS` and validation in `__post_init__`
3. Add parser test asserting raw fixture assumptions and canonical output
4. Add the verb to `protocol/v1.md`
5. Update `schemas/rest/v1/envelope.schema.json`
6. Wire the verb into `gateway.py`

## Do not

- Add POST endpoints — GET-only is a hard constraint (ADR 0001)
- Change the envelope format without bumping to v2 — it is a wire contract
- Remove tests
