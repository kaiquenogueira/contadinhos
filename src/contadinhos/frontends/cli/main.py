"""CLI principal do contadinhos."""
from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from slugify import slugify

from contadinhos.core import pipeline
from contadinhos.core.story import Story
from contadinhos.frontends.cli.deps import build_deps

app = typer.Typer(no_args_is_help=True, add_completion=False)


def _resolve_story(story_path: Path) -> Story:
    return Story.load(story_path)


@app.command()
def new(
    slug: Annotated[str, typer.Argument(help="Slug curto, será slugificado")],
    base_dir: Annotated[Path, typer.Option(help="Onde criar a story")] = Path("stories"),
):
    """Cria uma nova story em `<base_dir>/<YYYY-MM-DD>-<slug>/`."""
    base_dir.mkdir(parents=True, exist_ok=True)
    clean = slugify(slug, max_length=40, word_boundary=True)
    story = Story.create(slug=clean, base_dir=base_dir)
    typer.echo(str(story.path))


@app.command()
def transcribe(
    story_path: Path,
    with_fakes: Annotated[bool, typer.Option("--with-fakes")] = False,
):
    story = _resolve_story(story_path)
    deps = build_deps(with_fakes)
    with story.lock():
        out = pipeline.run_transcribe(story, deps)
    typer.echo(f"transcript em {out}")


@app.command()
def script(
    story_path: Path,
    with_fakes: Annotated[bool, typer.Option("--with-fakes")] = False,
    target_duration_s: float = 75,
):
    story = _resolve_story(story_path)
    deps = build_deps(with_fakes)
    try:
        with story.lock():
            roteiro = pipeline.run_script(story, deps, target_duration_s=target_duration_s)
    except pipeline.PipelineBlocked as exc:
        typer.echo(f"⚠️ pré-gate bloqueou: {exc}", err=True)
        raise typer.Exit(2) from exc
    typer.echo(f"roteiro com {len(roteiro.cenas)} cenas")


@app.command()
def images(
    story_path: Path,
    with_fakes: Annotated[bool, typer.Option("--with-fakes")] = False,
):
    story = _resolve_story(story_path)
    deps = build_deps(with_fakes)
    with story.lock():
        pipeline.run_images(story, deps)
    typer.echo("imagens-chave geradas")


@app.command()
def video(
    story_path: Path,
    with_fakes: Annotated[bool, typer.Option("--with-fakes")] = False,
):
    story = _resolve_story(story_path)
    deps = build_deps(with_fakes)
    with story.lock():
        pipeline.run_video(story, deps)
    typer.echo("clipes gerados")


@app.command()
def tts(
    story_path: Path,
    with_fakes: Annotated[bool, typer.Option("--with-fakes")] = False,
):
    story = _resolve_story(story_path)
    deps = build_deps(with_fakes)
    with story.lock():
        pipeline.run_tts(story, deps)
    typer.echo("narração gerada")


@app.command()
def assemble(
    story_path: Path,
    with_fakes: Annotated[bool, typer.Option("--with-fakes")] = False,
):
    story = _resolve_story(story_path)
    deps = build_deps(with_fakes)
    with story.lock():
        out = pipeline.run_assemble(story, deps)
    typer.echo(f"final.mp4 em {out}")


@app.command()
def publish(
    story_path: Path,
    with_fakes: Annotated[bool, typer.Option("--with-fakes")] = False,
):
    story = _resolve_story(story_path)
    deps = build_deps(with_fakes)
    with story.lock():
        result = pipeline.run_publish(story, deps)
    typer.echo(f"upload: {result.get('url', result.get('videoId'))}")


@app.command()
def run(
    story_path: Path,
    with_fakes: Annotated[bool, typer.Option("--with-fakes")] = False,
):
    """Roda todas as etapas a partir de `next_action` até `done`."""
    story = _resolve_story(story_path)
    deps = build_deps(with_fakes)
    with story.lock():
        pipeline.run_all(story, deps)
    typer.echo(f"story {story.path.name} completa")


@app.command()
def status(story_path: Path):
    story = _resolve_story(story_path)
    typer.echo(story.next_action())


if __name__ == "__main__":
    app()
