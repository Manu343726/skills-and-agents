---
name: parallel-execution
description: How the engine spends every core without becoming irreproducible — the task engine and its serial reference, the delta barrier that makes partitioning deterministic, the atomics and padding rules, what may never appear in a delta, and how a parallel change is measured before it is believed.
---

# Parallel execution

The engine must use every core it is given, and two runs of the same ROM with the same inputs must
produce the same state. Those pull against each other, and the design reconciles them instead of
trading one away.

## What is actually parallel

| Level | Parallel? | Note |
|---|---|---|
| Machines | yes, linearly | Every machine is independent. This is the cheap win and it comes first. |
| Netlist partitions | yes | A gate-level machine is cut into partitions that meet at a delta barrier. |
| One Z80 instruction | **no** | Decode → operands → execute → flags is serial, tens of nanoseconds. Never promise a parallel CPU. |
| Tracing, VCD, net stream, framebuffer | yes | Producer/consumer; one encoder thread; never on the worker's critical path. |

A design that claims a single functional Z80 gets faster with more cores is wrong. Say where the
cores go, and mean it.

## The task engine

Taskflow 4 (`taskflow/4.0.0`, MIT, header-only, conan-center) is the executor: per-worker
lock-free work-stealing deques, a lock-free steal path, explicit task graphs.

It is reached only through one seam:

```cpp
namespace z80::sched {
class Executor {
public:
  virtual ~Executor() = default;
  virtual uint32_t workers() const noexcept = 0;
  virtual void parallel_for(uint32_t n, const std::function<void(uint32_t)>& body) = 0;
  virtual void run(std::span<Task> tasks) = 0;
};
std::unique_ptr<Executor> make_serial();
std::unique_ptr<Executor> make_work_stealing(uint32_t threads = 0);
}
```

- **Nothing outside `sched/` includes Taskflow.** One header includes it, so replacing it is one
  file.
- `make_serial()` is the **reference executor**, not a test double: every parallel result must
  equal the serial one, and the determinism harness runs both.
- One executor per process, shared by every machine. A machine does not own workers; `--threads 1`
  selects the serial one and says so in the log.

## The determinism rule

> A partition reads only the **committed** values of nets it does not own, writes only its own, and
> a barrier commits the delta. No task observes a value produced in the same delta.

Implementation: every boundary net is double-buffered (`current` / `next`). During a delta a
partition writes `next` for its outputs and reads `current` for its inputs; the barrier swaps them.
Each net has exactly one writer partition.

Three properties follow, and they are the whole justification:

1. **Reproducible** — the committed value after delta *k* does not depend on which worker ran what.
2. **Race-free by construction** — one writer per net, one swap per delta, nothing else shared.
3. **Predictable cost** — one barrier per delta, amortised over thousands of gates.

Work stealing changes *when*, never *what*. If a change makes the result depend on scheduling, it
is a defect, not a speed-up.

## Rules that are reviewed, not suggested

- **No lock held across a task boundary.** A lock in the hot path is a defect.
- **No allocation in a delta.** Pools are sized at elaboration; `new` during simulation is a finding.
- **No `std::function` in a delta** — allocation plus an indirect call. Tasks are function pointer
  plus context; the `Executor` interface may take a `std::function` at the *seam* only.
- **Weakest correct atomics**: `relaxed` for counters, `release`/`acquire` for the ring and the
  barrier; `seq_cst` in a hot path needs a comment justifying it.
- **Pad every counter two workers write** to a cache line; a shared counter in a loop is a
  scalability bug that looks like a slow algorithm.
- **The control path never touches live state.** A `Step` from the API goes on the machine's SPSC
  ring and is drained at a tick boundary — the same boundary the fidelity hot swap uses. A command
  whose deadline expires before the boundary returns `deadline_exceeded`; it never mutates a
  running machine.

## Measuring, because "parallel" is a claim

```sh
engine/build/z80_bench --machines N --threads M     # instructions/s, M = 1..hardware_concurrency
```

- Report **scaling efficiency** (`speedup / cores`), not just throughput.
- A parallel change records before and after in its issue: machine, N, M, and the numbers.
- CI asserts only that the **serial** path did not regress (a noisy runner cannot assert a
  speedup); scaling is a nightly report.
- A `-fsanitize=thread` run of the netlist tests is part of the kernel's definition of done.

## The failure modes worth knowing by name

| Symptom | Usual cause |
|---|---|
| Results differ between runs | a boundary net read from `next` instead of `current` |
| Fast with 1 thread, flat at 4 | one shared counter or one mutex on the hot path |
| Works until the gate count doubles | partition table sized for the old netlist; re-elaborate on swap |
| A hang with no output | barrier entered from different partitions, or a task that throws |
| A 2× slowdown after "optimising" | false sharing: two partitions writing adjacent fields |
