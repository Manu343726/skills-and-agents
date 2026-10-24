---
name: openapi-contract
description: OpenAPI-first REST — the document is the only source of routes and types, the server and client are generated from it in the same change, request validation and a single error envelope, versioning that does not break a deployed client, pagination, and streaming that a browser can consume.
---

# OpenAPI-first REST

## The document is the contract

- **`api/openapi.yaml` is the only source of routes, parameters and types.** A handler that accepts a
  field the document does not declare is a second contract, and it will drift.
- **A hand-written type that mirrors a generated one is a defect**, in either language. Regenerate;
  never patch the generated file.
- **One change, both sides**: the document, the generated server interfaces, the generated client,
  and the code that uses them. A contract change that lands half-way is an outage waiting for a
  deploy order.

## Generating

```sh
# server: types and handlers from the document
oapi-codegen -config <project's config> api/openapi.yaml

# client: the same document, the frontend's language
npm run gen:api      # or the project's generator script
```

- **The generator version is pinned** and its invocation is in the repository, so a clone reproduces
  the output byte for byte.
- **Generated files are not hand-edited and not reviewed line by line.** The document and the config
  are what is reviewed.

## Shape

- **Resources in the path, verbs in the method.** `/machines/{id}/roms`, not `/loadRom`.
- **One error envelope**, the same for every failure, with a stable machine-readable code and a human
  message: `{ "code": "not_found", "message": "…", "details": […] }`.
- **Status codes are the protocol**: `201` with `Location` for creation, `204` for a delete, `409` for
  a state conflict, `422` for a body that parsed but cannot be honoured, `400` only for a malformed
  request.
- **Validation happens at the edge**, generated from the schema where possible; the handler receives
  something already valid, and does not repeat the checks.
- **Enums are additive.** A client that does not know a new value must not crash on it — say so in
  the document, and mean it.

## Versioning

- **Additive by default**: a new optional field, a new endpoint, a new enum value. It is not a break.
- **A removal or a rename is a version**, and the old one keeps working until its consumers have
  moved. A `400` for a field the document still declares is a contract bug, not a validation win.
- **Deprecation is announced in the document** (`deprecated: true`), with the replacement named.

## Lists and long responses

- **Cursor pagination** for anything that can grow: `limit`, `cursor`, and a response that carries
  `nextCursor` — a page number over a mutating collection loses rows silently.
- **A default page size and a maximum**, both in the document, because the client will assume them.
- **`ETag`/`If-None-Match`** where a client polls a representation that rarely changes.

## Streaming

- **Server-sent events for one-way streams** (a state, a frame, an event), chunked binary for bulk
  bytes. Both are HTTP/1.1, and both need the document to describe them: the event type, the payload,
  the reconnect behaviour.
- **Backpressure is designed, not discovered**: a slow consumer drops a frame or falls behind and is
  told, rather than growing a buffer until the process dies.
- **The document says what happens on reconnect** — resume from a cursor, or start again — because the
  client has to implement one of them.

## Review checklist

- [ ] Every route and type comes from the document; nothing hand-written mirrors it.
- [ ] The generated server and client are regenerated in this change, deterministically.
- [ ] Errors use the one envelope; no handler invents a shape.
- [ ] The change is additive, or it is a version with its deprecation announced.
- [ ] Validation is at the edge; the handler trusts its input.
- [ ] Lists paginate; streams document their backpressure and their reconnect.
