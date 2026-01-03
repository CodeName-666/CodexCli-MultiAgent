"""Helpers to convert between JSON and TOON payload formats."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Protocol, Tuple


class FormatConversionError(RuntimeError):
    """Raised when a format conversion cannot be performed."""
    pass


class FormatHandler(Protocol):
    """Protocol for format handlers that can decode and encode data."""
    name: str
    extensions: Tuple[str, ...]

    def decode(self, text: str) -> object:
        """Decode a serialized payload into a Python object."""
        ...

    def encode(self, data: object) -> str:
        """Encode a Python object into a serialized payload."""
        ...


@dataclass(frozen=True)
class JsonFormatHandler:
    """Handler for JSON serialization and deserialization."""
    name: str = "json"
    extensions: Tuple[str, ...] = (".json",)
    indent: int = 2

    def decode(self, text: str) -> object:
        """Decode JSON text into a Python object."""
        return json.loads(text)

    def encode(self, data: object) -> str:
        """Encode a Python object into JSON text."""
        return json.dumps(data, indent=self.indent, ensure_ascii=True)


@dataclass(frozen=True)
class ToonFormatHandler:
    """Handler for TOON serialization using the optional toon-format package."""
    name: str = "toon"
    extensions: Tuple[str, ...] = (".toon",)
    options: Dict[str, object] | None = None

    def _load(self) -> Any:
        """Import and return the toon_format module."""
        try:
            import toon_format  # type: ignore[import-not-found]
        except ImportError as exc:
            raise FormatConversionError(
                "TOON conversion requires the 'toon-format' package. "
                "Install it with: pip install toon-format"
            ) from exc
        return toon_format

    def decode(self, text: str) -> object:
        """Decode TOON text into a Python object."""
        toon_format = self._load()
        if self.options:
            return toon_format.decode(text, self.options)
        return toon_format.decode(text)

    def encode(self, data: object) -> str:
        """Encode a Python object into TOON text."""
        toon_format = self._load()
        if self.options:
            return toon_format.encode(data, self.options)
        return toon_format.encode(data)


class FormatConverter:
    """Registry and dispatcher for format conversion handlers."""

    def __init__(self, handlers: Iterable[FormatHandler] | None = None) -> None:
        """Initialize the converter and register any initial handlers."""
        self._handlers: Dict[str, FormatHandler] = {}
        if handlers:
            for handler in handlers:
                self.register(handler)

    def register(self, handler: FormatHandler) -> None:
        """Register a format handler by its name."""
        self._handlers[handler.name] = handler

    def get(self, name: str) -> FormatHandler:
        """Return a handler by name or raise if missing."""
        handler = self._handlers.get(name)
        if not handler:
            raise FormatConversionError(f"Unknown format handler: {name}")
        return handler

    def handler_for_extension(self, extension: str) -> FormatHandler | None:
        """Return a handler matching a file extension, if any."""
        ext = (extension or "").lower()
        for handler in self._handlers.values():
            if ext in handler.extensions:
                return handler
        return None

    def decode(self, text: str, format_name: str) -> object:
        """Decode text using the named handler."""
        return self.get(format_name).decode(text)

    def encode(self, data: object, format_name: str) -> str:
        """Encode data using the named handler."""
        return self.get(format_name).encode(data)

    def convert(self, text: str, source_format: str, target_format: str) -> str:
        """Convert text from one format to another."""
        data = self.decode(text, source_format)
        return self.encode(data, target_format)

    def convert_by_extension(self, text: str, extension: str, target_format: str) -> str:
        """Convert text using a handler inferred from a file extension."""
        handler = self.handler_for_extension(extension)
        if not handler:
            raise FormatConversionError(f"No handler registered for extension: {extension}")
        return self.convert(text, handler.name, target_format)


def build_default_converter(formatting_cfg: Dict[str, object] | None = None) -> FormatConverter:
    """Build a converter with JSON and TOON handlers configured."""
    formatting_cfg = formatting_cfg or {}
    toon_options_raw = formatting_cfg.get("toon_options") or {}
    toon_options = dict(toon_options_raw) if isinstance(toon_options_raw, dict) else {}
    return FormatConverter(
        handlers=[
            JsonFormatHandler(),
            ToonFormatHandler(options=toon_options),
        ]
    )


def extract_payload_from_markdown(text: str, format_name: str) -> str:
    """Extract a JSON or TOON payload block from Markdown text."""
    text = text or ""
    if format_name == "json":
        match = re.search(r"```json\s*\n(.*?)\n```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        match = re.search(r"```\s*\n(\{.*?\})\n```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return text.strip()

    if format_name == "toon":
        match = re.search(r"```toon\s*\n(.*?)\n```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        match = re.search(r"```\s*\n(.*?)\n```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return text.strip()

    return text.strip()
