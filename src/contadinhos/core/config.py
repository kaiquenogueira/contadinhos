"""Loader único de configs YAML.

Configs vivem em `config/` na raiz do repo e nunca são importadas como
módulo Python (§4, §20.1 de `docs/decisions.md`).
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_DIR = PROJECT_ROOT / "config"


def load_config(name: str, config_dir: Path | None = None) -> dict:
    """Carrega `<config_dir>/<name>.yaml` como dict.

    YAML vazio retorna `{}`. Arquivo ausente levanta `FileNotFoundError`
    com path explícito pra debug fácil.
    """
    base = config_dir or DEFAULT_CONFIG_DIR
    path = base / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"config '{name}' não encontrada em {path}")
    raw = path.read_text()
    if not raw.strip():
        return {}
    return yaml.safe_load(raw) or {}


def snapshot_prompt(story_dir: Path, key: str, value: str | dict) -> None:
    """Acrescenta entrada ao `prompts_snapshot.json` da story.

    Idempotente por chave: se chave já existe, sobrescreve (mesma execução
    pode chamar 2× — última vence). Ver §16 de `docs/decisions.md`.
    """
    snap_path = story_dir / "prompts_snapshot.json"
    data = json.loads(snap_path.read_text()) if snap_path.exists() else {"snapshots": {}}
    data.setdefault("snapshots", {})[key] = value
    snap_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
