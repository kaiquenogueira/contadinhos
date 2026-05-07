import pytest

from tests.contracts.tts_provider import TTSProviderContract
from tests.fakes.fake_tts import FakeTTS


class TestFakeTTS(TTSProviderContract):
    @pytest.fixture
    def provider(self):
        return FakeTTS()
