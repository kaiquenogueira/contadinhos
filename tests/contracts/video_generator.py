"""Contract test for VideoGenerator. Subclassed by Fake and Real impls."""
from pathlib import Path

import pytest


class VideoGeneratorContract:
    @pytest.fixture
    def generator(self):
        raise NotImplementedError("subclasse provê o generator")

    def test_t2v_retorna_mp4_existente(self, generator, tmp_path):
        out = generator.generate(
            prompt="paisagem aquarela",
            duration_s=5,
            output_path=tmp_path / "scene.mp4",
        )
        assert Path(out).exists()
        assert Path(out).suffix == ".mp4"
        assert Path(out).stat().st_size > 0

    def test_i2v_aceita_first_frame(self, generator, tmp_path, placeholder_png):
        out = generator.generate(
            prompt="raposa caminhando",
            duration_s=5,
            first_frame=placeholder_png,
            output_path=tmp_path / "scene_i2v.mp4",
        )
        assert Path(out).exists()

    def test_aborta_em_prompt_vazio(self, generator, tmp_path):
        with pytest.raises(ValueError):
            generator.generate(prompt="", duration_s=5, output_path=tmp_path / "bad.mp4")
