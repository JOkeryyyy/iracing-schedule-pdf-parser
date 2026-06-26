# Mobile JSON Mapper And Supabase Pipeline Design

## Summary

Build an automatic static-data pipeline in this repository:

```text
data/source/SeasonSchedule.pdf
  -> PDF parser
  -> raw parser JSON
  -> mobile JSON mapper
  -> contract validation
  -> immutable Supabase Storage release files
  -> manifest.json update
```

This is not a backend service. The mapper runs at build time in GitHub Actions when the committed PDF or pipeline code changes. Supabase is used as public static JSON hosting only.

## Goals

- Generate frontend-ready JSON from the raw parser JSON in this repository.
- Keep parser output and frontend output as separate layers.
- Publish immutable release files to Supabase Storage after validation passes.
- Update the stable mobile manifest only after all release files upload successfully.
- Keep the mobile app unaware of PDF parser quirks.
- Keep Supabase credentials in GitHub Actions secrets only.

## Non-Goals

- No Supabase Edge Function mapper.
- No runtime API for schedule data.
- No SQL transformation layer.
- No mobile-side mapping from raw parser JSON.
- No user account, favorites, owned content, or reminder sync data.

## Repository Ownership

The data parser repository owns the full data production flow:

```text
/Users/gaojiahao/Documents/GitHub/tools
  data/source/SeasonSchedule.pdf
  data/generated/*.json
  data/mobile/v1/**
  pdf_schedule_parser/**
  schedule_data_pipeline/**
```

The mobile repository consumes only the generated mobile contract:

```text
manifest.json
season.json
cars.json
tracks.json
```

The mobile repository must not import or duplicate the raw parser schema.

## Pipeline Architecture

Add a new package for post-parse pipeline work:

```text
schedule_data_pipeline/
  __init__.py
  mapper.py
  manifest.py
  validator.py
  publisher.py
  cli.py
```

Responsibilities:

- `mapper.py`: convert raw parser JSON into frontend-ready `season`, `cars`, and `tracks` objects.
- `manifest.py`: compute content hashes and build manifest metadata.
- `validator.py`: validate links, required fields, enum values, and checksums.
- `publisher.py`: upload files to Supabase Storage using CI secrets.
- `cli.py`: expose build and publish commands for local usage and GitHub Actions.

Keep `pdf_schedule_parser/` focused on PDF extraction and raw normalization.

## Data Layers

### Raw Parser Layer

Existing output remains available for audit/debug:

```text
data/generated/season.json
data/generated/cars.json
data/generated/tracks.json
data/generated/car-classes.json
data/generated/parser-report.json
```

This layer preserves parser evidence such as:

- `fixedSetup`
- `fixedSetupSource`
- `startType`
- `startTypeSource`
- parser warnings
- raw license text
- raw schedule text

### Frontend Contract Layer

Generate frontend-ready files under:

```text
data/mobile/v1/releases/{seasonId}/{contentHash}/season.json
data/mobile/v1/releases/{seasonId}/{contentHash}/cars.json
data/mobile/v1/releases/{seasonId}/{contentHash}/tracks.json
data/mobile/v1/manifest.json
```

The frontend layer is optimized for app consumption. It uses explicit fields and avoids requiring the app to reconstruct race rows from series/week data.

### Raw Release Layer

Also copy raw parser files to immutable Supabase paths for audit:

```text
data/raw/pdf-parser/releases/{seasonId}/{contentHash}/season.json
data/raw/pdf-parser/releases/{seasonId}/{contentHash}/cars.json
data/raw/pdf-parser/releases/{seasonId}/{contentHash}/tracks.json
data/raw/pdf-parser/releases/{seasonId}/{contentHash}/car-classes.json
data/raw/pdf-parser/releases/{seasonId}/{contentHash}/parser-report.json
```

These raw files are not consumed by the mobile app.

## Frontend JSON Shape

### `manifest.json`

The manifest is the stable app entry point and uses relative file references:

