from __future__ import annotations

import logging
from pathlib import Path

import pytest

from owl2vault import cli
from owl2vault.model import OModel


def test_cli_warns_and_exits_when_output_dirs_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    missing_linkml = tmp_path / "nope" / "schema.yaml"
    called = {"load": False}

    def _fake_load(_: str) -> OModel:
        called["load"] = True
        return OModel(ontology_iri=None)

    monkeypatch.setattr(cli, "load_owl", _fake_load)

    with caplog.at_level(logging.WARNING):
        with pytest.raises(SystemExit):
            cli.main(
                [
                    "-i",
                    "input.owl",
                    "--linkml",
                    str(missing_linkml),
                ]
            )

    assert "--linkml parent directory does not exist" in caplog.text
    assert called["load"] is False


def test_cli_creates_missing_dirs_when_requested(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    out_root = tmp_path / "out"
    linkml = out_root / "schema" / "schema.yaml"
    vault = out_root / "vault"
    mkdocs = out_root / "mkdocs"
    docsify = out_root / "docsify"
    hugo = out_root / "hugo"

    monkeypatch.setattr(cli, "load_owl", lambda _: OModel(ontology_iri=None))
    monkeypatch.setattr(cli, "write_linkml_yaml", lambda *_: None)
    monkeypatch.setattr(cli, "write_obsidian_vault", lambda *_: None)
    monkeypatch.setattr(cli, "write_mkdocs_docs", lambda *_: None)
    monkeypatch.setattr(cli, "write_docsify_docs", lambda *_: None)
    monkeypatch.setattr(cli, "write_hugo_site", lambda *_: None)

    cli.main(
        [
            "-i",
            "input.owl",
            "--create-dirs",
            "--linkml",
            str(linkml),
            "--vault",
            str(vault),
            "--mkdocs",
            str(mkdocs),
            "--docsify",
            str(docsify),
            "--hugo",
            str(hugo),
        ]
    )

    assert linkml.parent.is_dir()
    assert vault.is_dir()
    assert mkdocs.is_dir()
    assert docsify.is_dir()
    assert hugo.is_dir()
