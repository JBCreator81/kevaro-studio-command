import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent / "assets" / "aurelian"
TARGET = "Aurelian Parallel E2E Certification 20260903-B"


def manifest():
    return json.loads((ROOT / "ASSET_PROVENANCE_MANIFEST.json").read_text())


def test_manifest_has_exact_identity_and_every_asset_category():
    data = manifest()
    assert data["production_name"] == TARGET
    assert data["canonical_concept"] == "Symphony of Serenity"
    categories = {item["asset_type"] for item in data["assets"]}
    assert categories == {"FONT", "TALENT", "LOCATION_ENVIRONMENT", "MUSIC", "SFX", "PROP"}
    assert all(item["production"] == TARGET for item in data["assets"])
    assert all({"asset_id", "description", "source_origin", "generation_tool_provenance", "rights_classification", "licence_evidence_reference", "verification_status", "downstream_usage"} <= item.keys() for item in data["assets"])


def test_all_available_files_match_recorded_hashes():
    for item in manifest()["assets"]:
        if "file" not in item:
            continue
        payload = (ROOT / item["file"]).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == item["sha256"]
    font = next(x for x in manifest()["assets"] if x["asset_type"] == "FONT")
    licence = (ROOT / font["licence_evidence_reference"]).read_bytes()
    assert hashlib.sha256(licence).hexdigest() == font["licence_sha256"]
    assert b"SIL OPEN FONT LICENSE Version 1.1" in licence


def test_missing_evidence_remains_fail_closed():
    data = manifest()
    blocked = {item["asset_type"]: item["verification_status"] for item in data["assets"] if item["verification_status"].startswith("BLOCKED")}
    assert blocked == {
        "MUSIC": "BLOCKED_ASSET_NOT_CREATED",
        "SFX": "BLOCKED_ASSET_NOT_CREATED",
        "PROP": "BLOCKED_EXACT_IDENTITY_AND_OWNERSHIP_CONFIRMATION_REQUIRED",
    }
    assert data["manifest_status"] == "PARTIAL_EVIDENCE_PENDING_AUDIO_AND_PROP_DECISION"


def test_generated_environments_record_prompt_and_non_third_party_scope():
    provenance = (ROOT / "environments" / "GENERATION_PROVENANCE.md").read_text()
    locations = [x for x in manifest()["assets"] if x["asset_type"] == "LOCATION_ENVIRONMENT"]
    assert len(locations) == 2
    assert all(x["verification_status"] == "VERIFIED_PROMPT_AND_VISUAL_REVIEW" for x in locations)
    assert all(x["generation_tool_provenance"]["specification_file"] == "environments/GENERATION_PROVENANCE.md" for x in locations)
    assert "does not claim copyright registration, exclusivity" in provenance
    assert provenance.count("No people, faces, identifiable location") == 2
