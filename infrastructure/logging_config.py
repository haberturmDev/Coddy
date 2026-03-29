"""Structured logging setup (structlog). Call configure_logging() once at process startup."""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any

import structlog
from structlog.typing import EventDict


def _pretty_json_dumps(event_dict: Any, **kwargs: Any) -> str:
    """Multi-line JSON with indentation; blank line after each record for readability."""
    return json.dumps(event_dict, **kwargs) + "\n\n"


def _embed_json_strings_for_json_renderer(
    _logger: Any, _method_name: str, event_dict: EventDict
) -> EventDict:
    """Parse JSON-looking string fields into dict/list so JSON logs indent them."""
    for key in ("body", "body_preview"):
        val = event_dict.get(key)
        if not isinstance(val, str) or not val.strip():
            continue
        try:
            event_dict[key] = json.loads(val)
        except json.JSONDecodeError:
            pass
    return event_dict


def _pretty_json_stack_for_console(
    _logger: Any, _method_name: str, event_dict: EventDict
) -> EventDict:
    """Move headers / body / body_preview into multiline blocks below the main line."""
    blocks: list[str] = []

    hdr = event_dict.pop("headers", None)
    if hdr is not None:
        text = json.dumps(hdr, indent=2, ensure_ascii=False)
        blocks.append(f"headers=\n{text}")

    for key in ("body", "body_preview"):
        val = event_dict.pop(key, None)
        if val is None or val == "":
            continue
        if isinstance(val, str):
            try:
                parsed = json.loads(val)
            except json.JSONDecodeError:
                blocks.append(f"{key}=\n{val}")
                continue
            text = json.dumps(parsed, indent=2, ensure_ascii=False)
            blocks.append(f"{key}=\n{text}")
        else:
            text = json.dumps(val, indent=2, ensure_ascii=False)
            blocks.append(f"{key}=\n{text}")

    if not blocks:
        return event_dict

    extra = "\n\n".join(blocks)
    existing = event_dict.pop("stack", None)
    event_dict["stack"] = f"{existing}\n\n{extra}" if existing else extra
    return event_dict


def configure_logging() -> None:
    """Configure structlog for human-readable console output by default.

    Set LOG_FORMAT=json for JSON logs: indented (multi-line), UTF-8, sorted keys.
    Set LOG_LEVEL=DEBUG|INFO|WARNING|ERROR (default INFO).
    """
    log_format = os.environ.get("LOG_FORMAT", "").lower()
    use_json = log_format == "json"

    if use_json:
        timestamp: structlog.types.Processor = structlog.processors.TimeStamper(
            fmt="iso",
            utc=True,
        )
        # Pretty-printed JSON (indent, newlines) + blank line between records.
        renderer = structlog.processors.JSONRenderer(
            serializer=_pretty_json_dumps,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        json_payload_processor: structlog.types.Processor = (
            _embed_json_strings_for_json_renderer
        )
    else:
        # Local wall-clock time, no microsecond noise — easier to scan than ISO-UTC.
        timestamp = structlog.processors.TimeStamper(
            fmt="%Y-%m-%d %H:%M:%S",
            utc=False,
        )
        # sort_keys=False keeps fields in the order log.info(..., key=value) was called.
        renderer = structlog.dev.ConsoleRenderer(
            colors=True,
            pad_event_to=20,
            sort_keys=False,
            repr_native_str=True,
        )
        json_payload_processor = _pretty_json_stack_for_console

    processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        timestamp,
        json_payload_processor,
        renderer,
    ]

    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    # Avoid duplicate one-line "HTTP Request: ..." next to our structured logs.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )
