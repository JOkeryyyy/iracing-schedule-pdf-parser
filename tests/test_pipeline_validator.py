import copy
import unittest

from schedule_data_pipeline.manifest import build_manifest, checksums_for_files, content_hash_for_bundle, release_prefix
from schedule_data_pipeline.validator import validate_manifest, validate_mobile_bundle
from tests.test_pipeline_mapper import build_fixture_bundle


class ValidatorTests(unittest.TestCase):
    def test_validate_mobile_bundle_accepts_fixture_bundle_with_unknown_setup_warning(self):
        warnings = validate_mobile_bundle(build_fixture_bundle())

        self.assertTrue(any(warning["code"] == "setupTypeUnknown" for warning in warnings))

    def test_validate_mobile_bundle_rejects_invalid_setup_type(self):
        bundle = build_fixture_bundle()
        bundle["season"]["series"][0]["setupType"] = "maybe"

        with self.assertRaisesRegex(ValueError, "setupType"):
            validate_mobile_bundle(bundle)

    def test_validate_mobile_bundle_rejects_missing_series_reference(self):
        bundle = build_fixture_bundle()
        bundle["season"]["races"][0]["seriesId"] = "missing"

        with self.assertRaisesRegex(ValueError, "seriesId"):
            validate_mobile_bundle(bundle)

    def test_validate_mobile_bundle_rejects_empty_sessions(self):
        bundle = build_fixture_bundle()
        bundle["season"]["races"][0]["sessions"] = []

        with self.assertRaisesRegex(ValueError, "sessions"):
            validate_mobile_bundle(bundle)

    def test_validate_manifest_rejects_unsafe_reference(self):
        bundle = build_fixture_bundle()
        content_hash = content_hash_for_bundle(bundle)
        prefix = release_prefix("2026-s3", content_hash)
        files = {
            f"{prefix}/season.json": bundle["season"],
            f"{prefix}/cars.json": bundle["cars"],
            f"{prefix}/tracks.json": bundle["tracks"],
        }
        manifest = build_manifest("2026-s3", "2026-06-26T00:00:00Z", content_hash, checksums_for_files(files))
        manifest["seasonFile"] = "../season.json"

        with self.assertRaisesRegex(ValueError, "seasonFile"):
            validate_manifest(manifest, files)

    def test_validate_manifest_rejects_bad_checksum(self):
        bundle = build_fixture_bundle()
        content_hash = content_hash_for_bundle(bundle)
        prefix = release_prefix("2026-s3", content_hash)
        files = {
            f"{prefix}/season.json": bundle["season"],
            f"{prefix}/cars.json": bundle["cars"],
            f"{prefix}/tracks.json": bundle["tracks"],
        }
        manifest = build_manifest("2026-s3", "2026-06-26T00:00:00Z", content_hash, checksums_for_files(files))
        manifest = copy.deepcopy(manifest)
        manifest["checksums"][f"{prefix}/season.json"] = "sha256:bad"

        with self.assertRaisesRegex(ValueError, "checksum"):
            validate_manifest(manifest, files)


if __name__ == "__main__":
    unittest.main()
