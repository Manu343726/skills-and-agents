---
name: web-quality
description: Browser frontend conventions that survive a review — strict TypeScript, one owner per piece of state, a data layer that regenerates instead of hand-writing, canvas and streaming surfaces that degrade honestly, accessibility from the first line, and tests that assert behaviour.
---

# Web quality

## TypeScript

- **`strict` on, and `any` is a finding** — `unknown` plus a narrowing check, or a type that says what
  the value is.
- **Discriminated unions over booleans**: `{ status: "idle" } | { status: "ok"; data: T }`, so an
  impossible state cannot be represented.
- **No non-null assertion on data from outside**; parse at the boundary and hand the typed result in.
- **Generated clients are generated.** An API type written by hand next to the generated one is a
  second contract that will drift.
- **Exhaustive switches** (`never` in the default) for anything that maps a union to UI.

## State

- **One owner of each piece of state.** Data that comes from the server lives in the store, not copied
  into a component's `useState` and then reconciled by hand.
- **Derive, do not duplicate.** A value that can be computed from the store is a selector.
- **Effects are for the outside world** — subscribe, fetch, focus. An effect that computes state from
  state is a render loop with a delay.
- **Subscriptions are cleaned up**, and the cleanup is part of the code that opens them.

## The data layer

- **One module that speaks to the API**, one that speaks to the stream, and components that call them.
  A `fetch` buried in a component is a second place to change when the contract moves.
- **Errors are values in the UI**: loading, empty, failed and stale are states with a rendering, not a
  spinner that never ends.
- **Streams reconnect with backoff and say they are reconnecting**; a silent drop is indistinguishable
  from a frozen picture.
- **Binary or high-rate data is scheduled, not rendered per message**: a buffer ahead of the playhead
  for audio, a frame budget for a canvas, and a documented underrun behaviour.

## Rendering

- **Canvas work is measured**, not assumed: the draw happens at the source's rate, not at React's.
  Keep the draw loop out of the render path.
- **No layout thrash in an animation**, no work per frame that could be done per change.
- **Keyboard input is captured deliberately** (with a modifier or a focus rule), and the page stays
  usable without a mouse.

## Accessibility

- **Every control is reachable and named** when it is written: a real `<button>`, a label, an
  accessible name. `div onClick` is not a control.
- **Focus is visible and managed** — a modal traps it, closing a dialog returns it.
- **Contrast and sizing are part of the definition of done**, not a later pass.

## Tests

- **Vitest + Testing Library, asserting what the user sees**: roles and text, not implementation
  details or CSS classes.
- **A hook or a store gets its own test**; a component that needs five fakes to render is a design
  smell before it is a test problem.
- **The stream and the clock are faked** in tests, and the fake lives beside the setup, not in each
  file.
- **A test must fail if the behaviour is removed** — prove it once and say so in the pull request.

## Review checklist

- [ ] `strict` clean, no new `any`, no hand-written mirror of a generated type.
- [ ] One owner per piece of state; no effect computing state from state.
- [ ] Every failure path renders something a user can act on.
- [ ] New controls are keyboard-reachable and named.
- [ ] The test asserts behaviour and would fail without the change.
