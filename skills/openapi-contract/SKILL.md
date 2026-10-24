---
name: openapi-contract
description: OpenAPI-first REST for the Go backend — api/openapi.yaml as the only source of routes and types, the oapi-codegen invocation, request validation, the error envelope, versioning, pagination and the SSE endpoint.
---

# OpenAPI contract

`api/openapi.yaml` is the source of truth for the REST surface. Handlers are generated from it;
a hand-written type that mirrors a generated one is a defect.

## The document

```yaml
openapi: 3.1.0
info: { title: z80-emulator backend, version: 1.0.0 }
servers: [{ url: http://localhost:8081 }]
paths:
  /sessions:
    post:
      operationId: createSession
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/CreateSessionRequest' }
      responses:
        '201': { description: created, content: { application/json: { schema: { $ref: '#/components/schemas/Session' } } } }
        '400': { $ref: '#/components/responses/BadRequest' }
  /sessions/{id}/events:
    get:
      operationId: streamSession
      parameters: [{ name: id, in: path, required: true, schema: { type: string } }]
      responses: { '200': { description: SSE stream, content: { text/event-stream: { schema: { type: string } } } } }
```

Rules:

- **3.1**, not 3.0. `operationId` on every operation — it names the generated Go method and is
  the stable handle in review.
- Every request and response is a `$ref` to `components/schemas`; no anonymous inline object.
- Every operation declares its `4xx`/`5xx` responses, at least via the shared
  `components/responses` entries.
- `additionalProperties: false` on request bodies: an unknown field is a 400, not silently ignored.
- Types are precise: `format: int64` for T-states, `format: uuid` for ids, `enum` for a closed set,
  `nullable`/`type: [string, "null"]` for an optional field.

## Code generation

```sh
oapi-codegen -config cfg.yaml api/openapi.yaml
```

`cfg.yaml`:

```yaml
package: api
generate:
  chi-server: false
  std-http-server: true
  models: true
  client: true
output: backend/internal/api/generated.go
```

- Commit the generated file **and** the config, in the same change as the document.
- Never edit `generated.go`. Regenerate: `go generate ./...` or the `make api` target.
- A new module only when `cfg.yaml` needs it; `oapi-codegen` is pinned in `go.mod`.

## Validation

- Request bodies decode with `http.MaxBytesReader` (1 MiB) and `DisallowUnknownFields`.
- The generated types are validated by a `Validate()` per request, called by the handler wrapper —
  required fields, ranges, enum membership. A missing `name` is a 400 with
  `{"error":{"code":"invalid_request","message":"name is required"}}`, not a nil dereference.
- Path parameters are parsed, not trusted: an id that is not a UUID is a 404 (or 400, but choose
  one and document it in the operation).

## Error envelope

Every non-2xx body is exactly:

```json
{"error": {"code": "invalid_request", "message": "human sentence", "details": [{"field": "name"}]}}
```

`code` is a stable machine string (`invalid_request`, `not_found`, `conflict`, `unavailable`,
`internal`). `message` never carries internal error text; `details` is optional and
structurally typed. 500 means a bug and is logged with the request id.

## Versioning

- The URL carries no version while the project is pre-1.0; `info.version` documents the shape.
- A breaking change bumps `info.version` and lands with the client regenerated in the same change.
  A field is removed only after a release that stopped returning it.
- A deprecated operation carries `deprecated: true` and a `sunset` header on its responses.

## Pagination

Collection endpoints take `limit` (default 20, max 100) and `cursor` (opaque base64 of the last
id), and return `{"items": [...], "next_cursor": "..." | null}`. Offset pagination is not used —
it skips rows when the collection changes under the reader.

## The SSE endpoint

`GET /sessions/{id}/events` is the one non-JSON response:

```
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
X-Accel-Buffering: no

: ping

id: 42
event: state
data: {"pc":4133,"frame":42}

```

- One event per machine state, `event: state`; a heartbeat comment (`: ping`) every 15 s.
- `id` is monotonic per session, so a reconnect can send `Last-Event-ID` and resume.
- The handler returns when `r.Context().Done()` closes; it never holds an unbounded buffer.
- Documented in the spec as `text/event-stream`; the generated server interface carries it, the
  body is written by hand.

## Before reporting

```sh
oapi-codegen -config cfg.yaml api/openapi.yaml   # regenerates without diff
git diff --stat api/openapi.yaml backend/internal/api/generated.go
go build ./... && go test ./... -race -count=1
```

A document change with no regenerated code, or a generated file edited by hand, is a failing
change.