import hashlib
import json
from datetime import datetime, timezone

from pdf_schedule_parser.ids import stable_id


def build_output_bundle(series, warnings, source_pdf):
    season = build_season(series)
    cars = build_cars(series)
    tracks = build_tracks(series)
    car_classes = build_car_classes(series)

    public_parts = {
        "season": season,
        "cars": cars,
        "tracks": tracks,
        "car-classes": car_classes,
    }
    content_hash = compute_content_hash(public_parts)
    report = build_report(series, warnings, source_pdf, content_hash, cars, tracks, car_classes)

    return {
        **public_parts,
        "parser-report": report,
    }


def build_season(series):
    dates = [week.start_date for item in series for week in item.weeks]
    return {
        "schemaVersion": 1,
        "season": {
            "id": "2026-s3",
            "name": "2026 Season 3",
            "startDate": min(dates) if dates else None,
            "endDate": max(dates) if dates else None,
        },
        "series": [series_to_json(item) for item in series],
    }


def series_to_json(series):
    return {
        "id": series.id,
        "name": series.name,
        "discipline": series.discipline,
        "fixedSetup": series.fixed_setup,
        "fixedSetupSource": series.fixed_setup_source,
        "startType": series.start_type,
        "startTypeSource": series.start_type_source,
        "license": series.license,
        "carClassIds": series.car_class_ids,
        "carIds": series.car_ids,
        "schedule": series.schedule,
        "official": series.official,
        "weeks": [week_to_json(week) for week in series.weeks],
    }


def week_to_json(week):
    result = {
        "week": week.week,
        "startDate": week.start_date,
        "trackId": stable_id("track", week.track_name),
        "trackName": week.track_name,
    }
    if week.race_length is not None:
        result["raceLength"] = week.race_length
    if week.weather:
        result["weather"] = week.weather
    return result


def build_cars(series):
    records = {}
    for item in series:
        for car_id in item.car_ids:
            records.setdefault(
                car_id,
                {
                    "id": car_id,
                    "name": display_name_from_id(car_id, "car_"),
                    "disciplines": set(),
                    "mappingStatus": "fallback",
                },
            )["disciplines"].add(item.discipline)

    return {
        "schemaVersion": 1,
        "cars": sorted(finalize_disciplines(records.values()), key=lambda item: item["id"]),
    }


def build_tracks(series):
    records = {}
    for item in series:
        for week in item.weeks:
            track_id = stable_id("track", week.track_name)
            name, config = split_track_name(week.track_name)
            records.setdefault(
                track_id,
                {
                    "id": track_id,
                    "name": name,
                    "config": config,
                    "displayName": week.track_name,
                    "disciplines": set(),
                    "mappingStatus": "fallback",
                },
            )["disciplines"].add(item.discipline)

    return {
        "schemaVersion": 1,
        "tracks": sorted(finalize_disciplines(records.values()), key=lambda item: item["id"]),
    }


def build_car_classes(series):
    records = {}
    for item in series:
        for class_id in item.car_class_ids:
            records.setdefault(
                class_id,
                {
                    "id": class_id,
                    "name": display_name_from_id(class_id, "car_class_"),
                    "carIds": set(),
                    "disciplines": set(),
                    "mappingStatus": "fallback",
                },
            )
            records[class_id]["carIds"].update(item.car_ids)
            records[class_id]["disciplines"].add(item.discipline)

    values = []
    for record in records.values():
        record = dict(record)
        record["carIds"] = sorted(record["carIds"])
        record["disciplines"] = sorted(record["disciplines"])
        values.append(record)

    return {"schemaVersion": 1, "carClasses": sorted(values, key=lambda item: item["id"])}


def build_report(series, warnings, source_pdf, content_hash, cars, tracks, car_classes):
    return {
        "schemaVersion": 1,
        "sourcePdf": source_pdf,
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "contentHash": content_hash,
        "counts": {
            "series": len(series),
            "cars": len(cars["cars"]),
            "tracks": len(tracks["tracks"]),
            "carClasses": len(car_classes["carClasses"]),
            "warnings": len(warnings),
        },
        "warnings": [warning.to_json() for warning in warnings],
    }


def compute_content_hash(parts):
    payload = "\n".join(stable_json(parts[name]) for name in ["season", "cars", "tracks", "car-classes"])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def stable_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def finalize_disciplines(records):
    finalized = []
    for record in records:
        item = dict(record)
        item["disciplines"] = sorted(item["disciplines"])
        finalized.append(item)
    return finalized


def display_name_from_id(value, prefix):
    name = value.removeprefix(prefix).replace("_", " ").strip()
    return " ".join(word.upper() if len(word) <= 3 else word.capitalize() for word in name.split())


def split_track_name(display_name):
    if " - " not in display_name:
        return display_name, None
    name, config = display_name.rsplit(" - ", 1)
    return name, config
