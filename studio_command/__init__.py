def __getattr__(name):
    if name == "root_agent":
        from .agent import root_agent
        return root_agent
    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}"
    )


from .decisions import record_studio_head_decision
from .models import StudioHeadDecisionRecord

__all__ = [
    "root_agent",
    "record_studio_head_decision",
    "StudioHeadDecisionRecord",
]

from .decisions import derive_production_workflow_state
from .models import ProductionWorkflowState

__all__ += [
    "derive_production_workflow_state",
    "ProductionWorkflowState",
]

from .decisions import build_production_decision_history_entry
from .models import ProductionDecisionHistoryEntry

__all__ += [
    "build_production_decision_history_entry",
    "ProductionDecisionHistoryEntry",
]

from .decisions import build_corrective_work_record
from .models import CorrectiveWorkRecord

__all__ += [
    "build_corrective_work_record",
    "CorrectiveWorkRecord",
]

from .decisions import build_production_re_review_record
from .models import ProductionReReviewRecord

__all__ += [
    "build_production_re_review_record",
    "ProductionReReviewRecord",
]

from .decisions import record_studio_head_reapproval
from .models import StudioHeadReapprovalRecord

__all__ += [
    "record_studio_head_reapproval",
    "StudioHeadReapprovalRecord",
]

from .decisions import (
    build_governed_production_runtime_state,
    analyze_production_change_impact,
    build_studio_head_impact_brief,
    apply_change_impact_to_runtime,
)

from .models import (
    ProductionMemorySnapshot,
    ProductionChangeImpact,
    StudioHeadImpactBrief,
    GovernedProductionRuntimeState,
)

__all__ += [
    "build_governed_production_runtime_state",
    "analyze_production_change_impact",
    "build_studio_head_impact_brief",
    "apply_change_impact_to_runtime",
    "ProductionMemorySnapshot",
    "ProductionChangeImpact",
    "StudioHeadImpactBrief",
    "GovernedProductionRuntimeState",
]

from .decisions import build_production_execution_authorization
from .models import ProductionExecutionAuthorization

__all__ += [
    "build_production_execution_authorization",
    "ProductionExecutionAuthorization",
]

from .decisions import build_production_execution_authorization
from .models import ProductionExecutionAuthorization

__all__ += [
    "build_production_execution_authorization",
    "ProductionExecutionAuthorization",
]

from .persistence import (
    ProductionPersistence,
    ProductionPersistenceConfig,
)

__all__ += [
    "ProductionPersistence",
    "ProductionPersistenceConfig",
]

from .persistence import (
    ProductionPersistence,
    ProductionPersistenceConfig,
)

__all__ += [
    "ProductionPersistence",
    "ProductionPersistenceConfig",
]

from .graph import (
    build_production_graph,
    start_graph_node,
    complete_graph_node,
    propagate_graph_change,
    resume_stale_graph_nodes,
)
from .models import (
    ProductionGraphNode,
    ProductionGraphState,
)

__all__ += [
    "build_production_graph",
    "start_graph_node",
    "complete_graph_node",
    "propagate_graph_change",
    "resume_stale_graph_nodes",
    "ProductionGraphNode",
    "ProductionGraphState",
]
