from dataclasses import dataclass

from labellens.config import Settings


def _split(value: str | None) -> tuple[str, ...]:
    return tuple(part.strip() for part in (value or "").split(",") if part.strip())


@dataclass(frozen=True)
class ApiConfig:
    env: str = "development"
    api_keys: tuple[str, ...] = ()
    cors_origins: tuple[str, ...] = ("http://localhost:3000",)
    max_upload_bytes: int = 4_000_000
    rate_limit_per_minute: int = 60
    max_concurrent_runs: int = 2

    @classmethod
    def from_settings(cls, s: Settings) -> "ApiConfig":
        return cls(
            env=s.app_env,
            api_keys=_split(s.api_keys),
            cors_origins=_split(s.cors_origins),
            max_upload_bytes=s.api_max_upload_bytes,
            rate_limit_per_minute=s.api_rate_limit_per_minute,
            max_concurrent_runs=s.api_max_concurrent_runs,
        )
