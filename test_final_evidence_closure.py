from datetime import datetime, timezone
import pytest
from studio_command.accountability import human_actor
from studio_command.adoption import apply_first_party_adoption, PROP, LICENSING
from studio_command.closure import FINAL_STALE, PROP_NAME, REQUIRED_ASSETS, apply_final_evidence_closure
from studio_command.models import AssetStorageReference, ProductionAsset, ProductionAssetRegistry
from test_first_party_adoption import current_runtime

TARGET="Aurelian Parallel E2E Certification 20260903-B"
NOW=datetime(2026,9,7,tzinfo=timezone.utc)

def ready_runtime():
 r=apply_first_party_adoption(runtime_state=current_runtime(),actor=human_actor("Studio Head"),adopted_at=NOW)
 return r.model_copy(update={"memory_snapshot":r.memory_snapshot.model_copy(update={"stale_artifacts":[],"preserved_artifacts":["production_brief","research_packet","creative_treatment","production_plan","production_schedule","asset_media_plan","clearance_report","verification_report","decision_package"],"current_stage":"CONDITIONS_BLOCK_EXECUTION"}),"corrective_cycle_active":False,"current_stage":"CONDITIONS_BLOCK_EXECUTION"})

def registry(overrides=None):
 overrides=overrides or {}; assets=[]
 for i,(filename,checksum) in enumerate(REQUIRED_ASSETS.items()):
  values=overrides.get(filename,{})
  assets.append(ProductionAsset(asset_id=f"asset-{i}",version_id=f"asset-{i}:v1",production_identity=TARGET,node_id="Asset & Media",asset_category="AUDIO" if filename.endswith('.wav') else "OTHER_PRODUCTION_FILE",filename=filename,display_name=filename,media_document_type="audio/wav" if filename.endswith('.wav') else "file",storage=AssetStorageReference(location_type="GCS_URI",reference=f"gs://bucket/{filename}",checksum_sha256=values.get("checksum",checksum)),version_number=1,created_at=NOW,last_changed_at=NOW,status=values.get("status","REGISTERED"),clearance_state=values.get("clearance","EVIDENCE_ATTACHED"),provenance=values.get("provenance",{"source_classification":"ORIGINAL"})))
 return ProductionAssetRegistry(production_identity=TARGET,assets=assets)

def test_final_closure_is_exact_append_only_and_preserves_history():
 before=ready_runtime(); updated=apply_final_evidence_closure(runtime_state=before,registry=registry(),actor=human_actor("Studio Head"),adopted_at=NOW)
 assert updated.workflow_state.active_conditions==[]
 assert updated.decision_history==before.decision_history
 assert updated.evidence_amendments[:-2]==before.evidence_amendments
 assert [x.resolved_condition for x in updated.evidence_amendments[-2:]]==[PROP,LICENSING]
 assert updated.first_party_declarations[-1].declaration["prop_identity"]==PROP_NAME
 assert updated.memory_snapshot.stale_artifacts==FINAL_STALE
 assert updated.execution_authorized is False

def test_final_closure_requires_studio_head_and_exact_conditions():
 with pytest.raises(ValueError,match="Studio Head"):
  apply_final_evidence_closure(runtime_state=ready_runtime(),registry=registry(),actor=human_actor("Editor","Editor"))
 wrong=ready_runtime(); wrong=wrong.model_copy(update={"workflow_state":wrong.workflow_state.model_copy(update={"active_conditions":[PROP]})})
 with pytest.raises(ValueError,match="two exact"):
  apply_final_evidence_closure(runtime_state=wrong,registry=registry(),actor=human_actor("Studio Head"))

def test_final_closure_rejects_missing_forged_or_unverified_assets():
 missing=registry(); missing.assets=missing.assets[:-1]
 with pytest.raises(ValueError,match="missing"):
  apply_final_evidence_closure(runtime_state=ready_runtime(),registry=missing,actor=human_actor("Studio Head"))
 with pytest.raises(ValueError,match="checksum mismatch"):
  apply_final_evidence_closure(runtime_state=ready_runtime(),registry=registry({"symphony-of-serenity-score-v1.wav":{"checksum":"0"*64}}),actor=human_actor("Studio Head"))
 with pytest.raises(ValueError,match="provenance is missing"):
  apply_final_evidence_closure(runtime_state=ready_runtime(),registry=registry({"symphony-of-serenity-sfx-v1.wav":{"provenance":{}}}),actor=human_actor("Studio Head"))

def test_wrong_production_and_stale_state_reject():
 wrong=registry(); wrong.production_identity="Wrong Production"
 with pytest.raises(ValueError,match="identity"):
  apply_final_evidence_closure(runtime_state=ready_runtime(),registry=wrong,actor=human_actor("Studio Head"))
 stale=ready_runtime(); stale=stale.model_copy(update={"memory_snapshot":stale.memory_snapshot.model_copy(update={"stale_artifacts":["asset_media_plan"]})})
 with pytest.raises(ValueError,match="current governed"):
  apply_final_evidence_closure(runtime_state=stale,registry=registry(),actor=human_actor("Studio Head"))


def test_persistence_installs_complete_closure_atomically(monkeypatch):
    from hashlib import sha256
    import studio_command.persistence as persistence_module
    from studio_command.persistence import ProductionPersistence
    from test_evidence_amendment import Document, FirestoreClient
    monkeypatch.setattr(persistence_module.firestore, "transactional", lambda fn: fn)
    before=ready_runtime()
    doc=Document({**before.model_dump(mode="json"),"production_asset_registry":registry().model_dump(mode="json")})
    client=FirestoreClient({sha256(TARGET.encode()).hexdigest():doc})
    store=ProductionPersistence.__new__(ProductionPersistence); store.config=persistence_module.ProductionPersistenceConfig(); store.firestore_client=client; store.storage_client=object()
    updated=store.close_final_aurelian_evidence(production_name=TARGET,adopted_by=human_actor("Studio Head"))
    assert len(client.last_transaction.writes)==1
    written=client.last_transaction.writes[0][1]
    assert written["workflow_state"]["active_conditions"]==[]
    assert written["memory_snapshot"]["stale_artifacts"]==FINAL_STALE
    assert len(written["decision_history"])==len(before.decision_history)
    assert updated.first_party_declarations[-1].declaration["prop_identity"]==PROP_NAME
