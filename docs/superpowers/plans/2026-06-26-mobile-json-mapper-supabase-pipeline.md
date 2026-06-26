# Mobile JSON Mapper And Supabase Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a tested Python pipeline that maps raw PDF parser JSON into frontend-ready mobile JSON, validates it, and publishes immutable releases to Supabase Storage with manifest-last semantics.

**Architecture:** Keep the existing `pdf_schedule_parser` package focused on `PDF -> raw JSON`. Add a separate `schedule_data_pipeline` package for `raw JSON -> mobile JSON -> validation -> publish`. GitHub Actions runs parser, mapper, validation, artifacts, branch generated-file commits, and `main`/manual Supabase publish.

**Tech Stack:** Python 3.9+, stdlib `unittest`, `argparse`, `json`, `hashlib`, `urllib.request`, existing `pypdf` dependency for the parser, GitHub Actions, Supabase Storage REST API.

---

## File Structure

Create:

- `schedule_data_pipeline/__init__.py`: package marker.
- `schedule_data_pipeline/models.py`: lightweight dataclasses for pipeline config and generated file records.
- `schedule_data_pipeline/jsonio.py`: JSON load/write helpers and stable JSON serialization.
- `schedule_data_pipeline/mapper.py`: raw parser JSON to frontend-ready mobile JSON.
- `schedule_data_pipeline/manifest.py`: content hash, checksums, manifest, release directory helpers.
- `schedule_data_pipeline/validator.py`: frontend contract validation and warning collection.
- `schedule_data_pipeline/publisher.py`: Supabase Storage upload and public smoke-test client.
- `schedule_data_pipeline/cli.py`: `build`, `validate`, and `publish` commands.
- `tests/fixtures/raw_pipeline/season.json`: minimal raw parser fixture.
- `tests/fixtures/raw_pipeline/cars.json`: minimal raw cars fixture.
- `tests/fixtures/raw_pipeline/tracks.json`: minimal raw tracks fixture.
- `tests/fixtures/raw_pipeline/car-classes.json`: minimal raw car classes fixture.
- `tests/fixtures/raw_pipeline/parser-report.json`: minimal raw parser report fixture.
- `tests/test_pipeline_mapper.py`: mapper behavior tests.
- `tests/test_pipeline_manifest.py`: content hash and manifest tests.
- `tests/test_pipeline_validator.py`: frontend contract validation tests.
- `tests/test_pipeline_cli.py`: CLI build/validate tests.
- `tests/test_pipeline_publisher.py`: upload order and failure behavior tests.

Modify:

- `pyproject.toml`: include `schedule_data_pipeline*` package and add console script `iracing-schedule-data`.
- `README.md`: document local build/validate/publish commands and required Supabase secrets.
- `.github/workflows/parse-schedule.yml`: run mapper/validator, upload mobile artifacts, commit `data/mobile/v1/**` on non-main branches, and publish on `main`/manual dispatch.

Generated paths:

- `data/mobile/v1/manifest.json`
- `data/mobile/v1/releases/{seasonId}/{revision}/season.json`
- `data/mobile/v1/releases/{seasonId}/{revision}/cars.json`
- `data/mobile/v1/releases/{seasonId}/{revision}/tracks.json`

## Task 1: Raw Fixture And JSON Helpers

**Files:**
- Create: `schedule_data_pipeline/__init__.py`
- Create: `schedule_data_pipeline/jsonio.py`
- Create: `tests/fixtures/raw_pipeline/season.json`
- Create: `tests/fixtures/raw_pipeline/cars.json`
- Create: `tests/fixtures/raw_pipeline/tracks.json`
- Create: `tests/fixtures/raw_pipeline/car-classes.json`
- Create: `tests/fixtures/raw_pipeline/parser-report.json`
- Create: `tests/test_pipeline_mapper.py`

- [ ] **Step 1: Write the raw fixture files**

Create `tests/fixtures/raw_pipeline/season.json`:

```json
{
  "schemaVersion": 1,
  "season": {
    "id": "2026-s3",
    "name": "2026 Season 3",
    "startDate": "2026-01-20",
    "endDate": "2026-12-04"
  },
  "series": [
    {
      "id": "series_mini_stock_rookie_series_by_thrustmaster_2026_s3",
      "name": "Mini Stock Rookie Series by Thrustmaster",
      "discipline": "oval",
      "fixedSetup": null,
      "fixedSetupSource": "unknown",
      "startType": "rolling",
      "startTypeSource": "weatherText",
      "license": {
        "raw": "Rookie 1.0 --> Pro/WC 4.0",
        "minClass": "rookie",
        "minSafetyRating": 1.0,
        "maxClass": "pro_wc",
        "maxSafetyRating": 4.0
      },
      "carClassIds": ["car_class_mini_stock"],
      "carIds": ["car_mini_stock"],
      "schedule": {
        "raw": "Races every 30 minutes at :15 and :45",
        "type": "recurring",
        "intervalMinutes": 30,
        "minuteOffsets": [15, 45]
      },
      "official": {
        "minEntries": 6,
        "splitAt": 14,
        "drops": 4
      },
      "weeks": [
        {
          "week": 1,
          "startDate": "2026-06-16",
          "trackId": "track_charlotte_motor_speedway_oval",
          "trackName": "Charlotte Motor Speedway - Oval",
          "raceLength": {
            "type": "laps",
            "value": 15
          },
          "weather": {
            "rainChancePercent": 0,
            "temperatureF": 80,
            "temperatureC": 26
          }
        },
        {
          "week": 2,
          "startDate": "2026-06-23",
          "trackId": "track_langley_speedway",
          "trackName": "Langley Speedway",
          "raceLength": {
            "type": "laps",
            "value": 35
          },
          "weather": {
            "rainChancePercent": 10
          }
        }
      ]
    },
    {
      "id": "series_arca_menards_series_2026_s3",
      "name": "ARCA Menards Series",
      "discipline": "oval",
      "fixedSetup": true,
      "fixedSetupSource": "seriesName",
      "startType": "standing",
      "startTypeSource": "weatherText",
      "license": {
        "raw": "Rookie 4.0 --> Pro/WC 4.0",
        "minClass": "rookie",
        "minSafetyRating": 4.0
      },
      "carClassIds": ["car_class_arca"],
      "carIds": ["car_arca"],
      "schedule": {
        "raw": "Races every hour at :45 past",
        "type": "recurring",
        "intervalMinutes": 60,
        "minuteOffsets": [45]
      },
      "official": {
        "minEntries": 6,
        "splitAt": 20,
        "drops": 4
      },
      "weeks": [
        {
          "week": 1,
          "startDate": "2026-06-16",
          "trackId": "track_daytona_international_speedway_oval",
          "trackName": "Daytona International Speedway - Oval",
          "raceLength": {
            "type": "minutes",
            "value": 20
          },
          "weather": {
            "rainChancePercent": 15
          }
        }
      ]
    }
  ]
}
```

Create `tests/fixtures/raw_pipeline/cars.json`:

