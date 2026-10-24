---
name: rom-toolchain
description: The four ROM source kinds, the .rom container format, the host-module ABI, the romc build pipeline and the round-trip guarantee an assembler and disassembler must satisfy.
---

# ROM toolchain

`toolchain/cmd/romc` turns a ROM source into a `.rom` container the engine can load, and turns a
container back into source. The engine **only ever runs bytes**: every other kind is a build input.

## Rule zero

`engine/` never parses `.asm`, `.cpp` or `.go`. It receives the payload through `LoadRom` (Connect)
and executes it. Any parsing of a source kind outside `toolchain/` is a defect.

## The four source kinds

| Kind | Source | Built by | Output | Flags bit | Container |
|---|---|---|---|---|---|
| binary | `roms/<name>/<name>.bin` | `romc build`, wrapped | bytes at the load address | 0 | flat, CRC32 |
| Z80 assembly | `roms/<name>/<name>.asm` | the internal two-pass assembler | bytes | 0 | flat, CRC32 |
| C++ host module | `roms/<name>/<name>.cpp` + `host_api.h` | CMake target in `engine/`, `.so` recorded | shared object | bit 0 set | flat, CRC32 over the manifest |
| Go host module | `roms/<name>/<name>.go`, `package rom` | `go build -buildmode=c-shared` | `.so` + header | bit 0 set | flat, CRC32 over the manifest |

`roms/catalog.yaml` is the index: name, kind, source path, load address, entry point, description,
author, licence. `romc catalog list` reads it; a ROM file that the catalog does not list is not
part of the project.

## The `.rom` container

Little endian throughout. These offsets are the implementation in
`toolchain/internal/rom/format.go`, not a sketch: the engine reads them, so they are a
contract, and `roms/README.md` repeats the table for a human.

```
offset   size  field
0        4     magic "Z80R"
4        2     format version, currently 1
6        2     flags: bit 0 host module, bit 1 checksum present, bits 2-15 reserved (an
               unknown bit is an error, not something to ignore)
8        4     load address
12       4     entry point
16       4     payload length in bytes
20       4     bank count N
24       8*N   bank table: per bank {offset: u32, length: u32}, offsets relative to the
               payload start
24+8*N   4     CRC32 (IEEE, polynomial 0xEDB88320) of the payload, when flags bit 1 is
               set, else 0
...      0-7   zero padding to the next 8-byte boundary
...      ...   the payload, banks concatenated in index order
```

The bank record is **8 bytes**, not 4: `{offset, length}` is two 32-bit fields, so the
checksum lands at `24 + 8*N`. A spec that says `24 + 4*N` is arithmetically impossible
with that record and was the first thing the implementation had to correct.

Rules, each one an error that names its offset — never a panic, never a slice out of
range, never a best-effort parse:

- Magic and version are checked first; an unknown version is refused.
- Reserved flag bits are refused.
- `offset + length` of every bank fits the payload; a bank is at most 16 KiB; a flat
  payload is at most 64 KiB; a container declares at most 256 banks.
- The CRC32 covers the payload only, and it is verified before the bank table is trusted.
- A truncated file is an error at **every** prefix length — which is what the fuzzer
  exercises (over a million executions of the decoder in ten seconds is the bar a
  reader of untrusted ROM files should meet).

## The host-module ABI

A C++ or Go host module exports exactly three `extern "C"` / `//export` symbols, and the
loader resolves nothing else:

```c
uint32_t z80rom_abi_version(void);                  /* must equal 1 */
void     z80rom_init(void);                         /* called once, before any frame */
void     z80rom_frame(uint8_t *pixels, int w, int h); /* gray8, row-major, once a frame */
```

`roms/examples/z80rom.h` is the header a C++ module includes, so the prototypes exist in
one place instead of being repeated per example. The container's flags have bit 0 set and
the payload is a small manifest — ABI version, module file name, entry symbol — that the
engine turns into a `dlopen`.

**What is not implemented yet, and is filed as its own issue:** nothing on the engine side
`dlopen`s the module. The toolchain compiles it, reads its dynamic symbol table to verify
the three exports, and emits the manifest; `roms/README.md` says so in the ABI section. A
skill that promised the engine half worked would be lying, and the next agent would spend
an afternoon on it.

## The build pipeline

These are the commands that run today, with the paths the repository actually has:

```sh
cd toolchain
go run ./cmd/romc build ../roms/examples/hello.asm     # assemble and wrap
go run ./cmd/romc build ../roms/examples/blink.cpp     # compile the host module, record the .so
go run ./cmd/romc build ../roms/examples/hello.bin     # wrap raw bytes
go run ./cmd/romc disasm ../roms/build/hello.rom       # back to source, with bytes and T-states
cd ../roms && go run ../toolchain/cmd/romc catalog verify
```

The default artefact is `roms/build/<name>.rom`. A host module writes `<name>-host.rom` and
`<name>-host.so` beside it, because an assembly and a Go example can share a stem and would
otherwise overwrite each other's container. `roms/build/` is gitignored; `roms/` holds sources and
the catalog only.

`roms/` is its own small Go module with a `replace` to `../toolchain`, which is what makes
`cd roms && go run ../toolchain/cmd/romc …` work as written; without it Go answers "cannot find
main module".

## Round-trip guarantee (the definition of done)

- `assemble(disassemble(bytes)) == bytes`, byte for byte, for **every** opcode and prefix
  combination — a property test over `z80-isa/references/instructions.md`, not a sample.
- `disassemble(assemble(source)) == source` modulo formatting (register case, hex case, whitespace,
  label names). Labels are emitted from jump targets; a `DB` covers an undefined opcode so the
  round trip closes.
- Golden pairs in `toolchain/testdata/`: `<name>.asm` + `<name>.rom`, checked byte for byte.
- The engine executes an assembled program and the disassembled-reassembled one identically: same
  final memory, same total T-states.

## Before reporting

```sh
gofmt -l toolchain/ roms/
go vet ./...
go build ./...
go test ./... -race -count=1
go test ./toolchain/internal/rom -fuzz=FuzzROMReader -fuzztime=30s
```