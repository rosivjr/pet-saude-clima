"""
Testes da avaliação de qualidade dos dados.
"""

import pandas as pd
import pytest

from src import config, qualidade


@pytest.mark.parametrize(
    "percentual, esperado",
    [
        (0.0, "excelente"),
        (4.9, "excelente"),
        (5.0, "bom"),
        (9.9, "bom"),
        (10.0, "regular"),
        (19.9, "regular"),
        (20.0, "ruim"),
        (49.9, "ruim"),
        (50.0, "muito ruim"),
        (100.0, "muito ruim"),
    ],
)
def test_escala_romero_cunha(percentual, esperado):
    assert qualidade.classificar_incompletude(percentual) == esperado


def _sinan(**colunas):
    base = {
        "agravo": ["Leptospirose"] * 4,
        "CS_SEXO": ["M", "F", "I", ""],
        "idade_anos": [30.0, None, 5.0, 40.0],
        "DT_SIN_PRI": pd.to_datetime(["2024-01-01"] * 4),
        "DT_NOTIFIC": pd.to_datetime(["2024-01-05"] * 4),
        "CLASSI_FIN": ["1", "2", None, "1"],
        "EVOLUCAO": ["1", "9", "1", "1"],
        "NU_IDADE_N": ["4030", "4030", "4005", "4040"],
    }
    base.update(colunas)
    return pd.DataFrame(base)


def test_ignorado_conta_como_incompleto():
    """Sexo 'I' e em branco: 2 de 4 incompletos = 50%, muito ruim."""
    tabela = qualidade.completitude(pd.DataFrame(), _sinan(), pd.DataFrame(), pd.DataFrame())
    sexo = tabela[(tabela["base"] == "SINAN") & (tabela["campo"] == "Sexo")].iloc[0]
    assert (sexo["incompletos"], sexo["incompletude"], sexo["classificacao"]) == (
        2,
        50.0,
        "muito ruim",
    )
    evolucao = tabela[tabela["campo"] == "Evolução"].iloc[0]
    assert evolucao["incompletos"] == 1, "EVOLUCAO 9 deveria contar como ignorado"


def test_classificacao_final_exclui_animais_peconhentos():
    sinan = _sinan(
        agravo=["Leptospirose", "Leptospirose", "Leptospirose", config.SINAN_SEM_CLASSI_FIN[0]]
    )
    tabela = qualidade.completitude(pd.DataFrame(), sinan, pd.DataFrame(), pd.DataFrame())
    classi = tabela[tabela["campo"] == "Classificação final*"].iloc[0]
    assert (classi["registros"], classi["incompletos"]) == (3, 1)


def test_consistencia_e_duplicidade():
    sih = pd.DataFrame(
        {
            "DT_INTER": pd.to_datetime(["2024-01-10", "2024-01-10"]),
            "DT_SAIDA": pd.to_datetime(["2024-01-05", "2024-01-12"]),
            "DIAS_PERM": [2, -1],
            "idade_anos": [30.0, 115.0],
            "N_AIH": [1, 1],
        }
    )
    sinan = _sinan(DT_SIN_PRI=pd.to_datetime(["2024-01-10"] + ["2024-01-01"] * 3))
    sinan = pd.concat([sinan, sinan.iloc[[3]]], ignore_index=True)

    cons = qualidade.consistencia(sih, sinan, pd.DataFrame()).set_index("regra")
    assert cons.loc["Data de saída anterior à internação", "inconsistentes"] == 1
    assert cons.loc["Dias de permanência negativos", "inconsistentes"] == 1
    assert cons.loc["Idade acima de 110 anos", "inconsistentes"] == 1
    assert cons.loc["Primeiros sintomas depois da notificação", "inconsistentes"] == 1

    dup = qualidade.duplicidade(sih, sinan).set_index("base")
    assert dup.loc["SIH", "repetidos"] == 1
    assert dup.loc["SINAN", "repetidos"] == 1
