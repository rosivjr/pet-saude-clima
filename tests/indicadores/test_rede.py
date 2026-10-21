"""Testes de rede do CNES, local de internação e capacidade hospitalar."""

import pandas as pd

from src import config
from src.indicadores import (
    PerfilRede,
    capacidade_hospitalar,
    local_de_internacao,
    perfil_rede,
    rede_do_ano,
    serie_rede_por_ano,
)


class TestRedePorAno:
    def test_conta_hospitais_e_leitos_por_competencia(self):
        rede = pd.DataFrame(
            {
                "competencia_ano": [2024, 2024, 2025],
                "VINC_SUS": [True, False, True],
                "TP_UNID": ["05", "05", "05"],
                "URGEMERG": [True, False, True],
                "QTLEITP1": ["100", "50", "110"],
                "QTLEITP2": ["0", "0", "1"],
                "QTLEITP3": ["0", "0", "0"],
            }
        )
        serie = serie_rede_por_ano(rede).set_index("ano")
        assert serie.loc[2024, "estabelecimentos"] == 2
        assert serie.loc[2024, "hospitais_gerais_sus"] == 1
        assert serie.loc[2024, "leitos_hospitais_gerais_sus"] == 100
        assert serie.loc[2025, "leitos_hospitais_gerais_sus"] == 111


class TestLocalDeInternacao:
    def test_leitos_da_competencia_mais_recente(self):
        """O mesmo hospital em 2023 (126 leitos) e 2026 (111): vale 2026."""
        rede = pd.DataFrame(
            {
                "CNES": ["2615746", "2615746"],
                "competencia_ano": [2023, 2026],
                "QTLEITP1": ["126", "111"],
                "QTLEITP2": ["0", "0"],
                "QTLEITP3": ["0", "0"],
            }
        )
        internacoes = pd.DataFrame({"CNES": ["2615746", "2615746", "9999999"]})
        local = local_de_internacao(internacoes, rede)
        assert local["principal_leitos"] == 111
        assert local["dentro"] == 2
        # Wilson 2/3, z² = 3,8415: centro (0,6667 + 3,8415/6) / (1 + 3,8415/3) = 1,3069/2,2805
        # = 0,5731; meia largura 1,96·√(0,2222/3 + 3,8415/36) / 2,2805 = 0,3654;
        # IC = 20,8% a 93,9%. O de 1/3 é o complemento: 6,1% a 79,2%.
        assert local["ic_dentro"] == local["ic_principal"] == (20.8, 93.9)
        assert local["ic_fora"] == (6.1, 79.2)


class TestRede:
    def test_rede_do_ano(self):
        rede = pd.DataFrame({"competencia_ano": [2024, 2025, 2025], "CNES": ["A", "B", "C"]})
        assert list(rede_do_ano(rede)["CNES"]) == ["B", "C"]
        assert list(rede_do_ano(rede, 2024)["CNES"]) == ["A"]
        assert rede_do_ano(pd.DataFrame()).empty

    def test_serie_rede_vazia_volta_colunas(self):
        serie = serie_rede_por_ano(pd.DataFrame())
        assert serie.empty
        assert "leitos_hospitais_gerais_sus" in serie.columns

    def test_perfil_rede(self):
        """2 de 3 com SUS (66,7%; sem SUS 33,3%); entre os SUS, 1 com leito e 1 com urgência."""
        df = pd.DataFrame(
            {
                "VINC_SUS": [True, True, False],
                "tipo_unidade": ["Hospital geral", "Posto de saúde", "Hospital geral"],
                "LEITHOSP": [True, False, True],
                "URGEMERG": [True, False, True],
            }
        )
        assert perfil_rede(df) == PerfilRede(
            total=3,
            vinculados_sus=2,
            por_tipo_sus={"Hospital geral": 1, "Posto de saúde": 1},
            com_leitos=1,
            com_urgencia=1,
            percentual_sus=66.7,
            percentual_sem_sus=33.3,
        )

    def test_perfil_rede_vazio(self):
        assert perfil_rede(pd.DataFrame()) == PerfilRede(0, 0, {}, 0, 0)


class TestCapacidadeHospitalar:
    def _cnes(self):
        return pd.DataFrame(
            {
                "CNES": ["2615746", "0000001", "0000002", "0000003"],
                "VINC_SUS": [True, True, False, True],
                "TP_UNID": ["05", "05", "05", "02"],
                "URGEMERG": [True, False, True, False],
                "QTLEITP1": ["10", "3", "50", "0"],
                "QTLEITP2": ["5", "0", "0", "0"],
                "QTLEITP3": [None, "0", "0", "0"],
            }
        )

    def test_leitos_e_internacoes_por_hospital(self):
        """Hospitais gerais SUS: 2615746 (10+5+0 = 15 leitos, 2 internações)
        e 0000001 (3 leitos, 1 internação). 0000002 sem SUS e 0000003 tipo 02 saem."""
        internacoes = pd.DataFrame({"CNES": ["2615746", " 2615746 ", "0000001", "9999999"]})
        resultado = capacidade_hospitalar(self._cnes(), internacoes)
        assert list(resultado["cnes"]) == ["2615746", "0000001"]
        assert list(resultado["leitos"]) == [15, 3]
        assert list(resultado["internacoes"]) == [2, 1]
        assert list(resultado["urgencia"]) == ["sim", "não"]
        assert list(resultado["nome"]) == [config.CNES_NOMES["2615746"], "Estabelecimento 0000001"]

    def test_sem_hospital_geral_sus(self):
        internacoes = pd.DataFrame({"CNES": ["0000003"]})
        assert capacidade_hospitalar(self._cnes().iloc[2:], internacoes).empty
        assert capacidade_hospitalar(pd.DataFrame(), internacoes).empty
