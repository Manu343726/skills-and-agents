---
name: observability
description: How the estate's telemetry is written and read — query conventions that survive a window, the alert shapes that cannot fire and the ones that fire twice, why a window must hold several events of its signal, and why a rule is not done until it has been seen firing and resolving.
---

# Observability

The estate is measured in three stores — metrics, logs, traces — and each one answers a different
question. Metrics answer *what changed and when*; logs answer *what said so*; traces answer *where the
time went*. Reaching for the wrong one is the most common way to spend an hour and learn nothing.

## Reading

- **Start with the question, not the query.** *Is it up?* is `up` and a probe. *Is it slow?* is a
  latency quantile over a window. *What changed at 04:00?* is a range query over the hours around it.
- **Always bound the window**, and say what it is. An instant query answers now; a trend needs a range
  and a step, and a step coarser than the signal's cadence invents a shape.
- Ratios over counters use a rate; rate then aggregate, never aggregate then rate.
- **An empty result is not zero.** A series that stopped existing, a label that changed and a scrape
  that failed all return nothing, and nothing is not "healthy".

## The alert shapes that fail, and how each one reads

These four are not style. Each one is a rule that passed review and did nothing.

**1. A comparison where a boolean was meant.** A filtering comparison keeps the value; it does not
answer true or false. A rule built on one compares a number against a threshold and stays normal
through the fault. Make the expression answer a boolean explicitly, and read the rule's own state
during a deliberate fault rather than trusting its definition.

**2. A window that holds fewer events than the signal sends.** If a positive signal arrives every ten
minutes and the rule reads fifteen, the window holds one event and a single missed delivery empties it.
**The window must hold several events of what it reads**, and the delivery cadence is a measurement, not
a value written in a comment: measure the arrivals, then size the window. A dead-man's switch that pages
for a path that is working is worse than no switch, because the next page is doubted.

**3. An expression that answers more than once.** A per-series expression with a fallback produces one
instance for the series and one for the fallback — two notifications for one question, and a body
large enough to be refused by the channel. Aggregate first; one question, one instance.

**4. A notification the receiver refuses.** A payload over the channel's size limit is rejected, and
the rejection reads as an authentication or attachment error. Measure the delivery at the far end, in
the receiver's own store, and keep the payload small enough that the title is what a person reads.

## Designing a rule

- **The symptom, not the cause.** Alert on what a person would notice: the name does not answer, the
  queue is not drained, the backup did not land. A rule on CPU is a rule somebody silences.
- **A window longer than the flapping, shorter than the patience.** `for:` is the price of not being
  woken for a restart; the detection budget is that window plus the rule's own window.
- **Every rule names an owner and an action** in its annotation. An alert without either is a colour.
- **A quiet path needs a positive signal.** Something that must keep arriving, watched by a rule whose
  delivery does not travel through the thing being watched.
- **The rule is not done until it has fired and resolved, deliberately, and the notification was counted
  at the far end.** Provisioned is not delivered.

## Writing it down as code

Dashboards, rules, scrapes, pipelines and notification policies are provisioned from files the
repository owns. A change made in an interface exists only in whatever the interface stored, and the
next rebuild is the review that finds out.

- Provisioning is read at start: a change is proven by a restart and a query.
- **A panel is not evidence; the query behind it is.** Quote the expression and the value with its
  timestamp.
- Cardinality is a cost paid at every scrape. Keep the dimension somebody alerts on, drop the one
  nobody does.
- Retention is a decision with a number in it: what the estate can answer questions about after a week.

## Labels that make the data usable

A metric, log stream or span carries the identity of what produced it — service, instance, environment —
and never the identity of a request. A label whose values grow with traffic is a cardinality defect that
pays for itself at every scrape and every query.
