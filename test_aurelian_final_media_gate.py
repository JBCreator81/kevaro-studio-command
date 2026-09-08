import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).parent/"assets"/"aurelian"
TARGET="Aurelian Parallel E2E Certification 20260903-B"

def delivery_manifest(): return json.loads((ROOT/"delivery"/"FINAL_DELIVERABLE_MANIFEST.json").read_text())

def test_three_exact_deliverables_are_registered_reviewed_and_ready():
 data=delivery_manifest(); assert data["production_name"]==TARGET; assert data["status"]=="READY_FOR_DELIVERY"
 items=data["deliverables"]; assert [x["platform"] for x in items]==["Instagram Reels","YouTube Shorts","16:9 master/delivery"]
 assert all(x["production_identity"]==TARGET for x in items)
 assert all((ROOT/x["file_path_or_reference"]).is_file() and x["checksum_sha256"] for x in items)
 assert all(hashlib.sha256((ROOT/x["file_path_or_reference"]).read_bytes()).hexdigest()==x["checksum_sha256"] for x in items)
 assert all(x["verification_status"]=="VERIFIED_CLEARANCE_AND_INDEPENDENT_QA_PASS" for x in items)
 assert all(x["review_status"]["clearance"]=="PASS" and x["review_status"]["independent_qa"]=="PASS" for x in items)
 assert all(x["governed_asset_id"].startswith("asset-") and x["governed_version_id"].endswith(":v1") for x in items)
 assert data["finalization"]["status"]=="READY_FOR_DELIVERY" and data["finalization"]["readiness_score"]==100
 assert items[0]["checksum_sha256"]==items[1]["checksum_sha256"]

def test_delivery_specs_match_governed_targets():
 items=delivery_manifest()["deliverables"]
 assert all(x["required_duration_seconds"]==30.0 and x["required_frame_rate_fps"]==24.0 for x in items)
 assert [x["required_aspect_ratio"] for x in items]==["9:16","9:16","16:9"]
 assert [x["required_resolution"] for x in items]==[{"width":1080,"height":1920,"four_k_where_practical":False},{"width":1080,"height":1920,"four_k_where_practical":False},{"width":3840,"height":2160,"four_k_where_practical":True}]
 assert all(x["required_container"]=="MP4" and x["required_video_codec"]=="H.264" for x in items)
 assert all(x["required_audio"]["source_assets"]==["symphony-of-serenity-score-v1.wav","symphony-of-serenity-sfx-v1.wav"] for x in items)

def test_registration_gate_forbids_placeholders_and_self_certification():
 data=delivery_manifest(); gate=data["registration_gate"]
 assert "Actual media file exists" in gate["required_before_registration"]
 assert "Independent content and technical QA recorded by a reviewer separate from the creator" in gate["required_after_immutable_registration"]
 assert "Studio Head final approval recorded only if every deliverable passes" in gate["required_after_immutable_registration"]
 assert "Governed finalization succeeds only if all runtime gates are eligible" in gate["required_after_immutable_registration"]
 protocol=(ROOT/"delivery"/"CONTENT_QA_CHECKLIST.md").read_text()
 assert "CLEARANCE PASS — INDEPENDENT QA PASS — READY FOR DELIVERY" in protocol
 assert "cannot be the sole verifier" in protocol
 assert "do not invent captions" in protocol

def test_canonical_manifest_contains_same_governed_deliverables():
 canonical=json.loads((ROOT/"ASSET_PROVENANCE_MANIFEST.json").read_text())
 pending=[x for x in canonical["assets"] if x["asset_type"]=="FINAL_DELIVERABLE"]
 assert [x["asset_id"] for x in pending]==[x["asset_id"] for x in delivery_manifest()["deliverables"]]
 assert canonical["manifest_status"]=="GOVERNED_FINAL_MEDIA_READY_FOR_DELIVERY"
