"""Caminhos e leitura do Sivep-DDA usados pelos scripts de dda/."""

import zipfile

import pandas as pd

from src import config, proveniencia

BRUTOS = config.DADOS_BRUTOS
DICIONARIO = config.DADOS_INTERMEDIARIOS / "dda_metadata"
PROCESSADOS = config.DADOS_PROCESSADOS
FIGURAS = config.FIGURAS
ZIP_DICIONARIO = BRUTOS / "sivep_dda_metadata_csv.zip"


def ler_ano(ano: int) -> pd.DataFrame:
    """
    Parquet do Sivep-DDA de um ano, só com as semanas desse ano epidemiológico.

    Lê só as colunas de config.DDA_COLUNAS e filtra o ano durante a leitura,
    para o arquivo nacional não ficar inteiro na memória.
    """
    return pd.read_parquet(
        BRUTOS / f"sivep_dda_{ano}.parquet",
        columns=config.DDA_COLUNAS,
        filters=[("sem_epid_year", "==", ano)],
    )


def extracao_dda() -> proveniencia.Extracao | None:
    """
    Data dos parquets do Sivep-DDA de config.DDA_ANOS, para o rodapé das figuras.

    Usa a data do arquivo, marcada como tal (decisão 0017): os JSONs de
    proveniência gravados antes de baixar_dda.py registrar o download guardam
    a data da inspeção, não a do download.
    """
    for ano in config.DDA_ANOS:
        proveniencia.registrar_arquivo("Sivep-DDA", BRUTOS / f"sivep_dda_{ano}.parquet")
    return proveniencia.datas_de_extracao("Sivep-DDA")


def extrair_dicionario() -> list[str]:
    """
    Extrai o dicionário de colunas do zip baixado para data/interim.

    O zip e a proveniência dele ficam em data/raw, que nunca muda; o que é
    derivado do zip vai para data/interim.
    """
    DICIONARIO.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP_DICIONARIO) as z:
        z.extractall(DICIONARIO)
        return z.namelist()
