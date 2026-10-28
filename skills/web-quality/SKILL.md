---
name: web-quality
description: Browser frontend conventions that survive a review — strict TypeScript, one owner per piece of state, a data layer that regenerates instead of hand-writing, canvas and streaming surfaces that degrade honestly, accessibility from the first line, tests that assert behaviour, and a change exercised in a real browser before it is called verified.
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
- **And a real browser exercised the change**: § *A real browser exercised the change* — a green unit
  suite is not a verification of a screen.

## A real browser exercised the change

**A unit test does not verify a UI change.** It renders a component with a mocked world and asserts on
its output, and the defects a user reports are precisely the ones that world cannot contain: a control
that is off-screen or unreachable at a real viewport, a panel overlapping its neighbour, a label
wrapping into the next row, an empty state that reads as an error, an interaction that renders and does
nothing, an error in the console while the test's world stayed silent. None of those is a coverage
problem, and no amount of coverage reaches them — they are invisible to every test that never opens a
page.

So the condition on a frontend change is not "it has tests":

- **The change was exercised in a real browser, against a running application** — through the
  project's own end-to-end runner (Playwright where the project runs it), not a mocked tree and not a
  snapshot of the markup. Behaviour **and** appearance: the screen renders its content, the controls
  are visible and reachable at a viewport a user has, the interaction produces the change it claims,
  and the console carries no error. A snapshot asserts the pixels it was handed; it says nothing about
  whether the control can be clicked.
- **Or the change says what was not exercised, and why.** An environment that cannot start a browser
  is a finding with an owner, written in the pull request — never a `skip`, never a silent absence.
  *Covered by unit tests* is the sentence that means nobody looked, and it is worse than the honest
  gap because it reads like a measurement.
- **The end-to-end suite is the map the next agent reads.** Where a screen the change touched has no
  coverage, that is stated: the pull request lists what the run exercised and what it did not, by
  screen. That list is what tells the next person where to look, and the suite is part of what a UI
  change delivers — it grows, it does not borrow.
- **A screenshot is evidence.** A failing assertion captures the page; the run's artefacts — the
  screenshot, the trace, the name of the step that failed — are what a reviewer reads instead of the
  operator's screen. Say where they are. A run whose artefacts nobody can open is a report nobody
  can check.

**This is not a licence to break the gate.** The end-to-end suite is a gate like any other: the
branch's head is green before the pull request is opened (`git-workflow` § *A green head before the
PR*), a red one is a block, and a suite that is red because it cannot start a browser is a finding —
filed and named — not a reason to disable it.

**And it is not a framework advertisement.** No version, no configuration file, no runner chosen
here: the project keeps its own, and this section is the condition that runner has to satisfy. The
name above is the one the operator runs today; the requirement is a real browser driving the change.

## Review checklist

- [ ] `strict` clean, no new `any`, no hand-written mirror of a generated type.
- [ ] One owner per piece of state; no effect computing state from state.
- [ ] Every failure path renders something a user can act on.
- [ ] New controls are keyboard-reachable and named.
- [ ] The change was exercised in a real browser, or the pull request names what was not and why.
- [ ] The test asserts behaviour and would fail without the change.
