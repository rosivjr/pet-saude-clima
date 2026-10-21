"""
Testes da proveniência gravada por sinan/baixar_sinan.py, com arquivos sintéticos.
"""

import json

import pandas as pd

from sinan import baixar_sinan
from src import proveniencia


def test_salvar_grava_as_chaves_comuns_e_as_do_sinan(tmp_path, monkeypatch):
    """2 linhas copiadas do 'cache'; baixado_em é a data do arquivo no cache."""
    cache = tmp_path / "cache" / "HEPABR22.parquet"
    cache.parent.mkdir()
    pd.DataFrame({"x": [1, 2]}).to_parquet(cache)
    destino = tmp_path / "raw"
    destino.mkdir()
    monkeypatch.setattr(baixar_sinan, "DESTINO", destino)

    assert baixar_sinan.salvar(cache, 2022)

    registro = json.loads((destino / "HEPABR22_proveniencia.json").read_text())
    assert {"arquivo", "fonte", "origem", "baixado_em", "linhas", "sha256"} <= set(registro)
    assert registro["arquivo"] == "HEPABR22.parquet"
    assert registro["linhas"] == 2
    assert registro["baixado_em"] == proveniencia.data_do_arquivo(cache)
    assert registro["cache_pysus"] == str(cache)
    assert registro["sha256"] == proveniencia.sha256(destino / "HEPABR22.parquet")
    assert "year=2022" in registro["origem"]
