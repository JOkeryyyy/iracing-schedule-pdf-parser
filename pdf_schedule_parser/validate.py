VALID_START_TYPES = {"rolling", "standing", "unknown"}
VALID_FIXED_SETUP_VALUES = {True, False, None}


def validate_bundle(bundle):
    series_items = bundle.get("season", {}).get("series")
    if not isinstance(series_items, list) or not series_items:
        raise ValueError("season.series must be a non-empty list")

    for index, series in enumerate(series_items):
        validate_series(series, index)


def validate_series(series, index):
    for field in ["id", "name"]:
        if not isinstance(series.get(field), str) or not series[field].strip():
            raise ValueError(f"season.series[{index}].{field} must be a non-empty string")

    if "fixedSetup" not in series or series["fixedSetup"] not in VALID_FIXED_SETUP_VALUES:
        raise ValueError(f"season.series[{index}].fixedSetup must be true, false, or null")

    if series.get("startType") not in VALID_START_TYPES:
        raise ValueError(f"season.series[{index}].startType must be rolling, standing, or unknown")

    weeks = series.get("weeks")
    if not isinstance(weeks, list) or not weeks:
        raise ValueError(f"season.series[{index}].weeks must be a non-empty list")

    for week_index, week in enumerate(weeks):
        validate_week(week, index, week_index)


def validate_week(week, series_index, week_index):
    if not isinstance(week.get("week"), int):
        raise ValueError(f"season.series[{series_index}].weeks[{week_index}].week must be an integer")
    for field in ["startDate", "trackId"]:
        if not isinstance(week.get(field), str) or not week[field].strip():
            raise ValueError(f"season.series[{series_index}].weeks[{week_index}].{field} must be a non-empty string")
