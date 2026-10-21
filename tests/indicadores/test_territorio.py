"""Testes de cloro e E. coli por área e sazonalidade da E. coli."""

import pandas as pd

from src import config
from src.indicadores import (
    conformidade_por_area,
    ecoli_por_area,
    ecoli_por_ponto,
    sazonalidade_ecoli,
)
from tests.indicadores.sinteticos import amostra_agua


def _ecoli(grupos: list[str | None], resultados: list[str], coluna: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "PARAMETRO": ["Escherichia coli"] * len(grupos),
            "resultado_texto": resultados,
            coluna: grupos,
        }
    )


class TestConformidadePorArea:
    def _df(self):
        return pd.DataFrame(
            {
                "PARAMETRO": [config.PARAMETRO_CLORO] * 8 + ["pH"],
                "resultado_numerico": [0.1, 0.3, 0.15, 0.5, 0.1, 0.4, 0.6, 0.0, 5.0],
                "NO_AREA": ["A", "A", "A", "B", "B", "B", "B", None, "A"],
            }
        )

    def test_percentual_e_ic_por_area(self):
        """A: 0,1 e 0,15 < 0,2 → 2/3 = 66,7% (IC 20,8–93,9).

        B: só 0,1 → 1/4 = 25,0% (IC 4,6–69,9). Sem área e pH ficam de fora.
        """
        resumo = conformidade_por_area(self._df())
        assert list(resumo["area"]) == ["A", "B"]
        assert list(resumo["amostras"]) == [3, 4]
        assert list(resumo["fora_do_padrao"]) == [2, 1]
        assert list(resumo["percentual_fora"]) == [66.7, 25.0]
        assert list(resumo["ic_inferior"]) == [20.8, 4.6]
        assert list(resumo["ic_superior"]) == [93.9, 69.9]
        assert list(resumo["amostra_suficiente"]) == [False, False]

    def test_limiar_lido_do_config(self, monkeypatch):
        monkeypatch.setattr(config, "LIMIAR_AMOSTRAS_PROPORCAO", 4)
        resumo = conformidade_por_area(self._df())
        assert list(resumo["amostra_suficiente"]) == [False, True]

    def test_limiar_padrao_de_proporcao(self):
        """Padrão é LIMIAR_AMOSTRAS_PROPORCAO (30): C com 29 não basta, D com 30 basta."""
        df = pd.DataFrame(
            {
                "PARAMETRO": [config.PARAMETRO_CLORO] * 59,
                "resultado_numerico": [0.5] * 59,
                "NO_AREA": ["C"] * 29 + ["D"] * 30,
            }
        )
        resumo = conformidade_por_area(df).set_index("area")
        assert resumo.loc["C", "amostra_suficiente"] == False  # noqa: E712
        assert resumo.loc["D", "amostra_suficiente"] == True  # noqa: E712

    def test_sem_cloro_volta_vazio(self):
        df = amostra_agua("pH", [7.0]).assign(NO_AREA="A")
        assert conformidade_por_area(df).empty


class TestPositividade:
    def test_por_area(self):
        """A: 1/3 = 33,3% (IC 6,1–79,2). B: 2/2 = 100,0% (IC 34,2–100,0)."""
        df = _ecoli(
            ["A", "A", "A", "B", "B", None],
            ["PRESENTE", "AUSENTE", "AUSENTE", "PRESENTE", "PRESENTE", "PRESENTE"],
            "NO_AREA",
        )
        resumo = ecoli_por_area(df)
        assert list(resumo["area"]) == ["B", "A"]
        assert list(resumo["positivos"]) == [2, 1]
        assert list(resumo["percentual_positivo"]) == [100.0, 33.3]
        assert list(resumo["ic_inferior"]) == [34.2, 6.1]
        assert list(resumo["ic_superior"]) == [100.0, 79.2]

    def test_area_sem_ecoli_volta_vazio(self):
        df = _ecoli(["A"], ["PRESENTE"], "NO_AREA").assign(PARAMETRO="Coliformes totais")
        assert ecoli_por_area(df).empty

    def test_por_ponto(self):
        """Torneira: 1/2 = 50,0%. Bebedouro: 0/1 = 0,0%."""
        df = _ecoli(
            ["TORNEIRA", "TORNEIRA", "BEBEDOURO"],
            ["PRESENTE", "AUSENTE", "AUSENTE"],
            "TP_PONTO_COLETA",
        )
        resumo = ecoli_por_ponto(df)
        assert list(resumo["ponto"]) == ["TORNEIRA", "BEBEDOURO"]
        assert list(resumo["percentual_positivo"]) == [50.0, 0.0]


class TestSazonalidadeEcoli:
    def test_positividade_por_mes(self):
        """Jan: 1/2 = 50,0% (IC 9,5–90,5). Fev: 0/1 = 0,0% (IC 0,0–79,3)."""
        df = _ecoli([2024, 2024, 2024], ["PRESENTE", "AUSENTE", "AUSENTE"], "ano").assign(
            mes=[1, 1, 2]
        )
        resumo = sazonalidade_ecoli(df)
        assert list(resumo["mes"]) == [1, 2]
        assert list(resumo["percentual_positivo"]) == [50.0, 0.0]
        assert list(resumo["ic_inferior"]) == [9.5, 0.0]
        assert list(resumo["ic_superior"]) == [90.5, 79.3]

    def test_sem_ecoli_volta_vazio(self):
        assert sazonalidade_ecoli(pd.DataFrame({"PARAMETRO": ["pH"]})).empty
