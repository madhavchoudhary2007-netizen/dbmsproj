# ADR-005 — Ordered telemetry ingestion

Status: Accepted for F-DOM-04 implementation
Date: 2026-10-23

## Context

`POST /api/telemetry/ingest` currently inserts and publishes every valid packet. Retries duplicate laps in MongoDB and WebSocket, while delayed older packets can replace the apparent latest state. F-DOM-04 records this defect. ADR-001 permits a finding-backed API change with its own ADR.

## Decision

- For the same session and driver, accept telemetry only when lap/sector progression and `elapsed_ms` advance. Compare against persisted MongoDB telemetry so a restart does not reset ordering.
- An exact retry of a persisted packet is idempotent: return HTTP 202 with the original packet ID and existing success shape, without a second MongoDB insert or WebSocket publication.
- A nonidentical packet at the same logical position, or any older lap/sector/elapsed packet, returns HTTP 409 with a stable `detail` explaining that telemetry is out of order. No insert or publication occurs.
- Serialize the read/decision/insert path within the ADR-004 single active backend process. Do not rewrite or remove historical packets. Simulator production remains separately responsible for advancing its own monotone per-driver timeline.

## Consequences

- API-07's error contract gains the HTTP 409 case. Valid first packets and their 202 response keys are unchanged. Retry clients may safely resend an identical packet.
- W3 must first prove duplicate, delayed and conflicting packets on an isolated fake store, including no second publication and independent driver streams. W2 implements only after that proof. The orchestrator reruns the full disposable backend suite and live acceptance.
- Existing historical telemetry is read as-is. A new sequence check cannot retroactively repair older records; the first new packet compares with the latest stored record.

## Sections affected

- `.agent/ARCHITECT.md` B.3 telemetry contract and B.4 telemetry transitions.
- `.agent/ARCHITECT.md` G14, Phase C ADR-005 review, Risks R07.
- `docs/contracts.md` API-07 ingest errors after implementation.
