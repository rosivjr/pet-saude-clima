"""Nome, proveniência, leitura e recorte do SIH-RD usados pelos scripts de sih/."""

import json
from importlib.metadata import version
from pathlib import Path

import pandas as pd

from src import config, proveniencia

PASTA_BRUTOS = config.DADOS_BRUTOS / "sih"
PROVENIENCIA = PASTA_BRUTOS / "proveniencia_sih.json"


def nome_rd(uf: str, ano: int, mes: int) -> str:
    """Nome do arquivo RD de uma competência no cache do PySUS (ex.: RDPA2501.parquet)."""
    return f"RD{uf}{str(ano)[2:]}{mes:02d}.parquet"


def registro_sih(caminho: Path, consulta: str) -> dict:
    """
    Proveniência de um arquivo RD (proveniencia.registro_download), com o
    caminho no cache do PySUS em cache_pysus, como em sinan/baixar_sinan.py.

    A consulta é a chamada ao PySUS que trouxe o arquivo (ex.:
    'pysus.sih(state=PA, year=2025, month=1)'). O PySUS grava o arquivo no
    cache quando o baixa: a data do arquivo é a do download, e não a desta
    execução. Um Parquet pode vir como pasta; o número de linhas e o SHA-256
    cobrem a pasta inteira.
    """
    registro = proveniencia.registro_download(
        caminho,
        f"DATASUS, SIH/SUS (AIH Reduzida), via PySUS {version('pysus')}",
        f"{config.PYSUS_ENDERECOS[config.PYSUS_SOURCE]}; {consulta}",
        baixado_em=proveniencia.data_do_arquivo(caminho),
    )
    return {**registro, "cache_pysus": str(caminho)}


def arquivos_rdpa() -> list[str]:
    """
    Arquivos RD do Pará listados em proveniencia_sih.json, em ordem alfabética.

    O caminho está em cache_pysus; no JSON gravado antes de 21/10/2026, em arquivo.
    """
    registros = json.loads(PROVENIENCIA.read_text())["arquivos"]
    arquivos = [r.get("cache_pysus", r["arquivo"]) for r in registros]
    return sorted(a for a in arquivos if Path(a).name.startswith("RDPA"))


def ler_rd(arquivo, colunas: list[str]) -> pd.DataFrame:
    """
    Colunas de um arquivo RD, sem espaços nas pontas, com a data da internação.

    Acrescenta data_internacao (de DT_INTER; data inválida vira NaT), ano,
    mes e cid3, os 3 primeiros caracteres de DIAG_PRINC (decisões 0003 e
    0004). As colunas pedidas precisam incluir DT_INTER e DIAG_PRINC.
    """
    df = pd.read_parquet(arquivo, columns=colunas)
    for coluna in colunas:
        df[coluna] = df[coluna].astype(str).str.strip()
    df["data_internacao"] = pd.to_datetime(df["DT_INTER"], format="%Y%m%d", errors="coerce")
    df["ano"] = df["data_internacao"].dt.year
    df["mes"] = df["data_internacao"].dt.month
    df["cid3"] = df["DIAG_PRINC"].str[:3]
    return df


def filtrar_anos_dda(df: pd.DataFrame) -> pd.DataFrame:
    """Internações com data em config.DDA_ANOS."""
    return df[df["ano"].isin(config.DDA_ANOS)]


def rotulo_meses(meses: range, abreviado: bool = False) -> str:
    """'Janeiro a abril' para range(1, 5); abreviado, 'Jan.–abr.'."""
    if abreviado:
        primeiro, ultimo = config.MESES_ABREV[meses[0]], config.MESES_ABREV[meses[-1]]
        return f"{primeiro.capitalize()}.–{ultimo}."
    primeiro, ultimo = config.MESES_NOME[meses[0]], config.MESES_NOME[meses[-1]]
    return f"{primeiro.capitalize()} a {ultimo}"
