import pytest

from tests.contracts.image_generator import ImageGeneratorContract
from tests.fakes.fake_image_generator import FakeImageGenerator


class TestFakeImage(ImageGeneratorContract):
    @pytest.fixture
    def generator(self):
        return FakeImageGenerator()
