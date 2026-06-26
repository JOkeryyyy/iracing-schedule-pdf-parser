# iRacing Schedule PDF Parser

Standalone Python project for converting an iRacing season schedule PDF into the JSON bundle consumed by the planner data pipeline.

## Outputs

The parser writes these files to the selected output directory:

- `season.json`
- `cars.json`
- `tracks.json`
- `car-classes.json`
- `parser-report.json`

## Local usage

From this repository root:

```sh
python3 -m unittest discover -s tests
python3 -m pdf_schedule_parser.cli data/source/SeasonSchedule.pdf --output-dir data/generated
```

For editable installation:

```sh
python3 -m pip install -e .
iracing-schedule-pdf data/source/SeasonSchedule.pdf --output-dir data/generated
```

The compatibility wrapper also works from the repository root:

```sh
python3 parse_schedule_pdf.py data/source/SeasonSchedule.pdf --output-dir data/generated
```

## GitHub Actions

The workflow tests the parser, parses `data/source/SeasonSchedule.pdf`, uploads the generated JSON bundle as an artifact, and commits `data/generated/*.json` back to non-`main` update branches when the PDF changes.

Main is intended to be protected. Update the PDF on a branch, let Actions commit the regenerated JSON to that branch, then merge through a pull request after the parse workflow passes.
