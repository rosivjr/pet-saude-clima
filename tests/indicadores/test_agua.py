"""Testes de conformidade com a Portaria GM/MS nº 888/2021 e séries de água."""

import pandas as pd

from src import config
from src.indicadores import (
    avaliar_conformidade_agua,
    avaliar_microbiologico,
    serie_anual_agua,
    serie_mensal,
)
from tests.indicadores.sinteticos import amostra_agua


class TestConformidadeCloro:
    """Limite mínimo de cloro residual livre (0,2 mg/L)."""

    def test_todas_abaixo_do_limite(self):
        df = amostra_agua("Cloro residual livre (mg/L)", [0.0, 0.0, 0.0, 0.0])
        resultado = avaliar_conformidade_agua(df)[0]

        assert resultado.fora_do_padrao == 4
        assert resultado.total_amostras == 4
        assert resultado.percentual_fora == 100.0

    def test_todas_dentro_do_limite(self):
        df = amostra_agua("Cloro residual livre (mg/L)", [0.5, 0.8, 1.0])
        resultado = avaliar_conformidade_agua(df)[0]

        assert resultado.fora_do_padrao == 0
        assert resultado.percentual_fora == 0.0

    def test_valor_exatamente_no_limite_e_conforme(self):
        df = amostra_agua("Cloro residual livre (mg/L)", [0.2])
        assert avaliar_conformidade_agua(df)[0].fora_do_padrao == 0

    def test_amostras_sem_valor_saem_do_denominador(self):
        df = amostra_agua("Cloro residual livre (mg/L)", [0.0, None, 0.0])
        resultado = avaliar_conformidade_agua(df)[0]

        assert resultado.total_amostras == 2, "NaN entrou no denominador"
        assert resultado.fora_do_padrao == 2

    def test_ic_contem_o_percentual(self):
        df = amostra_agua("Cloro residual livre (mg/L)", [0.0, 0.5, 0.0, 0.5])
        r = avaliar_conformidade_agua(df)[0]
        assert r.ic_inferior <= r.percentual_fora <= r.ic_superior


class TestConformidadePH:
    def test_detecta_ph_baixo_e_alto(self):
        df = amostra_agua("pH", [5.0, 7.0, 10.0])
        resultado = avaliar_conformidade_agua(df)[0]

        assert resultado.fora_do_padrao == 2
        assert resultado.total_amostras == 3


class TestMicrobiologico:
    def test_calcula_percentual_de_presenca(self):
        df = pd.DataFrame(
            {
                "PARAMETRO": ["Escherichia coli"] * 4,
                "resultado_texto": ["PRESENTE", "AUSENTE", "PRESENTE", "AUSENTE"],
            }
        )
        resultado = avaliar_microbiologico(df)

        assert resultado.loc[0, "presentes"] == 2
        assert resultado.loc[0, "total"] == 4
        assert resultado.loc[0, "percentual_presenca"] == 50.0
        assert resultado.loc[0, "ic_inferior"] < 50 < resultado.loc[0, "ic_superior"]


class TestSerieAnualAgua:
    def test_percentual_por_ano(self):
        df = pd.DataFrame(
            {
                "PARAMETRO": ["Escherichia coli"] * 4,
                "resultado_texto": ["PRESENTE", "AUSENTE", "AUSENTE", "AUSENTE"],
                "resultado_numerico": [None] * 4,
                "ano": [2023, 2023, 2024, 2024],
            }
        )
        serie = serie_anual_agua(df).set_index("ano")
        assert serie.loc[2023, "percentual"] == 50.0
        assert serie.loc[2024, "percentual"] == 0.0


class TestSerieMensalAgua:
    def test_media_e_mediana_por_mes(self):
        """Mar: 0,1 0,3 0,5 → média 0,3, mediana 0,3. Abr: 1,0 2,0 → 1,5 e 1,5.

        O NaN e o pH ficam de fora.
        """
        df = pd.DataFrame(
            {
                "PARAMETRO": [config.PARAMETRO_CLORO] * 6 + ["pH"],
                "resultado_numerico": [0.1, 0.3, 0.5, 1.0, 2.0, None, 7.0],
                "ano": [2024] * 7,
                "mes": [3, 3, 3, 4, 4, 4, 3],
            }
        )
        serie = serie_mensal(df, config.PARAMETRO_CLORO)
        assert list(serie["mes"]) == [3, 4]
        assert list(serie["amostras"]) == [3, 2]
        assert list(serie["media"]) == [0.3, 1.5]
        assert list(serie["mediana"]) == [0.3, 1.5]

    def test_sem_dados_volta_vazio(self):
        df = pd.DataFrame({"PARAMETRO": ["pH"], "resultado_numerico": [7.0]})
        assert serie_mensal(df, config.PARAMETRO_CLORO).empty
