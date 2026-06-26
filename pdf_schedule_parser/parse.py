import re
from dataclasses import dataclass, field

from pdf_schedule_parser.ids import stable_id
from pdf_schedule_parser.models import ParsedSeries, ParsedWeek, ParserWarning


DISCIPLINES = {
    "OVAL": "oval",
    "SPORTS CAR": "sports_car",
    "FORMULA CAR": "formula_car",
    "DIRT OVAL": "dirt_oval",
    "DIRT ROAD": "dirt_road",
    "UNRANKED": "unranked",
}


@dataclass
class ParseResult:
    series: list[ParsedSeries] = field(default_factory=list)
    warnings: list[ParserWarning] = field(default_factory=list)


def parse_pages(pages):
    lines = extract_schedule_lines(pages)
    blocks = split_series_blocks(lines)
    result = ParseResult()

    for block in blocks:
        parsed = parse_series_block(block)
        if not parsed.weeks:
            result.warnings.append(
                ParserWarning(
                    "seriesWithoutWeeks",
                    f"Skipped series without parsed weeks: {parsed.name}",
                    page=parsed.source_page,
                )
            )
            continue

        result.series.append(parsed)
        if parsed.fixed_setup is None:
            result.warnings.append(
                ParserWarning(
                    "fixedSetupUnknown",
                    f"Fixed/open setup needs manual review for {parsed.name}",
                    page=parsed.source_page,
                )
            )
        if parsed.start_type == "unknown":
            result.warnings.append(
                ParserWarning(
                    "startTypeUnknown",
                    f"Start type needs manual review for {parsed.name}",
                    page=parsed.source_page,
                )
            )

    return result


def extract_schedule_lines(pages):
    lines = []
    schedule_started = False

    for page in pages:
        if not schedule_started and re.search(r"Week \d+ \(\d{4}-\d{2}-\d{2}\)", page.text):
            schedule_started = True
        if not schedule_started:
            continue

        for index, raw_line in enumerate(page.text.splitlines(), start=1):
            cleaned = clean_line(raw_line)
            if cleaned and cleaned != str(page.page):
                lines.append({"page": page.page, "line": index, "text": cleaned})

    return lines


def clean_line(value):
    return re.sub(r"\s+", " ", value).strip()


def split_series_blocks(lines):
    current_discipline = "unknown"
    blocks = []
    current = None

    for entry in lines:
        text = entry["text"]
        if text in DISCIPLINES:
            current_discipline = DISCIPLINES[text]
            continue

        if is_series_title(text):
            if current:
                blocks.append(current)
            current = {"discipline": current_discipline, "entries": [entry]}
            continue

        if current:
            current["entries"].append(entry)

    if current:
        blocks.append(current)
    return blocks


def is_series_title(text):
    return "2026 Season" in text and not text.startswith("Week ")


def parse_series_block(block):
    entries = block["entries"]
    title = entries[0]["text"]
    name, fixed_setup, fixed_source = parse_title(title)
    body = [entry["text"] for entry in entries[1:]]

    series = ParsedSeries(
        id=stable_id("series", f"{name}_2026_s3"),
        name=name,
        discipline=block["discipline"],
        fixed_setup=fixed_setup,
        fixed_setup_source=fixed_source,
        source_page=entries[0]["page"],
        raw_lines=[entry["text"] for entry in entries],
    )

    car_name = first_header_value(body)
    if car_name:
        series.car_class_ids = [stable_id("car_class", car_name)]
        series.car_ids = [stable_id("car", car_name)]

    for text in body:
        if "-->" in text:
            series.license = parse_license(text)
            break

    for text in body:
        if text.startswith("Races "):
            series.schedule = parse_schedule(text)
            break

    for text in body:
        official = parse_official(text)
        if official:
            series.official = official
            break

    series.weeks = parse_weeks(body)
    apply_start_type(series)
    return series


def parse_title(title):
    fixed = bool(re.search(r"\bFixed\b", title, re.IGNORECASE))
    name = re.sub(
        r"\s*-?\s*2026 Season(?:\s*3)?(?:\s*-\s*Fixed|\s*Fixed)?\s*$",
        "",
        title,
        flags=re.IGNORECASE,
    )
    name = re.sub(r"\s*-\s*Fixed\s*$", "", name, flags=re.IGNORECASE)
    name = clean_line(name)
    return name, fixed if fixed else None, "seriesName" if fixed else "unknown"


