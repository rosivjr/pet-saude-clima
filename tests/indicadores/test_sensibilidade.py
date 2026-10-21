"""Testes de sensibilidade sem o ano parcial."""

from datetime import date

import pandas as pd
import pytest

from src import config
from src.indicadores import (
    sensibilidade_sem_ano_parcial,
)
from tests.indicadores.sinteticos import internacoes_sinteticas


class TestSensibilidade:
    def test_recalcula_sem_ano_parcial_sem_mudar_config(self, monkeypatch):
        """2025 completo (20 internações) e 1º sem. 2026 (10); pop 100.000."""
        monkeypatch.setattr(config, "PERIODO_INICIO", date(2025, 1, 1))
        monkeypatch.setattr(config, "PERIODO_FIM", date(2026, 6, 30))
        monkeypatch.setattr(config, "POPULACAO_ANUAL", {2025: 100_000, 2026: 100_000})

        internacoes = internacoes_sinteticas(
            [("Feco-oral", 2025)] * 20 + [("Feco-oral", 2026)] * 10
        )
        internacoes["DT_INTER"] = pd.to_datetime(["2025-03-01"] * 20 + ["2026-03-01"] * 10)
        agua = pd.DataFrame(
            {
                "PARAMETRO": ["Escherichia coli"] * 2,
                "resultado_texto": ["PRESENTE", "AUSENTE"],
                "resultado_numerico": [None, None],
                "DT_COLETA": pd.to_datetime(["2025-05-01", "2026-05-01"]),
            }
        )

        sens = sensibilidade_sem_ano_parcial(internacoes, agua).set_index("indicador")

        pa_principal = 100_000 + 100_000 * 181 / 365
        assert sens.loc["Taxa de internação DRSAI", "principal"] == pytest.approx(
            round(30 / pa_principal * 1e5, 2)
        )
        assert sens.loc["Taxa de internação DRSAI", "sensibilidade"] == pytest.approx(20.0)
        assert sens.loc["Escherichia coli presente", "sensibilidade"] == 100.0
        # SIM300 confunde o atributo em maiúsculas com uma constante literal.
        assert config.PERIODO_FIM == date(2026, 6, 30), "config não pode mudar"  # noqa: SIM300
