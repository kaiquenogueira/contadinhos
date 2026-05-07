from pathlib import Path

import pytest

from contadinhos.core.config import load_config


def test_load_pipeline_yaml(tmp_path):
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir()
    (cfg_dir / "pipeline.yaml").write_text("target_duration_s: 75\n")
    cfg = load_config("pipeline", config_dir=cfg_dir)
    assert cfg["target_duration_s"] == 75


def test_load_yaml_inexistente_erro_claro(tmp_path):
    with pytest.raises(FileNotFoundError) as exc:
        load_config("nao_existe", config_dir=tmp_path)
    assert "nao_existe" in str(exc.value)


def test_load_yaml_vazio_retorna_dict_vazio(tmp_path):
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir()
    (cfg_dir / "vazio.yaml").write_text("")
    cfg = load_config("vazio", config_dir=cfg_dir)
    assert cfg == {}
