"""Contract test for ImageGenerator."""
from pathlib import Path

import pytest


class ImageGeneratorContract:
    @pytest.fixture
    def generator(self):
        raise NotImplementedError

    def test_generate_retorna_n_candidatos(self, generator, tmp_path):
        outs = generator.generate(prompt="raposa aquarela", n=4, output_dir=tmp_path)
        assert len(outs) == 4
        for p in outs:
            assert Path(p).exists()
            assert Path(p).suffix == ".png"

    def test_aborta_em_prompt_vazio(self, generator, tmp_path):
        with pytest.raises(ValueError):
            generator.generate(prompt="", n=4, output_dir=tmp_path)
