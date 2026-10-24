---
name: z80-isa
description: The Z80 instruction set an emulator, assembler and disassembler must agree on — registers, flags, prefixes, undocumented behaviour, interrupts and T-state timing, with a compact encoding table in references/instructions.md.
---

# The Z80 ISA

The reference is the Zilog *Z80 CPU User Manual* plus *The Undocumented Z80 Documented*. Where
they disagree with a test, the test is wrong until proven otherwise.

## Registers

| Register | Width | Notes |
|---|---|---|
| `A F` | 8+8 | accumulator, flags |
| `B C D E H L` | 8 each | `(HL)` is a memory operand, not a register |
| `AF BC DE HL` | 16 | pairs; `AF'` `BC'` `DE'` `HL'` behind the shadow latch |
| `IX IY` | 16 | index registers; `IXH`/`IXL`, `IYH`/`IYL` are their halves |
| `SP` | 16 | stack pointer, decrements before a push |
| `PC` | 16 | program counter |
| `I` | 8 | interrupt vector base |
| `R` | 8 | refresh counter: low 7 bits incremented on every M1, bit 7 preserved |
| `IFF1 IFF2` | 1 each | interrupt enable; `IFF2` is the mask for NMI return |

## Flags

`F = S Z 5 H 3 P/V N C` (bit 7 → bit 0). Bits 5 and 3 are the undocumented copies of the result:
they come from the result of the operation, **except** `BIT n,(HL)` and `BIT n,(IX+d)`, whose
bits 3/5 come from the high byte of the effective address. `SCF`/`CCF` set them from `A`.

| Flag | Set when |
|---|---|
| `S` | bit 7 of the result |
| `Z` | the result is zero |
| `H` | carry out of bit 3 (add) / borrow into bit 4 (sub, `CP`) |
| `P/V` | parity of the result (logic/rotate), overflow (arithmetic), `IFF2` (`LD A,I/R`) |
| `N` | last operation was a subtraction (`ADD` clears it, `SUB`/`CP`/`DEC` set it) |
| `C` | carry out / borrow, or the bit shifted out |

`DAA` corrects `A` after `ADD`/`ADC`/`SUB`/`SBC` on packed BCD, using `H`, `N`, `C` — it is not a
decimal add on its own. `CPL` sets `H` and `N`, preserves `C`.

## Prefixes

| Prefix | Effect |
|---|---|
| `CB` | rotate/shift, `BIT`, `RES`, `SET` on `r[z]` or `(HL)`; 8 T (15 with `(HL)`, 12 for `BIT (HL)`) |
| `ED` | block moves, `IN`/`OUT (C)`, 16-bit `ADC`/`SBC`, `NEG`, `RETN`/`RETI`, `IM`, `RRD`/`RLD`, `LD A,I/R` |
| `DD` / `FD` | the same opcode with `HL` replaced by `IX` / `IY`; `(HL)` becomes `(IX+d)` / `(IY+d)` |
| `DDCB` / `FDCB` | `DD CB d op`: a CB operation on `(IX+d)`, four bytes, 23 T (20 for `BIT`) |

A prefix costs 4 T-states and one M1 cycle (so `R` increments). Two prefixes in a row
(`DD DD ...`) — the second is a prefix, only the last counts, and each still costs 4 T.

## Undocumented behaviour, in scope

- `SLL` (`CB 30..37`) shifts left and sets bit 0; same timing as `SLA`.
- `IXH`, `IXL`, `IYH`, `IYL` for `LD`, `INC`, `DEC` and the ALU — only where the encoding has no
  memory operand: `DD 26 n` is `LD IXH,n`, but `DD 36 d n` is `LD (IX+d),n`.
- `DDCB` with `z != 6` writes the result **also** to `r[z]`, not only to `(IX+d)`; `BIT` ignores it.
- `OUT (C),0` (`ED 71`) writes `0` on NMOS and `0xFF` on CMOS; model one and say which.
- `IN (C)` (`ED 70`) sets flags from the byte read, `C` preserved.
- `ED` opcodes not in the table are two-byte `NOP`s.
- `LD A,I` / `LD A,R` take `P/V` from `IFF2`; an interrupt during them clears `P/V` (NMOS).

## Interrupts

| Mode | Entry | Accept |
|---|---|---|
| IM 0 | the byte on the bus is executed, usually `RST n` | 13 T |
| IM 1 | `RST 38h` | 13 T |
| IM 2 | vector = `(I << 8) | (bus & 0xFE)`; read the 16-bit handler from there | 19 T |
| NMI | push `PC`, jump `0x0066`, `IFF1=0`, `IFF2` preserved | 11 T |

On acceptance: `IFF1 = IFF2 = 0`, push `PC` high byte first, `R` increments once (twice for NMI).
`RETN` restores `IFF1` from `IFF2`; `RETI` does the same and is the only visible difference.

**`EI` has a one-instruction delay**: interrupts are not accepted after `EI` until the instruction
after it has executed. `DI` takes effect immediately. `HALT` executes `NOP`s (4 T each, `R`
increments) until an interrupt is accepted; `PC` stays after the `HALT` opcode.

## Timing

Every instruction has a base T-state count; conditions and indexed operands add to it:

- `JR cc` taken 12, not taken 7. `DJNZ` taken 13, not taken 8.
- `CALL cc` taken 17, not taken 10. `RET cc` taken 11, not taken 5.
- Any `(IX+d)`/`(IY+d)` operand costs 8 more than the `(HL)` form: `INC (IX+d)` 23, `LD (IX+d),n`
  19, `ADD A,(IX+d)` 19.
- Block instructions: `LDIR` 21 per repeat / 16 on the last; `CPIR` 21/16; `LDI` 16.

Full per-opcode counts are in `references/instructions.md`; the engine's `timing_test.cpp` is the
authority on disagreements.

## Encoding, for the assembler and the disassembler

The unprefixed opcode decodes as `x = op >> 6`, `y = (op >> 3) & 7`, `z = op & 7`, with
`p = y >> 1`, `q = y & 1`. `r[] = B C D E H L (HL) A`, `rp = BC DE HL SP`, `rp2 = BC DE HL AF`.
The full table, including `CB`, `ED`, `DD`/`FD` and `DDCB`, is in
`references/instructions.md` — use it as data, never as a hand-written switch.

## Accuracy checklist before a CPU change is done

1. A GoogleTest asserts registers, all eight flags (including 3/5), memory and T-states.
2. Documented and undocumented forms of the opcode both covered.
3. `DDCB` result-to-register and `BIT` flags-from-address covered.
4. `EI` delay, `HALT`, IM 0/1/2 and NMI covered by `interrupt_test.cpp`.
5. `R` asserted across a prefix, an interrupt and a block repeat.