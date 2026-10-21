"""
Testes de sih/comum.py (nome, proveniência, leitura e recorte do SIH-RD),
com parquet e JSON sintéticos.
"""

import hashlib
import json
import os
import re

import pandas as pd

from sih import comum
from src import config


def _parquet_sintetico(caminho) -> None:
    """
    4 internações: 2025, 2026, 2024 e uma com data inválida.

    Os campos vêm com espaços nas pontas, como nos arquivos do DATASUS, e há
    uma coluna que não é lida.
    """
    pd.DataFrame(
        {
            "MUNIC_RES": ["150553 ", " 150140", "150553", "150553"],
            "DIAG_PRINC": [" A090", "B159 ", "E86 ", "A01"],
            "DT_INTER": ["20250315", "20260102", "20241231", "2025XX01"],
            "IDENT": ["1", "1", "5", "1"],
            "NAO_USADA": ["a", "b", "c", "d"],
        }
    ).to_parquet(caminho)


def test_ler_rd_limpa_e_cria_data_ano_mes_e_cid3(tmp_path):
    caminho = tmp_path / "RDPA2501.parquet"
    _parquet_sintetico(caminho)

    df = comum.ler_rd(caminho, ["MUNIC_RES", "DIAG_PRINC", "DT_INTER"])

    assert list(df["MUNIC_RES"]) == ["150553", "150140", "150553", "150553"]
    assert list(df["cid3"]) == ["A09", "B15", "E86", "A01"]
    assert list(df["ano"][:3]) == [2025, 2026, 2024]
    assert list(df["mes"][:3]) == [3, 1, 12]
    assert df["data_internacao"].isna().sum() == 1
    assert "NAO_USADA" not in df.columns


def test_filtrar_anos_dda_mantem_so_os_anos_do_relatorio_dda(tmp_path):
    """Das 4 linhas, só 2025 e 2026 estão em DDA_ANOS; a data inválida sai."""
    caminho = tmp_path / "RDPA2501.parquet"
    _parquet_sintetico(caminho)

    df = comum.filtrar_anos_dda(comum.ler_rd(caminho, ["DIAG_PRINC", "DT_INTER"]))

    assert config.DDA_ANOS == (2025, 2026)
    assert list(df["ano"]) == [2025, 2026]


def test_arquivos_rdpa_so_do_para_em_ordem(tmp_path, monkeypatch):
    """Da lista com 3 arquivos, ficam os 2 do Pará, em ordem alfabética."""
    proveniencia = tmp_path / "proveniencia_sih.json"
    lista = [{"arquivo": str(tmp_path / nome)} for nome in ("RDPA2502", "RDAC2501", "RDPA2501")]
    proveniencia.write_text(json.dumps({"arquivos": lista}))
    monkeypatch.setattr(comum, "PROVENIENCIA", proveniencia)

    assert comum.arquivos_rdpa() == [str(tmp_path / "RDPA2501"), str(tmp_path / "RDPA2502")]


def test_arquivos_rdpa_le_cache_pysus_do_json_novo(tmp_path, monkeypatch):
    """JSON novo: arquivo é só o nome, e o caminho vem de cache_pysus."""
    proveniencia = tmp_path / "proveniencia_sih.json"
    lista = [
        {"arquivo": "RDPA2501.parquet", "cache_pysus": str(tmp_path / "RDPA2501.parquet")},
        {"arquivo": "RDAC2501.parquet", "cache_pysus": str(tmp_path / "RDAC2501.parquet")},
    ]
    proveniencia.write_text(json.dumps({"arquivos": lista}))
    monkeypatch.setattr(comum, "PROVENIENCIA", proveniencia)

    assert comum.arquivos_rdpa() == [str(tmp_path / "RDPA2501.parquet")]


def test_nome_rd():
    assert comum.nome_rd("PA", 2025, 1) == "RDPA2501.parquet"


def test_rotulo_meses_por_extenso_e_abreviado():
    assert comum.rotulo_meses(range(1, 5)) == "Janeiro a abril"
    assert comum.rotulo_meses(range(1, 5), abreviado=True) == "Jan.–abr."


DATA_FIXA = 1_758_200_000  # 18/09/2025 09:53:20 em Belém


def test_registro_sih_de_arquivo_parquet(tmp_path):
    """3 linhas; SHA-256 do próprio arquivo; data do arquivo como data do download."""
    arquivo = tmp_path / "RDPA2501.parquet"
    pd.DataFrame({"N_AIH": [1, 2, 3]}).to_parquet(arquivo)
    os.utime(arquivo, (DATA_FIXA, DATA_FIXA))

    registro = comum.registro_sih(arquivo, "pysus.sih(state=PA, year=2025, month=1)")

    assert registro["arquivo"] == "RDPA2501.parquet"
    assert registro["cache_pysus"] == str(arquivo)
    assert registro["linhas"] == 3
    assert registro["sha256"] == hashlib.sha256(arquivo.read_bytes()).hexdigest()
    assert registro["baixado_em"] == "2025-09-18T09:53:20-03:00"
    assert registro["origem"] == (
        f"{config.PYSUS_ENDERECOS[config.PYSUS_SOURCE]}; pysus.sih(state=PA, year=2025, month=1)"
    )
    assert registro["fonte"].startswith("DATASUS, SIH/SUS (AIH Reduzida), via PySUS ")


def test_registro_sih_de_pasta_parquet_soma_as_partes_e_tem_hash(tmp_path):
    """Pasta com partes de 2 e 3 linhas: 5 linhas e um SHA-256 de verdade."""
    pasta = tmp_path / "RDPA2502.parquet"
    pasta.mkdir()
    pd.DataFrame({"N_AIH": [1, 2]}).to_parquet(pasta / "parte-0.parquet")
    pd.DataFrame({"N_AIH": [3, 4, 5]}).to_parquet(pasta / "parte-1.parquet")

    registro = comum.registro_sih(pasta, "pysus.sih(state=PA, year=2025, month=2)")

    assert registro["linhas"] == 5
    assert re.fullmatch(r"[0-9a-f]{64}", registro["sha256"])
