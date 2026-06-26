import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

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

    def test_publish_reports_missing_supabase_secrets_without_traceback(self):
        with tempfile.TemporaryDirectory() as mobile_dir, tempfile.TemporaryDirectory() as raw_dir:
            manifest = {
                "seasonId": "2026-s3",
                "revision": "abc123",
                "seasonFile": "releases/2026-s3/abc123/season.json",
                "carsFile": "releases/2026-s3/abc123/cars.json",
                "tracksFile": "releases/2026-s3/abc123/tracks.json",
            }
            Path(mobile_dir, "manifest.json").write_text(json.dumps(manifest))
            for name in ["season.json", "cars.json", "tracks.json", "car-classes.json", "parser-report.json"]:
                Path(raw_dir, name).write_text("{}")
            for field in ["seasonFile", "carsFile", "tracksFile"]:
                path = Path(mobile_dir, manifest[field])
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}")

            env = {key: value for key, value in os.environ.items() if not key.startswith("SUPABASE_")}
            with patch.dict(os.environ, env, clear=True), patch("sys.stderr") as stderr:
                exit_code = run(["publish", "--mobile-dir", mobile_dir, "--raw-dir", raw_dir])

            self.assertEqual(exit_code, 1)
            stderr.write.assert_called_once()
            self.assertIn("missing required Supabase environment variables", stderr.write.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
