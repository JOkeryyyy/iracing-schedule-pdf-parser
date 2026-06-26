# iRacing Schedule PDF Parser

Standalone Python project for converting an iRacing season schedule PDF into JSON consumed by the planner data pipeline.

## Outputs

The parser writes raw audit/debug files to the selected output directory:

- `season.json`
- `cars.json`
- `tracks.json`
- `car-classes.json`
- `parser-report.json`

The mobile JSON pipeline then writes frontend-ready files under:

- `data/mobile/v1/manifest.json`
- `data/mobile/v1/releases/<season-id>/<revision>/season.json`
- `data/mobile/v1/releases/<season-id>/<revision>/cars.json`
- `data/mobile/v1/releases/<season-id>/<revision>/tracks.json`

## Local usage

From this repository root:

```sh
python3 -m unittest discover -s tests
python3 -m pdf_schedule_parser.cli data/source/SeasonSchedule.pdf --output-dir data/generated
python3 -m schedule_data_pipeline.cli build \
  --raw-dir data/generated \
  --output-dir data/mobile/v1 \
  --season-id 2026-s3 \
  --season-name "2026 Season 3" \
  --season-start 2026-06-16 \
  --season-end 2026-09-08 \
  --generated-at "$(date -u -r "$(git log -1 --format=%ct -- data/source/SeasonSchedule.pdf)" +%Y-%m-%dT%H:%M:%SZ)"
python3 -m schedule_data_pipeline.cli validate --mobile-dir data/mobile/v1
```

For editable installation:

```sh
python3 -m pip install -e .
iracing-schedule-pdf data/source/SeasonSchedule.pdf --output-dir data/generated
iracing-schedule-data build --raw-dir data/generated --output-dir data/mobile/v1 --season-id 2026-s3 --season-name "2026 Season 3" --season-start 2026-06-16 --season-end 2026-09-08 --generated-at "$(date -u -r "$(git log -1 --format=%ct -- data/source/SeasonSchedule.pdf)" +%Y-%m-%dT%H:%M:%SZ)"
```

The compatibility wrapper also works from the repository root:

```sh
python3 parse_schedule_pdf.py data/source/SeasonSchedule.pdf --output-dir data/generated
```

## Supabase publish

Supabase is used as static JSON hosting. The publish command uploads immutable release files first and overwrites `data/mobile/v1/manifest.json` last. If release upload or verification fails, the previous public manifest remains active.

Required environment variables:

```sh
export SUPABASE_URL="https://<project-ref>.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="<service-role-key>"
export SUPABASE_STORAGE_BUCKET="planner-data"
python3 -m schedule_data_pipeline.cli publish --mobile-dir data/mobile/v1 --raw-dir data/generated
```

## GitHub Actions

The workflow tests the parser and data pipeline, parses `data/source/SeasonSchedule.pdf`, builds mobile JSON, validates the contract, uploads generated JSON as an artifact, and commits `data/generated/*.json` plus `data/mobile/v1/**/*.json` back to non-`main` update branches when source data changes.

On `main`, after validation passes, the workflow publishes the immutable mobile release files and raw audit files to Supabase Storage, then updates the public manifest last.

Main is intended to be protected. Update the PDF on a branch, let Actions commit the regenerated JSON to that branch, then merge through a pull request after the parse workflow passes.
