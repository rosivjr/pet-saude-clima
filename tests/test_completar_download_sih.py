"""Testes da proveniência gravada por sih/completar_download_sih.py, com JSON sintético."""

import json

from sih import completar_download_sih as completar


def test_gravar_proveniencia_mantem_registros_anteriores(tmp_path, monkeypatch):
    """JSON com RDAC2501 e RDPA2501; chega RDPA2501 novo e RDAM2501: 3 arquivos, PA trocado."""
    caminho = tmp_path / "proveniencia_sih_nacional.json"
    monkeypatch.setattr(completar, "PROVENIENCIA_NACIONAL", caminho)
    anteriores = [
        {"arquivo": "RDAC2501.parquet", "sha256": "a"},
        {"arquivo": "RDPA2501.parquet", "sha256": "b"},
    ]
    caminho.write_text(json.dumps({"arquivos": anteriores}), encoding="utf-8")

    completar.gravar_proveniencia(
        [
            {"arquivo": "RDPA2501.parquet", "sha256": "c"},
            {"arquivo": "RDAM2501.parquet", "sha256": "d"},
        ]
    )

    arquivos = json.loads(caminho.read_text(encoding="utf-8"))["arquivos"]
    assert [(a["arquivo"], a["sha256"]) for a in arquivos] == [
        ("RDAC2501.parquet", "a"),
        ("RDAM2501.parquet", "d"),
        ("RDPA2501.parquet", "c"),
    ]


def test_consulta_registra_o_grupo_rd():
    assert (
        completar.consulta("PA", 2025, 1) == "pysus.ftp.sih(state=PA, year=2025, month=1, group=RD)"
    )
