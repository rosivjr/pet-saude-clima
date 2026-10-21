"""Testes de plano de amostragem e cobertura do Censo 2022."""

from datetime import date

import pandas as pd

from src import config
from src.indicadores import (
    cobertura_censo,
    conferir_subcategorias,
    cumprimento_plano_amostragem,
    minimo_mensal_amostras,
)


class TestPlanoAmostragem:
    def test_minimo_por_faixa(self, monkeypatch):
        """298.854 hab.: 20 + 298.854/20.000 = 20 + 14,94."""
        monkeypatch.setattr(config, "PLANO_AMOSTRAGEM_ARREDONDAMENTO", "cima")
        assert minimo_mensal_amostras(298_854) == 35
        monkeypatch.setattr(config, "PLANO_AMOSTRAGEM_ARREDONDAMENTO", "baixo")
        assert minimo_mensal_amostras(298_854) == 34

    def test_faixas_pequenas(self):
        assert minimo_mensal_amostras(4_000) == 6
        assert minimo_mensal_amostras(8_000) == 9
        assert minimo_mensal_amostras(30_000) == 12  # 8 + 30.000/7.500

    def test_cumprimento_por_ano(self, monkeypatch):
        """Jan-mar/2025, mínimo 6/mês: jan 6, fev 3, mar sem coleta."""
        monkeypatch.setattr(config, "PERIODO_INICIO", date(2025, 1, 1))
        monkeypatch.setattr(config, "PERIODO_FIM", date(2025, 3, 31))
        monkeypatch.setattr(config, "POPULACAO_ANUAL", {2025: 4_000})
        monkeypatch.setattr(config, "PLANO_AMOSTRAGEM_PARAMETROS", ("Turbidez (uT)",))

        agua = pd.DataFrame(
            {
                "ano": [2025] * 9,
                "mes": [1] * 6 + [2] * 3,
                "PARAMETRO": ["Turbidez (uT)"] * 9,
            }
        )
        linha = cumprimento_plano_amostragem(agua).iloc[0]

        assert linha["minimo_mensal"] == 6
        assert linha["meses_com_coleta"] == 2
        assert linha["meses_minimo_atingido"] == 1
        assert linha["amostras"] == 9
        assert linha["minimo_total"] == 18
        assert linha["percentual_cumprido"] == 50.0
        assert linha["meses_sem_coleta"] == [3]


class TestCoberturaCenso:
    def test_nivel_e_percentual(self):
        tabela = pd.DataFrame(
            {
                "categoria": ["Total", "Coletado", "Coletado - no domicílio", "Queimado"],
                "domicilios": [200, 150, 100, 50],
            }
        )
        resultado = cobertura_censo(tabela)
        assert list(resultado["nivel"]) == [0, 1, 2, 1]
        assert list(resultado["percentual"]) == [100.0, 75.0, 50.0, 25.0]

    def test_subcategoria_sem_hifen(self):
        """Esgotamento real de Parauapebas: 19.623 + 5.219 = 24.842."""
        tabela = pd.DataFrame(
            {
                "categoria": [
                    "Total",
                    "Rede geral, rede pluvial ou fossa ligada à rede",
                    "Rede geral ou pluvial",
                    "Fossa séptica ou fossa filtro ligada à rede",
                    "Vala",
                ],
                "domicilios": [87667, 24842, 19623, 5219, 1366],
            }
        )
        resultado = cobertura_censo(
            tabela, {"Rede geral ou pluvial", "Fossa séptica ou fossa filtro ligada à rede"}
        )
        assert list(resultado["nivel"]) == [0, 1, 2, 2, 1]
        assert conferir_subcategorias(resultado) == []

    def test_soma_que_nao_fecha(self):
        tabela = pd.DataFrame(
            {
                "categoria": ["Total", "Coletado", "Coletado - A", "Coletado - B"],
                "domicilios": [100, 90, 50, 30],
            }
        )
        assert conferir_subcategorias(cobertura_censo(tabela)) == ["Coletado"]


class TestPlanoSensibilidade:
    def test_arredondamento_para_baixo_na_mesma_tabela(self, monkeypatch):
        """298.854 hab.: mínimo 35 (cima) e 34 (baixo); mês com 34 conta só no segundo."""
        monkeypatch.setattr(config, "PERIODO_INICIO", date(2024, 1, 1))
        monkeypatch.setattr(config, "PERIODO_FIM", date(2024, 1, 31))
        monkeypatch.setattr(config, "POPULACAO_ANUAL", {2024: 298_854})
        monkeypatch.setattr(config, "PLANO_AMOSTRAGEM_ARREDONDAMENTO", "cima")
        monkeypatch.setattr(config, "PLANO_AMOSTRAGEM_PARAMETROS", ("Turbidez (uT)",))
        agua = pd.DataFrame(
            {"ano": [2024] * 34, "mes": [1] * 34, "PARAMETRO": ["Turbidez (uT)"] * 34}
        )

        linha = cumprimento_plano_amostragem(agua).iloc[0]
        assert (linha["minimo_mensal"], linha["meses_minimo_atingido"]) == (35, 0)
        assert (linha["minimo_mensal_baixo"], linha["meses_minimo_baixo"]) == (34, 1)
