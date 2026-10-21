"""Testes de mortalidade por grupo, ano e faixa etária."""

from datetime import date

import pandas as pd
import pytest

from src import config
from src.indicadores import (
    mortalidade_por_faixa,
    mortalidade_por_grupo,
    serie_anual_mortalidade,
)


class TestMortalidade:
    def test_denominador_so_dos_anos_carregados(self, monkeypatch):
        """2024 e 2025 no período, só 2024 carregado: 3 óbitos / 100.000 p-a."""
        monkeypatch.setattr(config, "PERIODO_INICIO", date(2024, 1, 1))
        monkeypatch.setattr(config, "PERIODO_FIM", date(2025, 12, 31))
        monkeypatch.setattr(config, "POPULACAO_ANUAL", {2024: 100_000, 2025: 100_000})
        obitos = pd.DataFrame(
            {
                "grupo_agravo": ["Feco-oral", "Feco-oral", "Inseto vetor", None],
                "ano": [2024] * 4,
                "faixa_etaria": ["<1", "1-4", "80+", "80+"],
            }
        )

        por_grupo = mortalidade_por_grupo(obitos, [2024]).set_index("grupo")
        assert por_grupo.loc["DRSAI (agregado)", "obitos"] == 3
        assert por_grupo.loc["DRSAI (agregado)", "taxa_100mil"] == pytest.approx(3.0)

        serie = serie_anual_mortalidade(obitos, [2024]).iloc[0]
        assert (serie["obitos_total"], serie["obitos_drsai"]) == (4, 3)
        assert serie["proporcao_drsai"] == 75.0
        # Wilson 3/4, z² = 3,8415: centro (0,75 + 3,8415/8) / (1 + 3,8415/4) = 1,2302/1,9604
        # = 0,6275; meia largura 1,96·√(0,1875/4 + 3,8415/64) / 1,9604 = 0,3269;
        # IC = 30,06% a 95,44%.
        assert (serie["proporcao_ic_inferior"], serie["proporcao_ic_superior"]) == (30.06, 95.44)

        faixa = mortalidade_por_faixa(obitos).set_index("faixa_etaria")
        assert faixa["obitos"].sum() == 3

    def test_por_faixa_com_ic_de_wilson(self):
        """3 óbitos DRSAI, 1 por faixa: 33,3% cada, Wilson 1/3 = 6,1% a 79,2%.

        Wilson 1/3: centro (0,3333 + 3,8415/6) / (1 + 3,8415/3) = 0,9736/2,2805
        = 0,4269; meia largura 1,96·√(0,2222/3 + 3,8415/36) / 2,2805 = 0,3661.
        A morte sem grupo DRSAI não entra no denominador.
        """
        obitos = pd.DataFrame(
            {
                "grupo_agravo": ["Feco-oral", "Feco-oral", "Inseto vetor", None],
                "faixa_etaria": ["<1", "1-4", "80+", "80+"],
            }
        )
        faixa = mortalidade_por_faixa(obitos).set_index("faixa_etaria")
        assert list(faixa["percentual"]) == [33.3, 33.3, 33.3]
        assert list(faixa["ic_inferior"]) == [6.1, 6.1, 6.1]
        assert list(faixa["ic_superior"]) == [79.2, 79.2, 79.2]
