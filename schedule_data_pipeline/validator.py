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

    series_with_races = {race["seriesId"] for race in race_items}
    for series_id in series_ids:
        if series_id not in series_with_races:
            raise ValueError(f"series has no races: {series_id}")

    weeks_with_races = {race["weekNumber"] for race in race_items}
    for week_number in week_numbers:
        if week_number not in weeks_with_races:
            raise ValueError(f"week has no races: {week_number}")

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
