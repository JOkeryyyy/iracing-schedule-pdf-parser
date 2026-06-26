import unittest

from schedule_data_pipeline.manifest import build_manifest, checksums_for_files, content_hash_for_bundle
from tests.test_pipeline_mapper import build_fixture_bundle


class ManifestTests(unittest.TestCase):
    def test_content_hash_is_stable_for_same_bundle(self):
        bundle = build_fixture_bundle()

        first = content_hash_for_bundle(bundle)
        second = content_hash_for_bundle(bundle)

        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)

    def test_build_manifest_uses_release_relative_paths_and_revision(self):
        bundle = build_fixture_bundle()
        content_hash = content_hash_for_bundle(bundle)
        revision = content_hash[:8]
        files = {
            f"releases/2026-s3/{revision}/season.json": bundle["season"],
            f"releases/2026-s3/{revision}/cars.json": bundle["cars"],
            f"releases/2026-s3/{revision}/tracks.json": bundle["tracks"],
        }

        manifest = build_manifest(
            season_id="2026-s3",
            generated_at="2026-06-26T00:00:00Z",
            content_hash=content_hash,
            checksums=checksums_for_files(files),
        )

        self.assertEqual(manifest["revision"], revision)
        self.assertEqual(manifest["seasonFile"], f"releases/2026-s3/{revision}/season.json")
        self.assertEqual(manifest["carsFile"], f"releases/2026-s3/{revision}/cars.json")
        self.assertEqual(manifest["tracksFile"], f"releases/2026-s3/{revision}/tracks.json")
        self.assertEqual(
            sorted(manifest["checksums"].keys()),
            [
                f"releases/2026-s3/{revision}/cars.json",
                f"releases/2026-s3/{revision}/season.json",
                f"releases/2026-s3/{revision}/tracks.json",
            ],
        )


if __name__ == "__main__":
    unittest.main()
