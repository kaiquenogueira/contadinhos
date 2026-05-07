"""Cost ledger por story (decisions §11.3)."""
import json
from datetime import date

from contadinhos.core.budget import append_ledger_entry, read_ledger, total_out_of_pocket
from contadinhos.core.story import Story


def test_append_entry_cria_ledger(tmp_path):
    story = Story.create(slug="x", base_dir=tmp_path, today=date(2026, 5, 7))
    append_ledger_entry(
        story=story,
        step="transcribe",
        provider="gpt-4o-transcribe",
        cost_usd=0.018,
        paid_via="out_of_pocket",
    )
    raw = json.loads((story.path / "cost_ledger.json").read_text())
    assert raw["story_id"] == story.path.name
    assert len(raw["items"]) == 1
    assert raw["items"][0]["paid_via"] == "out_of_pocket"


def test_append_idempotente_em_steps_distintos(tmp_path):
    story = Story.create(slug="x", base_dir=tmp_path, today=date(2026, 5, 7))
    append_ledger_entry(story, "transcribe", "gpt-4o-transcribe", 0.018, "out_of_pocket")
    append_ledger_entry(story, "script", "gpt-5-mini", 0.005, "out_of_pocket")
    append_ledger_entry(story, "pre_gate", "gemini-2.5-flash", 0.01, "google_credits")
    raw = read_ledger(story)
    assert len(raw["items"]) == 3
    steps = {item["step"] for item in raw["items"]}
    assert steps == {"transcribe", "script", "pre_gate"}


def test_total_out_of_pocket_ignora_credits(tmp_path):
    story = Story.create(slug="x", base_dir=tmp_path, today=date(2026, 5, 7))
    append_ledger_entry(story, "transcribe", "gpt-4o-transcribe", 0.02, "out_of_pocket")
    append_ledger_entry(story, "video", "veo-3.1", 50.0, "google_credits")
    append_ledger_entry(story, "script", "gpt-5-mini", 0.005, "out_of_pocket")
    assert total_out_of_pocket(story) == 0.02 + 0.005