```json
{
  "schemaVersion": 1,
  "generatedAt": "2026-06-26T00:00:00Z",
  "seasonId": "2026-s3",
  "seasonFile": "releases/2026-s3/7b27b33e/season.json",
  "carsFile": "releases/2026-s3/7b27b33e/cars.json",
  "tracksFile": "releases/2026-s3/7b27b33e/tracks.json",
  "revision": "7b27b33e",
  "checksums": {
    "releases/2026-s3/7b27b33e/season.json": "sha256:...",
    "releases/2026-s3/7b27b33e/cars.json": "sha256:...",
    "releases/2026-s3/7b27b33e/tracks.json": "sha256:..."
  }
}
```

The manifest is uploaded last. If publish fails before this step, the app remains on the previous valid release.

### `season.json`

Use top-level `series[]` and flat `races[]`. Races conceptually belong to a series, but the frontend contract must not duplicate full race objects inside each series.

```json
{
  "schemaVersion": 1,
  "generatedAt": "2026-06-26T00:00:00Z",
  "seasonId": "2026-s3",
  "seasonName": "2026 Season 3",
  "seasonStart": "2026-06-16T00:00:00Z",
  "seasonEnd": "2026-09-08T00:00:00Z",
  "weekSeasonStart": "2026-06-16T00:00:00Z",
  "weeks": [
    {
      "weekNumber": 1,
      "startsAt": "2026-06-16T00:00:00Z",
      "endsAt": "2026-06-23T00:00:00Z"
    }
  ],
  "series": [
    {
      "seriesId": "series_mini_stock_rookie_series_by_thrustmaster_2026_s3",
      "name": "Mini Stock Rookie Series by Thrustmaster",
      "category": "Oval",
      "license": {
        "className": "Rookie",
        "safetyRating": 1.0,
        "raw": "Rookie 1.0 --> Pro/WC 4.0"
      },
      "isOfficial": true,
      "setupType": "unknown",
      "setupSource": "unknown",
      "startType": "rolling",
      "startTypeSource": "weatherText",
      "raceIds": [
        "2026-s3-series_mini_stock_rookie_series_by_thrustmaster_2026_s3-w1-track_charlotte_motor_speedway_oval"
      ]
    }
  ],
  "races": [
    {
      "raceId": "2026-s3-series_mini_stock_rookie_series_by_thrustmaster_2026_s3-w1-track_charlotte_motor_speedway_oval",
      "seriesId": "series_mini_stock_rookie_series_by_thrustmaster_2026_s3",
      "seriesName": "Mini Stock Rookie Series by Thrustmaster",
      "category": "Oval",
      "weekNumber": 1,
      "startsAt": "2026-06-16T00:00:00Z",
      "endsAt": "2026-06-23T00:00:00Z",
      "trackPackageId": "track_charlotte_motor_speedway_oval",
      "trackName": "Charlotte Motor Speedway",
      "trackConfigName": "Oval",
      "carSkus": [
        "car_mini_stock"
      ],
      "carClasses": [
        "Mini Stock"
      ],
      "setupType": "unknown",
      "setupSource": "unknown",
      "startType": "rolling",
      "startTypeSource": "weatherText",
      "raceLength": {
        "laps": 15
      },
      "precipChance": 0,
      "sessions": [
        {
          "type": "recurring",
          "firstSessionOffsetMinutes": 15,
          "repeatEveryMinutes": 30
        }
      ]
    }
  ]
}
```

### `cars.json`

Map raw parser car IDs into app catalog IDs:

```json
{
  "schemaVersion": 1,
  "generatedAt": "2026-06-26T00:00:00Z",
  "cars": [
    {
      "sku": "car_mini_stock",
      "displayName": "Mini Stock",
      "categories": [
        "Oval"
      ],
      "carClasses": [
        "Mini Stock"
      ]
    }
  ]
}
```

### `tracks.json`

Map raw parser track IDs into app track package IDs:

