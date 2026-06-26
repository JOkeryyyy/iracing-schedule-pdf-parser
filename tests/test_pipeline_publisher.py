import unittest
from io import BytesIO
from urllib.error import HTTPError

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


class HttpErrorTransport(FakeTransport):
    def request(self, method, url, headers=None, data=None):
        self.calls.append({"method": method, "url": url, "headers": headers or {}, "data": data})
        if method == "GET":
            raise HTTPError(url, 400, "Bad Request", hdrs={}, fp=BytesIO(b"bucket is not public"))
        return FakeResponse(200, b"{}")


class ExistingObjectTransport(FakeTransport):
    def __init__(self, existing_body):
        super().__init__()
        self.existing_body = existing_body

    def request(self, method, url, headers=None, data=None):
        self.calls.append({"method": method, "url": url, "headers": headers or {}, "data": data})
        if method == "POST" and "releases/2026-s3/abc123/season.json" in url:
            raise HTTPError(url, 400, "Bad Request", hdrs={}, fp=BytesIO(b"The resource already exists"))
        if method == "GET" and "releases/2026-s3/abc123/season.json" in url:
            return FakeResponse(200, self.existing_body)
        return FakeResponse(200, b"{}")


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

    def test_publish_wraps_public_verification_http_errors(self):
        transport = HttpErrorTransport()
        publisher = SupabasePublisher(
            supabase_url="https://example.supabase.co",
            service_role_key="secret",
            bucket="planner-data",
            transport=transport,
        )

        with self.assertRaisesRegex(
            UploadFailure,
            "failed to verify public access for data/mobile/v1/releases/2026-s3/abc123/season.json: 400 Bad Request bucket is not public",
        ):
            publisher.publish(
                release_files={"data/mobile/v1/releases/2026-s3/abc123/season.json": b"{}"},
                raw_files={},
                manifest_path="data/mobile/v1/manifest.json",
                manifest_bytes=b"{}",
            )

        uploaded_paths = [call["url"].split("/planner-data/")[1] for call in transport.calls if call["method"] == "POST"]
        self.assertNotIn("data/mobile/v1/manifest.json", uploaded_paths)

    def test_publish_treats_existing_immutable_file_as_success_when_content_matches(self):
        transport = ExistingObjectTransport(existing_body=b'{"ok": true}')
        publisher = SupabasePublisher(
            supabase_url="https://example.supabase.co",
            service_role_key="secret",
            bucket="planner-data",
            transport=transport,
        )

        publisher.publish(
            release_files={"data/mobile/v1/releases/2026-s3/abc123/season.json": b'{"ok": true}'},
            raw_files={},
            manifest_path="data/mobile/v1/manifest.json",
            manifest_bytes=b"{}",
        )

        uploaded_paths = [call["url"].split("/planner-data/")[1] for call in transport.calls if call["method"] == "POST"]
        self.assertEqual(uploaded_paths[-1], "data/mobile/v1/manifest.json")

    def test_publish_rejects_existing_immutable_file_when_content_differs(self):
        transport = ExistingObjectTransport(existing_body=b'{"ok": false}')
        publisher = SupabasePublisher(
            supabase_url="https://example.supabase.co",
            service_role_key="secret",
            bucket="planner-data",
            transport=transport,
        )

        with self.assertRaisesRegex(
            UploadFailure,
            "existing immutable file differs from generated content: data/mobile/v1/releases/2026-s3/abc123/season.json",
        ):
            publisher.publish(
                release_files={"data/mobile/v1/releases/2026-s3/abc123/season.json": b'{"ok": true}'},
                raw_files={},
                manifest_path="data/mobile/v1/manifest.json",
                manifest_bytes=b"{}",
            )

        uploaded_paths = [call["url"].split("/planner-data/")[1] for call in transport.calls if call["method"] == "POST"]
        self.assertNotIn("data/mobile/v1/manifest.json", uploaded_paths)


if __name__ == "__main__":
    unittest.main()
