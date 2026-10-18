from davdeploy.domain import LifecycleState

LEGAL_TRANSITIONS: dict[LifecycleState, set[LifecycleState]] = {
    LifecycleState.DRAFT: {LifecycleState.ANALYZING},
    LifecycleState.ANALYZING: {
        LifecycleState.NEEDS_INPUT,
        LifecycleState.PLANNED,
        LifecycleState.POLICY_DENIED,
    },
    LifecycleState.NEEDS_INPUT: {LifecycleState.ANALYZING},
    LifecycleState.PLANNED: {
        LifecycleState.APPROVAL_REQUIRED,
        LifecycleState.APPROVED,
        LifecycleState.QUEUED,
        LifecycleState.POLICY_DENIED,
    },
    LifecycleState.POLICY_DENIED: set(),
    LifecycleState.APPROVAL_REQUIRED: {LifecycleState.APPROVED, LifecycleState.POLICY_DENIED},
    LifecycleState.APPROVED: {LifecycleState.QUEUED},
    LifecycleState.QUEUED: {LifecycleState.PROVISIONING, LifecycleState.DESTROYING},
    LifecycleState.PROVISIONING: {LifecycleState.DEPLOYING, LifecycleState.FAILED},
    LifecycleState.DEPLOYING: {LifecycleState.VERIFYING, LifecycleState.FAILED},
    LifecycleState.VERIFYING: {
        LifecycleState.READY,
        LifecycleState.DEGRADED,
        LifecycleState.FAILED,
    },
    LifecycleState.READY: {
        LifecycleState.CHANGE_PROPOSED,
        LifecycleState.QUEUED,
        LifecycleState.DESTROY_REQUESTED,
    },
    LifecycleState.DEGRADED: {
        LifecycleState.CHANGE_PROPOSED,
        LifecycleState.QUEUED,
        LifecycleState.DESTROY_REQUESTED,
    },
    LifecycleState.CHANGE_PROPOSED: {
        LifecycleState.APPROVAL_REQUIRED,
        LifecycleState.APPROVED,
        LifecycleState.QUEUED,
        LifecycleState.FAILED,
    },
    LifecycleState.FAILED: {LifecycleState.DESTROY_REQUESTED, LifecycleState.DESTROYED},
    LifecycleState.DESTROY_REQUESTED: {
        LifecycleState.DESTROY_APPROVAL_REQUIRED,
        LifecycleState.QUEUED,
    },
    LifecycleState.DESTROY_APPROVAL_REQUIRED: {LifecycleState.APPROVED},
    LifecycleState.DESTROYING: {LifecycleState.DESTROYED, LifecycleState.FAILED},
    LifecycleState.DESTROYED: set(),
}


def require_transition(current: LifecycleState, target: LifecycleState) -> None:
    if target not in LEGAL_TRANSITIONS[current]:
        raise ValueError(f"illegal lifecycle transition: {current} -> {target}")
