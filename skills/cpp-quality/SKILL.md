---
name: cpp-quality
description: C++20 conventions that survive a review — ownership and RAII, errors without exceptions where they cannot afford them, ABI and const-correctness, a CMake target layout, sanitizers, warnings as errors, and determinism.
---

# C++ quality

## Ownership

- **RAII, always.** A resource is a constructor's job and a destructor's, never a comment in a
  `close()` someone must remember. `std::unique_ptr` for ownership, `std::shared_ptr` only when the
  lifetime is genuinely shared, raw pointers and references for borrowing.
- **A function that does not own what it takes does not delete it.** `T*` and `T&` mean "borrowed,
  outlives this call" and the signature says so.
- **`const` is the default**: `const` methods, `const&` parameters, `constexpr` for what is known at
  compile time. A mutable member is a design decision and gets a comment.
- **Five special members out loud.** If a type owns something, say which of the copy/move operations
  exist; `= delete` the ones that cannot be right.
- **No naked `new`.** No `malloc` outside an allocator.

## Errors

- **Pick one policy per layer and write it down**: exceptions at the API boundary, error codes or
  `std::optional`/`std::expected` in a hot path, `noexcept` where a throw would be a lie.
- **A function that can fail says how** — return type, `[[nodiscard]]`, or a documented precondition.
  Failure that is neither returned nor thrown is a crash waiting for a customer.
- **Validate at the boundary, trust inside it.** A parser validates untrusted input once; the code
  behind it does not re-check the same invariant.
- **No exceptions in a destructor, no exceptions across a C ABI**, no exception used for control flow.

## The shape of the code

- **Small translation units, one responsibility per header.** A header includes what it uses and
  nothing else; forward declarations before includes where a pointer would do.
- **`[[nodiscard]]`, `[[maybe_unused]]`, `[[likely]]` sparingly and honestly** — each one is a claim
  the compiler will not check for you.
- **No global mutable state.** A singleton is global mutable state with a nicer name; pass what is
  needed, or own it in a context object.
- **Names say the unit**: `_tstates`, `_bytes`, `_hz`. A number without a unit is a bug in waiting.
- **Signed/unsigned and narrowing**: `std::size_t` for sizes, explicit casts where a width changes,
  `-Wconversion` on.

## The build

- **Targets, not a soup of files.** A library per concern, an executable that links them, tests as a
  target of their own. `target_*` commands, never `include_directories` at the top.
- **The compiler is the project's, not the host's.** Whatever installs the toolchain owns the
  compiler, and a check fails the build when it resolves another.
- **Warnings as errors** at the project's level, and the level is in the build file, not in a
  contributor's memory.
- **Reproducible**: pinned versions, no date or path baked into a binary, no uninitialised read.
- **Sanitizers are a build flag**, not a separate project: ASan+UBSan in CI, TSan where threads exist.

## Tests

- One test file per unit, named for the family it covers.
- **Assert on values, with the unit and the source of the expected number beside it.** A test that
  asserts "it did not crash" is a smoke test and is labelled as one.
- **A test that cannot fail is not a test**: prove it fails against the defect, keep both runs in the
  pull request.
- Deterministic: no sleep, no wall clock, no ordering assumption that the standard does not give.

## Review checklist

- [ ] Every resource has an owner and a destructor.
- [ ] Every failure path is returned, thrown or terminated — chosen, not accidental.
- [ ] No allocation, lock or `std::function` added to a hot path without a measurement.
- [ ] No new global mutable state.
- [ ] The test would fail if the change were reverted.
- [ ] The build file says what the target needs, and nothing global.
