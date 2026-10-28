---
name: networking
description: How the path from a name to a process is built and measured — one resolver and why a second is a wrong answer, split-horizon and the vantage point, TLS issuance versus renewal versus trust, ingress routes, port forwards and leases, and why a lookup inside a loop is a denial of service the operator performs on themselves.
---

# Networking

The path is a chain of answers, and a fault lives at one link of it: a name resolved by a zone, a
resolver that answered it, a certificate offered, a proxy that terminated it, a route to a process, a
forward that made it reachable, a firewall that did not stop it. **Diagnose in that order, and at the
layer that fails**, not at the layer that is easiest to test.

## The vantage point is part of the measurement

The same name answers differently depending on who asks, and a fault is defined by where it is seen.

| Vantage point | Tells you |
|---|---|
| a client on the private network | what the estate serves to itself, including split-horizon answers |
| a client outside | what is actually published, after every forward and proxy |
| the host itself | what the process binds, before any proxy |
| one container on one bridge | what the service's own dependency chain resolves |

A name that works inside and fails outside is one defect; work everywhere and fail in one place is
another; and the fix for one is not the fix for the other. Say the vantage point in every report,
because a measurement whose vantage point is unstated cannot be reproduced.

## DNS: one resolver, and the answer belongs to the client

- **Split-horizon is a feature, not a bug to normalise away.** A name that resolves to a private address
  inside and a public one outside will answer both answers truthfully, to different clients.
- **A second resolver is a silent wrong answer.** The client that falls back to a public resolver gets
  the public address for a name that only exists privately, and the failure looks like a service outage.
  One resolver, so the failure is visible and the search has one place to look.
- **The stub the client reads is generated.** Editing it loses the change on the next restart and takes
  the split-horizon with it. Change the source of truth, then re-read the client's state.
- **Resolve once, then use the address.** A loop that resolves per attempt — a port scan naming its
  target, a retry that builds a URL from a hostname, a healthcheck that re-resolves every second — is a
  burst of queries, and a resolver that rate-limits per client will refuse the client doing it, which
  may be the same machine. The failure is partial and therefore confusing: cached answers keep working
  while everything needing an upstream forward stops.
- **A rate limit is the symptom.** Raising it buys a larger loop before the same failure returns.

## TLS: three failures that share a message

An expired certificate, an incomplete chain and a wrong clock all surface as *the certificate is not
valid* or *the handshake failed*:

- **Expiry** works until it does not, and fails at one moment for every client at once.
- **An incomplete chain** works in every browser — they fetch the missing intermediate — and fails in
  every client that does not, which is most CLIs and every service-to-service call.
- **A clock that drifted** refuses a certificate that is valid tomorrow, and reads as a broken service
  rather than as a clock. Check the clock before the certificate.

**Never disable verification to get past one.** A `-k` or an "insecure" flag turns the one measurement
that would have named the fault into a green check.

## Ingress and the published path

- The route and the name are two objects, and a published name that answers an SSO challenge from a
  machine is the proxy doing its job: a probe must expect the redirect, and a service must be reached by
  a route that does not sit behind a browser-only gate.
- **A path that depends on the proxy must have a route that does not**, for the case where the proxy is
  the thing that is broken.
- A forward on a router that is tied to a DHCP lease survives only while the lease does. An address that
  moved is a published name that stopped working, and the finding is the lease, not the service.
- **Hairpin is a configuration.** When the network does not route its own public name back inside, the
  inside client needs the internal name; a check that uses the public name from inside is measuring the
  absent hairpin.

## Traps, in the order they bite

1. A lookup inside a loop, or a sweep of a wide port range across hosts.
2. Raising a rate limit to route around a loop.
3. Adding a resolver, or editing a generated resolver file.
4. Testing the public name from inside and reading the answer as the service.
5. Leaving a temporary `hosts` entry, forward or bypass in place, and calling it a fix.

## What a report carries

The name, the vantage point, the command and the answer for each hop — resolution, connection,
certificate, proxy, route — the change with its rollback, and the check that now proves the path from the
side that reported it.
