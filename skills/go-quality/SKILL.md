---
name: go-quality
description: Go conventions for the backend and toolchain — package layout, context propagation, error wrapping, concurrency ownership, no package-level mutable state, testing with -race and the lint gates.
---

# Go quality

Two Go programs: `backend/` (network service) and `toolchain/` (CLI and libraries). Same rules;
the backend adds the HTTP and MQTT boundaries.

## Layout

```
backend/cmd/server/main.go     wiring only: config, clients, mux, graceful shutdown
backend/internal/api/          generated types + handlers
backend/internal/engine/       Connect client
backend/internal/session/      session lifecycle
backend/internal/events/       MQTT publisher
backend/internal/stream/       SSE handler
toolchain/cmd/romc/main.go     flag parsing, one call into internal
toolchain/internal/{asm,disasm,rom,catalog}
```

`internal/` for anything not meant to be imported. `cmd/` holds `main` and nothing else: no
business logic, no global variable. A package is named for what it provides (`rom`, not `romutils`).

## Context

- `ctx context.Context` is the **first parameter** of every function that does I/O or can block,
  and it is propagated. `context.Background()` appears only in `main` and tests.
- `context.TODO()` does not ship.
- The SSE handler and every `http.Handler` stop when `r.Context().Done()` closes.
- `http.NewRequestWithContext`, `exec.CommandContext`, the MQTT publish path: all take the caller's
  context.

## Errors

```go
if err != nil {
    return fmt.Errorf("load rom %s: %w", name, err)
}
```

- Wrap with `%w`; branch with `errors.Is`/`errors.As`; never match on strings.
- Sentinel errors at the package boundary (`var ErrNotFound = errors.New("not found")`).
- No `panic` outside `main`; no `log.Fatal` outside `main`; no swallowed error (`_ =` needs a
  comment saying why it cannot fail or why it is safe).
- One error per failure, named for what the caller can do about it.

## State and concurrency

- **No package-level mutable state.** Dependencies are struct fields injected in `main`. A global
  `var db *sql.DB` makes every test a race and every package a singleton.
- Every goroutine has an owner that waits for it (`errgroup.Group` for fan-out, `sync.WaitGroup`
  otherwise). A channel has a documented close and a single sender.
- Shared state behind a `sync.Mutex` or confined to one goroutine; `sync/atomic` for counters.
- `time.After` in a loop is a leak — use `time.NewTicker` and `defer ticker.Stop()`.
- An MQTT publish from a request path is non-blocking: a broker outage must not fail the REST call.
  Log at `Warn` with the topic and session id.

## Errors at the edge

```go
func (h *Handler) create(w http.ResponseWriter, r *http.Request) {
    r.Body = http.MaxBytesReader(w, r.Body, 1<<20)
    // decode, validate, call the service
    // error envelope: {"error":{"code":"invalid_request","message":"..."}}
}
```

Status codes are the contract: 400 invalid input, 404 unknown id, 409 conflict, 422 semantic
violation, 500 only for a bug. A 500 body never carries the internal error text.

## Tests

- Table-driven with `t.Run` per case, in `_test.go` beside the code.
- `-race -count=1` always. A data race is a failing test.
- `httptest.NewServer` for handlers; `testdata/` for fixtures; a real broker or an in-process fake
  for MQTT.
- Do **not** mock the engine's Connect wire format or the `.rom` layout — those are the contract.
- Fuzz the parsers (`.rom`, any byte input): `go test -fuzz=FuzzROMReader -fuzztime=30s`.

## Gates

```sh
gofmt -l backend/ toolchain/    # must print nothing
go vet ./...
go build ./...
go test ./... -race -count=1
golangci-lint run               # if configured; otherwise say it was not run
go test ./... -coverprofile=cover.out && go tool cover -func=cover.out
```

Coverage gate: 80 % per module. Add a module to `go.mod` only when the stdlib cannot do the job,
pin it in `go.sum`, and name the reason in the commit body.