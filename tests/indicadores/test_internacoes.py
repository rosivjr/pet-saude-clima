"""Testes de internações: DRSAI, séries, perfil etário e todas as causas."""

from datetime import date

import pandas as pd
import pytest

from src import config
from src.indicadores import (
    indicador_drsai,
    perfil_etario,
    perfil_etario_feco_oral,
    perfil_por_grupo,
    residentes_fora_do_para,
    serie_anual_internacoes,
    serie_anual_todas_causas,
    serie_mensal_internacoes,
)
from tests.indicadores.sinteticos import internacoes_sinteticas


def _com_faixa(grupos: list[str], faixas: list[str | None]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "grupo_agravo": grupos,
            "faixa_etaria": pd.Categorical(faixas, categories=config.FAIXA_ETARIA_ROTULOS),
        }
    )


class TestIndicadorDrsai:
    @pytest.mark.usefixtures("periodo_um_ano")
    def test_taxa_por_pessoa_ano(self):
        """50 internações DRSAI em 100.000 pessoas-ano = 50 por 100 mil."""
        df = internacoes_sinteticas([("Feco-oral", 2025)] * 50)
        perfil = indicador_drsai(df)
        assert perfil.taxa_100mil == pytest.approx(50.0)
        assert perfil.taxa_ic_inferior < 50 < perfil.taxa_ic_superior

    @pytest.mark.usefixtures("periodo_um_ano")
    def test_exclui_grupos_fora_do_drsai(self):
        df = internacoes_sinteticas(
            [("Feco-oral", 2025), ("Sensibilidade", 2025), ("Contexto climático", 2025)]
        )
        assert indicador_drsai(df).internacoes == 1


class TestPeriodoComoArgumento:
    def test_fim_explicito_nao_usa_config(self, monkeypatch):
        """Config até 30/06/2026, mas fim = 31/12/2025: só 2025 entra.

        Pessoa-tempo = 100.000 (2025 inteiro); 20 internações = 20 por 100 mil.
        """
        monkeypatch.setattr(config, "PERIODO_INICIO", date(2025, 1, 1))
        monkeypatch.setattr(config, "PERIODO_FIM", date(2026, 6, 30))
        monkeypatch.setattr(config, "POPULACAO_ANUAL", {2025: 100_000, 2026: 100_000})

        df = internacoes_sinteticas([("Feco-oral", 2025)] * 20)
        fim = date(2025, 12, 31)

        assert indicador_drsai(df, fim=fim).taxa_100mil == pytest.approx(20.0)
        assert perfil_por_grupo(df, fim=fim)[0].taxa_100mil == pytest.approx(20.0)


class TestSerieAnualInternacoes:
    @pytest.fixture
    def periodo_com_ano_parcial(self, monkeypatch):
        """2025 inteiro e 1º semestre de 2026; populações 100.000 e 365.000."""
        monkeypatch.setattr(config, "PERIODO_INICIO", date(2025, 1, 1))
        monkeypatch.setattr(config, "PERIODO_FIM", date(2026, 6, 30))
        monkeypatch.setattr(config, "POPULACAO_ANUAL", {2025: 100_000, 2026: 365_000})

    @pytest.mark.usefixtures("periodo_com_ano_parcial")
    def test_ano_parcial_anualizado_e_marcado(self):
        """2025 inteiro (100 mil p-a) e 1º semestre de 2026 (181 mil p-a).

        20 internações em cada: taxa 2025 = 20; taxa 2026 = 20/181.000 x 100 mil.
        A taxa anualizada fica como descrição, e 2026 é marcado como parcial.
        """
        df = internacoes_sinteticas([("Feco-oral", 2025)] * 20 + [("Feco-oral", 2026)] * 20)
        serie = serie_anual_internacoes(df)
        agregado = serie[serie["indicador"] == "DRSAI (agregado)"].set_index("ano")

        assert agregado.loc[2025, "taxa"] == pytest.approx(20.0)
        assert agregado.loc[2026, "taxa"] == pytest.approx(round(20 / 181_000 * 1e5, 2))
        assert not agregado.loc[2025, "ano_parcial"]
        assert agregado.loc[2026, "ano_parcial"]
        assert pd.isna(agregado.loc[2025, "razao_taxas"]), "ano de referência sem RT"

    @pytest.mark.usefixtures("periodo_com_ano_parcial")
    def test_razao_de_taxas_nos_meses_comuns(self):
        """Decisão 0008: a comparação usa só jan-jun, presentes nos dois anos.

        2025: 10 internações em março e 10 em setembro; 2026: 20 em março.
        Pessoa-tempo jan-jun: 2025 = 100.000 x 181/365 = 49.589,04;
                              2026 = 365.000 x 181/365 = 181.000.
        Taxa jan-jun: 2025 = 10 / 49.589,04 x 100 mil = 20,17;
                      2026 = 20 / 181.000 x 100 mil = 11,05.
        RT = (20 / 181.000) / (10 / 49.589,04) = 0,55;
        IC = exp(ln 0,548 ± 1,96 x √(1/10 + 1/20)) = 0,26 a 1,17.
        """
        df = pd.concat(
            [
                internacoes_sinteticas([("Feco-oral", 2025)] * 10, mes=3),
                internacoes_sinteticas([("Feco-oral", 2025)] * 10, mes=9),
                internacoes_sinteticas([("Feco-oral", 2026)] * 20, mes=3),
            ]
        )
        serie = serie_anual_internacoes(df)
        agregado = serie[serie["indicador"] == "DRSAI (agregado)"].set_index("ano")

        assert serie.attrs["meses_comuns"] == [1, 2, 3, 4, 5, 6]
        assert agregado.loc[2025, "internacoes"] == 20
        assert agregado.loc[2025, "internacoes_mc"] == 10
        assert agregado.loc[2025, "taxa_mc"] == pytest.approx(20.17)
        assert agregado.loc[2026, "taxa_mc"] == pytest.approx(11.05)
        assert agregado.loc[2026, "razao_taxas"] == pytest.approx(0.55)
        assert agregado.loc[2026, "rt_ic_inferior"] == pytest.approx(0.26)
        assert agregado.loc[2026, "rt_ic_superior"] == pytest.approx(1.17)

    @pytest.mark.usefixtures("periodo_um_ano")
    def test_grupo_pequeno_fica_so_no_agregado(self):
        df = internacoes_sinteticas([("Feco-oral", 2025)] * 12 + [("Higiene", 2025)] * 2)
        indicadores = set(serie_anual_internacoes(df)["indicador"])
        assert "Feco-oral" in indicadores
        assert "Higiene" not in indicadores


