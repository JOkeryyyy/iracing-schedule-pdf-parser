import argparse
import json
from pathlib import Path

from pdf_schedule_parser.extract import extract_pdf_text
from pdf_schedule_parser.models import ExtractedPage
from pdf_schedule_parser.normalize import build_output_bundle
from pdf_schedule_parser.parse import parse_pages
from pdf_schedule_parser.validate import validate_bundle


OUTPUT_FILES = {
    "season": "season.json",
    "cars": "cars.json",
    "tracks": "tracks.json",
    "car-classes": "car-classes.json",
    "parser-report": "parser-report.json",
}


def run(argv=None):
    args = parse_args(argv)
    pages = load_pages(args)
    parse_result = parse_pages(pages)
    source = str(args.text_fixture or args.pdf_path)
    bundle = build_output_bundle(parse_result.series, parse_result.warnings, source_pdf=source)
    validate_bundle(bundle)
    write_json_files(bundle, args.output_dir)

    report = bundle["parser-report"]
    print(
        "Parsed {series} series, {tracks} tracks, {cars} cars, {warnings} warnings".format(
            **report["counts"]
        )
    )
    return 0


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Parse iRacing season schedule PDF into JSON.")
    parser.add_argument("pdf_path", nargs="?", type=Path)
    parser.add_argument("--text-fixture", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("output/schedule"))
    args = parser.parse_args(argv)

    if args.pdf_path is None and args.text_fixture is None:
        parser.error("provide a PDF path or --text-fixture")
    if args.pdf_path is not None and args.text_fixture is not None:
        parser.error("provide either a PDF path or --text-fixture, not both")
    return args


def load_pages(args):
    if args.text_fixture:
        return [ExtractedPage(page=1, text=args.text_fixture.read_text())]
    return extract_pdf_text(args.pdf_path)


def write_json_files(bundle, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    for key, filename in OUTPUT_FILES.items():
        path = output_dir / filename
        path.write_text(json.dumps(bundle[key], indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def main():
    raise SystemExit(run())


if __name__ == "__main__":
    main()
