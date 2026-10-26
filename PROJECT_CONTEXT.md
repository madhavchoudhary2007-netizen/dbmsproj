# ApexGrid

Full-stack motorsport league and live race operations platform. The source presentations are in `~/Downloads/ApexGrid_Professional_Project_Presentation.pptx` and `~/Downloads/ApexGrid_Academic_Project_Presentation.pptx`.

Architecture: Next.js/React frontend, FastAPI modular monolith, PostgreSQL authoritative relational core, MongoDB telemetry store, WebSocket live session stream, Docker Compose deployment. `docs/contracts.md` is an API inventory; reconcile current packet types with source/snapshot and accepted ADRs.

Critical rules: PostgreSQL trigger accumulates approved penalty points and bans drivers at 12; PostgreSQL standings routine uses an explicit cursor; pit reservation locks the box row, checks overlap and commits transactionally; PostgreSQL enforces session transitions, unique classified positions, and nonoverlapping team memberships; DBMS Operations Center reports real database behavior. Simulation and external telemetry ingest share one packet contract. External ingest requires an admin/steward token and an active session. WebSocket auth uses the `apexgrid.jwt` subprotocol.

Local URLs: frontend `http://localhost:3000`, API `http://localhost:8000/api`, API docs `http://localhost:8000/docs`. Demo credentials, run commands, and verification steps are in `README.md`.

Engineering execution: AGENTS.md -> .agent/protocol/delivery-workflow.md. Current verified state and permission/queue: .agent/CURRENT_STATE.md and .agent/NEXT_STATE.md. Product scope/design: docs/overhaul-plan.md; this product overview does not restart setup or establish current quality results.

Antigravity execution contract: [.agent/protocol/antigravity.md](.agent/protocol/antigravity.md) — Gemini 3.8 Flash HIGH orchestrator / LOW workers, maximum two workers. Record observed UI settings or UNVERIFIED; declarations do not prove model binding. Current permission and evidence remain in the state files and latest owner instruction.

Document roles and retired instructions: [.agent/DOC_AUTHORITY.md](.agent/DOC_AUTHORITY.md). Operator commands here are not authorization for an agent to write real databases or restart setup.
