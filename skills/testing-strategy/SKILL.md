---
name: testing-strategy
description: What to test at which level for each stack — golden vectors for the Z80, differential testing, coverage gates (engine 90 %, Go 80 %, web 70 %), fuzzing the decoder and the ROM parser, and what must never be mocked.
---

# Testing strategy

Tests are the definition of done. A behaviour with no test is not implemented; a golden file edited
to match new output is a regression disguised as a fix.

## The pyramid, per stack

| Level | Engine | Backend | Toolchain | Web |
|---|---|---|---|---|
| Unit | `z80_tests`, one `*_test.cpp` per unit | table-driven `_test.go` | table-driven + golden files | Vitest component test |
| Integration | `z80_machine` with a real 64 KiB memory | `httptest` handler + Connect fake | `romc build` end to end | component + mocked `EventSource` |
| Contract | Connect unary over HTTP | REST against `api/openapi.yaml` | `.rom` byte layout | generated client types |
| End to end | a known ROM's full run | REST → engine → MQTT → SSE | assemble → load → run | browser against a live backend |

The contract tests exist once and are not duplicated as mocks at every level.

## Coverage gates

| Stack | Gate | Command |
|---|---|---|
| `engine/` | **90 %** of `z80_core` | `ctest` + `gcovr --fail-under-line 90 -r engine` |
| `backend/`, `toolchain/` | **80 %** | `go test ./... -coverprofile=cover.out && go tool cover -func=cover.out` |
| `web/` | **70 %** | `npm test -- --run --coverage` |

Quote the measured number and name the uncovered region. "Coverage is good" is not a measurement;
`go tool cover -func` printing `internal/rom/read.go:61 78.2 %` is.

## Engine — golden vectors

One table row per opcode and per documented/unhandled form:

```cpp
struct Vector {
  const char* name;                 // "DDCB_BIT_7_(IX+0x05)"
  std::array<uint8_t, 4> code;      // bytes, only `len` of them used
  CpuState before;                  // registers, flags, memory at the addresses touched
  CpuState after;                   // registers, all 8 flags including bits 3/5
  int tstates;
};
```

Files by family: `engine/tests/ld_test.cpp`, `alu_test.cpp`, `cb_test.cpp`, `ed_test.cpp`,
`dd_test.cpp`, `interrupt_test.cpp`, `timing_test.cpp`. Every timing-change commit updates
`timing_test.cpp` in the same change and says why in the body.

## Differential testing

Run the same program through this core and a reference (a checked-in trace, or a second core built
behind `-DZ80_DIFFERENTIAL=ON`) and compare the **whole machine state** after every step: registers,
flags, memory image, T-state count. On divergence print the step index, PC, opcode bytes, and both
states. A divergence is a bug in one of them; resolve it with the manual, not by relaxing the test.

## Fuzzing — the two untrusted byte streams

```sh
# The decoder: arbitrary bytes must never crash, loop or read out of bounds.
clang++ -std=c++20 -g -fsanitize=fuzzer,address engine/fuzz/decode_fuzz.cpp engine/src/*.cpp \
  -o build/decode_fuzz && ./build/decode_fuzz -max_total_time=30

# The ROM parser: arbitrary files must return an error, never panic.
go test ./toolchain/internal/rom -fuzz=FuzzROMReader -fuzztime=30s
```

A crash corpus entry is checked in beside a regression test in the same change. A fuzz target that
only calls `noop()` is not a fuzz target.

## What must never be mocked

- **The engine's Connect wire format** — path, headers, JSON body shape.
- **The `.rom` byte layout** — offsets, CRC32, bank table.
- **The MQTT envelope** — `emulator/<session>/<event>` and its JSON shape.
- **The CPU's timing** — a test that produces any T-state count proves nothing.

Those are the contracts. A test that mocks a contract proves the mock works.

## Rules that catch flakiness before review

- No `sleep`; use fake timers, channels, `httptest` servers, or a `require.Eventually` with a bound.
- No test depends on another test's order or on shared package state (that is why package-level
  mutable state is banned).
- No network beyond `localhost`; no test that needs the operator's machine.
- `-race -count=1` for Go, `--run` for Vitest, fresh `ctest` run for the engine. A flaky test is
  run three times and all three results are reported.