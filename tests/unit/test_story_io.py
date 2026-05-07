import json
import os
import subprocess
import sys
import textwrap
from datetime import date
from pathlib import Path

import pytest

from contadinhos.core.story import Story


def test_story_create_estrutura(tmp_path):
    story = Story.create(slug="raposa", base_dir=tmp_path, today=date(2026, 5, 7))
    assert story.path.exists()
    assert story.path.name == "2026-05-07-raposa"
    for sub in ("images", "clips", "audio"):
        assert (story.path / sub).is_dir()


def test_story_load_round_trip(tmp_path, roteiro_minimo_dict):
    story = Story.create(slug="raposa", base_dir=tmp_path, today=date(2026, 5, 7))
    (story.path / "roteiro.json").write_text(json.dumps(roteiro_minimo_dict))
    loaded = Story.load(story.path)
    assert loaded.path == story.path
    assert loaded.read_roteiro().titulo == "A raposa curiosa"


def test_next_action_inicial(tmp_path):
    story = Story.create(slug="x", base_dir=tmp_path, today=date(2026, 5, 7))
    # diretório recém-criado, sem audio.m4a → "new"
    assert story.next_action() == "new"
    (story.path / "audio.m4a").write_bytes(b"x")
    assert story.next_action() == "transcribe"


def test_next_action_progressao(tmp_path):
    story = Story.create(slug="x", base_dir=tmp_path, today=date(2026, 5, 7))
    (story.path / "audio.m4a").write_bytes(b"x")
    assert story.next_action() == "transcribe"
    (story.path / "transcript.txt").write_text("ola")
    assert story.next_action() == "script"


def test_collision_appendsufixo(tmp_path):
    s1 = Story.create(slug="raposa", base_dir=tmp_path, today=date(2026, 5, 7))
    s2 = Story.create(slug="raposa", base_dir=tmp_path, today=date(2026, 5, 7))
    s3 = Story.create(slug="raposa", base_dir=tmp_path, today=date(2026, 5, 7))
    assert s1.path.name == "2026-05-07-raposa"
    assert s2.path.name == "2026-05-07-raposa-2"
    assert s3.path.name == "2026-05-07-raposa-3"


def test_lock_bloqueia_segundo_processo(tmp_path):
    """Adquirir lock no PID A; subprocess B tenta non-blocking e falha."""
    story = Story.create(slug="x", base_dir=tmp_path, today=date(2026, 5, 7))
    script = textwrap.dedent(f"""
        import fcntl, sys
        from pathlib import Path
        lock_path = Path({str(story.path / ".lock")!r})
        f = open(lock_path, "w")
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            sys.exit(0)  # adquiriu = falhou
        except BlockingIOError:
            sys.exit(42)  # esperado
    """)
    with story.lock():
        proc = subprocess.run([sys.executable, "-c", script], capture_output=True)
        assert proc.returncode == 42, f"Esperava 42, deu {proc.returncode}: {proc.stderr.decode()}"
