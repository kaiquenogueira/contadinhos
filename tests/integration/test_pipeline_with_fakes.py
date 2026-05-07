"""Pipeline ponta-a-ponta com Fakes — DoD da Sprint 1."""
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

from contadinhos.core.story import Story


@pytest.mark.integration
def test_run_completo_gera_final_mp4(tmp_path, silencio_30s_m4a):
    """`contadinhos run --with-fakes` produz final.mp4 sem chamadas HTTP."""
    base = tmp_path / "stories"
    base.mkdir()
    story = Story.create(slug="raposa", base_dir=base, today=date(2026, 5, 7))
    # input cru
    (story.path / "audio.m4a").write_bytes(silencio_30s_m4a.read_bytes())

    env = {**os.environ, "CONTADINHOS_FAKES": "1"}
    proc = subprocess.run(
        [sys.executable, "-m", "contadinhos.frontends.cli.main", "run", str(story.path)],
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"stdout={proc.stdout}\nstderr={proc.stderr}"

    final = story.path / "final.mp4"
    assert final.exists(), f"final.mp4 não foi criado em {story.path}"
    assert final.stat().st_size > 0
