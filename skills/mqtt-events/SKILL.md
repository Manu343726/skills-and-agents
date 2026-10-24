---
name: mqtt-events
description: The emulator event bus — topic taxonomy emulator/<session>/<event>, the JSON payload envelope, QoS and retained state, the no-secrets rule and at-least-once consumers.
---

# MQTT events

MQTT is the backend's outbound event bus: the machine's lifecycle and its state changes are
published so other processes (a TUI, an integration, a second browser tab) can follow a session
without polling the REST API.

## Broker

```sh
# local broker, as the backend connects
mqtt://localhost:1883
```

Credentials come from configuration (`.env`, never committed). The backend connects once in
`main`, subscribes to nothing unless a component needs it, and passes the client into the
publisher as an injected dependency.

## Topic taxonomy

```
emulator/<session>/<event>
```

- `<session>` is the session id, and it is **sanitised**: `[A-Za-z0-9_-]{1,64}`. A value with `/`,
  `+`, `#`, or `..` is rejected at the REST boundary — never concatenated into a topic (see
  `security-reviewer`).
- `<event>` is one of a closed set:

| Topic | Published when | Retained |
|---|---|---|
| `emulator/<session>/created` | the session is created | yes |
| `emulator/<session>/state` | the machine state advances (throttled to ≤ 20 Hz) | no |
| `emulator/<session>/halted` | the CPU halts or the ROM ends | yes |
| `emulator/<session>/error` | the engine returned an error | no |
| `emulator/<session>/deleted` | the session is disposed | yes |

A wildcard consumer uses `emulator/+/created` or `emulator/<session>/#`; never `#` alone on a
shared broker.

## Payload envelope

Every message is UTF-8 JSON with the same envelope:

```json
{
  "id": "0f5c2b1e-4a0e-4a7e-9d38-4f0b2a6c9a11",
  "type": "state",
  "time": "2026-10-24T06:12:44.183Z",
  "session": "abc",
  "data": { "pc": 4133, "sp": 65534, "state": "running", "frame": 42 }
}
```

- `id` is a UUID v4 per message, unique; a consumer deduplicates on it (at-least-once delivery).
- `type` equals the topic's `<event>` segment; a mismatch is a bug.
- `time` is RFC 3339 with milliseconds, UTC.
- `session` repeats the topic segment so the consumer needs no topic parsing.
- `data` is the event's own object; `state` carries `pc`, `sp`, `af..hl`, `frame`, `state`
  (`running`, `halted`, `error`). Never put the whole 64 KiB RAM in a message.

## QoS and retained state

| Event | QoS | Retain | Why |
|---|---|---|---|
| `created` | 1 | yes | a late subscriber learns the session exists |
| `state` | 0 | no | lossy is acceptable; the next frame supersedes it |
| `halted` | 1 | yes | the last known outcome must survive a subscriber restart |
| `error` | 1 | no | an error is an event, not a status |
| `deleted` | 1 | yes | a late subscriber learns not to wait |

A retained message is overwritten by the next retained message on the same topic; `deleted` is the
tombstone. Never retain a per-subscriber or private value.

## Rules

- **No secrets.** No session token, no file path from the operator's machine, no ROM content, no
  personal data. A log line and a message body obey the same rule.
- **Broker outage must not fail a REST call.** The publish is fired and logged at `Warn` with the
  topic and the session id; the session continues.
- **At-least-once**: the consumer deduplicates on the envelope `id`, and treats a repeated message
  as a no-op.
- The publisher owns no goroutine that outlives `main`: close the client on shutdown, after the
  HTTP server has stopped.
- `state` is throttled and coalesced: publishing on every 4-T-state step saturates the broker and
  the SSE stream. One message per frame, sequence from the envelope.

## Verify by hand

```sh
# watch one session for 6 s, 10 messages, with topics
timeout 6 mosquitto_sub -h localhost -t 'emulator/#' -v -C 10

# publish a fake event to prove a consumer handles the envelope
mosquitto_pub -h localhost -t 'emulator/abc/state' \
  -m '{"id":"x","type":"state","time":"2026-10-24T06:12:44.183Z","session":"abc","data":{"pc":0}}'
```

A `state` message missing `id`, `type`, `time` or `session` is a contract violation, tested with a
table of envelope cases in `backend/internal/events`.