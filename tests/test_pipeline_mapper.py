from pathlib import Path
import unittest

from schedule_data_pipeline.jsonio import load_json_file, stable_json
from schedule_data_pipeline.mapper import MappingConfig, build_mobile_bundle


FIXTURE_DIR = Path("tests/fixtures/raw_pipeline")


class JsonIoTests(unittest.TestCase):
    def test_load_json_file_reads_fixture_object(self):
        loaded = load_json_file(FIXTURE_DIR / "season.json")

        self.assertEqual(loaded["schemaVersion"], 1)
        self.assertEqual(len(loaded["series"]), 2)

    def test_stable_json_sorts_keys_without_extra_spaces(self):
        self.assertEqual(stable_json({"b": 2, "a": 1}), '{"a":1,"b":2}')


class MapperTests(unittest.TestCase):
    def test_build_mobile_bundle_maps_series_and_flat_races(self):
        bundle = build_fixture_bundle()

        season = bundle["season"]

        self.assertEqual(season["schemaVersion"], 1)
        self.assertEqual(season["seasonId"], "2026-s3")
        self.assertEqual(season["seasonStart"], "2026-06-16T00:00:00Z")
        self.assertEqual(season["seasonEnd"], "2026-09-08T00:00:00Z")
        self.assertEqual(season["weekSeasonStart"], "2026-06-16T00:00:00Z")
        self.assertEqual([week["weekNumber"] for week in season["weeks"]], [1, 2])
        self.assertEqual(len(season["series"]), 2)
        self.assertEqual(len(season["races"]), 3)

        mini_stock = season["series"][1]
        self.assertEqual(mini_stock["setupType"], "unknown")
        self.assertEqual(mini_stock["setupSource"], "unknown")
        self.assertEqual(mini_stock["startType"], "rolling")
        self.assertEqual(mini_stock["category"], "Oval")
        self.assertEqual(mini_stock["license"]["className"], "Rookie")
        self.assertEqual(mini_stock["license"]["safetyRating"], 1.0)
        self.assertEqual(len(mini_stock["raceIds"]), 2)

        arca = season["series"][0]
        self.assertEqual(arca["setupType"], "fixed")
        self.assertEqual(arca["setupSource"], "seriesName")
        self.assertEqual(arca["startType"], "standing")

    def test_build_mobile_bundle_maps_race_rows_for_frontend_scanning(self):
        bundle = build_fixture_bundle()

        race = bundle["season"]["races"][0]

        self.assertEqual(
            race["raceId"],
            "2026-s3-series_arca_menards_series_2026_s3-w1-track_daytona_international_speedway_oval",
        )
        self.assertEqual(race["seriesName"], "ARCA Menards Series")
        self.assertEqual(race["category"], "Oval")
        self.assertEqual(race["startsAt"], "2026-06-16T00:00:00Z")
        self.assertEqual(race["endsAt"], "2026-06-23T00:00:00Z")
        self.assertEqual(race["trackName"], "Daytona International Speedway")
        self.assertEqual(race["trackConfigName"], "Oval")
        self.assertEqual(race["carSkus"], ["car_arca"])
        self.assertEqual(race["carClasses"], ["ARCA"])
        self.assertEqual(race["setupType"], "fixed")
        self.assertEqual(race["startType"], "standing")
        self.assertEqual(race["raceLength"], {"minutes": 20})
        self.assertEqual(race["precipChance"], 15)
        self.assertEqual(
            race["sessions"],
            [
                {
                    "type": "recurring",
                    "firstSessionOffsetMinutes": 45,
                    "repeatEveryMinutes": 60,
                }
            ],
        )

    def test_build_mobile_bundle_maps_catalogs(self):
        bundle = build_fixture_bundle()

        self.assertEqual(bundle["cars"]["generatedAt"], "2026-06-26T00:00:00Z")
        self.assertEqual(bundle["tracks"]["generatedAt"], "2026-06-26T00:00:00Z")
        self.assertEqual(bundle["cars"]["cars"][0]["sku"], "car_arca")
        self.assertEqual(bundle["cars"]["cars"][1]["displayName"], "Mini Stock")
        self.assertEqual(bundle["tracks"]["tracks"][0]["packageId"], "track_charlotte_motor_speedway_oval")
        self.assertEqual(bundle["tracks"]["tracks"][0]["type"], "oval")
        self.assertEqual(bundle["tracks"]["tracks"][0]["sourceTrackIds"], [])


def build_fixture_bundle():
    return build_mobile_bundle(
        raw_season=load_json_file(FIXTURE_DIR / "season.json"),
        raw_cars=load_json_file(FIXTURE_DIR / "cars.json"),
        raw_tracks=load_json_file(FIXTURE_DIR / "tracks.json"),
        raw_car_classes=load_json_file(FIXTURE_DIR / "car-classes.json"),
        config=MappingConfig(
            season_id="2026-s3",
            season_name="2026 Season 3",
            season_start="2026-06-16",
            season_end="2026-09-08",
            generated_at="2026-06-26T00:00:00Z",
        ),
    )


if __name__ == "__main__":
    unittest.main()
