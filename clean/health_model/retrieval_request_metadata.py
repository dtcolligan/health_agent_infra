from __future__ import annotations

from datetime import datetime
from typing import Any


def validate_and_echo_request_metadata(*, request_id: Any, requested_at: Any) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    request_echo = {
        "request_id": request_id,
        "requested_at": requested_at,
    }

    semantic_issues: list[dict[str, str]] = []
    if not isinstance(request_id, str) or not request_id.strip():
        semantic_issues.append(
            {
                "code": "invalid_request_id",
                "message": "request_id must be a non-empty string.",
                "path": "request_id",
            }
        )

    if not isinstance(requested_at, str):
        semantic_issues.append(
            {
                "code": "invalid_requested_at",
                "message": "requested_at must be an ISO 8601 datetime string with timezone information.",
                "path": "requested_at",
            }
        )
    else:
        try:
            parsed = datetime.fromisoformat(requested_at)
            if parsed.tzinfo is None:
                raise ValueError("missing timezone")
        except ValueError:
            semantic_issues.append(
                {
                    "code": "invalid_requested_at",
                    "message": "requested_at must be an ISO 8601 datetime string with timezone information.",
                    "path": "requested_at",
                }
            )

    if semantic_issues:
        return (
            {
                "is_valid": False,
                "schema_issues": [],
                "semantic_issues": semantic_issues,
                "request_echo": request_echo,
            },
            request_echo,
        )

    return (
        {
            "is_valid": True,
            "schema_issues": [],
            "semantic_issues": [],
            "request_echo": request_echo,
        },
        request_echo,
    )
