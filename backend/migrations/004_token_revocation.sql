CREATE TABLE IF NOT EXISTS revoked_tokens (
    jti uuid PRIMARY KEY,
    expires_at timestamptz NOT NULL
);

CREATE INDEX IF NOT EXISTS revoked_tokens_expires_at_idx
    ON revoked_tokens (expires_at);
