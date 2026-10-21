"""Testes de pessoa-tempo, meses comuns e IC de Wilson (src/indicadores/_comum.py)."""

from datetime import date

import pandas as pd
import pytest

from src import config
from src.indicadores import (
    meses_comuns,
    pessoa_ano_anos,
    pessoa_ano_periodo,
    ultimo_ano_completo,
)
from src.indicadores._comum import _adicionar_wilson


class TestMesesComuns:
    def test_ano_parcial_restringe_a_jan_jun(self):
        assert meses_comuns(date(2023, 1, 1), date(2026, 6, 30)) == [1, 2, 3, 4, 5, 6]

    def test_anos_completos_tem_os_doze_meses(self):
        assert meses_comuns(date(2024, 1, 1), date(2025, 12, 31)) == list(range(1, 13))

    def test_inicio_no_meio_do_ano(self):
        assert meses_comuns(date(2024, 3, 1), date(2025, 12, 31)) == list(range(3, 13))


class TestPessoaTempoDoPeriodo:
    """
    População 365.000 em 2023 e 366.000 em 2024 (bissexto); período 01/01/2023 a 31/01/2024.

    2023 inteiro: 365.000 × 365/365 = 365.000. 2024: 366.000 × 31/366 = 31.000.
    """

    @pytest.fixture(autouse=True)
    def _config(self, monkeypatch):
        monkeypatch.setattr(config, "POPULACAO_ANUAL", {2023: 365_000, 2024: 366_000})
        monkeypatch.setattr(config, "PERIODO_INICIO", date(2023, 1, 1))
        monkeypatch.setattr(config, "PERIODO_FIM", date(2024, 1, 31))

    def test_pessoa_ano_periodo(self):
        """365.000 + 31.000 = 396.000."""
        assert pessoa_ano_periodo() == pytest.approx(396_000)

    def test_pessoa_ano_periodo_com_fim_explicito(self):
        """Só 2023: 365.000."""
        assert pessoa_ano_periodo(date(2023, 12, 31)) == pytest.approx(365_000)

    def test_pessoa_ano_anos_ignora_ano_fora_do_periodo(self):
        """2025 não está no período e não entra."""
        assert pessoa_ano_anos([2024, 2025]) == {2024: pytest.approx(31_000)}

    def test_ultimo_ano_completo_com_fim_em_janeiro(self):
        """Fim em 31/01/2024: o último ano inteiro é 2023."""
        assert ultimo_ano_completo() == 2023

    def test_ultimo_ano_completo_com_fim_em_dezembro(self, monkeypatch):
        """Fim em 31/12/2024: o próprio 2024 é completo."""
        monkeypatch.setattr(config, "PERIODO_FIM", date(2024, 12, 31))
        assert ultimo_ano_completo() == 2024


class TestAdicionarWilson:
    def test_tabela_vazia_ganha_colunas_de_ic(self):
        resultado = _adicionar_wilson(pd.DataFrame(columns=["s", "n"]), "s", "n")
        assert resultado.empty
        assert {"ic_inferior", "ic_superior"} <= set(resultado.columns)
