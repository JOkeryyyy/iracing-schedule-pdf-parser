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
                    "carClasses": [
                        class_names_by_id.get(value, display_from_id(value, "car_class_"))
                        for value in raw_series.get("carClassIds", [])
                    ],
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
                "raceIds": sorted(race_ids),
            }
        )

    cars["generatedAt"] = config.generated_at
    tracks["generatedAt"] = config.generated_at
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
