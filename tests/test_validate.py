import unittest

from pdf_schedule_parser.validate import validate_bundle


class ValidateTests(unittest.TestCase):
    def test_validate_bundle_rejects_series_without_weeks(self):
        bundle = {
            "season": {
                "series": [
                    {
                        "id": "series_test",
                        "name": "Test",
                        "fixedSetup": None,
                        "startType": "rolling",
                        "weeks": [],
                    }
                ]
            }
        }

        with self.assertRaises(ValueError):
            validate_bundle(bundle)

    def test_validate_bundle_accepts_nullable_fixed_setup(self):
        bundle = {
            "season": {
                "series": [
                    {
                        "id": "series_test",
                        "name": "Test",
                        "fixedSetup": None,
                        "startType": "unknown",
                        "weeks": [{"week": 1, "startDate": "2026-06-16", "trackId": "track_test"}],
                    }
                ]
            }
        }

        validate_bundle(bundle)


if __name__ == "__main__":
    unittest.main()
