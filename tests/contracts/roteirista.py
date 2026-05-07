"""Contract test for Roteirista (LLM)."""
from contadinhos.core.schemas import Roteiro

import pytest


class RoteiristaContract:
    @pytest.fixture
    def roteirista(self):
        raise NotImplementedError

    def test_gera_roteiro_valido_de_transcript(self, roteirista):
        roteiro = roteirista.generate(
            transcript="Era uma vez uma raposa que encontrou uma flor.",
            target_duration_s=75,
        )
        assert isinstance(roteiro, Roteiro)
        assert len(roteiro.cenas) >= 1
        assert roteiro.sinopse_curta
