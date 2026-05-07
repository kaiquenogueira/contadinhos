"""Cost ledger por story (decisions §11.3).

Filesystem-as-state. Cada story tem `cost_ledger.json` com items append-only.
Total out-of-pocket alimenta o teto mensal.
"""
from __future__ import annotations

import json
from typing import Literal, TypedDict

from contadinhos.core.story import Story


PaidVia = Literal["out_of_pocket", "google_credits"]


class LedgerItem(TypedDict, total=False):
    step: str
    provider: str
    cost_usd: float
    paid_via: PaidVia
    qty: int


class Ledger(TypedDict):
    story_id: str
    items: list[LedgerItem]


def _ledger_path(story: Story):
    return story.path / "cost_ledger.json"


def read_ledger(story: Story) -> Ledger:
    path = _ledger_path(story)
    if not path.exists():
        return {"story_id": story.path.name, "items": []}
    return json.loads(path.read_text())


def append_ledger_entry(
    story: Story,
    step: str,
    provider: str,
    cost_usd: float,
    paid_via: PaidVia,
    qty: int | None = None,
) -> None:
    """Append-only. Persiste ledger atomicamente após adicionar item."""
    ledger = read_ledger(story)
    item: LedgerItem = {
        "step": step,
        "provider": provider,
        "cost_usd": cost_usd,
        "paid_via": paid_via,
    }
    if qty is not None:
        item["qty"] = qty
    ledger["items"].append(item)
    _write_ledger(story, ledger)


def _write_ledger(story: Story, ledger: Ledger) -> None:
    path = _ledger_path(story)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(ledger, indent=2, ensure_ascii=False))
    tmp.replace(path)


def total_out_of_pocket(story: Story) -> float:
    ledger = read_ledger(story)
    return sum(
        item["cost_usd"]
        for item in ledger["items"]
        if item.get("paid_via") == "out_of_pocket"
    )


def total_nominal(story: Story) -> float:
    ledger = read_ledger(story)
    return sum(item["cost_usd"] for item in ledger["items"])
