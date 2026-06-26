import json
from pathlib import Path
import tempfile
import unittest

from pdf_schedule_parser.cli import run


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample_schedule_text.txt"


class CliTests(unittest.TestCase):
    def test_cli_writes_all_json_files_from_text_fixture(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exit_code = run(["--text-fixture", str(FIXTURE), "--output-dir", tmpdir])

            self.assertEqual(exit_code, 0)
            for name in [
                "season.json",
                "cars.json",
                "tracks.json",
                "car-classes.json",
                "parser-report.json",
            ]:
                self.assertTrue((Path(tmpdir) / name).exists(), name)

            report = json.loads((Path(tmpdir) / "parser-report.json").read_text())
            self.assertEqual(report["counts"]["series"], 2)


if __name__ == "__main__":
    unittest.main()
