"""Testes das funções auxiliares de sih/figuras_sih.py, com dados sintéticos."""

import json
from datetime import date

from sih import figuras_sih as fc


def test_extracao_sih_le_as_datas_de_download(tmp_path):
    caminho = tmp_path / "proveniencia_sih.json"
    arquivos = [
        {"arquivo": "RDPA2501.parquet", "baixado_em": "2026-09-02T10:00:00-03:00"},
        {"arquivo": "RDPA2604.parquet", "baixado_em": "2026-09-20T08:00:00-03:00"},
    ]
    caminho.write_text(json.dumps({"arquivos": arquivos}), encoding="utf-8")
    assert fc.extracao_sih(caminho) == (date(2026, 9, 2), date(2026, 9, 20), True)


def test_extracao_sih_no_formato_antigo_nao_tem_data(tmp_path):
    """Formato anterior: só arquivo e sha256 por arquivo."""
    caminho = tmp_path / "proveniencia_sih.json"
    caminho.write_text(json.dumps({"arquivos": [{"arquivo": "a", "sha256": "x"}]}))
    assert fc.extracao_sih(caminho) is None
    assert fc.extracao_sih(tmp_path / "ausente.json") is None
