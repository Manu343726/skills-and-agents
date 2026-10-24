# The Z80 encoding table

Decode an unprefixed opcode as `x = op >> 6`, `y = (op >> 3) & 7`, `z = op & 7`, `p = y >> 1`,
`q = y & 1`. Registers: `r[] = B C D E H L (HL) A`, `rp[] = BC DE HL SP`,
`rp2[] = BC DE HL AF`.

This table is **data**. Generators, the assembler and the disassembler all read it; none of them
grows a hand-written switch beside it.

## Main table (`x = 0`)

| z | q=0 (y) | q=1 (y) | T |
|---|---|---|---|
| 0 | `NOP`; `EX AF,AF'`; `DJNZ d`; `JR d,y=3`; `JR cc[y-4],d` | — | 4/4/13-8/12/12-7 |
| 1 | `LD rp[p],nn` | `ADD HL,rp[p]` | 10 / 11 |
| 2 | `LD (BC),A`; `LD (DE),A`; `LD (nn),HL`; `LD (nn),A` | `LD A,(BC)`; `LD A,(DE)`; `LD HL,(nn)`; `LD A,(nn)` | 7/7/16/13 |
| 3 | `INC rp[p]` | `DEC rp[p]` | 6 |
| 4 | `INC r[y]` | — | 4 (11 for `(HL)`) |
| 5 | `DEC r[y]` | — | 4 (11 for `(HL)`) |
| 6 | `LD r[y],n` | — | 7 (10 for `(HL)`) |
| 7 | `RLCA`,`RRCA`,`RLA`,`RRA`,`DAA`,`CPL`,`SCF`,`CCF` | — | 4 |

## Main table (`x = 1`, 2, 3)

| x | Operation | T |
|---|---|---|
| 1 | `LD r[y],r[z]`; `0x76` is `HALT` | 4 (7 if either is `(HL)`) |
| 2 | `alu[y] A,r[z]` — `ADD ADC SUB SBC AND XOR OR CP` | 4 (7 for `(HL)`) |
| 3 z=0 | `RET cc[y]` | 5 / 11 taken |
| 3 z=1 | `POP rp2[p]` / (`RET`, `EXX`, `JP (HL)`, `LD SP,HL`) | 10 / 4/4/4/6 |
| 3 z=2 | `JP cc[y],nn` | 10 |
| 3 z=3 | `JP nn`; `CB`; `OUT (n),A`; `IN A,(n)`; `EX (SP),HL`; `EX DE,HL`; `DI`; `EI` | 10/4/11/11/19/4/4/4 |
| 3 z=4 | `CALL cc[y],nn` | 10 / 17 taken |
| 3 z=5 | `PUSH rp2[p]` / (`CALL nn`, `DD`, `ED`, `FD`) | 11 / 17/4/4/4 |
| 3 z=6 | `alu[y] A,n` | 7 |
| 3 z=7 | `RST y*8` | 11 |

`cc[] = NZ Z NC C PO PE P M`.

## `CB` prefix

`CB op` costs 8 T (12 for `BIT n,(HL)`, 15 for a rotate/shift on `(HL)`).

| x | Operation | T (register / `(HL)`) |
|---|---|---|
| 0 | `rot[y] r[z]` — `RLC RRC RL RR SLA SRA SLL SRL` | 8 / 15 |
| 1 | `BIT y,r[z]` | 8 / 12 |
| 2 | `RES y,r[z]` | 8 / 15 |
| 3 | `SET y,r[z]` | 8 / 15 |

## `ED` prefix

Every `ED` opcode costs 8 T unless noted. Unlisted `ED` opcodes are two-byte `NOP`s.

| Block | Operation | T |
|---|---|---|
| x=1 z=0 | `IN r[y],(C)` (`y=6` is `IN (C)` with flags) | 12 |
| x=1 z=1 | `OUT (C),r[y]` (`y=6` is `OUT (C),0`) | 12 |
| x=1 z=2 q=0 | `SBC HL,rp[p]` | 15 |
| x=1 z=2 q=1 | `ADC HL,rp[p]` | 15 |
| x=1 z=3 q=0 | `LD (nn),rp[p]` | 20 |
| x=1 z=3 q=1 | `LD rp[p],(nn)` | 20 |
| x=1 z=4 | `NEG` | 8 |
| x=1 z=5 | `RETN` (`y=1` is `RETI`) | 14 |
| x=1 z=6 | `IM im[y]` — `0,0,1,2,0,0,1,2` | 8 |
| x=1 z=7 | `LD I,A`; `LD R,A`; `LD A,I`; `LD A,R`; `RRD`; `RLD`; `NOP`; `NOP` | 9/9/9/9/18/18 |
| x=2 z≤3 y≥4 | block ops, see below | 16–21 |

Block ops: `y=4` `LDI LDD LDIR LDDR`, `y=5` `CPI CPD CPIR CPDR`, `y=6`
`INI IND INIR INDR`, `y=7` `OUTI OUTD OTIR OTDR`. `z=0` non-repeating (`y` even = increment,
odd = decrement), `z=1` the `CPI`/`INI` family, `z=2`/`z=3` the repeating pair; the repeat form is
16 T on the last iteration and 21 T while it repeats.

## `DD` / `FD` prefixes

The bytes after the prefix are decoded by the same tables with these substitutions, and each
prefix byte adds 4 T:

- `HL` → `IX` (DD) / `IY` (FD); `(HL)` → `(IX+d)` / `(IY+d)` — one extra displacement byte.
- `LD r[y],(IX+d)` and `LD (IX+d),r[z]` are `x=1` with `z=6` / `y=6`.
- `x=1` with `y` and `z` both register halves selects `IXH`/`IXL` (`y=4/5`), never with a memory
  operand: `DD 26 n` is `LD IXH,n`, `DD 36 d n` is `LD (IX+d),n`.
- `x=2` works on `(IX+d)` for `z=6`, on `IXH`/`IXL` for `z=4/5`, else as documented.
- `x=0 z=1 q=1` is `ADD IX,rp[p]`; `x=0 z=2 q=1 p=2` is `LD IX,(nn)` and `p=3` is `LD (nn),IX`;
  `x=0 z=3` is `INC IX`/`DEC IX`.

## `DDCB` / `FDCB`

`DD CB d op`, four bytes, 23 T (20 for `BIT`). The operation is the `CB` table applied to
`(IX+d)`; when `z != 6`, the result is **also** written to `r[z]`. `BIT` ignores `z` and takes
flags 3/5 from the high byte of `IX+d`.

## Assembler/disassembler agreement

- `disasm(assemble(src))` reproduces `src` modulo formatting (register case, hex case, whitespace);
  `assemble(disasm(bytes))` reproduces `bytes` exactly. Both are property tests over this table.
- An undefined opcode disassembles to `DB 0xNN`, a form the assembler accepts, so the round trip
  closes.
- Indexed forms print as `(IX+d)` with `d` signed decimal, or `(IX-d)`.
- Conditional forms print `JR NZ,label`, `CALL C,label`.