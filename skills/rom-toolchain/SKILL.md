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

All integers little endian except the trailing CRC32.

```
offset  size  field
0       4     magic "Z80R"
4       1     version (currently 1)
5       1     flags   bit0: banked, bit1: host module, bits 2-7 reserved and zero
6       2     entry point
8       2     load address (binary and assembly kinds)
10      1     bank count (0 ⇒ flat 64 KiB image, or a single payload for a host module)
11      1     reserved, zero
12      ...   bank table, one 12-byte record per bank, ascending bank index:
              4 bytes offset into the payload
              4 bytes length
              2 bytes bank index
              2 bytes CRC32 of the bank payload
...           payload, banks concatenated in index order
last 4        4  CRC32 (IEEE 802.3, polynomial 0xEDB88320) of every preceding byte,
                stored big endian
```

Rules that make it a contract:

- `len(payload) >= end of the last bank`, `offset + length <= len(payload)`; a violation is an
  error, never a panic or a slice out of range.
- Bank indices are unique and contiguous from 0 when `banked`. Total payload ≤ 64 KiB for a flat
  image unless `banked`; a bank ≤ 16 KiB.
- The whole-file CRC32 covers everything before the last four bytes. Verify **before** parsing the
  bank table.
- `version` unknown ⇒ error naming the version, never a best-effort parse.
- `unsafe` is not allowed in `toolchain/internal/rom`.

## The host-module ABI

A C++ or Go host module exports exactly these `extern "C"` / `//export` symbols; nothing else is
resolved:

```c
uint32_t rom_abi_version(void);          /* must equal 1 */
const char *rom_name(void);              /* NUL-terminated, owned by the module */
int  rom_init(const uint8_t *rom, uint32_t len);
void rom_reset(void);
void rom_step(uint64_t tstates);          /* called once per instruction boundary */
uint8_t rom_io_read(uint16_t port);       /* 0 when the module does not decode it */
void rom_io_write(uint16_t port, uint8_t value);
```

- No exception may cross the boundary: every entry point is `noexcept` / wrapped in
  `defer recover()` that aborts the module and records the failure.
- `rom_abi_version` is checked at load; a mismatch is refused with both versions in the error.
- Loading a host module is **an explicit opt-in** of the operator. Never load one from a downloaded
  ROM by default (see `security-reviewer`).

## The build pipeline

```sh
romc build roms/pong/pong.asm -o build/roms/pong.rom      # assemble and wrap
romc build roms/boot/boot.cpp  -o build/roms/boot.rom     # compile the host module, record .so
romc build roms/hello/hello.bin -o build/roms/hello.rom   # wrap
romc disasm build/roms/pong.rom > build/roms/pong.asm     # back to source
romc catalog list --json                                  # the catalog, for the backend
```

`build/roms/` is build output and is gitignored; `roms/` holds sources and the catalog only.

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