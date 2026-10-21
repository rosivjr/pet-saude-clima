"""
Validação das tabelas padronizadas com pandera.

Para a execução quando uma base chega com estrutura diferente da esperada
(coluna ausente, tipo errado, valor impossível), em vez de produzir
números errados sem aviso.

Dois níveis:
- regras estruturais: se falharem, a execução para (SchemaErrors);
- regras de conteúdo que podem ter exceções legítimas: geram aviso
  (raise_warning=True) e a contagem aparece na seção de qualidade.
"""

import logging

import pandas as pd
import pandera.pandas as pa

from src import config

logger = logging.getLogger(__name__)


def _data() -> pa.Column:
    """Coluna de data já convertida (qualquer resolução), sem vazios."""
    return pa.Column(
        checks=pa.Check(
            pd.api.types.is_datetime64_any_dtype,
            element_wise=False,
            error="coluna de data não convertida",
        ),
        nullable=False,
    )


def _idade() -> pa.Column:
    return pa.Column(float, pa.Check.in_range(0, 130), nullable=True, coerce=True)


def _esquema_sih() -> pa.DataFrameSchema:
    return pa.DataFrameSchema(
        {
            "DT_INTER": _data(),
            "MUNIC_RES": pa.Column(
                str,
                pa.Check(lambda s: s.str.strip() == config.MUNICIPIO_IBGE_6_STR),
                coerce=True,
            ),
            "IDENT": pa.Column(str, pa.Check.isin([config.SIH_IDENT_NORMAL]), coerce=True),
            "DIAG_PRINC": pa.Column(str, coerce=True),
            "MORTE": pa.Column(int, pa.Check.isin([0, 1])),
            "DIAS_PERM": pa.Column(
                float, pa.Check.ge(0, raise_warning=True), nullable=True, coerce=True
            ),
            "idade_anos": _idade(),
            "ano": pa.Column(int, pa.Check.isin(config.ANOS), coerce=True),
        },
        name="SIH",
    )


def _esquema_sinan() -> pa.DataFrameSchema:
    return pa.DataFrameSchema(
        {
            "DT_NOTIFIC": _data(),
            "ID_MN_RESI": pa.Column(
                str,
                pa.Check(lambda s: s.str.strip() == config.MUNICIPIO_IBGE_6_STR),
                coerce=True,
            ),
            "grupo_agravo": pa.Column(str, pa.Check.isin(list(config.GRUPOS_AGRAVO))),
            "idade_anos": _idade(),
        },
        name="SINAN",
    )


def _esquema_sim() -> pa.DataFrameSchema:
    return pa.DataFrameSchema(
        {
            "DTOBITO": _data(),
            "CODMUNRES": pa.Column(
                str,
                pa.Check(lambda s: s.str.strip().str[:6] == config.MUNICIPIO_IBGE_6_STR),
                coerce=True,
            ),
            "CAUSABAS": pa.Column(str, coerce=True),
            "idade_anos": _idade(),
        },
        name="SIM",
    )


def _esquema_agua() -> pa.DataFrameSchema:
    return pa.DataFrameSchema(
        {
            "DT_COLETA": _data(),
            "PARAMETRO": pa.Column(str, nullable=False),
            "resultado_numerico": pa.Column(
                float, pa.Check.ge(0, raise_warning=True), nullable=True, coerce=True
            ),
            "resultado_texto": pa.Column(str),
            "NU_SOLUCAO_ABASTECIMENTO": pa.Column(nullable=True),
        },
        name="SISAGUA",
    )


def _esquema_cadastro() -> pa.DataFrameSchema:
    return pa.DataFrameSchema(
        {
            "NU_SOLUCAO_ABASTECIMENTO": pa.Column(str, nullable=False),
            "ano": pa.Column(float, pa.Check.isin([float(a) for a in config.ANOS]), coerce=True),
            "TP_ABASTECIMENTO": pa.Column(
                str, pa.Check.isin(["SAA", "SAC", "SAI"], raise_warning=True), nullable=True
            ),
        },
        name="SISAGUA cadastro",
    )


def _esquema_cnes() -> pa.DataFrameSchema:
    return pa.DataFrameSchema(
        {
            "CNES": pa.Column(str, nullable=False),
            "CODUFMUN": pa.Column(str, pa.Check.eq(config.MUNICIPIO_IBGE_6_STR)),
            "VINC_SUS": pa.Column(bool),
            "competencia_ano": pa.Column(int, pa.Check.isin(config.ANOS), coerce=True),
            # Leitos: só a presença; o valor é convertido com pd.to_numeric em rede.py.
            **{coluna: pa.Column(nullable=True) for coluna in ("QTLEITP1", "QTLEITP2", "QTLEITP3")},
        },
        name="CNES",
    )


ESQUEMAS = {
    "SIH": _esquema_sih,
    "SINAN": _esquema_sinan,
    "SIM": _esquema_sim,
    "SISAGUA": _esquema_agua,
    "SISAGUA cadastro": _esquema_cadastro,
    "CNES": _esquema_cnes,
}


def validar(nome: str, df: pd.DataFrame) -> pd.DataFrame:
    """
    Valida uma tabela padronizada contra o esquema da base.

    Tabela vazia não é validada (a ausência de dados já é tratada e
    registrada pelos carregadores).

    Args:
        nome: chave de ESQUEMAS.
        df: tabela padronizada e filtrada.

    Returns:
        A própria tabela, se passar.

    Raises:
        pandera.errors.SchemaErrors: com todas as falhas estruturais juntas.
    """
    if df.empty:
        return df
    esquema = ESQUEMAS[nome]()
    esquema.validate(df, lazy=True)
    logger.info("%s: validação estrutural aprovada (%d registros)", nome, len(df))
    return df
