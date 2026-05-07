"""Contract test for PostGate (multimodal)."""
from contadinhos.core.schemas import PolicyCheck

import pytest


class PostGateContract:
    @pytest.fixture
    def post_gate(self):
        raise NotImplementedError

    def test_audit_retorna_policy_check(self, post_gate, placeholder_mp4):
        result = post_gate.audit(video_path=placeholder_mp4)
        assert isinstance(result, PolicyCheck)
        assert result.verdict in ("ok", "review_required")
