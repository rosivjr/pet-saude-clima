"""
Testes da leitura do Sivep-DDA (dda/comum.py), com parquet sintético.
"""

import os
from datetime import date

import pandas as pd

from dda import comum
from src import config, proveniencia


def _parquet_sintetico(pasta, ano: int) -> None:
    """3 linhas: duas do ano pedido e uma do ano seguinte, mais uma coluna não usada."""
    dados = {coluna: [1, 2, 3] for coluna in config.DDA_COLUNAS}
    dados["sem_epid_year"] = pd.array([ano, ano, ano + 1], dtype="int32")
    dados["sem_epid_week"] = [52, 1, 1]
    dados["coluna_nao_usada"] = ["a", "b", "c"]
    pd.DataFrame(dados).to_parquet(pasta / f"sivep_dda_{ano}.parquet")


def test_le_so_as_colunas_usadas_e_as_semanas_do_ano(tmp_path, monkeypatch):
    """Das 3 linhas, 2 são de 2025; a coluna não usada não é lida."""
    monkeypatch.setattr(comum, "BRUTOS", tmp_path)
    _parquet_sintetico(tmp_path, 2025)

    df = comum.ler_ano(2025)

    assert list(df.columns) == config.DDA_COLUNAS
    assert len(df) == 2
    assert list(df["sem_epid_year"]) == [2025, 2025]
    assert list(df["sem_epid_week"]) == [52, 1]


def test_extracao_dda_usa_a_data_do_arquivo(tmp_path, monkeypatch):
    """Parquets de 18/09/2025 e 17/04/2026: intervalo marcado como data do arquivo."""
    monkeypatch.setattr(comum, "BRUTOS", tmp_path)
    proveniencia.reiniciar()
    for ano, instante in ((2025, 1_758_200_000), (2026, 1_776_420_000)):
        _parquet_sintetico(tmp_path, ano)
        os.utime(tmp_path / f"sivep_dda_{ano}.parquet", (instante, instante))

    assert comum.extracao_dda() == (date(2025, 9, 18), date(2026, 4, 17), False)