class TestTodasCausas:
    def test_taxa_geral_e_proporcao_drsai(self, monkeypatch):
        """2025: 1.000 internações e 10 DRSAI em 100.000 p-a.

        Taxa geral = 1.000 por 100 mil; proporção DRSAI = 1,00%.
        """
        monkeypatch.setattr(config, "PERIODO_INICIO", date(2025, 1, 1))
        monkeypatch.setattr(config, "PERIODO_FIM", date(2025, 12, 31))
        monkeypatch.setattr(config, "POPULACAO_ANUAL", {2025: 100_000})

        todas = pd.DataFrame({"ano": [2025] * 1000, "mes": [3] * 1000})
        internacoes = internacoes_sinteticas(
            [("Feco-oral", 2025)] * 10 + [("Sensibilidade", 2025)] * 5
        )
        linha = serie_anual_todas_causas(todas, internacoes).iloc[0]

        assert linha["taxa"] == pytest.approx(1000.0)
        assert linha["drsai"] == 10
        assert linha["proporcao_drsai"] == pytest.approx(1.0)
        assert linha["prop_ic_inferior"] < 1.0 < linha["prop_ic_superior"]

    def test_razao_de_taxas_nos_meses_comuns(self, monkeypatch):
        """2025: 100 internações em fevereiro e 100 em outubro; 2026: 100 em fevereiro.

        Só jan-jun entra na comparação: 100 em cada ano.
        RT = (100 / 181.000) / (100 / 49.589,04) = 49.589,04 / 181.000 = 0,27.
        """
        monkeypatch.setattr(config, "PERIODO_INICIO", date(2025, 1, 1))
        monkeypatch.setattr(config, "PERIODO_FIM", date(2026, 6, 30))
        monkeypatch.setattr(config, "POPULACAO_ANUAL", {2025: 100_000, 2026: 365_000})

        todas = pd.DataFrame(
            {"ano": [2025] * 200 + [2026] * 100, "mes": [2] * 100 + [10] * 100 + [2] * 100}
        )
        serie = serie_anual_todas_causas(todas, internacoes_sinteticas([])).set_index("ano")

        assert serie.loc[2025, "total"] == 200
        assert serie.loc[2025, "total_mc"] == 100
        assert serie.loc[2026, "ano_parcial"]
        assert serie.loc[2026, "razao_taxas"] == pytest.approx(0.27)


