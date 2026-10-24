---
name: web-quality
description: React 19 and strict TypeScript conventions for the emulator frontend — components, zustand state, the REST and SSE data layer, canvas rendering, keyboard input, accessibility and Vitest tests.
---

# Web quality

React 19 + TypeScript strict + Vite + Tailwind, state in zustand, tests in Vitest with Testing
Library. The browser talks to the backend's REST API and one SSE stream per session.

## TypeScript

- `web/tsconfig.json` keeps `strict`, `noUncheckedIndexedAccess`, `noImplicitOverride`,
  `verbatimModuleSyntax`. Do not weaken it to make a build pass.
- **No `any`.** A boundary is `unknown`, then a narrowing guard or a generated type from
  `api/openapi.yaml`. `as` is allowed only for a DOM cast after a `null` check.
- Exported functions state their return type; components do not need one.
- Types come from the contract (`npm run gen:api`), never hand-written duplicates.

## Components

- Function components only; no `React.FC`, no default export for a component that is imported by
  name (`export function Screen(...)`).
- Props as `type Props = { ... }`, readonly where the component does not mutate.
- Server state comes from the API client; UI state (the selected session, the panel layout, the
  ROM catalog filters) lives in a zustand store:

```ts
type MachineState = { session: string | null; frame: number; connect: (id: string) => void };
export const useMachine = create<MachineState>()((set, get) => ({ ... }));
```

- One `useEffect` per concern, with its cleanup. No effect that fetches what the store already
  holds; no `useState` for something another component reads.

## Data layer

- REST through the generated client; a failed request surfaces the error envelope
  `{"error":{"code","message"}}` in the UI, not a blank screen.
- **SSE**: one `EventSource` per session, created in a store action and closed by the same action's
  cleanup (`return () => es.close()`). `onerror` reconnects with capped exponential backoff
  (1 s → 30 s) and stops when the session is deselected. A closed stream must never become a hot
  loop; the backoff is tested with fake timers.
- The canvas redraws in `requestAnimationFrame`, keyed by the frame counter from the stream — never
  once per React render. No allocation inside the draw loop; the palette is cached.
- Keyboard input: one `keydown` listener on `window`, registered on mount and removed on unmount.
  Never swallow `Tab`, `F5`, `Ctrl/Cmd+L`, `Ctrl/Cmd+R`. The mapping (the Z80 matrix) is documented
  in `docs/`.

## Accessibility and style

- Every control has an accessible name: `<label htmlFor>` or `aria-label`. Icon-only buttons always
  carry `aria-label`.
- The canvas has a text alternative that describes the machine state (running, halted, PC, frame).
- Focus is visible (`focus-visible:` ring) and never trapped; modals restore focus on close.
- Tailwind for styling; no inline `style` except dynamic canvas geometry and transformed values.
- Colour is never the only signal (a flag is not just red/green).

## Tests

`web/src/**/*.test.tsx`, Vitest + Testing Library, beside the component:

```tsx
render(<Controls session="abc" />);
await userEvent.click(screen.getByRole("button", { name: /reset/i }));
expect(onReset).toHaveBeenCalledOnce();
```

- Query by role and accessible name, not by CSS class or test id.
- `EventSource` is mocked in `web/src/test/setup.ts`; assert on rendered state after a dispatched
  event, not on store internals.
- Fake timers for the SSE backoff; no `sleep` in a test.
- Coverage gate: 70 %.

## Gates

```sh
npm ci
npm run lint
npx tsc --noEmit
npm test -- --run
npm run build
```

`npm ci` (not `npm install`) so `package-lock.json` is the only source of versions. A dependency
added to `package.json` lands with a refreshed lockfile in the same change.