```json
{
  "schemaVersion": 1,
  "generatedAt": "2026-06-26T00:00:00Z",
  "tracks": [
    {
      "packageId": "track_charlotte_motor_speedway_oval",
      "displayName": "Charlotte Motor Speedway - Oval",
      "sourceTrackIds": [],
      "type": "oval",
      "supportedTypes": [
        "oval"
      ]
    }
  ]
}
```

## Mapping Rules

- `seasonId` is configured explicitly for MVP, defaulting to `2026-s3`.
- `seasonStart` and `seasonEnd` are configured explicitly for MVP through CLI flags or environment variables. For the current 2026 Season 3 feed, use the dates from the official season schedule rather than deriving bounds from all parsed rows, because the PDF includes special year-long series that create date outliers.
- `weekSeasonStart` defaults to `seasonStart`.
- `contentHash` is SHA-256 over frontend `season`, `cars`, and `tracks` JSON.
- `revision` is the first 8 characters of `contentHash`.
- Raw parser `discipline` maps to display category:
  - `oval` -> `Oval`
  - `sports_car` -> `Sports Car`
  - `formula_car` -> `Formula Car`
  - `dirt_oval` -> `Dirt Oval`
  - `dirt_road` -> `Dirt Road`
  - `unranked` -> `Unranked`
- Raw parser `fixedSetup` maps to:
  - `true` -> `setupType: "fixed"`
  - `false` -> `setupType: "open"`
  - `null` -> `setupType: "unknown"`
- Preserve `fixedSetupSource` as `setupSource`.
- Preserve `startType` and `startTypeSource`.
- Race rows are generated from each raw series week.
- Race start/end timestamps are derived from raw week `startDate` as UTC midnight and plus 7 days.
- Track display names are split on the final ` - `:
  - left side -> `trackName`
  - right side -> `trackConfigName`
  - full raw display name remains in `tracks[].displayName`
- Raw race length maps to either `raceLength.laps` or `raceLength.minutes`.
- Raw weather `rainChancePercent` maps to `precipChance`.
- Raw recurring schedules map to `sessions[].type = "recurring"` with:
  - first offset = first `minuteOffsets` value
  - repeat interval = `intervalMinutes`
- If no schedule can be normalized, validation fails for that race.

## Validation Rules

Validation must run before any Supabase upload.

Fail the pipeline if:

- Any required file is missing.
- Any JSON file cannot be parsed.
- Any top-level `schemaVersion` is unsupported.
- Any race references a missing series, week, car, or track.
- Any series has no races.
- Any week has no races.
- `setupType` is not `fixed`, `open`, or `unknown`.
- `startType` is not `rolling`, `standing`, or `unknown`.
- Any race has an empty `sessions[]`.
- Manifest file references are absolute URLs, start with `/`, contain `..`, or point outside the release directory.
- Manifest checksums do not match generated files.

Warn but do not fail if:

- `setupType` is `unknown`.
- `startType` is `unknown`.
- raw parser warnings exist in `parser-report.json`.
- a catalog item uses fallback IDs because the PDF lacks official iRacing IDs.

Warnings are printed in CI and included in a generated report.

## Supabase Publish Strategy

Publish to one public Storage bucket named `planner-data`.

Release files are immutable:

```text
data/mobile/v1/releases/{seasonId}/{contentHash}/season.json
data/mobile/v1/releases/{seasonId}/{contentHash}/cars.json
data/mobile/v1/releases/{seasonId}/{contentHash}/tracks.json
```

Raw audit files are immutable:

```text
data/raw/pdf-parser/releases/{seasonId}/{contentHash}/...
```

Only this pointer is overwritten:

```text
data/mobile/v1/manifest.json
```

Upload order:

1. Upload frontend release files.
2. Upload raw audit release files.
3. Verify uploaded release files can be fetched.
4. Upload `manifest.json`.
5. Verify public manifest and all referenced files can be fetched.

If any step before manifest upload fails, leave the existing manifest unchanged.

## GitHub Actions Design

Extend the existing workflow or add a dedicated publish workflow.

