---
name: connect-rpc
description: The protobuf contract rules and the Connect unary wire details — path, headers, JSON codec, error shape — for the generated Go client and the hand-rolled C++ server, plus backward compatibility.
---

# Connect RPC

The engine is a Connect server; the backend is its client. The contract is
`proto/emulator/engine/v1/engine.proto` and nothing else.

## The contract file

```protobuf
syntax = "proto3";
package emulator.engine.v1;

option go_package = "manu343726/z80-emulator/backend/gen/emulator/engine/v1;enginev1";

service EngineService {
  rpc Reset(ResetRequest) returns (ResetResponse);
  rpc LoadRom(LoadRomRequest) returns (LoadRomResponse);
  rpc Step(StepRequest) returns (StepResponse);
  rpc GetState(GetStateRequest) returns (GetStateResponse);
  rpc SetKey(SetKeyRequest) returns (SetKeyResponse);
}
```

Rules:

- **Unary only.** No streaming RPC in the contract; the state stream is the backend's SSE, not a
  Connect stream. The C++ server cannot cheaply implement bidi streaming and does not have to.
- Package ends in a version: `emulator.engine.v1`. A breaking change is `v2`, never an edit of `v1`.
- Fields are `snake_case`, messages are `PascalCase`, enums are prefixed with the enum name and
  carry a zero value (`STATE_UNSPECIFIED = 0`).
- **Never reuse a field number**, and never renumber. Removal uses `reserved 4;` and
  `reserved "old_name";` — a comment is not a reservation.
- No C++ or Go type leaks into the contract: bytes are `bytes`, time is `int64` epoch millis or a
  `google.protobuf.Timestamp`, flags are named booleans, not a bitmask without a message.
- A field added to the contract is regenerated on **both** sides in the same change:
  `buf generate` (or `protoc --go_out --connect-go_out`) for Go, `protoc --cpp_out` for the C++
  message types — or the C++ side hand-parses the JSON per the message, and then the `.proto` is
  still the source and the test is the guard.

## The Connect unary wire

One endpoint per service, method in the path, HTTP/1.1 POST:

```
POST /emulator.engine.v1.EngineService/Step
Content-Type: application/json
Connect-Protocol-Version: 1

{"tstates": 4}
```

Success is HTTP 200 with the response JSON body and `Content-Type: application/json`. An error is
a non-200 status **with a JSON body**:

```json
{"code": "invalid_argument", "message": "tstates must be positive"}
```

`code` is one of the Connect/protobuf codes (`canceled`, `unknown`, `invalid_argument`,
`deadline_exceeded`, `not_found`, `already_exists`, `permission_denied`, `resource_exhausted`,
`failed_precondition`, `aborted`, `out_of_range`, `unimplemented`, `internal`, `unavailable`,
`data_loss`, `unauthenticated`). The HTTP status carries the class (400, 404, 409, 429, 500, 503)
and the body carries the code; a client reads both.

Additional headers Connect may send and the server must ignore gracefully:
`Connect-Timeout-Ms`, `Connect-Accept-Encoding`, `Connect-Content-Encoding`.

## The hand-rolled C++ unary server

Constraints, because the engine does not take grpc or connect-cpp as a dependency:

- HTTP/1.1 keep-alive, one request per connection at a time, `Content-Length` required; a chunked
  body or an absent length is `invalid_argument`, not a guess.
- The body is bounded (`1 MiB`) and read fully before parsing; `Content-Length` is never trusted as
  an allocation size without the bound.
- The JSON parser is strict: unknown fields are rejected or explicitly documented as ignored, and
  a parse failure returns `invalid_argument` with the byte offset — never a 500 and never a crash.
- One thread per connection is acceptable; the CPU is `const`-guarded by a single mutex, and the
  server never steps the machine on two threads at once.
- `OPTIONS /` returns 204 with the CORS headers the browser needs; the browser talks to the Go
  backend, not to the engine directly, so this is for tooling only.
- Every handler returns `noexcept`-safe code; a `std::bad_alloc` during parsing closes the
  connection with `resource_exhausted`.

## The generated Go client

```go
client := enginev1connect.NewEngineServiceClient(http.DefaultClient, "http://localhost:8080")
ctx, cancel := context.WithTimeout(ctx, 2*time.Second)
defer cancel()
resp, err := client.Step(ctx, connect.NewRequest(&enginev1.StepRequest{Tstates: 4}))
```

- Wrap the transport error with `%w`; surface a `*connect.Error`'s `Code()` as the REST error
  code, never as a 500 for a client mistake.
- The client is created once in `main` and injected; the base URL comes from configuration, not a
  constant.
- A timeout on `Step` is `deadline_exceeded`, not `unavailable`; the REST layer maps it to 504 and
  keeps the session alive.

## Compatibility test

```sh
# the contract's own guard, run against a live engine
curl -sS -X POST http://localhost:8080/emulator.engine.v1.EngineService/GetState \
  -H 'Content-Type: application/json' -H 'Connect-Protocol-Version: 1' -d '{}' \
  -w '\nHTTP %{http_code}\n'
```

The response must carry every field the Go struct expects with the contract's types. A field
renamed in `.proto` without regenerating the Go side is caught by this, not by the compiler.