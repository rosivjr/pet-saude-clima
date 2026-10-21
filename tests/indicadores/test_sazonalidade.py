"""Testes de precipitação mensal e sazonalidade comparada."""

from datetime import date

import pandas as pd

from src import config
from src.indicadores import (
    precipitacao_mensal,
    sazonalidade_comparada,
)


class TestPrecipitacao:
    def test_mensal_soma_e_conta_dias(self):
        prec = pd.DataFrame(
            {
                "data": pd.to_datetime(["2025-01-01", "2025-01-02", "2025-02-01"]),
                "precipitacao_mm": [10.0, 5.5, None],
            }
        )
        mensal = precipitacao_mensal(prec).set_index("mes")
        assert mensal.loc[1, "precipitacao_mm"] == 15.5
        assert mensal.loc[2, "dias_com_dado"] == 0
        assert pd.isna(mensal.loc[2, "precipitacao_mm"]), "mês sem dado virou 0 mm"

    def test_mes_sem_internacao_entra_como_zero(self, monkeypatch):
        """Jan/2024 com 10 internações e jan/2025 sem: média 5, não 10."""
        monkeypatch.setattr(config, "PERIODO_INICIO", date(2024, 1, 1))
        monkeypatch.setattr(config, "PERIODO_FIM", date(2025, 12, 31))
        chuva = pd.DataFrame(
            {"ano": [2024, 2025], "mes": [1, 1], "precipitacao_mm": [300.0, 200.0]}
        )
        ecoli = pd.DataFrame({"ano": [2024], "mes": [1], "amostras": [10], "positivos": [2]})
        internacoes = pd.DataFrame({"ano": [2024], "mes": [1], "internacoes": [10]})

        janeiro = sazonalidade_comparada(chuva, ecoli, internacoes).iloc[0]
        assert janeiro["chuva_media_mm"] == 250.0
        assert janeiro["ecoli_percentual"] == 20.0
        assert janeiro["internacoes_media"] == 5.0
