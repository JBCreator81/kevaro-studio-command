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
    assert categories == {"FONT", "TALENT", "LOCATION_ENVIRONMENT", "MUSIC", "SFX", "PROP", "FINAL_DELIVERABLE"}
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


def test_final_evidence_files_and_governed_prop_adoption_are_verified():
    data = manifest()
    assert not [item for item in data["assets"] if item["verification_status"].startswith("BLOCKED")]
    by_type = {item["asset_type"]: item for item in data["assets"]}
    assert by_type["PROP"]["description"] == "Aurelian Renewal Serum"
    assert by_type["PROP"]["verification_status"] == "GOVERNED_STUDIO_HEAD_AUTHORIZATION_RECORDED"
    assert by_type["MUSIC"]["verification_status"] == "VERIFIED_FILE_PROVENANCE_AND_TECHNICAL_PROPERTIES"
    assert by_type["SFX"]["verification_status"] == "VERIFIED_FILE_PROVENANCE_AND_TECHNICAL_PROPERTIES"
    assert data["manifest_status"] == "GOVERNED_FINAL_MEDIA_READY_FOR_DELIVERY"


def test_generated_environments_record_prompt_and_non_third_party_scope():
    provenance = (ROOT / "environments" / "GENERATION_PROVENANCE.md").read_text()
    locations = [x for x in manifest()["assets"] if x["asset_type"] == "LOCATION_ENVIRONMENT"]
    assert len(locations) == 2
    assert all(x["verification_status"] == "VERIFIED_PROMPT_AND_VISUAL_REVIEW" for x in locations)
    assert all(x["generation_tool_provenance"]["specification_file"] == "environments/GENERATION_PROVENANCE.md" for x in locations)
    assert "does not claim copyright registration, exclusivity" in provenance
    assert provenance.count("No people, faces, identifiable location") == 2
