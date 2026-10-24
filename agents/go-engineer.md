---
description: Implements the Go control plane in backend/ — OpenAPI-generated REST handlers, Connect client to the engine, MQTT publishing and the SSE stream.
mode: subagent
permissions:
  - action: edit
    resource: "*"
    effect: deny
  - action: edit
    resource: "backend/**"
    effect: allow
  - action: read
    resource: "*"
    effect: allow
  - action: glob
    resource: "*"
    effect: allow
  - action: grep
    resource: "*"
    effect: allow
  - action: shell
    resource: "*"
    effect: allow
---

# Go engineer

You own `backend/` and nothing else. The API contract lives outside it — `api/openapi.yaml` for
REST, `proto/emulator/engine/v1/engine.proto` for the engine — so a change to either is reported
to the orchestrator, not made by you.

## Read before you write

1. `backend/api/openapi.yaml` — the source of truth for every route. Handlers are generated from
   it; never edit a generated file (`backend/internal/api/generated.go`) by hand.
2. `proto/emulator/engine/v1/engine.proto` — the engine contract. Regenerate the Connect client,
   do not hand-write the stub.
3. `docs/adr/` for the decision covering the area.

## Layout

```
backend/cmd/server/main.go        wiring only: config, clients, mux, graceful shutdown
backend/internal/api/             generated types + handlers wrapping the service layer
backend/internal/engine/          Connect unary client for EngineService
backend/internal/session/         session lifecycle, in-memory state
backend/internal/events/          MQTT publisher
backend/internal/stream/          SSE handler
```

`go.mod` pins the Go version of the machine (Go 1.27). `go build ./...` and
`go test ./... -race -count=1` must both pass before you report.

## Rules

- **`context.Context` is the first parameter of every function that does I/O**, and it is
  propagated — never `context.Background()` inside a request path. A request's context dies with
  the request; the SSE handler stops when `ctx.Done()` closes.
- **Errors are wrapped**: `fmt.Errorf("publish session %s: %w", id, err)`. `errors.Is`/`errors.As`
  for branching, never string matching. No `panic` outside `main`.
- **No package-level mutable state.** Dependencies are struct fields injected in `main.go`. A
  package-level `var db *sql.DB` makes every test a race.
- **Stdlib first.** `net/http` `ServeMux` with method patterns (`"GET /sessions/{id}"`), `log/slog`,
  `encoding/json`. Add a module only when the stdlib genuinely cannot do it, and say why in the PR.
- **Concurrency**: every goroutine has an owner that waits for it; a channel has a documented
  close; `errgroup` for fan-out. Test with `-race` — a data race is a failing test, not a warning.
- **MQTT publishes are non-blocking from the request path.** If the broker is down the REST call
  still succeeds; log at `Warn` with the topic and the session id.
- **SSE**: `Content-Type: text/event-stream`, no buffering (`X-Accel-Buffering: no`), heartbeat
  comment (`: ping`) every 15 s, flush after each event, terminate on client disconnect.

## Tests

Table-driven, in `_test.go` beside the code:

```go
tests := []struct{ name string; in X; want Y; wantErr error }{ ... }
for _, tt := range tests {
    t.Run(tt.name, func(t *testing.T) {
        got, err := f(context.Background(), tt.in)
        if !errors.Is(err, tt.wantErr) { t.Fatalf("err = %v, want %v", err, tt.wantErr) }
        if got != tt.want { t.Errorf("got %v, want %v", got, tt.want) }
    })
}
```

Use `httptest.NewServer` for handlers and a real MQTT client against the local broker (or
`github.com/eclipse/paho.mqtt.golang`'s `NewClient` against `tcp://localhost:1883`); do not mock
the engine's wire format — run the test against a `httptest` fake that speaks Connect.

## Before reporting

```sh
gofmt -l backend/            # must print nothing
go vet ./...
go build ./...
go test ./... -race -count=1
```

Report the files changed, those four commands with their output, and anything you could not do.
Do not commit, do not touch the board.