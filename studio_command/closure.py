from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from .adoption import LICENSING, PROP
from .identity import require_production_identity
from .models import AccountabilityActor, EvidenceSourceReference, GovernedEvidenceAmendment, GovernedFirstPartyDeclaration, GovernedProductionRuntimeState, ProductionAssetRegistry

PROP_NAME="Aurelian Renewal Serum"
FINAL_STALE=["asset_media_plan","clearance_report","verification_report","decision_package"]
REQUIRED_ASSETS={
 "retreat-dawn-interior-v1.png":"5a4fc0cd38a83322b4c85fe4bc98bb5f7bdb535e286f57f7b16bb213d5f61a04",
 "retreat-blue-hour-pavilion-v1.png":"2283958b96a023e7397cf6548ce2e8827185f8abcbd514b6b5954332b03fd0cb",
 "symphony-of-serenity-score-v1.wav":"5325ece2e9a8fd33194fa14abb5434b6a360e9284757a48f078b956cfb968820",
 "symphony-of-serenity-sfx-v1.wav":"5218b49cb8aba8e28017278310c30731f807a302f8f100cbdc47ace4c0fe4433",
 "NotoSans-wdth-wght.ttf":"bfb7bb691513f12e734dc346c03a03f784912432d7e3fa8e56efcf906fe86b3d",
 "OFL.txt":"cee9892f9f0cc8fe882c9e9537ee6a89621d86ee7ceaf70b02e2b2b1c25c061a",
 "GENERATION_PROVENANCE.md":"d002d0ca88df30abfe3594059e5ca4434963fd7330171737bb72abb69e278580",
 "CREATION_SPECIFICATIONS.md":"b5dcf3f2638405ca66a0e3c041d916f22106d25f313f9d6501dc3b0c4f422837",
 "generate_original_audio.py":"ed02991383c49fc37a78838838dee52af5e6c1893910f616be0a1e487f7f6c9d",
 "ASSET_PROVENANCE_MANIFEST.json":"d8803d9ab6c3767271a3332ad36491d1e672967c5f675e9bea8c91db113033f3",
}

def verified_asset_evidence(registry: ProductionAssetRegistry) -> dict[str,dict[str,Any]]:
 require_production_identity(registry.production_identity)
 latest={}
 for asset in registry.assets:
  prior=latest.get(asset.filename)
  if prior is None or asset.version_number>prior.version_number: latest[asset.filename]=asset
 evidence={}
 for filename,checksum in REQUIRED_ASSETS.items():
  asset=latest.get(filename)
  if asset is None: raise ValueError(f"Required governed asset is missing: {filename}")
  if asset.storage.checksum_sha256!=checksum: raise ValueError(f"Governed asset checksum mismatch: {filename}")
  if asset.status in {"REJECTED","CHANGES_REQUESTED"} or asset.clearance_state!="EVIDENCE_ATTACHED": raise ValueError(f"Governed asset is not verified for evidence use: {filename}")
  if not asset.provenance.get("source_classification"): raise ValueError(f"Governed asset provenance is missing: {filename}")
  evidence[filename]={"asset_id":asset.asset_id,"version_id":asset.version_id,"checksum_sha256":checksum,"source_classification":asset.provenance["source_classification"]}
 return evidence

def apply_final_evidence_closure(*,runtime_state:GovernedProductionRuntimeState,registry:ProductionAssetRegistry,actor:AccountabilityActor,adopted_at:datetime|None=None)->GovernedProductionRuntimeState:
 require_production_identity(runtime_state.production_name,registry.production_identity)
 if actor.actor_type!="HUMAN" or actor.role!="Studio Head": raise ValueError("Final evidence closure requires authenticated Studio Head authority.")
 if runtime_state.memory_snapshot.stale_artifacts: raise ValueError("Final evidence closure requires current governed artifacts.")
 if runtime_state.workflow_state.active_conditions!=[PROP,LICENSING]: raise ValueError("Final evidence closure requires the two exact active conditions.")
 evidence=verified_asset_evidence(registry); now=adopted_at or datetime.now(timezone.utc)
 declaration=GovernedFirstPartyDeclaration(production_name=runtime_state.production_name,declaration_type="PROP_USAGE_AUTHORIZATION",resolved_condition=PROP,declaration={"prop_identity":PROP_NAME,"ownership_classification":"Fictional client-owned Aurelian brand asset","scope":"Limited to Aurelian Parallel E2E Certification 20260903-B","exclusions":["real third-party products","third-party manufacturers","unrelated productions"]},adopted_by=actor,adopted_at=now)
 amendments=[
  GovernedEvidenceAmendment(production_name=runtime_state.production_name,resolved_condition=PROP,resolution_summary="Authenticated Studio Head approved Aurelian Renewal Serum as the exact fictional client-owned prop for this production only.",amended_artifact="asset_media_plan",source_references=[EvidenceSourceReference(source_production_name=runtime_state.production_name,artifact_key="first_party_declarations",field_path=[len(runtime_state.first_party_declarations),"declaration"],verified_value=declaration.declaration)],stale_artifacts=FINAL_STALE,recorded_by=actor,recorded_at=now),
  GovernedEvidenceAmendment(production_name=runtime_state.production_name,resolved_condition=LICENSING,resolution_summary="Verified rights-avoiding asset package uses no identifiable talent or real location, production-specific generated environments and original procedural audio, and pinned Noto Sans with OFL-1.1.",amended_artifact="asset_media_plan",source_references=[EvidenceSourceReference(source_production_name=runtime_state.production_name,artifact_key="production_asset_registry",field_path=[name],verified_value=value) for name,value in evidence.items()],stale_artifacts=FINAL_STALE,recorded_by=actor,recorded_at=now),]
 workflow=runtime_state.workflow_state.model_copy(update={"active_conditions":[]})
 memory=runtime_state.memory_snapshot.model_copy(update={"active_conditions":[],"stale_artifacts":FINAL_STALE,"preserved_artifacts":[x for x in runtime_state.memory_snapshot.preserved_artifacts if x not in FINAL_STALE],"current_stage":"EVIDENCE_REFRESH_REQUIRED"})
 return runtime_state.model_copy(update={"workflow_state":workflow,"memory_snapshot":memory,"first_party_declarations":[*runtime_state.first_party_declarations,declaration],"evidence_amendments":[*runtime_state.evidence_amendments,*amendments],"execution_authorized":False,"corrective_cycle_active":True,"current_stage":"EVIDENCE_REFRESH_REQUIRED"})
