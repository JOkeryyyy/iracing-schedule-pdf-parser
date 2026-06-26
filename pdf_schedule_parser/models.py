from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class ExtractedPage:
    page: int
    text: str


@dataclass
class ParserWarning:
    code: str
    message: str
    page: Optional[int] = None
    line: Optional[int] = None

    def to_json(self):
        result = {"code": self.code, "message": self.message}
        if self.page is not None:
            result["page"] = self.page
        if self.line is not None:
            result["line"] = self.line
        return result


@dataclass
class ParsedWeek:
    week: int
    start_date: str
    track_name: str
    race_length: Optional[dict] = None
    weather: dict = field(default_factory=dict)
    raw_lines: list[str] = field(default_factory=list)


@dataclass
class ParsedSeries:
    id: str
    name: str
    discipline: str
    fixed_setup: Optional[bool] = None
    fixed_setup_source: str = "unknown"
    start_type: str = "unknown"
    start_type_source: str = "unknown"
    license: dict = field(default_factory=dict)
    car_class_ids: list[str] = field(default_factory=list)
    car_ids: list[str] = field(default_factory=list)
    schedule: dict = field(default_factory=dict)
    official: dict = field(default_factory=dict)
    weeks: list[ParsedWeek] = field(default_factory=list)
    source_page: Optional[int] = None
    raw_lines: list[str] = field(default_factory=list)
