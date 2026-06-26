import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "sample_schedule_text.txt"


class ProjectPackagingTests(unittest.TestCase):
    def test_parser_runs_as_a_standalone_module_from_project_root(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pdf_schedule_parser.cli",
                    "--text-fixture",
                    str(FIXTURE),
                    "--output-dir",
                    tmpdir,
                ],
                cwd=PROJECT_ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((Path(tmpdir) / "season.json").exists())


if __name__ == "__main__":
    unittest.main()
