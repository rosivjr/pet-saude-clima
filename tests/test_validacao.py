"""
Testes da validação estrutural com pandera.
"""

import pandas as pd
import pandera.errors
import pytest

from src import config
from src.validacao import validar


def _sih(**colunas):
    base = {
        "DT_INTER": pd.to_datetime(["2024-01-10", "2024-02-10"]),
        "MUNIC_RES": [config.MUNICIPIO_IBGE_6_STR] * 2,
        "IDENT": ["1", "1"],
        "DIAG_PRINC": ["A090", "A900"],
        "MORTE": [0, 1],
        "DIAS_PERM": [3.0, 5.0],
        "idade_anos": [0.0, 45.0],
        "ano": [2024, 2024],
    }
    base.update(colunas)
    return pd.DataFrame(base)


def test_sih_valido_passa():
    assert len(validar("SIH", _sih())) == 2


def test_idade_impossivel_para_a_execucao():
    """Idade 150 indica erro na decodificação: a execução deve parar."""
    with pytest.raises(pandera.errors.SchemaErrors):
        validar("SIH", _sih(idade_anos=[0.0, 150.0]))


def test_outro_municipio_para_a_execucao():
    with pytest.raises(pandera.errors.SchemaErrors):
        validar("SIH", _sih(MUNIC_RES=[config.MUNICIPIO_IBGE_6_STR, "150420"]))


def test_coluna_ausente_para_a_execucao():
    with pytest.raises(pandera.errors.SchemaErrors):
        validar("SIH", _sih().drop(columns="MORTE"))


def test_data_nao_convertida_para_a_execucao():
    with pytest.raises(pandera.errors.SchemaErrors):
        validar("SIH", _sih(DT_INTER=["20240110", "20240210"]))


def test_tabela_vazia_nao_e_validada():
    assert validar("SIM", pd.DataFrame()).empty


def _cnes(**colunas):
    base = {
        "CNES": ["2615746", "2615747"],
        "CODUFMUN": [config.MUNICIPIO_IBGE_6_STR] * 2,
        "VINC_SUS": [True, False],
        "competencia_ano": [2024, 2024],
        "QTLEITP1": ["10", None],
        "QTLEITP2": ["0", None],
        "QTLEITP3": ["0", None],
    }
    base.update(colunas)
    return pd.DataFrame(base)


def test_cnes_valido_passa():
    assert len(validar("CNES", _cnes())) == 2


def test_cnes_sem_coluna_de_leitos_para_a_execucao():
    """rede.py soma QTLEITP1 a 3 sem conferir se existem."""
    with pytest.raises(pandera.errors.SchemaErrors):
        validar("CNES", _cnes().drop(columns="QTLEITP2"))
