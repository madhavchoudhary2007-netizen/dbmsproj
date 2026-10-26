# Architecture

A modular FastAPI backend holds the transaction boundary for official race operations. PostgreSQL is authoritative for competition, user, steward, result and pit data. MongoDB stores timestamped telemetry. Both stores use UUID strings for session and driver links. A Next.js frontend reads REST snapshots and uses a session WebSocket for live updates.

The simulator produces the same normalized packet shape as the external ingest API. This lets a real provider replace the simulator without changing the pit wall UI. See `contracts.md` for payloads and states.

Engineering changes follow [the locked architecture](../.agent/ARCHITECT.md), [the overhaul scope](overhaul-plan.md) and [the delivery workflow](../.agent/protocol/delivery-workflow.md). Runtime contracts stay in contracts.md; current implementation evidence stays in .agent/CURRENT_STATE.md.

Antigravity execution contract: [.agent/protocol/antigravity.md](../.agent/protocol/antigravity.md) — Gemini 3.8 Flash HIGH orchestrator / LOW workers, maximum two workers. Record observed UI settings or UNVERIFIED; declarations do not prove model binding. Current permission and evidence remain in the state files and latest owner instruction.