```json
{
  "schemaVersion": 1,
  "cars": [
    {
      "id": "car_mini_stock",
      "name": "Mini Stock",
      "disciplines": ["oval"],
      "mappingStatus": "fallback"
    },
    {
      "id": "car_arca",
      "name": "ARCA",
      "disciplines": ["oval"],
      "mappingStatus": "fallback"
    }
  ]
}
```

Create `tests/fixtures/raw_pipeline/tracks.json`:

```json
{
  "schemaVersion": 1,
  "tracks": [
    {
      "id": "track_charlotte_motor_speedway_oval",
      "name": "Charlotte Motor Speedway",
      "config": "Oval",
      "displayName": "Charlotte Motor Speedway - Oval",
      "disciplines": ["oval"],
      "mappingStatus": "fallback"
    },
    {
      "id": "track_langley_speedway",
      "name": "Langley Speedway",
      "config": null,
      "displayName": "Langley Speedway",
      "disciplines": ["oval"],
      "mappingStatus": "fallback"
    },
    {
      "id": "track_daytona_international_speedway_oval",
      "name": "Daytona International Speedway",
      "config": "Oval",
      "displayName": "Daytona International Speedway - Oval",
      "disciplines": ["oval"],
      "mappingStatus": "fallback"
    }
  ]
}
```

Create `tests/fixtures/raw_pipeline/car-classes.json`:

```json
{
  "schemaVersion": 1,
  "carClasses": [
    {
      "id": "car_class_mini_stock",
      "name": "Mini Stock",
      "carIds": ["car_mini_stock"],
      "disciplines": ["oval"],
      "mappingStatus": "fallback"
    },
    {
      "id": "car_class_arca",
      "name": "ARCA",
      "carIds": ["car_arca"],
      "disciplines": ["oval"],
      "mappingStatus": "fallback"
    }
  ]
}
```

Create `tests/fixtures/raw_pipeline/parser-report.json`:

```json
{
  "schemaVersion": 1,
  "sourcePdf": "data/source/SeasonSchedule.pdf",
  "generatedAt": "2026-06-26T00:00:00Z",
  "contentHash": "raw-fixture-hash",
  "counts": {
    "series": 2,
    "cars": 2,
    "tracks": 3,
    "carClasses": 2,
    "warnings": 1
  },
  "warnings": [
    {
      "code": "fixedSetupUnknown",
      "message": "Fixed/open setup needs manual review for Mini Stock Rookie Series by Thrustmaster"
    }
  ]
}
```

- [ ] **Step 2: Write the failing helper test**

Create `tests/test_pipeline_mapper.py` with this first test:

```python
from pathlib import Path
import unittest

from schedule_data_pipeline.jsonio import load_json_file, stable_json


FIXTURE_DIR = Path("tests/fixtures/raw_pipeline")


class JsonIoTests(unittest.TestCase):
    def test_load_json_file_reads_fixture_object(self):
        loaded = load_json_file(FIXTURE_DIR / "season.json")

        self.assertEqual(loaded["schemaVersion"], 1)
        self.assertEqual(len(loaded["series"]), 2)

    def test_stable_json_sorts_keys_without_extra_spaces(self):
        self.assertEqual(stable_json({"b": 2, "a": 1}), '{"a":1,"b":2}')


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the helper test to verify it fails**

Run:

```bash
python -m unittest tests.test_pipeline_mapper.JsonIoTests
```

Expected: `ERROR` because `schedule_data_pipeline.jsonio` does not exist.

- [ ] **Step 4: Implement JSON helpers**

Create `schedule_data_pipeline/__init__.py`:

```python
"""Build, validate, and publish mobile-ready schedule JSON."""
```

Create `schedule_data_pipeline/jsonio.py`:

```python
import json
from pathlib import Path


