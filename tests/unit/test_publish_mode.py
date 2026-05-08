"""publish_mode → privacy_status mapping (decisions §Publish mode)."""
from __future__ import annotations

import pytest

from contadinhos.core.upload.publish_mode import to_privacy_status, valid_modes


def test_private_only_vira_private():
    assert to_privacy_status("private_only") == "private"


def test_unlisted_review_vira_unlisted():
    assert to_privacy_status("unlisted_review") == "unlisted"


def test_direct_public_vira_public():
    assert to_privacy_status("direct_public") == "public"


def test_modo_desconhecido_levanta_value_error():
    with pytest.raises(ValueError, match="publish_mode"):
        to_privacy_status("yolo")


def test_valid_modes_lista_canonica():
    assert valid_modes() == {"private_only", "unlisted_review", "direct_public"}
