import unittest

from pdf_schedule_parser.ids import stable_id, slugify


class IdHelperTests(unittest.TestCase):
    def test_slugify_normalizes_names_for_stable_json_ids(self):
        self.assertEqual(
            slugify("Charlotte Motor Speedway  - Oval"),
            "charlotte_motor_speedway_oval",
        )

    def test_stable_id_prefixes_normalized_value(self):
        self.assertEqual(
            stable_id("track", "Charlotte Motor Speedway - Oval"),
            "track_charlotte_motor_speedway_oval",
        )


if __name__ == "__main__":
    unittest.main()
