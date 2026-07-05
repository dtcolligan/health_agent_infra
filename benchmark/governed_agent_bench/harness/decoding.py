"""Roster decoding-settings pass-through for provider chat requests.

Pre-registration audit fix A7: the request builders previously forwarded
only ``temperature`` / ``top_p`` / ``max_tokens``, which made
vendor-recommended per-model sampling (``top_k``, ``min_p``,
``repetition_penalty``, ``seed``, ``stop``) inexpressible. This module is
the single seam through which a roster condition's ``decoding_settings``
reach the provider request, so the roster stays the single source of
decoding truth for the pre-registered run.
"""

from __future__ import annotations

from typing import Any, Mapping

from governed_agent_bench.harness.core import HarnessError


# The full expressible decoding surface for the OpenAI-compatible chat
# APIs used by the roster ladder. ``stop`` is string-valued; every other
# key is numeric.
DECODING_ALLOWED_KEYS = frozenset({
    "temperature",
    "top_p",
    "top_k",
    "min_p",
    "presence_penalty",
    "repetition_penalty",
    "max_tokens",
    "seed",
    "stop",
    # Vendor-documented template switch (e.g. Qwen3.5's
    # {"enable_thinking": false} to run a thinking-by-default model in
    # non-thinking mode; mechanism documented on the Together model page).
    "chat_template_kwargs",
})
_STRING_VALUED_KEYS = frozenset({"stop"})
_DICT_VALUED_KEYS = frozenset({"chat_template_kwargs"})


def decoding_request_fields(
    decoding_settings: Mapping[str, Any],
) -> dict[str, Any]:
    """Map a roster condition's ``decoding_settings`` onto request fields.

    - Unknown keys raise: a typo'd or unsupported setting must never be
      silently dropped from a metered, pre-registered run.
    - Numeric keys pass through ``int`` / ``float`` values. A string value
      is a declared placeholder (e.g. the roster's
      ``seed: "provider_does_not_support_seed"``) and is skipped, never
      sent to the provider. ``None`` is skipped likewise.
    - ``stop`` passes through a string or a list of strings.
    """

    unknown = sorted(set(decoding_settings) - DECODING_ALLOWED_KEYS)
    if unknown:
        raise HarnessError(
            f"decoding_settings has unsupported keys: {unknown}; "
            f"allowed keys: {sorted(DECODING_ALLOWED_KEYS)}"
        )
    fields: dict[str, Any] = {}
    for key in sorted(decoding_settings):
        value = decoding_settings[key]
        if value is None:
            continue
        if key in _DICT_VALUED_KEYS:
            if isinstance(value, Mapping) and all(
                isinstance(k, str) for k in value
            ):
                fields[key] = dict(value)
                continue
            raise HarnessError(
                f"decoding_settings[{key!r}] must be a string-keyed object, "
                f"got: {value!r}"
            )
        if key in _STRING_VALUED_KEYS:
            if isinstance(value, str) or (
                isinstance(value, list)
                and all(isinstance(item, str) for item in value)
            ):
                fields[key] = value
                continue
            raise HarnessError(
                f"decoding_settings[{key!r}] must be a string or a list of "
                f"strings, got: {value!r}"
            )
        if isinstance(value, str):
            # Declared non-numeric placeholder (e.g. the seed sentinel):
            # skipped, never sent on the wire.
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise HarnessError(
                f"decoding_settings[{key!r}] must be numeric, got: {value!r}"
            )
        fields[key] = value
    return fields
