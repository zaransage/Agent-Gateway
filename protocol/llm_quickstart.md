# Agent Gateway — LLM Quickstart

You have access to an agent fleet via a REST gateway. All calls are HTTP GET.
Replace `{{GATEWAY}}` with the actual gateway URL before use.

---

## Check the gateway

```
GET {{GATEWAY}}/health
```

Returns: `{"status":"ok","gateway":"agent-gateway/1.0"}`

---

## Ping — see queue state

```
GET {{GATEWAY}}/agent?msg=AGENT%2FAGENT%3Aping+v1%0Afrom%3A+you
```

Returns:
```
AGENT/AGENT:pong v1
gateway: agent-gateway/1.0
projects: ipo_scanner,creepos
queue_depth: 4
agents_active: 1
```

---

## Submit a task

Build the envelope, then URL-encode it:
- Replace newlines with `%0A`
- Replace spaces with `+`
- Replace `:` in field values with `%3A`

**Raw envelope:**
```
AGENT/TASK:submit v1
title: Your task title here
desc: What the agent should do
pri: high
tags: code,backend
project: ipo_scanner
```

**URL-encoded GET:**
```
GET {{GATEWAY}}/agent?msg=AGENT%2FTASK%3Asubmit+v1%0Atitle%3A+Your+task+title+here%0Adesc%3A+What+the+agent+should+do%0Apri%3A+high%0Atags%3A+code%2Cbackend%0Aproject%3A+ipo_scanner
```

Returns:
```
AGENT/TASK:ack v1
id: 012
status: queued
poll: /task/status?id=012&project=ipo_scanner
```

Save the `id` and `project` — you need them to poll.

---

## Poll for result

```
GET {{GATEWAY}}/task/status?id=012&project=ipo_scanner
```

Returns one of:

**Still queued:**
```
AGENT/TASK:result v1
id: 012
project: ipo_scanner
status: queued
title: Your task title here
```

**Agent working:**
```
AGENT/TASK:result v1
id: 012
project: ipo_scanner
status: active
agent: claude-abc123
notes: implementing format flag
```

**Done:**
```
AGENT/TASK:result v1
id: 012
project: ipo_scanner
status: done
agent: claude-abc123
pr: https://github.com/zaransage/IPO-Tracker/pull/42
```

---

## See all tasks

```
GET {{GATEWAY}}/board
```

Returns JSON array. Filter by project:

```
GET {{GATEWAY}}/board?project=creepos
```

---

## Projects available

| Project | What it is |
|---|---|
| `ipo_scanner` | SEC EDGAR IPO pipeline (Python, FastAPI, PostgreSQL) |
| `creepos` | Android space shooter (Godot 4, GDScript) |

---

## Field reference

| Field | Required | Values | Notes |
|---|---|---|---|
| `title` | yes | string | Short task title |
| `desc` | yes | string | What to implement |
| `project` | no | `ipo_scanner`, `creepos` | Defaults to `ipo_scanner` |
| `pri` | no | `high`, `normal`, `low` | Default: `normal` |
| `tags` | no | comma-separated | `code`, `backend`, `gdscript`, `art`, `frontend` |
| `files` | no | comma-separated paths | Files agent should focus on |
| `accept` | no | comma-separated | Expected output formats |

---

## URL-encoding cheat sheet

| Character | Encoded |
|---|---|
| newline | `%0A` |
| space | `+` or `%20` |
| `/` | `%2F` |
| `:` | `%3A` |
| `,` | `%2C` |
