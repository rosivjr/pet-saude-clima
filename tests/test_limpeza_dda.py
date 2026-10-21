"""Testes da correção do número de unidades do Sivep-DDA (dda/limpeza_dda.py)."""

import pandas as pd

from dda.limpeza_dda import corrigir_unidades


def test_valor_acima_de_100_vezes_a_mediana_vira_a_mediana():
    """Município A: 2, 2, 2, 300 → mediana 2; 300 > 100 × 2 vira 2, e 150 em B não muda."""
    df = pd.DataFrame(
        {
            "municipio_ibge": ["A"] * 4 + ["B"] * 4,
            "nu_unidades_inf": [2, 2, 2, 300, 2, 2, 2, 150],
            "nu_usaude_sem": [3, 3, 3, 3, 3, 3, 3, 3],
        }
    )
    corrigido = corrigir_unidades(df, mostrar=False)
    assert list(corrigido["nu_unidades_inf"]) == [2, 2, 2, 2, 2, 2, 2, 150]
    assert list(df["nu_unidades_inf"])[3] == 300  # o original não muda


def test_limite_menor_corrige_mais():
    """Com limite 50, 150 > 50 × 2 também vira a mediana."""
    df = pd.DataFrame(
        {"municipio_ibge": ["B"] * 4, "nu_unidades_inf": [2, 2, 2, 150], "nu_usaude_sem": [3] * 4}
    )
    assert list(corrigir_unidades(df, limite=50, mostrar=False)["nu_unidades_inf"]) == [2, 2, 2, 2]