class TestPerfilEtario:
    def test_distribui_drsai_e_conta_sem_idade(self):
        """DRSAI: <1, 1-4 e um sem idade → 1 e 1 (50% cada), 1 excluído.

        A internação de Contexto climático não entra.
        """
        df = _com_faixa(
            ["Feco-oral", "Higiene", "Feco-oral", "Contexto climático"],
            ["<1", "1-4", None, "<1"],
        )
        resumo, excluidos = perfil_etario(df)
        por_faixa = resumo.set_index("faixa_etaria")
        assert excluidos == 1
        assert por_faixa.loc["<1", "internacoes"] == 1
        assert por_faixa.loc["1-4", "internacoes"] == 1
        assert por_faixa.loc["<1", "percentual"] == 50.0
        assert por_faixa.loc["1-4", "percentual"] == 50.0
        assert resumo["internacoes"].sum() == 2

    def test_percentual_com_ic_de_wilson(self):
        """1 em <1 e 3 em 1-4: 25,0% (IC 4,6–69,9) e 75,0% (IC 30,1–95,4).

        Wilson 1/4, z² = 3,8415: centro (0,25 + 3,8415/8) / (1 + 3,8415/4)
        = 0,7302/1,9604 = 0,3725; meia largura 1,96·√(0,1875/4 + 3,8415/64)
        / 1,9604 = 0,3269. 3/4 é o simétrico: 100 − 69,9 e 100 − 4,6.
        Faixa sem internação: Wilson 0/4 = 0,0% a 49,0%
        (centro 0,4802/1,9604 = 0,2449; meia largura 0,2449).
        """
        df = _com_faixa(["Feco-oral"] * 4, ["<1", "1-4", "1-4", "1-4"])
        por_faixa = perfil_etario(df)[0].set_index("faixa_etaria")
        assert tuple(por_faixa.loc["<1", ["percentual", "ic_inferior", "ic_superior"]]) == (
            25.0,
            4.6,
            69.9,
        )
        assert tuple(por_faixa.loc["1-4", ["percentual", "ic_inferior", "ic_superior"]]) == (
            75.0,
            30.1,
            95.4,
        )
        assert tuple(por_faixa.loc["5-9", ["ic_inferior", "ic_superior"]]) == (0.0, 49.0)

    def test_feco_oral_so_conta_o_grupo(self):
        df = _com_faixa(["Feco-oral", "Inseto vetor"], ["<1", "1-4"])
        resumo, excluidos = perfil_etario_feco_oral(df)
        por_faixa = resumo.set_index("faixa_etaria")
        assert excluidos == 0
        assert por_faixa.loc["<1", "percentual"] == 100.0
        assert resumo["internacoes"].sum() == 1

    def test_sem_drsai_volta_vazio(self):
        resumo, excluidos = perfil_etario(_com_faixa(["Contexto climático"], ["<1"]))
        assert resumo.empty
        assert excluidos == 0


class TestSerieMensalInternacoes:
    def _df(self):
        return pd.DataFrame(
            {
                "grupo_agravo": ["Feco-oral", "Feco-oral", "Higiene", "Contexto climático"],
                "ano": [2024, 2024, 2024, 2024],
                "mes": [1, 1, 2, 2],
            }
        )

    def test_conta_drsai_por_mes(self):
        """Jan: 2 feco-oral. Fev: 1 higiene (Contexto climático fora)."""
        serie = serie_mensal_internacoes(self._df())
        assert serie.values.tolist() == [[2024, 1, 2], [2024, 2, 1]]

    def test_aceita_grupos_explicitos(self):
        serie = serie_mensal_internacoes(self._df(), grupos=("Contexto climático",))
        assert serie.values.tolist() == [[2024, 2, 1]]

    def test_sem_internacoes_volta_vazio(self):
        assert serie_mensal_internacoes(self._df(), grupos=("Sensibilidade",)).empty


class TestResidentesForaDoPara:
    def test_percentual_por_ano(self, monkeypatch):
        """3 de 200 = 1,5%; 1 de 8 = 12,5% (arredonda para 12,5)."""
        monkeypatch.setattr(config, "SIH_RESIDENTES_FORA_DO_PARA", {2025: (3, 200), 2026: (1, 8)})
        tabela = residentes_fora_do_para()
        assert list(tabela["ano"]) == [2025, 2026]
        assert list(tabela["percentual"]) == [1.5, 12.5]
        assert list(tabela["fora"]) == [3, 1]

    def test_ic_de_wilson(self, monkeypatch):
        """
        3 de 200, z = 1,96: centro = (0,015 + 3,8416/400) / (1 + 3,8416/200) = 0,02414;
        margem = 1,96 × √(0,015 × 0,985/200 + 3,8416/160.000) / 1,019208 = 0,01903;
        IC 0,51–4,32% → 0,5–4,3. 1 de 8: centro = 0,2467; margem = 0,2242;
        IC 2,24–47,09% → 2,2–47,1.
        """
        monkeypatch.setattr(config, "SIH_RESIDENTES_FORA_DO_PARA", {2025: (3, 200), 2026: (1, 8)})
        tabela = residentes_fora_do_para()
        assert list(tabela["ic_inferior"]) == [0.5, 2.2]
        assert list(tabela["ic_superior"]) == [4.3, 47.1]
