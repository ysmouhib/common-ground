"""Files generated from the engine must match what the engine produces now."""
import os
from pathlib import Path

from commonground.__main__ import render_analysis

ROOT = Path(__file__).resolve().parents[2]


def test_app_analysis_is_up_to_date(monkeypatch):
    monkeypatch.chdir(ROOT)
    target = "contracts/analysis.generated.ts"
    fresh = render_analysis("engine/examples/plastic_bags.json", target)
    assert (ROOT / target).read_text(encoding="utf-8") == fresh, (
        "run: python -m commonground analyze engine/examples/plastic_bags.json --out " + target)
    assert os.path.exists(ROOT / "engine" / "examples" / "plastic_bags.json")
