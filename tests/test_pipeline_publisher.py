import unittest

from schedule_data_pipeline.publisher import SupabasePublisher, UploadFailure


class FakeTransport:
    def __init__(self, fail_on_path=None):
        self.fail_on_path = fail_on_path
        self.calls = []

    def request(self, method, url, headers=None, data=None):
        self.calls.append({"method": method, "url": url, "headers": headers or {}, "data": data})
        if self.fail_on_path and self.fail_on_path in url:
            return FakeResponse(500, b"upload failed")
        return FakeResponse(200, b"{}")


class FakeResponse:
    def __init__(self, status, body):
        self.status = status
        self.body = body

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class PublisherTests(unittest.TestCase):
    def test_publish_uploads_manifest_last(self):
        transport = FakeTransport()
        publisher = SupabasePublisher(
            supabase_url="https://example.supabase.co",
            service_role_key="secret",
            bucket="planner-data",
            transport=transport,
        )

        publisher.publish(
            release_files={
                "data/mobile/v1/releases/2026-s3/abc123/season.json": b"{}",
                "data/mobile/v1/releases/2026-s3/abc123/cars.json": b"{}",
            },
            raw_files={
                "data/raw/pdf-parser/releases/2026-s3/abc123/parser-report.json": b"{}",
            },
            manifest_path="data/mobile/v1/manifest.json",
            manifest_bytes=b"{}",
        )

        uploaded_paths = [call["url"].split("/planner-data/")[1] for call in transport.calls if call["method"] == "POST"]
        self.assertEqual(uploaded_paths[-1], "data/mobile/v1/manifest.json")

    def test_publish_does_not_upload_manifest_when_release_upload_fails(self):
        transport = FakeTransport(fail_on_path="season.json")
        publisher = SupabasePublisher(
            supabase_url="https://example.supabase.co",
            service_role_key="secret",
            bucket="planner-data",
            transport=transport,
        )

        with self.assertRaises(UploadFailure):
            publisher.publish(
                release_files={"data/mobile/v1/releases/2026-s3/abc123/season.json": b"{}"},
                raw_files={},
                manifest_path="data/mobile/v1/manifest.json",
                manifest_bytes=b"{}",
            )

        uploaded_paths = [call["url"].split("/planner-data/")[1] for call in transport.calls if call["method"] == "POST"]
        self.assertNotIn("data/mobile/v1/manifest.json", uploaded_paths)


if __name__ == "__main__":
    unittest.main()
