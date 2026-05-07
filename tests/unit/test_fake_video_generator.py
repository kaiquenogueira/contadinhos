"""FakeVideoGenerator subclassa o contract — mesma asserção que VeoGenerator real terá."""
import pytest

from tests.contracts.video_generator import VideoGeneratorContract
from tests.fakes.fake_video_generator import FakeVideoGenerator


class TestFakeVideo(VideoGeneratorContract):
    @pytest.fixture
    def generator(self):
        return FakeVideoGenerator()