def first_header_value(lines):
    for text in lines:
        if text.startswith("Week ") or "-->" in text or text.startswith("Races "):
            return None
        if text.startswith("Min entries ") or text.startswith("No incident "):
            return None
        return text
    return None


def parse_license(text):
    result = {"raw": text}
    match = re.match(r"(.+?)\s+([0-9.]+)\s+-->\s+(.+?)\s+([0-9.]+)$", text)
    if match:
        result.update(
            {
                "minClass": normalize_license_class(match.group(1)),
                "minSafetyRating": float(match.group(2)),
                "maxClass": normalize_license_class(match.group(3)),
                "maxSafetyRating": float(match.group(4)),
            }
        )
    return result


def normalize_license_class(value):
    return value.strip().lower().replace("/", "_").replace(" ", "_")


def parse_schedule(text):
    schedule = {"raw": text}
    match = re.search(r"every (\d+) minutes.*:([0-9]{2}).*:([0-9]{2})", text)
    if match:
        schedule.update(
            {
                "type": "recurring",
                "intervalMinutes": int(match.group(1)),
                "minuteOffsets": [int(match.group(2)), int(match.group(3))],
            }
        )
        return schedule

    hourly = re.search(r"every hour at :?([0-9]{2})", text)
    if hourly:
        schedule.update({"type": "recurring", "intervalMinutes": 60, "minuteOffsets": [int(hourly.group(1))]})
        return schedule

    every_hours = re.search(r"at (\d+) past every (\d+) hours", text)
    if every_hours:
        schedule.update(
            {
                "type": "recurring",
                "intervalMinutes": int(every_hours.group(2)) * 60,
                "minuteOffsets": [int(every_hours.group(1))],
            }
        )
    return schedule


def parse_official(text):
    match = re.search(r"Min entries for official: (\d+) \| Split at: (\d+) \| Drops: (\d+)", text)
    if not match:
        return None
    return {"minEntries": int(match.group(1)), "splitAt": int(match.group(2)), "drops": int(match.group(3))}


def parse_weeks(lines):
    weeks = []
    current = None
    for text in lines:
        match = re.match(r"Week (\d+) \((\d{4}-\d{2}-\d{2})\) (.+)", text)
        if match:
            if current:
                finalize_week(current)
                weeks.append(current)
            current = ParsedWeek(
                week=int(match.group(1)),
                start_date=match.group(2),
                track_name=clean_track_name(match.group(3)),
            )
            continue

        if current:
            current.raw_lines.append(text)

    if current:
        finalize_week(current)
        weeks.append(current)
    return weeks


def finalize_week(week):
    joined = " ".join(week.raw_lines)
    length_match = re.search(r"(\d+) laps", joined)
    if length_match:
        week.race_length = {"type": "laps", "value": int(length_match.group(1))}
    else:
        time_match = re.search(r"(\d+) min", joined)
        if time_match:
            week.race_length = {"type": "minutes", "value": int(time_match.group(1))}

    rain_match = re.search(r"Rain chance (None|\d+%)", joined)
    if rain_match:
        week.weather["rainChancePercent"] = 0 if rain_match.group(1) == "None" else int(rain_match.group(1).rstrip("%"))

    temp_match = re.search(r"(\d+)°F/(\d+)°C", joined)
    if temp_match:
        week.weather["temperatureF"] = int(temp_match.group(1))
        week.weather["temperatureC"] = int(temp_match.group(2))


def clean_track_name(value):
    return clean_line(value.replace("  -", " -"))


def apply_start_type(series):
    starts = set()
    for week in series.weeks:
        joined = " ".join(week.raw_lines).lower()
        if "rolling start" in joined:
            starts.add("rolling")
        if "standing start" in joined:
            starts.add("standing")

    if len(starts) == 1:
        series.start_type = starts.pop()
        series.start_type_source = "weatherText"
    elif len(starts) > 1:
        series.start_type = "unknown"
        series.start_type_source = "unknown"
