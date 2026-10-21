"""Dados sintéticos usados por mais de um arquivo de teste dos indicadores."""

import pandas as pd


def amostra_agua(parametro: str, valores: list[float]) -> pd.DataFrame:
    """DataFrame mínimo no formato esperado pelos indicadores de água."""
    return pd.DataFrame(
        {
            "PARAMETRO": [parametro] * len(valores),
            "resultado_numerico": valores,
            "resultado_texto": [str(v) for v in valores],
        }
    )


def internacoes_sinteticas(
    grupos_anos: list[tuple[str, int]], morte: int = 0, mes: int = 3
) -> pd.DataFrame:
    """Internações mínimas: uma linha por (grupo, ano), todas no mesmo mês."""
    return pd.DataFrame(
        {
            "grupo_agravo": [g for g, _ in grupos_anos],
            "ano": [a for _, a in grupos_anos],
            "mes": [mes] * len(grupos_anos),
            "MORTE": [morte] * len(grupos_anos),
            "DIAS_PERM": [3] * len(grupos_anos),
        }
    )
