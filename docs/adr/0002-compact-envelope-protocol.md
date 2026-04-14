# ADR 0002: Compact Envelope Protocol

## Status
Accepted

## Context
Natural language prose between agents costs 400–800 tokens per exchange. Over a fleet of agents
exchanging task descriptions, status updates, and results, this becomes a significant cost and
latency overhead. A structured format that conveys the same intent in 40–60 tokens reduces cost
by an order of magnitude and makes inter-agent exchanges auditable and replayable.

## Decision
Define a versioned envelope format (`AGENT/<verb> v1`) with key-value header fields and an
optional prose body. The format is line-oriented, human-readable, and trivially parseable
without a JSON library.

## Consequences
- Token cost per agent exchange drops ~10x vs prose.
- All inter-agent exchanges are logged as structured records (verb, fields, body).
- The protocol is versionable — `v2` can coexist with `v1` during transition.
- LLMs can produce and parse the format without prompt engineering.
- English prose remains available in the body field for human context when needed.
