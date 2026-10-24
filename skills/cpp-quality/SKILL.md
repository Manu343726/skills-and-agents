---
name: cpp-quality
description: C++20 conventions for the emulation core — ownership and RAII, error handling without exceptions in the hot path, ABI stability, the CMake target layout, sanitizers, clang-tidy and deterministic behaviour.
---

# C++ quality

The core is a library that must be fast, deterministic and safe on untrusted input. These rules are
checked in review; a deviation is a finding, not a preference.

## Reuse before you write

**Before implementing a mechanism, name the library that already implements it, and use that
library.** Writing the mechanism instead is a recorded decision with a reason — no maintained
library, a licence that forbids it, a measured cost that rules it out — carried in the commit body.
It is never the default, and "it was quick to write" is not a reason.

- **The standard library before a third-party one**: `<chrono>`, `<random>`, `<filesystem>`,
  `<format>`, `<span>`, `<expected>`, `<string_view>` before a hand-rolled or imported equivalent.
- **Conan before vendoring**: a dependency is a `requires()` in `conanfile.py` with its version,
  its lockfile entry and its licence. No header is pasted into `third_party/` without an ADR.
- **JSON and serialisation**: `google::protobuf::util::JsonStringToMessage` and
  `MessageToJsonString` on the message types generated from `engine.proto`. A hand-written JSON
  codec beside a protobuf schema is a defect, not a shortcut.
- **HTTP**: a maintained HTTP library for the Connect unary server. A hand-written HTTP/1.1 parser
  and serialiser over raw sockets is the same defect — `engine/src/server/http.cpp` was it.
- **Tests**: GoogleTest from Conan (`GTest::gtest_main`), never a bespoke main-and-assert harness.
- **Also in scope**: CLI parsing, configuration, logging and log rotation, retries and backoff,
  assertions and mocking, process supervision, date and time handling, UUIDs, globbing, test
  fixtures. Each of them has a library; find it before you write it.

**Out of scope: domain code.** The Z80 decoder, the assembler and disassembler, the netlist kernel,
the ULA and PSG models are the product. No library supplies them and writing them is the work — this
rule is not "never write code".

In review, a reinvented library is a **`BLOCK`** finding, and the evidence names the library that
should have been used.

## Language and standard

- **C++20**, declared once per target: `target_compile_features(z80_core PUBLIC cxx_std_20)`.
  No compiler-extension dialects (`-std=gnu++20` only if a CMake feature requires it, and say why).
- Warnings on every target, errors on new ones:
  `-Wall -Wextra -Wpedantic -Wconversion -Wshadow -Werror`.
- `clang-format` with the repository `.clang-format`; formatting is not a review topic.

## Ownership

- **RAII for every resource.** `std::array`, `std::span`, `std::string_view`, `std::unique_ptr`.
  No `new`, no `delete`, no owning raw pointer, no `malloc`.
- A function that does not own takes `T&` or `std::span<T>`; a function that observes only takes
  `const T&`. `std::shared_ptr` only where lifetime is genuinely shared, never as a default.
- `z80_core` and `z80_machine` allocate at construction. After `reset()` they may not allocate.

## Errors

- **No exception may leave the hot path** (`step()`, memory read/write, interrupt dispatch). Those
  functions are `noexcept`. An invalid state is a bug caught by an assertion or a test, not a throw.
- Fallible setup (`load_rom`, `open_server`, `parse_header`) returns `std::expected<T, E>` (C++23) or
  a documented `bool`/`std::error_code` pair while on C++20. Choose one per module and say it.
- Never `catch (...)` silently. A catch clause that does not rethrow must log and convert at a
  documented boundary, and that boundary is tested.

## The hot path

- No allocation, no `std::function` indirect call, no virtual dispatch per instruction in `step()`.
  Dispatch is a table of function pointers or a `switch` the compiler turns into a jump table —
  measure with `perf stat` before claiming either is faster.
- No wall clock, no `rand()`, no locale, no `std::cout` in the core. Determinism is a test property:
  the same ROM and input sequence produce the same memory image and the same T-state count.
- `static` mutable state is forbidden in the core; a lookup table is `constexpr` or `inline
  constexpr`.

## CMake targets

| Target | Type | Contents |
|---|---|---|
| `z80_core` | static library | CPU, registers, bus interface, timing. No I/O, no RPC. |
| `z80_machine` | static library | 64 KiB RAM, interrupt wiring, machine loop. Links `z80_core`. |
| `engine_server` | executable | Connect unary server, links `z80_machine`. |
| `z80_tests` | executable | GoogleTest, `engine/tests/*_test.cpp`. |

One `CMakeLists.txt` per directory, `target_sources`/`target_link_libraries` on the target, no
directory-wide `include_directories` or `add_definitions`. Public headers under `engine/include/`,
included as `#include "z80/cpu.hpp"`. Conan supplies `conan_toolchain.cmake` and `CMakeDeps`
targets (`GTest::gtest_main`); do not hardcode include paths.

## Tooling gates

```sh
conan install . --output-folder=build --build=missing -pr:a=profiles/linux-gcc-release
cmake --preset conan-release && cmake --build --preset conan-release
ctest --preset conan-release --output-on-failure
cmake --preset conan-asan && cmake --build --preset conan-asan && ctest --preset conan-asan
clang-tidy -p build engine/src/*.cpp engine/include/**/*.hpp
```

Sanitizers: ASan + UBSan in the `linux-clang-asan` profile; TSan when a thread is introduced (the
core is single-threaded by design — the server is not). A sanitizer finding is a failing build.

## ABI stability

- The engine's binary interface to Go is **Connect over HTTP**, not C++. The C++ ABI that matters
  is the one between `z80_core`, `z80_machine` and `engine_server`, and it is rebuilt together —
  so prefer value semantics over pimpl, and do not freeze a layout needlessly.
- The host-module ABI for C++ ROMs is the exception: it is `extern "C"`, versioned in the `.rom`
  header, and documented in `rom-toolchain`. A change there is a contract change.
- `engine.proto` is the wire contract; see `connect-rpc`. Never expose a C++ type in it.

## Checklist

1. Every new behaviour has a GoogleTest with registers, all eight flags, memory and T-states.
2. No allocation or exception added to a `noexcept` function.
3. Sanitizer preset passes.
4. `clang-tidy` adds no new finding.
5. Timing unchanged unless the change is a timing fix with its test updated.