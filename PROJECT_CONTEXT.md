# ApexGrid

Full-stack motorsport league and live race operations platform. The source presentations are in `~/Downloads/ApexGrid_Professional_Project_Presentation.pptx` and `~/Downloads/ApexGrid_Academic_Project_Presentation.pptx`.

Architecture: Next.js/React frontend, FastAPI modular monolith, PostgreSQL authoritative relational core, MongoDB telemetry store, WebSocket live session stream, Docker Compose deployment. `docs/contracts.md` is the cross-component contract.

Critical rules: PostgreSQL trigger accumulates approved penalty points and bans drivers at 12; PostgreSQL standings routine uses an explicit cursor; pit reservation locks the box row, checks overlap and commits transactionally; PostgreSQL enforces session transitions, unique classified positions, and nonoverlapping team memberships; DBMS Operations Center reports real database behavior. Simulation and external telemetry ingest share one packet contract. External ingest requires an admin/steward token and an active session. WebSocket auth uses the `apexgrid.jwt` subprotocol.

Local URLs: frontend `http://localhost:3000`, API `http://localhost:8000/api`, API docs `http://localhost:8000/docs`. Demo credentials, run commands, and verification steps are in `README.md`.