### Pull Request And Branch Push

Run on changes to:

- `data/source/SeasonSchedule.pdf`
- `pdf_schedule_parser/**`
- `schedule_data_pipeline/**`
- `tests/**`
- `pyproject.toml`
- workflow files

Steps:

```text
checkout
setup-python
pip install -e .
run tests
parse committed PDF to data/generated
map raw JSON to data/mobile/v1
validate frontend JSON
upload generated JSON artifacts
commit generated JSON back to non-main update branches
```

### Main Branch Publish

Run after merge to `main` and on manual `workflow_dispatch`.

Steps:

```text
checkout
setup-python
pip install -e .
run tests
parse committed PDF to data/generated
map raw JSON to data/mobile/v1
validate frontend JSON
publish to Supabase Storage
smoke-test public manifest and referenced files
```

Use GitHub Actions secrets:

```text
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
SUPABASE_STORAGE_BUCKET
```

Optional environment variables:

```text
IWP_SEASON_ID=2026-s3
IWP_SEASON_START=2026-06-16
IWP_SEASON_END=2026-09-08
IWP_MOBILE_BASE_PATH=data/mobile/v1
IWP_RAW_BASE_PATH=data/raw/pdf-parser
```

## Local Commands

Expected local workflow after implementation:

```sh
python -m unittest discover -s tests
python -m pdf_schedule_parser.cli data/source/SeasonSchedule.pdf --output-dir data/generated
python -m schedule_data_pipeline.cli build --raw-dir data/generated --output-dir data/mobile/v1 --season-id 2026-s3
python -m schedule_data_pipeline.cli validate --mobile-dir data/mobile/v1
```

Publish is available but requires explicit credentials:

```sh
python -m schedule_data_pipeline.cli publish --mobile-dir data/mobile/v1 --raw-dir data/generated
```

Local publish fails clearly if required Supabase environment variables are missing.

## Testing Strategy

Add unit tests for:

- setup type mapping
- start type preservation
- discipline/category mapping
- track name/config splitting
- race row generation from raw series weeks
- session rule mapping
- content hash and manifest generation
- validation failure for missing cross-references
- validation failure for invalid enum values

Add CLI tests for:

- build command writes `manifest.json`, `season.json`, `cars.json`, and `tracks.json`
- validate command accepts generated output
- validate command rejects unsafe manifest references

Add publisher tests with a fake HTTP client:

- release files upload before manifest
- manifest is not uploaded if a release upload fails
- public smoke checks use manifest references

## Mobile Compatibility

The mobile app currently consumes the manifest, season, cars, and tracks contract. This pipeline intentionally outputs those files directly.

Because the frontend contract adds `setupType`, `setupSource`, `startType`, `startTypeSource`, `seriesName`, and `category` to race/series rows, the mobile repository must later update DTO/domain/mapper code before using the published production feed with strict JSON decoding.

Until that mobile change lands, the generated feed is the target contract but may not decode in the current app build.

## Failure Behavior

- Parser failure stops the workflow.
- Mapper failure stops the workflow.
- Validation failure stops the workflow.
- Supabase upload failure stops the workflow.
- Manifest upload is skipped unless all release files upload and verify successfully.
- Existing public manifest remains valid after failed publish.

## Rollout Plan

1. Implement mapper and validation locally.
2. Generate frontend JSON from current committed PDF.
3. Update workflow to build and validate frontend JSON on PRs.
4. Add Supabase publish step for `main` and manual dispatch.
5. Configure GitHub Actions secrets.
6. Run manual dispatch once against the existing Supabase bucket.
7. Verify public manifest and referenced JSON URLs.

## Implementation Defaults

- Supabase bucket name: `planner-data`.
- Short revision hash length: 8 characters.
- Generated frontend files under `data/mobile/v1/**` are committed back to non-main update branches, matching the existing `data/generated/*.json` workflow.
- Supabase publish runs only on `main` pushes and manual dispatch after validation succeeds.
