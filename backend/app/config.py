import os

APP_ENV = os.getenv("APP_ENV", "production").strip().lower()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://apexgrid:apexgrid@localhost:5432/apexgrid")
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "apexgrid")
AUTO_DEMO_RACE = os.getenv("AUTO_DEMO_RACE", "0").strip() == "1" and APP_ENV == "local"
SEED_DEMO_DATA = os.getenv("SEED_DEMO_DATA", "1").strip() == "1"
_LOCAL_DEMO_SECRET = "local-development-secret-change-me"  # noqa: S105 -- public local-only fallback rejected outside local mode
_WEAK_SECRETS = {
    "dev-change-me",
    "local-development-secret-change-me",
    "change-this-for-any-shared-environment",
}
JWT_SECRET = os.getenv("JWT_SECRET", "").strip()
if APP_ENV == "local":
    JWT_SECRET = JWT_SECRET or _LOCAL_DEMO_SECRET
elif (
    not JWT_SECRET or JWT_SECRET.casefold() in _WEAK_SECRETS or len(JWT_SECRET.encode("utf-8")) < 32
):
    raise RuntimeError("Set a unique JWT_SECRET of at least 32 bytes outside APP_ENV=local")
JWT_ALGORITHM = "HS256"
JWT_MINUTES = int(os.getenv("JWT_MINUTES", "720"))
CORS_ORIGINS = [
    x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if x.strip()
]
