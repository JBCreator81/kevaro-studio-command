from __future__ import annotations


def canonical_production_name(production_name: str) -> str:
    """Return the production identity used by persistence, APIs, and runtime."""
    normalized_name = production_name.strip()

    if not normalized_name:
        raise ValueError("Production name must not be empty.")

    return normalized_name


def require_production_identity(
    production_name: str,
    *artifact_production_names: str,
) -> str:
    """Validate that identity-bearing artifacts belong to one production."""
    canonical_name = canonical_production_name(production_name)

    for artifact_name in artifact_production_names:
        if canonical_production_name(artifact_name) != canonical_name:
            raise ValueError(
                "Production identity does not match the canonical production."
            )

    return canonical_name