def load_json_file(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json_file(path, value):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def stable_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
```

- [ ] **Step 5: Run the helper test to verify it passes**

Run:

```bash
python -m unittest tests.test_pipeline_mapper.JsonIoTests
```

Expected: `OK`.

- [ ] **Step 6: Commit**

Run:

```bash
git add schedule_data_pipeline/__init__.py schedule_data_pipeline/jsonio.py tests/fixtures/raw_pipeline tests/test_pipeline_mapper.py
git commit -m "test: add pipeline json fixtures"
```

## Task 2: Mapper Core

**Files:**
- Create: `schedule_data_pipeline/models.py`
- Create: `schedule_data_pipeline/mapper.py`
- Modify: `tests/test_pipeline_mapper.py`

- [ ] **Step 1: Add failing mapper tests**

Append to `tests/test_pipeline_mapper.py`:

```python
from schedule_data_pipeline.mapper import MappingConfig, build_mobile_bundle


class MapperTests(unittest.TestCase):
    def test_build_mobile_bundle_maps_series_and_flat_races(self):
        bundle = build_fixture_bundle()

        season = bundle["season"]

        self.assertEqual(season["schemaVersion"], 1)
        self.assertEqual(season["seasonId"], "2026-s3")
        self.assertEqual(season["seasonStart"], "2026-06-16T00:00:00Z")
        self.assertEqual(season["seasonEnd"], "2026-09-08T00:00:00Z")
        self.assertEqual(season["weekSeasonStart"], "2026-06-16T00:00:00Z")
        self.assertEqual([week["weekNumber"] for week in season["weeks"]], [1, 2])
        self.assertEqual(len(season["series"]), 2)
        self.assertEqual(len(season["races"]), 3)

        mini_stock = season["series"][0]
        self.assertEqual(mini_stock["setupType"], "unknown")
        self.assertEqual(mini_stock["setupSource"], "unknown")
        self.assertEqual(mini_stock["startType"], "rolling")
        self.assertEqual(mini_stock["category"], "Oval")
        self.assertEqual(mini_stock["license"]["className"], "Rookie")
        self.assertEqual(mini_stock["license"]["safetyRating"], 1.0)
        self.assertEqual(len(mini_stock["raceIds"]), 2)

        arca = season["series"][1]
        self.assertEqual(arca["setupType"], "fixed")
        self.assertEqual(arca["setupSource"], "seriesName")
        self.assertEqual(arca["startType"], "standing")

    def test_build_mobile_bundle_maps_race_rows_for_frontend_scanning(self):
        bundle = build_fixture_bundle()

        race = bundle["season"]["races"][0]

        self.assertEqual(
            race["raceId"],
            "2026-s3-series_mini_stock_rookie_series_by_thrustmaster_2026_s3-w1-track_charlotte_motor_speedway_oval",
        )
        self.assertEqual(race["seriesName"], "Mini Stock Rookie Series by Thrustmaster")
        self.assertEqual(race["category"], "Oval")
        self.assertEqual(race["startsAt"], "2026-06-16T00:00:00Z")
        self.assertEqual(race["endsAt"], "2026-06-23T00:00:00Z")
        self.assertEqual(race["trackName"], "Charlotte Motor Speedway")
        self.assertEqual(race["trackConfigName"], "Oval")
        self.assertEqual(race["carSkus"], ["car_mini_stock"])
        self.assertEqual(race["carClasses"], ["Mini Stock"])
        self.assertEqual(race["setupType"], "unknown")
        self.assertEqual(race["startType"], "rolling")
        self.assertEqual(race["raceLength"], {"laps": 15})
        self.assertEqual(race["precipChance"], 0)
        self.assertEqual(
            race["sessions"],
            [
                {
                    "type": "recurring",
                    "firstSessionOffsetMinutes": 15,
                    "repeatEveryMinutes": 30,
                }
            ],
        )

    def test_build_mobile_bundle_maps_catalogs(self):
        bundle = build_fixture_bundle()

        self.assertEqual(bundle["cars"]["cars"][0]["sku"], "car_arca")
        self.assertEqual(bundle["cars"]["cars"][1]["displayName"], "Mini Stock")
        self.assertEqual(bundle["tracks"]["tracks"][0]["packageId"], "track_charlotte_motor_speedway_oval")
        self.assertEqual(bundle["tracks"]["tracks"][0]["type"], "oval")
        self.assertEqual(bundle["tracks"]["tracks"][0]["sourceTrackIds"], [])


def build_fixture_bundle():
    return build_mobile_bundle(
        raw_season=load_json_file(FIXTURE_DIR / "season.json"),
        raw_cars=load_json_file(FIXTURE_DIR / "cars.json"),
        raw_tracks=load_json_file(FIXTURE_DIR / "tracks.json"),
        raw_car_classes=load_json_file(FIXTURE_DIR / "car-classes.json"),
        config=MappingConfig(
            season_id="2026-s3",
            season_name="2026 Season 3",
            season_start="2026-06-16",
            season_end="2026-09-08",
            generated_at="2026-06-26T00:00:00Z",
        ),
    )
```

- [ ] **Step 2: Run mapper tests to verify they fail**

Run:

```bash
python -m unittest tests.test_pipeline_mapper
```

Expected: `ERROR` because `schedule_data_pipeline.mapper` does not exist.

- [ ] **Step 3: Implement mapper models**

Create `schedule_data_pipeline/models.py`:

```python
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
```

- [ ] **Step 4: Implement mapper**

Create `schedule_data_pipeline/mapper.py`:

```python
from datetime import date, timedelta

from schedule_data_pipeline.models import MappingConfig, date_to_utc_midnight


DISCIPLINE_LABELS = {
    "oval": "Oval",
    "sports_car": "Sports Car",
    "formula_car": "Formula Car",
    "dirt_oval": "Dirt Oval",
    "dirt_road": "Dirt Road",
    "unranked": "Unranked",
}

TRACK_TYPES = {
    "oval": "oval",
    "sports_car": "road",
    "formula_car": "road",
    "dirt_oval": "dirtOval",
    "dirt_road": "dirtRoad",
    "unranked": "unranked",
}


MappingConfig = MappingConfig


def build_mobile_bundle(raw_season, raw_cars, raw_tracks, raw_car_classes, config):
    class_names_by_id = {item["id"]: item["name"] for item in raw_car_classes.get("carClasses", [])}
    cars = build_cars(raw_cars, raw_car_classes)
    tracks = build_tracks(raw_tracks)
    series_items = []
    race_items = []
    week_starts = {}

    for raw_series in raw_season.get("series", []):
        category = category_label(raw_series.get("discipline"))
        setup_type = map_setup_type(raw_series.get("fixedSetup"))
        setup_source = raw_series.get("fixedSetupSource") or "unknown"
        start_type = raw_series.get("startType") or "unknown"
        start_type_source = raw_series.get("startTypeSource") or "unknown"
        race_ids = []

        for raw_week in raw_series.get("weeks", []):
            week_number = raw_week["week"]
            starts_at = date_to_utc_midnight(raw_week["startDate"])
            ends_at = date_to_utc_midnight(add_days(raw_week["startDate"], 7))
            week_starts[week_number] = raw_week["startDate"]
            race_id = f"{config.season_id}-{raw_series['id']}-w{week_number}-{raw_week['trackId']}"
            race_ids.append(race_id)
            race_items.append(
                {
                    "raceId": race_id,
                    "seriesId": raw_series["id"],
                    "seriesName": raw_series["name"],
                    "category": category,
                    "weekNumber": week_number,
                    "startsAt": starts_at,
                    "endsAt": ends_at,
                    "trackPackageId": raw_week["trackId"],
                    **track_name_fields(raw_week["trackName"]),
                    "carSkus": list(raw_series.get("carIds", [])),
                    "carClasses": [class_names_by_id.get(value, display_from_id(value, "car_class_")) for value in raw_series.get("carClassIds", [])],
                    "setupType": setup_type,
                    "setupSource": setup_source,
                    "startType": start_type,
                    "startTypeSource": start_type_source,
                    **optional_race_length(raw_week.get("raceLength")),
                    **optional_precip(raw_week.get("weather", {})),
                    "sessions": map_sessions(raw_series.get("schedule", {})),
                }
            )

        series_items.append(
            {
                "seriesId": raw_series["id"],
                "name": raw_series["name"],
                "category": category,
                "license": map_license(raw_series.get("license", {})),
                "isOfficial": bool(raw_series.get("official")),
                "setupType": setup_type,
                "setupSource": setup_source,
                "startType": start_type,
                "startTypeSource": start_type_source,
                "raceIds": race_ids,
            }
        )

    season = {
        "schemaVersion": 1,
        "generatedAt": config.generated_at,
        "seasonId": config.season_id,
        "seasonName": config.season_name,
        "seasonStart": config.season_start_timestamp,
        "seasonEnd": config.season_end_timestamp,
        "weekSeasonStart": config.week_season_start_timestamp,
        "weeks": [
            {
                "weekNumber": week_number,
                "startsAt": date_to_utc_midnight(start_date),
                "endsAt": date_to_utc_midnight(add_days(start_date, 7)),
            }
            for week_number, start_date in sorted(week_starts.items())
        ],
        "series": sorted(series_items, key=lambda item: item["seriesId"]),
        "races": sorted(race_items, key=lambda item: (item["weekNumber"], item["seriesId"], item["raceId"])),
    }
    return {"season": season, "cars": cars, "tracks": tracks}


def build_cars(raw_cars, raw_car_classes):
    classes_by_car_id = {}
    for car_class in raw_car_classes.get("carClasses", []):
        for car_id in car_class.get("carIds", []):
            classes_by_car_id.setdefault(car_id, []).append(car_class["name"])

    return {
        "schemaVersion": 1,
        "generatedAt": None,
        "cars": sorted(
            [
                {
                    "sku": car["id"],
                    "displayName": car["name"],
                    "categories": sorted(category_label(value) for value in car.get("disciplines", [])),
                    "carClasses": sorted(classes_by_car_id.get(car["id"], [])),
                }
                for car in raw_cars.get("cars", [])
            ],
            key=lambda item: item["sku"],
        ),
    }


def build_tracks(raw_tracks):
    return {
        "schemaVersion": 1,
        "generatedAt": None,
        "tracks": sorted(
            [
                {
                    "packageId": track["id"],
                    "displayName": track["displayName"],
                    "sourceTrackIds": [],
                    "type": primary_track_type(track.get("disciplines", [])),
                    "supportedTypes": sorted({TRACK_TYPES.get(value, value) for value in track.get("disciplines", [])}),
                }
                for track in raw_tracks.get("tracks", [])
            ],
            key=lambda item: item["packageId"],
        ),
    }


def category_label(value):
    return DISCIPLINE_LABELS.get(value, value or "Unknown")


def primary_track_type(disciplines):
    if not disciplines:
        return None
    return TRACK_TYPES.get(disciplines[0], disciplines[0])


def map_setup_type(value):
    if value is True:
        return "fixed"
    if value is False:
        return "open"
    return "unknown"


def map_license(raw_license):
    result = {"className": license_class_label(raw_license.get("minClass") or "Unknown")}
    if "minSafetyRating" in raw_license:
        result["safetyRating"] = raw_license["minSafetyRating"]
    if "raw" in raw_license:
        result["raw"] = raw_license["raw"]
    return result


def license_class_label(value):
    labels = {"rookie": "Rookie", "pro_wc": "Pro/WC"}
    return labels.get(value, str(value).replace("_", " ").title())


def track_name_fields(display_name):
    if " - " not in display_name:
        return {"trackName": display_name}
    name, config = display_name.rsplit(" - ", 1)
    return {"trackName": name, "trackConfigName": config}


def optional_race_length(raw_length):
    if not raw_length:
        return {}
    if raw_length.get("type") == "laps":
        return {"raceLength": {"laps": raw_length["value"]}}
    if raw_length.get("type") == "minutes":
        return {"raceLength": {"minutes": raw_length["value"]}}
    return {}


def optional_precip(weather):
    if "rainChancePercent" not in weather:
        return {}
    return {"precipChance": weather["rainChancePercent"]}


def map_sessions(raw_schedule):
    if raw_schedule.get("type") == "recurring" and raw_schedule.get("minuteOffsets") and raw_schedule.get("intervalMinutes"):
        return [
            {
                "type": "recurring",
                "firstSessionOffsetMinutes": raw_schedule["minuteOffsets"][0],
                "repeatEveryMinutes": raw_schedule["intervalMinutes"],
            }
        ]
    return []


def display_from_id(value, prefix):
    raw = value.removeprefix(prefix).replace("_", " ")
    return " ".join(part.upper() if len(part) <= 4 else part.capitalize() for part in raw.split())


def add_days(yyyy_mm_dd, days):
    parsed = date.fromisoformat(yyyy_mm_dd)
    return (parsed + timedelta(days=days)).isoformat()
```

- [ ] **Step 5: Run mapper tests**

Run:

```bash
python -m unittest tests.test_pipeline_mapper
```

Expected: `OK`.

- [ ] **Step 6: Refactor generatedAt propagation**

Update `build_mobile_bundle` in `schedule_data_pipeline/mapper.py` so `cars["generatedAt"]` and `tracks["generatedAt"]` are set to `config.generated_at` before returning:

```python
    cars["generatedAt"] = config.generated_at
    tracks["generatedAt"] = config.generated_at
    return {"season": season, "cars": cars, "tracks": tracks}
```

- [ ] **Step 7: Add generatedAt assertions**

Add to `test_build_mobile_bundle_maps_catalogs`:

```python
        self.assertEqual(bundle["cars"]["generatedAt"], "2026-06-26T00:00:00Z")
        self.assertEqual(bundle["tracks"]["generatedAt"], "2026-06-26T00:00:00Z")
```

- [ ] **Step 8: Run mapper tests**

Run:

```bash
python -m unittest tests.test_pipeline_mapper
```

Expected: `OK`.

- [ ] **Step 9: Commit**

Run:

```bash
git add schedule_data_pipeline/models.py schedule_data_pipeline/mapper.py tests/test_pipeline_mapper.py
git commit -m "feat: map raw parser json to mobile contract"
```

## Task 3: Manifest Generation

**Files:**
- Create: `schedule_data_pipeline/manifest.py`
- Create: `tests/test_pipeline_manifest.py`

- [ ] **Step 1: Write failing manifest tests**

Create `tests/test_pipeline_manifest.py`:

```python
import unittest

from schedule_data_pipeline.manifest import build_manifest, checksums_for_files, content_hash_for_bundle
from tests.test_pipeline_mapper import build_fixture_bundle


class ManifestTests(unittest.TestCase):
    def test_content_hash_is_stable_for_same_bundle(self):
        bundle = build_fixture_bundle()

        first = content_hash_for_bundle(bundle)
        second = content_hash_for_bundle(bundle)

        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)

    def test_build_manifest_uses_release_relative_paths_and_revision(self):
        bundle = build_fixture_bundle()
        content_hash = content_hash_for_bundle(bundle)
        revision = content_hash[:8]
        files = {
            f"releases/2026-s3/{revision}/season.json": bundle["season"],
            f"releases/2026-s3/{revision}/cars.json": bundle["cars"],
            f"releases/2026-s3/{revision}/tracks.json": bundle["tracks"],
        }

        manifest = build_manifest(
            season_id="2026-s3",
            generated_at="2026-06-26T00:00:00Z",
            content_hash=content_hash,
            checksums=checksums_for_files(files),
        )

        self.assertEqual(manifest["revision"], revision)
        self.assertEqual(manifest["seasonFile"], f"releases/2026-s3/{revision}/season.json")
        self.assertEqual(manifest["carsFile"], f"releases/2026-s3/{revision}/cars.json")
        self.assertEqual(manifest["tracksFile"], f"releases/2026-s3/{revision}/tracks.json")
        self.assertEqual(
            sorted(manifest["checksums"].keys()),
            [
                f"releases/2026-s3/{revision}/cars.json",
                f"releases/2026-s3/{revision}/season.json",
                f"releases/2026-s3/{revision}/tracks.json",
            ],
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run manifest tests to verify they fail**

Run:

```bash
python -m unittest tests.test_pipeline_manifest
```

Expected: `ERROR` because `schedule_data_pipeline.manifest` does not exist.

- [ ] **Step 3: Implement manifest helpers**

Create `schedule_data_pipeline/manifest.py`:

```python
import hashlib

from schedule_data_pipeline.jsonio import stable_json


def content_hash_for_bundle(bundle):
    payload = "\n".join(stable_json(bundle[name]) for name in ["season", "cars", "tracks"])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def checksum_for_json(value):
    return "sha256:" + hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def checksums_for_files(files):
    return {path: checksum_for_json(value) for path, value in sorted(files.items())}


def release_prefix(season_id, content_hash):
    return f"releases/{season_id}/{content_hash[:8]}"


def build_manifest(season_id, generated_at, content_hash, checksums):
    prefix = release_prefix(season_id, content_hash)
    return {
        "schemaVersion": 1,
        "generatedAt": generated_at,
        "seasonId": season_id,
        "seasonFile": f"{prefix}/season.json",
        "carsFile": f"{prefix}/cars.json",
        "tracksFile": f"{prefix}/tracks.json",
        "revision": content_hash[:8],
        "checksums": checksums,
    }
```

- [ ] **Step 4: Run manifest tests**

Run:

```bash
python -m unittest tests.test_pipeline_manifest
```

Expected: `OK`.

- [ ] **Step 5: Commit**

Run:

```bash
git add schedule_data_pipeline/manifest.py tests/test_pipeline_manifest.py
git commit -m "feat: build mobile data manifest"
```

## Task 4: Frontend Contract Validator

**Files:**
- Create: `schedule_data_pipeline/validator.py`
- Create: `tests/test_pipeline_validator.py`

- [ ] **Step 1: Write failing validator tests**

Create `tests/test_pipeline_validator.py`:

```python
import copy
import unittest

from schedule_data_pipeline.manifest import build_manifest, checksums_for_files, content_hash_for_bundle, release_prefix
from schedule_data_pipeline.validator import validate_mobile_bundle, validate_manifest
from tests.test_pipeline_mapper import build_fixture_bundle


class ValidatorTests(unittest.TestCase):
    def test_validate_mobile_bundle_accepts_fixture_bundle_with_unknown_setup_warning(self):
        warnings = validate_mobile_bundle(build_fixture_bundle())

        self.assertTrue(any(warning["code"] == "setupTypeUnknown" for warning in warnings))

    def test_validate_mobile_bundle_rejects_invalid_setup_type(self):
        bundle = build_fixture_bundle()
        bundle["season"]["series"][0]["setupType"] = "maybe"

        with self.assertRaisesRegex(ValueError, "setupType"):
            validate_mobile_bundle(bundle)

    def test_validate_mobile_bundle_rejects_missing_series_reference(self):
        bundle = build_fixture_bundle()
        bundle["season"]["races"][0]["seriesId"] = "missing"

        with self.assertRaisesRegex(ValueError, "seriesId"):
            validate_mobile_bundle(bundle)

    def test_validate_mobile_bundle_rejects_empty_sessions(self):
        bundle = build_fixture_bundle()
        bundle["season"]["races"][0]["sessions"] = []

        with self.assertRaisesRegex(ValueError, "sessions"):
            validate_mobile_bundle(bundle)

    def test_validate_manifest_rejects_unsafe_reference(self):
        bundle = build_fixture_bundle()
        content_hash = content_hash_for_bundle(bundle)
        prefix = release_prefix("2026-s3", content_hash)
        files = {
            f"{prefix}/season.json": bundle["season"],
            f"{prefix}/cars.json": bundle["cars"],
            f"{prefix}/tracks.json": bundle["tracks"],
        }
        manifest = build_manifest("2026-s3", "2026-06-26T00:00:00Z", content_hash, checksums_for_files(files))
        manifest["seasonFile"] = "../season.json"

        with self.assertRaisesRegex(ValueError, "seasonFile"):
            validate_manifest(manifest, files)

    def test_validate_manifest_rejects_bad_checksum(self):
        bundle = build_fixture_bundle()
        content_hash = content_hash_for_bundle(bundle)
        prefix = release_prefix("2026-s3", content_hash)
        files = {
            f"{prefix}/season.json": bundle["season"],
            f"{prefix}/cars.json": bundle["cars"],
            f"{prefix}/tracks.json": bundle["tracks"],
        }
        manifest = build_manifest("2026-s3", "2026-06-26T00:00:00Z", content_hash, checksums_for_files(files))
        manifest = copy.deepcopy(manifest)
        manifest["checksums"][f"{prefix}/season.json"] = "sha256:bad"

        with self.assertRaisesRegex(ValueError, "checksum"):
            validate_manifest(manifest, files)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run validator tests to verify they fail**

Run:

```bash
python -m unittest tests.test_pipeline_validator
```

Expected: `ERROR` because `schedule_data_pipeline.validator` does not exist.

- [ ] **Step 3: Implement validator**

Create `schedule_data_pipeline/validator.py`:

```python
from schedule_data_pipeline.manifest import checksum_for_json


VALID_SETUP_TYPES = {"fixed", "open", "unknown"}
VALID_START_TYPES = {"rolling", "standing", "unknown"}
VALID_SESSION_TYPES = {"recurring", "setTimes"}


def validate_mobile_bundle(bundle):
    warnings = []
    season = require_object(bundle, "season")
    series_items = require_list(season, "series")
    race_items = require_list(season, "races")
    week_items = require_list(season, "weeks")
    car_items = require_list(require_object(bundle, "cars"), "cars")
    track_items = require_list(require_object(bundle, "tracks"), "tracks")

    series_ids = {item["seriesId"] for item in series_items}
    week_numbers = {item["weekNumber"] for item in week_items}
    car_skus = {item["sku"] for item in car_items}
    track_ids = {item["packageId"] for item in track_items}
    race_ids = {item["raceId"] for item in race_items}

    for series in series_items:
        require_non_empty_string(series, "seriesId")
        require_non_empty_string(series, "name")
        validate_enum(series, "setupType", VALID_SETUP_TYPES)
        validate_enum(series, "startType", VALID_START_TYPES)
        if series["setupType"] == "unknown":
            warnings.append({"code": "setupTypeUnknown", "message": f"Setup type needs review for {series['name']}"})
        if series["startType"] == "unknown":
            warnings.append({"code": "startTypeUnknown", "message": f"Start type needs review for {series['name']}"})
        for race_id in require_list(series, "raceIds"):
            if race_id not in race_ids:
                raise ValueError(f"series.raceIds references missing raceId: {race_id}")

    series_with_races = {race["seriesId"] for race in race_items}
    for series_id in series_ids:
        if series_id not in series_with_races:
            raise ValueError(f"series has no races: {series_id}")

    weeks_with_races = {race["weekNumber"] for race in race_items}
    for week_number in week_numbers:
        if week_number not in weeks_with_races:
            raise ValueError(f"week has no races: {week_number}")

    for race in race_items:
        require_non_empty_string(race, "raceId")
        if race["seriesId"] not in series_ids:
            raise ValueError(f"race.seriesId references missing seriesId: {race['seriesId']}")
        if race["weekNumber"] not in week_numbers:
            raise ValueError(f"race.weekNumber references missing weekNumber: {race['weekNumber']}")
        if race["trackPackageId"] not in track_ids:
            raise ValueError(f"race.trackPackageId references missing track: {race['trackPackageId']}")
        for sku in require_list(race, "carSkus"):
            if sku not in car_skus:
                raise ValueError(f"race.carSkus references missing car: {sku}")
        validate_enum(race, "setupType", VALID_SETUP_TYPES)
        validate_enum(race, "startType", VALID_START_TYPES)
        sessions = require_list(race, "sessions")
        if not sessions:
            raise ValueError(f"race.sessions must not be empty: {race['raceId']}")
        for session in sessions:
            validate_enum(session, "type", VALID_SESSION_TYPES)

    return warnings


def validate_manifest(manifest, files):
    for field in ["seasonFile", "carsFile", "tracksFile"]:
        ref = manifest.get(field)
        validate_safe_reference(field, ref)
        if ref not in files:
            raise ValueError(f"{field} references missing file: {ref}")
        expected_checksum = checksum_for_json(files[ref])
        actual_checksum = manifest.get("checksums", {}).get(ref)
        if actual_checksum != expected_checksum:
            raise ValueError(f"manifest checksum mismatch for {ref}")


def validate_safe_reference(field, ref):
    if not isinstance(ref, str) or not ref:
        raise ValueError(f"{field} must be a non-empty relative path")
    if ref.startswith("/") or "://" in ref or ref.startswith("..") or "/../" in ref or ref.endswith("/.."):
        raise ValueError(f"{field} must be a safe relative path: {ref}")


def require_object(parent, field):
    value = parent.get(field)
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def require_list(parent, field):
    value = parent.get(field)
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    return value


def require_non_empty_string(parent, field):
    value = parent.get(field)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")


def validate_enum(parent, field, allowed):
    value = parent.get(field)
    if value not in allowed:
        raise ValueError(f"{field} must be one of {sorted(allowed)}")
```

- [ ] **Step 4: Run validator tests**

Run:

```bash
python -m unittest tests.test_pipeline_validator
```

Expected: `OK`.

- [ ] **Step 5: Commit**

Run:

```bash
git add schedule_data_pipeline/validator.py tests/test_pipeline_validator.py
git commit -m "feat: validate mobile schedule contract"
```

## Task 5: Build And Validate CLI

**Files:**
- Create: `schedule_data_pipeline/cli.py`
- Create: `tests/test_pipeline_cli.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Write failing CLI tests**

Create `tests/test_pipeline_cli.py`:

```python
import json
from pathlib import Path
import tempfile
import unittest

from schedule_data_pipeline.cli import run


FIXTURE_DIR = Path("tests/fixtures/raw_pipeline")


class PipelineCliTests(unittest.TestCase):
    def test_build_writes_manifest_and_release_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exit_code = run(
                [
                    "build",
                    "--raw-dir",
                    str(FIXTURE_DIR),
                    "--output-dir",
                    tmpdir,
                    "--season-id",
                    "2026-s3",
                    "--season-name",
                    "2026 Season 3",
                    "--season-start",
                    "2026-06-16",
                    "--season-end",
                    "2026-09-08",
                    "--generated-at",
                    "2026-06-26T00:00:00Z",
                ]
            )

            self.assertEqual(exit_code, 0)
            manifest_path = Path(tmpdir) / "manifest.json"
            self.assertTrue(manifest_path.exists())
            manifest = json.loads(manifest_path.read_text())
            self.assertEqual(manifest["seasonId"], "2026-s3")
            for field in ["seasonFile", "carsFile", "tracksFile"]:
                self.assertTrue((Path(tmpdir) / manifest[field]).exists(), field)

    def test_validate_accepts_build_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run(
                [
                    "build",
                    "--raw-dir",
                    str(FIXTURE_DIR),
                    "--output-dir",
                    tmpdir,
                    "--season-id",
                    "2026-s3",
                    "--season-name",
                    "2026 Season 3",
                    "--season-start",
                    "2026-06-16",
                    "--season-end",
                    "2026-09-08",
                    "--generated-at",
                    "2026-06-26T00:00:00Z",
                ]
            )

            self.assertEqual(run(["validate", "--mobile-dir", tmpdir]), 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run CLI tests to verify they fail**

Run:

```bash
python -m unittest tests.test_pipeline_cli
```

Expected: `ERROR` because `schedule_data_pipeline.cli` does not exist.

- [ ] **Step 3: Implement CLI build/validate**

Create `schedule_data_pipeline/cli.py`:

```python
import argparse
from datetime import datetime, timezone
from pathlib import Path

from schedule_data_pipeline.jsonio import load_json_file, write_json_file
from schedule_data_pipeline.manifest import build_manifest, checksums_for_files, content_hash_for_bundle, release_prefix
from schedule_data_pipeline.mapper import MappingConfig, build_mobile_bundle
from schedule_data_pipeline.validator import validate_manifest, validate_mobile_bundle


def run(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "build":
        return run_build(args)
    if args.command == "validate":
        return run_validate(args)
    if args.command == "publish":
        from schedule_data_pipeline.publisher import publish_from_disk

        publish_from_disk(args.mobile_dir, args.raw_dir)
        return 0
    parser.error(f"unknown command: {args.command}")


def build_parser():
    parser = argparse.ArgumentParser(description="Build, validate, and publish mobile schedule JSON.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build")
    build.add_argument("--raw-dir", type=Path, required=True)
    build.add_argument("--output-dir", type=Path, required=True)
    build.add_argument("--season-id", default="2026-s3")
    build.add_argument("--season-name", default="2026 Season 3")
    build.add_argument("--season-start", required=True)
    build.add_argument("--season-end", required=True)
    build.add_argument("--generated-at", default=None)

    validate = subparsers.add_parser("validate")
    validate.add_argument("--mobile-dir", type=Path, required=True)

    publish = subparsers.add_parser("publish")
    publish.add_argument("--mobile-dir", type=Path, required=True)
    publish.add_argument("--raw-dir", type=Path, required=True)

    return parser


def run_build(args):
    raw_dir = args.raw_dir
    generated_at = args.generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    config = MappingConfig(
        season_id=args.season_id,
        season_name=args.season_name,
        season_start=args.season_start,
        season_end=args.season_end,
        generated_at=generated_at,
    )
    bundle = build_mobile_bundle(
        raw_season=load_json_file(raw_dir / "season.json"),
        raw_cars=load_json_file(raw_dir / "cars.json"),
        raw_tracks=load_json_file(raw_dir / "tracks.json"),
        raw_car_classes=load_json_file(raw_dir / "car-classes.json"),
        config=config,
    )
    warnings = validate_mobile_bundle(bundle)
    content_hash = content_hash_for_bundle(bundle)
    prefix = release_prefix(args.season_id, content_hash)
    files = {
        f"{prefix}/season.json": bundle["season"],
        f"{prefix}/cars.json": bundle["cars"],
        f"{prefix}/tracks.json": bundle["tracks"],
    }
    manifest = build_manifest(args.season_id, generated_at, content_hash, checksums_for_files(files))
    validate_manifest(manifest, files)

    output_dir = args.output_dir
    for relative_path, value in files.items():
        write_json_file(output_dir / relative_path, value)
    write_json_file(output_dir / "manifest.json", manifest)
    for warning in warnings:
        print(f"WARNING {warning['code']}: {warning['message']}")
    print(f"Built mobile JSON release {manifest['revision']} at {output_dir}")
    return 0


def run_validate(args):
    mobile_dir = args.mobile_dir
    manifest = load_json_file(mobile_dir / "manifest.json")
    files = {
        manifest["seasonFile"]: load_json_file(mobile_dir / manifest["seasonFile"]),
        manifest["carsFile"]: load_json_file(mobile_dir / manifest["carsFile"]),
        manifest["tracksFile"]: load_json_file(mobile_dir / manifest["tracksFile"]),
    }
    validate_manifest(manifest, files)
    validate_mobile_bundle({"season": files[manifest["seasonFile"]], "cars": files[manifest["carsFile"]], "tracks": files[manifest["tracksFile"]]})
    print(f"Validated mobile JSON release {manifest['revision']}")
    return 0


def main():
    raise SystemExit(run())


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Add package script**

Modify `pyproject.toml`:

```toml
[project.scripts]
iracing-schedule-pdf = "pdf_schedule_parser.cli:main"
iracing-schedule-data = "schedule_data_pipeline.cli:main"
```

Modify package discovery:

```toml
[tool.setuptools.packages.find]
include = ["pdf_schedule_parser*", "schedule_data_pipeline*"]
```

- [ ] **Step 5: Run CLI tests**

Run:

```bash
python -m unittest tests.test_pipeline_cli
```

Expected: `OK`.

- [ ] **Step 6: Run all pipeline tests so far**

Run:

```bash
python -m unittest tests.test_pipeline_mapper tests.test_pipeline_manifest tests.test_pipeline_validator tests.test_pipeline_cli
```

Expected: `OK`.

- [ ] **Step 7: Commit**

Run:

```bash
git add schedule_data_pipeline/cli.py tests/test_pipeline_cli.py pyproject.toml
git commit -m "feat: add mobile json pipeline cli"
```

## Task 6: Supabase Publisher

**Files:**
- Create: `schedule_data_pipeline/publisher.py`
- Create: `tests/test_pipeline_publisher.py`

- [ ] **Step 1: Write failing publisher tests**

Create `tests/test_pipeline_publisher.py`:

```python
import unittest

from schedule_data_pipeline.publisher import SupabasePublisher, UploadFailure


class FakeTransport:
    def __init__(self, fail_on_path=None):
        self.fail_on_path = fail_on_path
        self.calls = []

    def request(self, method, url, headers=None, data=None):
        self.calls.append({"method": method, "url": url, "headers": headers or {}, "data": data})
        if self.fail_on_path and self.fail_on_path in url:
            return FakeResponse(500, b"upload failed")
        return FakeResponse(200, b"{}")


class FakeResponse:
    def __init__(self, status, body):
        self.status = status
        self.body = body

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class PublisherTests(unittest.TestCase):
    def test_publish_uploads_manifest_last(self):
        transport = FakeTransport()
        publisher = SupabasePublisher(
            supabase_url="https://example.supabase.co",
            service_role_key="secret",
            bucket="planner-data",
            transport=transport,
        )

        publisher.publish(
            release_files={
                "data/mobile/v1/releases/2026-s3/abc123/season.json": b"{}",
                "data/mobile/v1/releases/2026-s3/abc123/cars.json": b"{}",
            },
            raw_files={
                "data/raw/pdf-parser/releases/2026-s3/abc123/parser-report.json": b"{}",
            },
            manifest_path="data/mobile/v1/manifest.json",
            manifest_bytes=b"{}",
        )

        uploaded_paths = [call["url"].split("/planner-data/")[1] for call in transport.calls if call["method"] == "POST"]
        self.assertEqual(uploaded_paths[-1], "data/mobile/v1/manifest.json")

    def test_publish_does_not_upload_manifest_when_release_upload_fails(self):
        transport = FakeTransport(fail_on_path="season.json")
        publisher = SupabasePublisher(
            supabase_url="https://example.supabase.co",
            service_role_key="secret",
            bucket="planner-data",
            transport=transport,
        )

        with self.assertRaises(UploadFailure):
            publisher.publish(
                release_files={"data/mobile/v1/releases/2026-s3/abc123/season.json": b"{}"},
                raw_files={},
                manifest_path="data/mobile/v1/manifest.json",
                manifest_bytes=b"{}",
            )

        uploaded_paths = [call["url"].split("/planner-data/")[1] for call in transport.calls if call["method"] == "POST"]
        self.assertNotIn("data/mobile/v1/manifest.json", uploaded_paths)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run publisher tests to verify they fail**

Run:

```bash
python -m unittest tests.test_pipeline_publisher
```

Expected: `ERROR` because `schedule_data_pipeline.publisher` does not exist.

- [ ] **Step 3: Implement publisher**

Create `schedule_data_pipeline/publisher.py`:

```python
import os
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


class UploadFailure(RuntimeError):
    pass


class UrlopenTransport:
    def request(self, method, url, headers=None, data=None):
        request = Request(url=url, method=method, headers=headers or {}, data=data)
        return urlopen(request)


class SupabasePublisher:
    def __init__(self, supabase_url, service_role_key, bucket, transport=None):
        self.supabase_url = supabase_url.rstrip("/")
        self.service_role_key = service_role_key
        self.bucket = bucket
        self.transport = transport or UrlopenTransport()

    def publish(self, release_files, raw_files, manifest_path, manifest_bytes):
        for path, payload in sorted(release_files.items()):
            self.upload(path, payload, upsert=False)
            self.verify_public(path)
        for path, payload in sorted(raw_files.items()):
            self.upload(path, payload, upsert=False)
            self.verify_public(path)
        self.upload(manifest_path, manifest_bytes, upsert=True)
        self.verify_public(manifest_path)

    def upload(self, path, payload, upsert):
        encoded_path = quote(path, safe="/")
        url = f"{self.supabase_url}/storage/v1/object/{self.bucket}/{encoded_path}"
        headers = {
            "Authorization": f"Bearer {self.service_role_key}",
            "Content-Type": "application/json",
            "x-upsert": "true" if upsert else "false",
        }
        with self.transport.request("POST", url, headers=headers, data=payload) as response:
            body = response.read()
            if response.status >= 300:
                raise UploadFailure(f"failed to upload {path}: {response.status} {body.decode('utf-8', errors='replace')}")

    def verify_public(self, path):
        encoded_path = quote(path, safe="/")
        url = f"{self.supabase_url}/storage/v1/object/public/{self.bucket}/{encoded_path}"
        with self.transport.request("GET", url) as response:
            body = response.read()
            if response.status >= 300:
                raise UploadFailure(f"failed to verify {path}: {response.status} {body.decode('utf-8', errors='replace')}")


def publisher_from_env():
    required = ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_STORAGE_BUCKET"]
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise UploadFailure(f"missing required Supabase environment variables: {', '.join(missing)}")
    return SupabasePublisher(
        supabase_url=os.environ["SUPABASE_URL"],
        service_role_key=os.environ["SUPABASE_SERVICE_ROLE_KEY"],
        bucket=os.environ["SUPABASE_STORAGE_BUCKET"],
    )


def publish_from_disk(mobile_dir, raw_dir):
    mobile_dir = Path(mobile_dir)
    raw_dir = Path(raw_dir)
    manifest_bytes = (mobile_dir / "manifest.json").read_bytes()
    import json

    manifest = json.loads(manifest_bytes.decode("utf-8"))
    release_files = {
        f"data/mobile/v1/{manifest['seasonFile']}": (mobile_dir / manifest["seasonFile"]).read_bytes(),
        f"data/mobile/v1/{manifest['carsFile']}": (mobile_dir / manifest["carsFile"]).read_bytes(),
        f"data/mobile/v1/{manifest['tracksFile']}": (mobile_dir / manifest["tracksFile"]).read_bytes(),
    }
    revision = manifest["revision"]
    season_id = manifest["seasonId"]
    raw_files = {}
    for name in ["season.json", "cars.json", "tracks.json", "car-classes.json", "parser-report.json"]:
        raw_files[f"data/raw/pdf-parser/releases/{season_id}/{revision}/{name}"] = (raw_dir / name).read_bytes()
    publisher_from_env().publish(
        release_files=release_files,
        raw_files=raw_files,
        manifest_path="data/mobile/v1/manifest.json",
        manifest_bytes=manifest_bytes,
    )
```

- [ ] **Step 4: Run publisher tests**

Run:

```bash
python -m unittest tests.test_pipeline_publisher
```

Expected: `OK`.

- [ ] **Step 5: Run all pipeline tests**

Run:

```bash
python -m unittest discover -s tests
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

Run:

```bash
git add schedule_data_pipeline/publisher.py tests/test_pipeline_publisher.py
git commit -m "feat: publish schedule json to supabase"
```

## Task 7: Workflow And Documentation

**Files:**
- Modify: `.github/workflows/parse-schedule.yml`
- Modify: `README.md`

- [ ] **Step 1: Update workflow paths and environment**

Modify `.github/workflows/parse-schedule.yml` path filters to include:

```yaml
      - "schedule_data_pipeline/**"
      - "docs/superpowers/specs/**"
      - "docs/superpowers/plans/**"
```

Add workflow-level environment:

```yaml
env:
  IWP_SEASON_ID: "2026-s3"
  IWP_SEASON_NAME: "2026 Season 3"
  IWP_SEASON_START: "2026-06-16"
  IWP_SEASON_END: "2026-09-08"
```

- [ ] **Step 2: Add mapper and validator workflow steps**

After `Parse committed PDF`, add:

```yaml
      - name: Build mobile JSON
        run: |
          python -m schedule_data_pipeline.cli build \
            --raw-dir data/generated \
            --output-dir data/mobile/v1 \
            --season-id "$IWP_SEASON_ID" \
            --season-name "$IWP_SEASON_NAME" \
            --season-start "$IWP_SEASON_START" \
            --season-end "$IWP_SEASON_END"

      - name: Validate mobile JSON
        run: python -m schedule_data_pipeline.cli validate --mobile-dir data/mobile/v1
```

Update artifact step:

```yaml
      - name: Upload generated JSON
        uses: actions/upload-artifact@v4
        with:
          name: schedule-json
          path: |
            data/generated/*.json
            data/mobile/v1/**/*.json
          if-no-files-found: error
```

Update generated JSON commit pattern:

```yaml
          file_pattern: data/generated/*.json data/mobile/v1/**/*.json
```

- [ ] **Step 3: Add main/manual Supabase publish step**

After the commit step, add:

```yaml
      - name: Publish mobile JSON to Supabase
        if: github.ref_name == 'main'
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
          SUPABASE_STORAGE_BUCKET: ${{ secrets.SUPABASE_STORAGE_BUCKET }}
        run: python -m schedule_data_pipeline.cli publish --mobile-dir data/mobile/v1 --raw-dir data/generated
```

Keep `workflow_dispatch` enabled. Manual dispatch on non-main will still build/validate/artifact but will not publish unless the run targets `main`.

- [ ] **Step 4: Update README**

Append a section to `README.md`:

````markdown
## Mobile JSON pipeline

The repository has two data layers:

- `data/generated/*.json`: raw parser output for audit/debug.
- `data/mobile/v1/**`: frontend-ready mobile JSON and manifest.

Build locally:

```sh
python -m unittest discover -s tests
python -m pdf_schedule_parser.cli data/source/SeasonSchedule.pdf --output-dir data/generated
python -m schedule_data_pipeline.cli build \
  --raw-dir data/generated \
  --output-dir data/mobile/v1 \
  --season-id 2026-s3 \
  --season-name "2026 Season 3" \
  --season-start 2026-06-16 \
  --season-end 2026-09-08
python -m schedule_data_pipeline.cli validate --mobile-dir data/mobile/v1
```

Publish to Supabase Storage:

```sh
export SUPABASE_URL="https://<project-ref>.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="<service-role-key>"
export SUPABASE_STORAGE_BUCKET="planner-data"
python -m schedule_data_pipeline.cli publish --mobile-dir data/mobile/v1 --raw-dir data/generated
```

The publish command uploads immutable release files first and overwrites `data/mobile/v1/manifest.json` last. If release upload or verification fails, the previous public manifest remains active.
````

- [ ] **Step 5: Run full tests**

Run:

```bash
python -m unittest discover -s tests
```

Expected: all tests pass.

- [ ] **Step 6: Run local end-to-end build against committed PDF**

Run:

```bash
python -m pdf_schedule_parser.cli data/source/SeasonSchedule.pdf --output-dir data/generated
python -m schedule_data_pipeline.cli build --raw-dir data/generated --output-dir data/mobile/v1 --season-id 2026-s3 --season-name "2026 Season 3" --season-start 2026-06-16 --season-end 2026-09-08
python -m schedule_data_pipeline.cli validate --mobile-dir data/mobile/v1
```

Expected:

- parser prints parsed series/counts
- build prints release revision
- validate prints `Validated mobile JSON release <revision>`
- `data/mobile/v1/manifest.json` exists
- manifest references all three release files

- [ ] **Step 7: Run whitespace check**

Run:

```bash
git diff --check
```

Expected: no output.

- [ ] **Step 8: Commit**

Run:

```bash
git add .github/workflows/parse-schedule.yml README.md data/generated data/mobile/v1
git commit -m "ci: build and publish mobile schedule json"
```

## Task 8: Final Verification

**Files:**
- No new files unless fixes are required.

- [ ] **Step 1: Run full test suite**

Run:

```bash
python -m unittest discover -s tests
```

Expected: all tests pass.

- [ ] **Step 2: Run full local pipeline**

Run:

```bash
python -m pdf_schedule_parser.cli data/source/SeasonSchedule.pdf --output-dir data/generated
python -m schedule_data_pipeline.cli build --raw-dir data/generated --output-dir data/mobile/v1 --season-id 2026-s3 --season-name "2026 Season 3" --season-start 2026-06-16 --season-end 2026-09-08
python -m schedule_data_pipeline.cli validate --mobile-dir data/mobile/v1
```

Expected: all three commands exit 0.

- [ ] **Step 3: Inspect manifest**

Run:

```bash
python -m json.tool data/mobile/v1/manifest.json
```

Expected:

- `seasonId` is `2026-s3`
- `revision` is 8 characters
- `seasonFile`, `carsFile`, and `tracksFile` start with `releases/2026-s3/`
- all referenced local files exist

- [ ] **Step 4: Verify publish fails clearly without secrets**

Run:

```bash
python -m schedule_data_pipeline.cli publish --mobile-dir data/mobile/v1 --raw-dir data/generated
```

Expected: fails with a clear message naming missing Supabase environment variables.

- [ ] **Step 5: Run git checks**

Run:

```bash
git status --short
git diff --check
```

Expected:

- only intentional generated JSON changes are present
- whitespace check has no output

## Self-Review Notes

- Spec coverage: tasks cover mapper, manifest, validation, publisher, GitHub Actions, README, local commands, generated frontend JSON, immutable release paths, raw audit publish, and manifest-last behavior.
- Placeholder scan: no task uses `TBD`, `TODO`, "similar to", or unexpanded "write tests for this" language.
- Type consistency: plan consistently uses `MappingConfig`, `build_mobile_bundle`, `content_hash_for_bundle`, `build_manifest`, `validate_mobile_bundle`, `validate_manifest`, `SupabasePublisher`, and `run`.
