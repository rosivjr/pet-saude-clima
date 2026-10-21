"""Testes de cadastro das soluções de abastecimento e ligação amostra-cadastro."""

from datetime import date

import pandas as pd
import pytest

from src import config
from src.indicadores import (
    composicao_cadastro_por_ano,
    divergencia_desinfeccao,
    ecoli_por_captacao,
    ligar_cadastro_por_ano,
    perfil_abastecimento,
    resumo_cloro_areas,
)


class TestLigacaoCadastro:
    def _cadastro(self):
        return pd.DataFrame(
            {
                "NU_SOLUCAO_ABASTECIMENTO": ["S1", "S1", "S2"],
                "ano": [2023, 2025, 2025],
                "CAPTACAO_SUBTERRANEA": [True, False, True],
                "CAPTACAO_SUPERFICIAL": [False, True, False],
            }
        )

    def test_usa_ano_da_amostra_ou_anterior(self):
        """S1 muda de subterrânea (2023) para superficial (2025)."""
        amostras = pd.DataFrame(
            {
                "NU_SOLUCAO_ABASTECIMENTO": ["S1", "S1", "S1"],
                "ano": [2023, 2024, 2025],
            }
        )
        ligada = ligar_cadastro_por_ano(amostras, self._cadastro(), ["CAPTACAO_SUBTERRANEA"])
        assert list(ligada["CAPTACAO_SUBTERRANEA"]) == [True, True, False]
        assert ligada.attrs["ligacao"]["mesmo_ano"] == 2
        assert ligada.attrs["ligacao"]["ano_anterior"] == 1

    def test_sem_passado_usa_ano_seguinte_e_sem_cadastro_fica_sem_par(self):
        amostras = pd.DataFrame(
            {
                "NU_SOLUCAO_ABASTECIMENTO": ["S2", "S9"],
                "ano": [2023, 2023],
            }
        )
        ligada = ligar_cadastro_por_ano(amostras, self._cadastro(), ["CAPTACAO_SUBTERRANEA"])
        assert ligada.attrs["ligacao"]["ano_seguinte"] == 1
        assert ligada.attrs["ligacao"]["sem_par"] == 1
        assert ligada.attrs["ligacao"]["solucoes_sem_par"] == 1

    def test_sem_par_conta_amostras_e_mantem_a_ordem(self):
        """S9 não tem cadastro em nenhum ano: as duas amostras ficam sem par, com NaN."""
        amostras = pd.DataFrame(
            {
                "NU_SOLUCAO_ABASTECIMENTO": ["S9", "S1", "S9"],
                "ano": [2024, 2023, 2026],
            }
        )
        ligada = ligar_cadastro_por_ano(amostras, self._cadastro(), ["CAPTACAO_SUBTERRANEA"])
        assert list(ligada["NU_SOLUCAO_ABASTECIMENTO"]) == ["S9", "S1", "S9"]
        assert ligada["CAPTACAO_SUBTERRANEA"].isna().tolist() == [True, False, True]
        assert ligada.attrs["ligacao"]["sem_par"] == 2
        assert ligada.attrs["ligacao"]["solucoes_sem_par"] == 1
        assert "_merge" not in ligada.columns

    def test_solucao_repetida_no_mesmo_ano_interrompe(self):
        """Duas linhas de S1 em 2023: o merge_asof escolheria uma sem avisar."""
        cadastro = pd.concat([self._cadastro(), self._cadastro().iloc[[0]]])
        amostras = pd.DataFrame({"NU_SOLUCAO_ABASTECIMENTO": ["S1"], "ano": [2023]})
        with pytest.raises(ValueError, match="1 linha"):
            ligar_cadastro_por_ano(amostras, cadastro, ["CAPTACAO_SUBTERRANEA"])

    def test_captacao_classifica_origem(self):
        amostras = pd.DataFrame(
            {
                "PARAMETRO": ["Escherichia coli"] * 2,
                "resultado_texto": ["PRESENTE", "AUSENTE"],
                "NU_SOLUCAO_ABASTECIMENTO": ["S1", "S1"],
                "ano": [2023, 2025],
            }
        )
        resumo = ecoli_por_captacao(amostras, self._cadastro()).set_index("origem")
        assert resumo.loc["Subterrânea", "positivos"] == 1
        assert resumo.loc["Superficial", "positivos"] == 0


class TestPerfilAbastecimento:
    def test_usa_so_o_ano_mais_recente(self):
        """S1 existia em 2023 e em 2025; S2 só em 2023 (desativada)."""
        cadastro = pd.DataFrame(
            {
                "NU_SOLUCAO_ABASTECIMENTO": ["S1", "S2", "S1"],
                "ano": [2023, 2023, 2025],
                "TP_ABASTECIMENTO": ["SAC", "SAC", "SAC"],
                "DESINFECCAO": [True, None, True],
                "FILTRACAO": [False, None, True],
                "CAPTACAO_SUBTERRANEA": [True, True, False],
                "NU_VALOR_POPULACAO_ESTIMADA": [100, 50, 120],
            }
        )
        perfil = perfil_abastecimento(cadastro)
        assert perfil.ano_referencia == 2025
        assert perfil.total_solucoes == 1
        assert perfil.declaram_desinfeccao == 1
        assert perfil.captacao_subterranea == 0


