from pathlib import Path
import unittest

from schedule_data_pipeline.jsonio import load_json_file, stable_json


FIXTURE_DIR = Path("tests/fixtures/raw_pipeline")


class JsonIoTests(unittest.TestCase):
    def test_load_json_file_reads_fixture_object(self):
        loaded = load_json_file(FIXTURE_DIR / "season.json")

        self.assertEqual(loaded["schemaVersion"], 1)
        self.assertEqual(len(loaded["series"]), 2)

    def test_stable_json_sorts_keys_without_extra_spaces(self):
        self.assertEqual(stable_json({"b": 2, "a": 1}), '{"a":1,"b":2}')


if __name__ == "__main__":
    unittest.main()
