
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Environment & Modes
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "VASP-Trace"
    API_V1_PREFIX: str = "/api/v1"
    DEMO_MODE: bool = True
    LIVE_MODE: bool = False

    # Security & Auth
    SECRET_KEY: str = "dev-secret-key-must-be-changed-in-production-at-least-32-chars-long"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://vasp:vasp_secret@localhost:5432/vasp_trace"
    DATABASE_URL_SYNC: str = "postgresql://vasp:vasp_secret@localhost:5432/vasp_trace"

    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Graph Engine Caps (FR-GRAPH-03)
    DEFAULT_MAX_HOPS: int = 3
    GLOBAL_MAX_HOPS: int = 5
    MIN_TRACED_USD: float = 100.0
    MAX_TX_PER_NODE: int = 200
    MAX_NODES_PER_HOP: int = 50
    GLOBAL_NODE_CAP: int = 1500
    GLOBAL_EDGE_CAP: int = 10000
    HIGH_DEGREE_THRESHOLD: int = 1000
    CALL_BUDGET: int = 600

    # Blockchain Explorer & RPC Keys (Optional in DEMO mode)
    ETHERSCAN_API_KEY: str | None = None
    BSCSCAN_API_KEY: str | None = None
    POLYGONSCAN_API_KEY: str | None = None
    TRONGRID_API_KEY: str | None = None
    ETHEREUM_RPC_URL: str | None = None
    BNB_RPC_URL: str | None = None
    POLYGON_RPC_URL: str | None = None
    TRON_RPC_URL: str | None = None


settings = Settings()
