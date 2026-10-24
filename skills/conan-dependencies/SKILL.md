---
name: conan-dependencies
description: Conan 2 in this repository — conanfile.py with layout() and generate(), tool_requires for cmake and ninja, requires for gtest, the three profiles, lockfiles that pin what the recipe leaves as a range, and the measured facts about what conan-center actually has.
---

# Conan 2 dependencies

Conan 2 resolves the C++ build toolchain and libraries for `engine/`. It is installed with
`pipx` at `~/.local/bin/conan`, home `~/.conan2`.

## Measured on this machine (facts, not guesses)

| Fact | Value |
|---|---|
| conan-center `cmake` | **prebuilt** for linux x86_64: 4.4.4, package id `63fead0844576fc02943e16909f08fcdddd6f44b` |
| conan-center `ninja` | **prebuilt** for linux x86_64: 1.13.2 |
| conan-center `gcc/15.2.0` | **no packages** — "This recipe version has no packages"; a `tool_requires` builds GCC from source (hours, several GB) |
| host toolchain | gcc 16.2.1, cmake 4.4.3, ninja 1.13.2, protobuf 36.0 (`protoc`), Go 1.27, Node 26 |

Consequences, and they are not negotiable by convenience:

- The default profile uses the **host gcc** and pins only `cmake` and `ninja` as `tool_requires`.
- A pinned compiler (`tool_requires("gcc/...")`) is the **documented exception**, reached through
  `--profile:build=cross` on the day a reproducible compiler is genuinely required. It is never
  the default, because it turns a 2-minute build into hours.

## `conanfile.py`

```python
from conan import ConanFile
from conan.tools.cmake import cmake_layout, CMakeToolchain, CMakeDeps

class EngineConan(ConanFile):
    name = "z80-engine"
    version = "0.1.0"
    settings = "os", "compiler", "build_type", "arch"
    generators = "CMakeDeps"

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires("gtest/[>=1.14 <2]")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.25 <5]")
        self.tool_requires("ninja/[>=1.11]")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()
```

- `layout()` calls `cmake_layout(self)` so the build folders land where the generated
  `CMakePresets.json` expects them (`build/<build_type>/generators`).
- `generate()` uses `CMakeToolchain` + `CMakeDeps`; the toolchain file writes
  `build/<...>/generators/conan_toolchain.cmake` and `CMakePresets.json` beside it.
- `tool_requires` for build tools and the toolchain; `requires` for libraries. Never put a build
  tool in `requires`.
- Ranges in the recipe (`>=3.25 <5`), exact versions in the lockfile. That is the whole point of
  the split: the recipe states intent, the lock states resolution.
- Never `--build=always` in a documented command; `--build=missing` builds only what has no binary.

## Profiles

```
engine/profiles/linux-gcc-release    compiler=gcc, version=16, libcxx=libstdc++11, build_type=Release
engine/profiles/linux-gcc-debug      same, build_type=Debug, -g -O0
engine/profiles/linux-clang-asan     compiler=clang, build_type=Debug, ASan + UBSan flags
```

Each is a full profile file (`[settings]`, `[conf]`, `[buildenv]` where needed), committed, and
used with `-pr:a=<path>` so host and build use it. No ad-hoc `-s build_type=...` on a command
line: a flag that only exists in a shell history is not reproducible.

## Install

```sh
cd engine
conan install . --output-folder=build --build=missing -pr:a=profiles/linux-gcc-release
cmake --preset conan-release
cmake --build --preset conan-release
ctest --preset conan-release --output-on-failure
```

`conan install` writes `build/CMakePresets.json`; `cmake --preset conan-release` consumes it.
Re-run the install after changing the recipe, a profile or a lockfile — not after changing a
source file.

## Lockfiles

```sh
conan lock create . -pr:a=profiles/linux-gcc-release --lockfile-out=locks/linux-gcc-release.lock
conan lock create . -pr:a=profiles/linux-clang-asan --lockfile-out=locks/linux-clang-asan.lock
conan install . --output-folder=build --build=missing \
  -pr:a=profiles/linux-gcc-release --lockfile=locks/linux-gcc-release.lock
conan lock build-order locks/linux-gcc-release.lock --json=build-order.json
```

- `engine/locks/*.lock` is **committed**. It pins every resolved version and revision, including
  the `cmake` and `ninja` binaries.
- Changing a range in the recipe without refreshing the lock is a defect; refreshing the lock
  without saying why in the commit is a silent upgrade.
- CI and every developer install with `--lockfile=` so the same graph is built everywhere.

## Diagnosing the graph

```sh
conan profile show -pr:a=profiles/linux-gcc-release
conan graph info . -pr:a=profiles/linux-gcc-release          # the full dependency graph
conan graph explain --requires=gtest/1.15.0                 # why this binary (or why none)
conan list 'cmake/*' -r=conancenter                         # what versions have recipes
conan search 'ninja/*' -r=conancenter
conan cache path cmake/4.4.4:63fead0844576fc02943e16909f08fcdddd6f44b
conan cache clean 'cmake/*' --build                         # bounded cache maintenance
conan cache clean '*' --build --temp                        # the whole thing, when it is corrupt
conan audit list --lockfile=locks/linux-gcc-release.lock     # CVEs known for the locked graph
```

`conan graph explain` is the answer to "why is it building this from source": it names the
constraint that eliminated the binary (a setting, a `compiler.cppstd`, an option).

## Binary compatibility

A binary from the cache is reused only when the package id matches: settings (os, arch, compiler
and version, `libcxx`, `build_type`), options, and dependency versions. Consequences:

- Bumping gcc or changing `compiler.cppstd` invalidates every C++ package and triggers a rebuild.
  Say so in the commit that does it.
- `linux-clang-asan` shares no binaries with `linux-gcc-release`; expect the first install to
  resolve and build more.
- A change to `build_type` is a new package id, not an option of the old one.

## Adding a dependency

1. Check the binary actually exists: `conan graph explain --requires=<pkg>/<ver>`.
2. Add a **range** to `requires`/`tool_requires`, never an exact pin.
3. Refresh the lockfiles for all three profiles in the same change.
4. State the licence and the resolved version in the commit body.
5. `conan audit list` on the new lock; a known CVE is a blocker unless the issue says otherwise.

## Gates

```sh
conan install . --output-folder=build --build=missing -pr:a=profiles/linux-gcc-release \
  --lockfile=locks/linux-gcc-release.lock
conan audit list --lockfile=locks/linux-gcc-release.lock
git status --short            # engine/locks must be clean after the install
```