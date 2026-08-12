from studio_command.service import RealityShiftRequest, reality_shift


result = reality_shift(
    RealityShiftRequest(
        changed_node_ids=["Scheduling"],
        reason="Launch moved from Friday to Wednesday.",
    )
)

assert result["status"] == "REALITY_SHIFT_DETECTED"

assert "Scheduling" in result["stale_nodes"]
assert "Clearance & Compliance" in result["stale_nodes"]
assert "Verification QA" in result["stale_nodes"]
assert "Studio Head Decision" in result["stale_nodes"]
assert "Final Package" in result["stale_nodes"]

assert "Asset & Media" in result["preserved_nodes"]
assert "Research" in result["preserved_nodes"]
assert "Creative Development" in result["preserved_nodes"]

assert result["human_decision_required"] is True

print("MILESTONE 24 REALITY SHIFT DETECTION: PASS")
print("MILESTONE 24 DOWNSTREAM IMPACT PROPAGATION: PASS")
print("MILESTONE 24 UNAFFECTED WORK PRESERVATION: PASS")
print("MILESTONE 24 HUMAN REAUTHORIZATION GATE: PASS")
print("MILESTONE 1-24 PRODUCTION REALITY PATH: PASS")
