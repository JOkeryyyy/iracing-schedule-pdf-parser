import json
import os
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


class UploadFailure(RuntimeError):
    pass


class UrlopenTransport:
    def request(self, method, url, headers=None, data=None):
        request = Request(url=url, method=method, headers=headers or {}, data=data)
        return urlopen(request)


class SupabasePublisher:
    def __init__(self, supabase_url, service_role_key, bucket, transport=None):
        self.supabase_url = supabase_url.rstrip("/")
        self.service_role_key = service_role_key
        self.bucket = bucket
        self.transport = transport or UrlopenTransport()

    def publish(self, release_files, raw_files, manifest_path, manifest_bytes):
        for path, payload in sorted(release_files.items()):
            self.upload(path, payload, upsert=False)
            self.verify_public(path)
        for path, payload in sorted(raw_files.items()):
            self.upload(path, payload, upsert=False)
            self.verify_public(path)
        self.upload(manifest_path, manifest_bytes, upsert=True)
        self.verify_public(manifest_path)

    def upload(self, path, payload, upsert):
        encoded_path = quote(path, safe="/")
        url = f"{self.supabase_url}/storage/v1/object/{self.bucket}/{encoded_path}"
        headers = {
            "Authorization": f"Bearer {self.service_role_key}",
            "Content-Type": "application/json",
            "x-upsert": "true" if upsert else "false",
        }
        with self.transport.request("POST", url, headers=headers, data=payload) as response:
            body = response.read()
            if response.status >= 300:
                raise UploadFailure(f"failed to upload {path}: {response.status} {body.decode('utf-8', errors='replace')}")

    def verify_public(self, path):
        encoded_path = quote(path, safe="/")
        url = f"{self.supabase_url}/storage/v1/object/public/{self.bucket}/{encoded_path}"
        with self.transport.request("GET", url) as response:
            body = response.read()
            if response.status >= 300:
                raise UploadFailure(f"failed to verify {path}: {response.status} {body.decode('utf-8', errors='replace')}")


def publisher_from_env():
    required = ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_STORAGE_BUCKET"]
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise UploadFailure(f"missing required Supabase environment variables: {', '.join(missing)}")
    return SupabasePublisher(
        supabase_url=os.environ["SUPABASE_URL"],
        service_role_key=os.environ["SUPABASE_SERVICE_ROLE_KEY"],
        bucket=os.environ["SUPABASE_STORAGE_BUCKET"],
    )


def publish_from_disk(mobile_dir, raw_dir):
    mobile_dir = Path(mobile_dir)
    raw_dir = Path(raw_dir)
    manifest_bytes = (mobile_dir / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    release_files = {
        f"data/mobile/v1/{manifest['seasonFile']}": (mobile_dir / manifest["seasonFile"]).read_bytes(),
        f"data/mobile/v1/{manifest['carsFile']}": (mobile_dir / manifest["carsFile"]).read_bytes(),
        f"data/mobile/v1/{manifest['tracksFile']}": (mobile_dir / manifest["tracksFile"]).read_bytes(),
    }
    revision = manifest["revision"]
    season_id = manifest["seasonId"]
    raw_files = {}
    for name in ["season.json", "cars.json", "tracks.json", "car-classes.json", "parser-report.json"]:
        raw_files[f"data/raw/pdf-parser/releases/{season_id}/{revision}/{name}"] = (raw_dir / name).read_bytes()
    publisher_from_env().publish(
        release_files=release_files,
        raw_files=raw_files,
        manifest_path="data/mobile/v1/manifest.json",
        manifest_bytes=manifest_bytes,
    )
