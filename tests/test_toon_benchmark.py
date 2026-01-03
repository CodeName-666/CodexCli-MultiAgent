import json

import pytest

from multi_agent.format_converter import build_default_converter
from multi_agent.utils import estimate_tokens

toon_format = pytest.importorskip("toon_format")


def _count_tokens(text: str) -> int:
    counter = getattr(toon_format, "count_tokens", None)
    if counter is None:
        return estimate_tokens(text)
    try:
        return int(counter(text))
    except Exception:
        return estimate_tokens(text)


def test_toon_benchmark_token_savings() -> None:
    data = {
        "items": [
            {
                "id": idx,
                "name": f"Item {idx}",
                "category": "tools",
                "price": round(3.5 * idx, 2),
                "active": idx % 2 == 0,
            }
            for idx in range(1, 51)
        ],
        "meta": {"source": "benchmark", "version": 1},
    }

    json_text = json.dumps(data, indent=2, ensure_ascii=True)
    converter = build_default_converter({})
    toon_text = converter.encode(data, "toon")

    json_tokens = _count_tokens(json_text)
    toon_tokens = _count_tokens(toon_text)

    print(f"json_tokens={json_tokens} toon_tokens={toon_tokens}")
    assert toon_tokens < json_tokens
