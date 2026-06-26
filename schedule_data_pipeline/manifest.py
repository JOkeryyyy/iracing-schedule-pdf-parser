import hashlib

from schedule_data_pipeline.jsonio import stable_json


def content_hash_for_bundle(bundle):
    payload = "\n".join(stable_json(bundle[name]) for name in ["season", "cars", "tracks"])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def checksum_for_json(value):
    return "sha256:" + hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def checksums_for_files(files):
    return {path: checksum_for_json(value) for path, value in sorted(files.items())}


def release_prefix(season_id, content_hash):
    return f"releases/{season_id}/{content_hash[:8]}"


def build_manifest(season_id, generated_at, content_hash, checksums):
    prefix = release_prefix(season_id, content_hash)
    return {
        "schemaVersion": 1,
        "generatedAt": generated_at,
        "seasonId": season_id,
        "seasonFile": f"{prefix}/season.json",
        "carsFile": f"{prefix}/cars.json",
        "tracksFile": f"{prefix}/tracks.json",
        "revision": content_hash[:8],
        "checksums": checksums,
    }
