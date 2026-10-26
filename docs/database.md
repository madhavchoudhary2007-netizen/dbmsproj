# Database design

Operator/schema overview, not permission to seed, migrate or mutate a running database. Agent checks use only guarded apexgrid-test with scoped fixtures/cleanup; existing implementation statements require current test evidence before a completion claim.

The relational model is normalized to keep user identity, team membership, circuits, events, sessions, penalties and results in separate tables. PostgreSQL owns official state. MongoDB owns high-rate telemetry documents.

The required database demonstrations are implemented in migrations: constraints, a composite B-tree index on session and lap time, a licence lookup index, penalty trigger, explicit-cursor standings routine, and pit reservation transaction. `docs/demo-guide.md` contains the observable flow once the stack is verified.
