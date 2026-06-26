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
    validate_mobile_bundle(
        {
            "season": files[manifest["seasonFile"]],
            "cars": files[manifest["carsFile"]],
            "tracks": files[manifest["tracksFile"]],
        }
    )
    print(f"Validated mobile JSON release {manifest['revision']}")
    return 0


def main():
    raise SystemExit(run())


if __name__ == "__main__":
    main()
