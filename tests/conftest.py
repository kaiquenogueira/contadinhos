"""Fixtures compartilhadas entre todos os testes."""
import json
from pathlib import Path

import pytest

from contadinhos.core.schemas import Roteiro

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def roteiro_minimo_dict() -> dict:
    return json.loads((FIXTURES / "roteiros" / "valido_minimo.json").read_text())


@pytest.fixture
def roteiro_completo_dict() -> dict:
    return json.loads((FIXTURES / "roteiros" / "valido_completo.json").read_text())


@pytest.fixture
def roteiro_violencia_dict() -> dict:
    return json.loads((FIXTURES / "roteiros" / "violencia.json").read_text())


@pytest.fixture
def roteiro_minimo(roteiro_minimo_dict) -> Roteiro:
    return Roteiro.model_validate(roteiro_minimo_dict)


@pytest.fixture
def placeholder_png() -> Path:
    return FIXTURES / "images" / "placeholder.png"


@pytest.fixture
def placeholder_mp4() -> Path:
    return FIXTURES / "video" / "placeholder_5s.mp4"


@pytest.fixture
def silencio_30s_m4a() -> Path:
    return FIXTURES / "audio" / "silencio_30s.m4a"
