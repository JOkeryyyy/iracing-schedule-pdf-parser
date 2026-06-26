from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class MappingConfig:
    season_id: str
    season_name: str
    season_start: str
    season_end: str
    generated_at: str
    week_season_start: Optional[str] = None

    @property
    def season_start_timestamp(self):
        return date_to_utc_midnight(self.season_start)

    @property
    def season_end_timestamp(self):
        return date_to_utc_midnight(self.season_end)

    @property
    def week_season_start_timestamp(self):
        return date_to_utc_midnight(self.week_season_start or self.season_start)


@dataclass(frozen=True)
class BuildOutputPaths:
    mobile_dir: Path
    revision: str
    release_dir: Path


def date_to_utc_midnight(value):
    if value.endswith("Z"):
        return value
    return f"{value}T00:00:00Z"
