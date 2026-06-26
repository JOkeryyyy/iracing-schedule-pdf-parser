import unittest

from pdf_schedule_parser.models import ParsedSeries, ParsedWeek
from pdf_schedule_parser.normalize import build_output_bundle


class NormalizeTests(unittest.TestCase):
    def test_build_output_bundle_creates_schedule_and_catalogs(self):
        series = ParsedSeries(
            id="series_test",
            name="Test Series",
            discipline="oval",
            fixed_setup=True,
            fixed_setup_source="seriesName",
            start_type="rolling",
            start_type_source="weatherText",
            car_class_ids=["car_class_mini_stock"],
            car_ids=["car_mini_stock"],
            weeks=[
                ParsedWeek(
                    week=1,
                    start_date="2026-06-16",
                    track_name="Charlotte Motor Speedway - Oval",
                    race_length={"type": "laps", "value": 15},
                )
            ],
        )

        bundle = build_output_bundle([series], [], source_pdf="SeasonSchedule.pdf")

        self.assertEqual(bundle["season"]["season"]["id"], "2026-s3")
        self.assertEqual(bundle["season"]["series"][0]["fixedSetup"], True)
        self.assertEqual(bundle["tracks"]["tracks"][0]["id"], "track_charlotte_motor_speedway_oval")
        self.assertEqual(bundle["cars"]["cars"][0]["id"], "car_mini_stock")
        self.assertEqual(bundle["car-classes"]["carClasses"][0]["id"], "car_class_mini_stock")
        self.assertEqual(bundle["parser-report"]["counts"]["series"], 1)
        self.assertIn("contentHash", bundle["parser-report"])


if __name__ == "__main__":
    unittest.main()
