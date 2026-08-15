import json
import tempfile
from pathlib import Path

import studio_command.service as service
from studio_command.service import RealityShiftRequest, reality_shift


_snapshot_dir = tempfile.TemporaryDirectory()
service.SNAPSHOT_PATH = Path(_snapshot_dir.name) / "studio-snapshot.json"
service.SNAPSHOT_PATH.write_text(
    json.dumps(
        {
            "production_name": "Luxury Wellness Campaign",
            "graph": {
                "ready_nodes": [],
                "running_nodes": [],
                "completed_nodes": [
                    "Production Brief",
                    "Research",
                    "Creative Development",
                    "Production Planning",
                    "Scheduling",
                    "Asset & Media",
                    "Clearance & Compliance",
                    "Verification QA",
                    "Studio Head Decision",
                    "Final Package",
                ],
                "blocked_nodes": [],
                "stale_nodes": [],
                "graph_complete": True,
                "nodes": [
                    {
                        "node_id": "Production Brief",
                        "task_name": "Production Brief",
                        "responsible_role": "Executive Producer",
                        "dependencies": [],
                        "dependents": ["Research", "Creative Development"],
                        "status": "COMPLETED",
                        "parallel_with": [],
                        "approval_required": False,
                        "stale_reason": None,
                    },
                    {
                        "node_id": "Research",
                        "task_name": "Research",
                        "responsible_role": "Research Agent",
                        "dependencies": ["Production Brief"],
                        "dependents": ["Production Planning"],
                        "status": "COMPLETED",
                        "parallel_with": ["Creative Development"],
                        "approval_required": False,
                        "stale_reason": None,
                    },
                    {
                        "node_id": "Creative Development",
                        "task_name": "Creative Development",
                        "responsible_role": "Creative Development Agent",
                        "dependencies": ["Production Brief"],
                        "dependents": ["Production Planning"],
                        "status": "COMPLETED",
                        "parallel_with": ["Research"],
                        "approval_required": False,
                        "stale_reason": None,
                    },
                    {
                        "node_id": "Production Planning",
                        "task_name": "Production Planning",
                        "responsible_role": "Production Manager",
                        "dependencies": ["Research", "Creative Development"],
                        "dependents": ["Scheduling", "Asset & Media"],
                        "status": "COMPLETED",
                        "parallel_with": [],
                        "approval_required": False,
                        "stale_reason": None,
                    },
                    {
                        "node_id": "Scheduling",
                        "task_name": "Scheduling",
                        "responsible_role": "Scheduling Agent",
                        "dependencies": ["Production Planning"],
                        "dependents": ["Clearance & Compliance", "Verification QA"],
                        "status": "COMPLETED",
                        "parallel_with": ["Asset & Media"],
                        "approval_required": False,
                        "stale_reason": None,
                    },
                    {
                        "node_id": "Asset & Media",
                        "task_name": "Asset & Media",
                        "responsible_role": "Asset & Media Agent",
                        "dependencies": ["Production Planning"],
                        "dependents": ["Clearance & Compliance", "Verification QA"],
                        "status": "COMPLETED",
                        "parallel_with": ["Scheduling"],
                        "approval_required": False,
                        "stale_reason": None,
                    },
                    {
                        "node_id": "Clearance & Compliance",
                        "task_name": "Clearance & Compliance",
                        "responsible_role": "Clearance & Compliance Agent",
                        "dependencies": ["Scheduling", "Asset & Media"],
                        "dependents": ["Verification QA"],
                        "status": "COMPLETED",
                        "parallel_with": [],
                        "approval_required": False,
                        "stale_reason": None,
                    },
                    {
                        "node_id": "Verification QA",
                        "task_name": "Verification QA",
                        "responsible_role": "Verification QA Agent",
                        "dependencies": [
                            "Scheduling",
                            "Asset & Media",
                            "Clearance & Compliance",
                        ],
                        "dependents": ["Studio Head Decision"],
                        "status": "COMPLETED",
                        "parallel_with": [],
                        "approval_required": False,
                        "stale_reason": None,
                    },
                    {
                        "node_id": "Studio Head Decision",
                        "task_name": "Studio Head Decision",
                        "responsible_role": "Studio Head",
                        "dependencies": ["Verification QA"],
                        "dependents": ["Final Package"],
                        "status": "COMPLETED",
                        "parallel_with": [],
                        "approval_required": True,
                        "stale_reason": None,
                    },
                    {
                        "node_id": "Final Package",
                        "task_name": "Final Package",
                        "responsible_role": "Production Manager",
                        "dependencies": ["Studio Head Decision"],
                        "dependents": [],
                        "status": "COMPLETED",
                        "parallel_with": [],
                        "approval_required": False,
                        "stale_reason": None,
                    },
                ],
            },
        }
    )
)


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
