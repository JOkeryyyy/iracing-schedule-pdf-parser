import json
from pathlib import Path
import tempfile
import unittest

from schedule_data_pipeline.cli import run


FIXTURE_DIR = Path("tests/fixtures/raw_pipeline")


class PipelineCliTests(unittest.TestCase):
    def test_build_writes_manifest_and_release_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exit_code = run(
                [
                    "build",
                    "--raw-dir",
                    str(FIXTURE_DIR),
                    "--output-dir",
                    tmpdir,
                    "--season-id",
                    "2026-s3",
                    "--season-name",
                    "2026 Season 3",
                    "--season-start",
                    "2026-06-16",
                    "--season-end",
                    "2026-09-08",
                    "--generated-at",
                    "2026-06-26T00:00:00Z",
                ]
            )

            self.assertEqual(exit_code, 0)
            manifest_path = Path(tmpdir) / "manifest.json"
            self.assertTrue(manifest_path.exists())
            manifest = json.loads(manifest_path.read_text())
            self.assertEqual(manifest["seasonId"], "2026-s3")
            for field in ["seasonFile", "carsFile", "tracksFile"]:
                self.assertTrue((Path(tmpdir) / manifest[field]).exists(), field)

    def test_validate_accepts_build_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run(
                [
                    "build",
                    "--raw-dir",
                    str(FIXTURE_DIR),
                    "--output-dir",
                    tmpdir,
                    "--season-id",
                    "2026-s3",
                    "--season-name",
                    "2026 Season 3",
                    "--season-start",
                    "2026-06-16",
                    "--season-end",
                    "2026-09-08",
                    "--generated-at",
                    "2026-06-26T00:00:00Z",
                ]
            )

            self.assertEqual(run(["validate", "--mobile-dir", tmpdir]), 0)


if __name__ == "__main__":
    unittest.main()
