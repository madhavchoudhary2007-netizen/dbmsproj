# Architecture

A modular FastAPI backend holds the transaction boundary for official race operations. PostgreSQL is authoritative for competition, user, steward, result and pit data. MongoDB stores timestamped telemetry. Both stores use UUID strings for session and driver links. A Next.js frontend reads REST snapshots and uses a session WebSocket for live updates.

The simulator produces the same normalized packet shape as the external ingest API. This lets a real provider replace the simulator without changing the pit wall UI. See `contracts.md` for payloads and states.
