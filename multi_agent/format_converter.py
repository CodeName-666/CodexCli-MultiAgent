from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Protocol, Tuple


class FormatConversionError(RuntimeError):
    pass


class FormatHandler(Protocol):
    name: str
    extensions: Tuple[str, ...]

    def decode(self, text: str) -> object:
        ...

    def encode(self, data: object) -> str:
        ...


@dataclass(frozen=True)
class JsonFormatHandler:
    name: str = "json"
    extensions: Tuple[str, ...] = (".json",)
    indent: int = 2

    def decode(self, text: str) -> object:
        return json.loads(text)

    def encode(self, data: object) -> str:
        return json.dumps(data, indent=self.indent, ensure_ascii=True)


@dataclass(frozen=True)
class ToonFormatHandler:
    name: str = "toon"
    extensions: Tuple[str, ...] = (".toon",)
    options: Dict[str, object] | None = None

    def _load(self) -> Any:
        try:
            import toon_format  # type: ignore[import-not-found]
        except ImportError as exc:
            raise FormatConversionError(
                "TOON conversion requires the 'toon-format' package. "
                "Install it with: pip install toon-format"
            ) from exc
        return toon_format

    def decode(self, text: str) -> object:
        toon_format = self._load()
        if self.options:
            return toon_format.decode(text, self.options)
        return toon_format.decode(text)

    def encode(self, data: object) -> str:
        toon_format = self._load()
        if self.options:
            return toon_format.encode(data, self.options)
        return toon_format.encode(data)


class FormatConverter:
    def __init__(self, handlers: Iterable[FormatHandler] | None = None) -> None:
        self._handlers: Dict[str, FormatHandler] = {}
        if handlers:
            for handler in handlers:
                self.register(handler)

    def register(self, handler: FormatHandler) -> None:
        self._handlers[handler.name] = handler

    def get(self, name: str) -> FormatHandler:
        handler = self._handlers.get(name)
        if not handler:
            raise FormatConversionError(f"Unknown format handler: {name}")
        return handler

    def handler_for_extension(self, extension: str) -> FormatHandler | None:
        ext = (extension or "").lower()
        for handler in self._handlers.values():
            if ext in handler.extensions:
                return handler
        return None

    def decode(self, text: str, format_name: str) -> object:
        return self.get(format_name).decode(text)

    def encode(self, data: object, format_name: str) -> str:
        return self.get(format_name).encode(data)

    def convert(self, text: str, source_format: str, target_format: str) -> str:
        data = self.decode(text, source_format)
        return self.encode(data, target_format)

    def convert_by_extension(self, text: str, extension: str, target_format: str) -> str:
        handler = self.handler_for_extension(extension)
        if not handler:
            raise FormatConversionError(f"No handler registered for extension: {extension}")
        return self.convert(text, handler.name, target_format)


def build_default_converter(formatting_cfg: Dict[str, object] | None = None) -> FormatConverter:
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