class TestCadastroPorAno:
    def _cadastro(self):
        return pd.DataFrame(
            {
                "NU_SOLUCAO_ABASTECIMENTO": ["S1", "S2", "S1", "S1"],
                "ano": [2024, 2024, 2025, 2026],
                "TP_ABASTECIMENTO": ["SAA", "SAC", "SAA", "SAA"],
                "DESINFECCAO": [True, False, True, True],
                "FILTRACAO": [True, False, True, True],
                "CAPTACAO_SUBTERRANEA": [False, True, False, False],
                "NU_VALOR_POPULACAO_ESTIMADA": [100, 50, 110, 120],
            }
        )

    def test_composicao_uma_linha_por_ano(self):
        comp = composicao_cadastro_por_ano(self._cadastro()).set_index("ano")
        assert comp.loc[2024, "solucoes"] == 2
        assert comp.loc[2024, "SAC"] == 1
        assert comp.loc[2026, "populacao_estimada"] == 120

    def test_perfil_usa_ultimo_ano_completo(self, monkeypatch):
        """Período até 30/06/2026: último ano completo é 2025."""
        monkeypatch.setattr(config, "PERIODO_FIM", date(2026, 6, 30))
        assert perfil_abastecimento(self._cadastro()).ano_referencia == 2025

    def test_perfil_aceita_ano_explicito(self):
        assert perfil_abastecimento(self._cadastro(), ano=2024).total_solucoes == 2

    def test_percentual_por_tipo(self):
        """2 SAC e 1 SAA em 3 soluções: 2/3 = 66,7% e 1/3 = 33,3%, sem IC."""
        cadastro = pd.DataFrame(
            {
                "ano": [2025] * 3,
                "TP_ABASTECIMENTO": ["SAC", "SAA", "SAC"],
                "DESINFECCAO": [True] * 3,
                "FILTRACAO": [True] * 3,
                "CAPTACAO_SUBTERRANEA": [False] * 3,
                "NU_VALOR_POPULACAO_ESTIMADA": [10] * 3,
            }
        )
        perfil = perfil_abastecimento(cadastro, ano=2025)
        assert perfil.percentual_por_tipo == {"SAC": 66.7, "SAA": 33.3}


class TestResumoCloroAreas:
    def test_conta_areas_com_todas_amostras_fora(self):
        df = pd.DataFrame(
            {
                "amostras": [20, 15, 5],
                "fora_do_padrao": [20, 10, 5],
                "amostra_suficiente": [True, True, False],
            }
        )
        assert resumo_cloro_areas(df) == {"areas": 3, "suficientes": 2, "todas_fora": 1}


class TestDivergenciaDesinfeccao:
    def _cadastro(self, s1_desinfecta=True):
        return pd.DataFrame(
            {
                "NU_SOLUCAO_ABASTECIMENTO": ["S1", "S2"],
                "ano": [2024, 2024],
                "DESINFECCAO": [s1_desinfecta, False],
            }
        )

    def _qualidade(self):
        return pd.DataFrame(
            {
                "NU_SOLUCAO_ABASTECIMENTO": ["S1", "S1", "S2", "S1"],
                "ano": [2024, 2024, 2024, 2024],
                "PARAMETRO": [
                    config.PARAMETRO_CLORO,
                    config.PARAMETRO_CLORO,
                    config.PARAMETRO_CLORO,
                    "pH",
                ],
                "resultado_numerico": [0.1, 0.5, 0.0, 7.0],
            }
        )

    def test_cloro_baixo_em_quem_declara_desinfeccao(self):
        """S1 declara: 0,1 e 0,5 → 1/2 = 50,0% (IC 9,5–90,5). S2 não declara."""
        resultado = divergencia_desinfeccao(self._cadastro(), self._qualidade())
        assert resultado == {
            "solucoes_declarantes": 1,
            "amostras_avaliadas": 2,
            "fora_do_padrao": 1,
            "percentual_fora": 50.0,
            "ic_inferior": 9.5,
            "ic_superior": 90.5,
            "ligacao": {
                "mesmo_ano": 3,
                "ano_anterior": 0,
                "ano_seguinte": 0,
                "sem_par": 0,
                "solucoes_sem_par": 0,
            },
        }

    def test_nenhuma_solucao_declarante(self):
        resultado = divergencia_desinfeccao(self._cadastro(False), self._qualidade())
        assert resultado == {
            "solucoes_declarantes": 0,
            "amostras_avaliadas": 0,
            "percentual_fora": 0.0,
            "ligacao": {
                "mesmo_ano": 3,
                "ano_anterior": 0,
                "ano_seguinte": 0,
                "sem_par": 0,
                "solucoes_sem_par": 0,
            },
        }

    def test_conta_amostras_de_cloro_sem_cadastro(self):
        """Duas amostras de S9, que não está no cadastro: 2 amostras, 1 solução sem par."""
        qualidade = pd.concat(
            [
                self._qualidade(),
                pd.DataFrame(
                    {
                        "NU_SOLUCAO_ABASTECIMENTO": ["S9", "S9"],
                        "ano": [2024, 2025],
                        "PARAMETRO": [config.PARAMETRO_CLORO, config.PARAMETRO_CLORO],
                        "resultado_numerico": [0.1, 0.3],
                    }
                ),
            ],
            ignore_index=True,
        )
        ligacao = divergencia_desinfeccao(self._cadastro(), qualidade)["ligacao"]
        assert ligacao["mesmo_ano"] == 3
        assert ligacao["sem_par"] == 2
        assert ligacao["solucoes_sem_par"] == 1

    def test_dados_insuficientes(self):
        assert divergencia_desinfeccao(pd.DataFrame(), self._qualidade()) == {}
