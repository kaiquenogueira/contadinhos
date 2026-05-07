"""Contract test for PreGateAuditor."""
from contadinhos.core.schemas import PolicyCheck, Roteiro

import pytest


class PreGateAuditorContract:
    @pytest.fixture
    def auditor(self):
        raise NotImplementedError

    def test_audit_retorna_policy_check(self, auditor, roteiro_minimo):
        result = auditor.audit(roteiro_minimo)
        assert isinstance(result, PolicyCheck)
        assert result.verdict in ("ok", "review_required")
