"""Testes de notificações do SINAN e cruzamento com as internações."""

import pandas as pd
import pytest

from src import config
from src.indicadores import (
    cruzar_notificacoes_internacoes,
    notificacoes_por_ano,
    perfil_notificacoes,
)


def _sinan(linhas: list[tuple[str, str, str, int]]) -> pd.DataFrame:
    """Notificações mínimas: (grupo, agravo, classificação, ano)."""
    return pd.DataFrame(
        {
            "grupo_agravo": [g for g, _, _, _ in linhas],
            "agravo": [a for _, a, _, _ in linhas],
            "classificacao": [c for _, _, c, _ in linhas],
            "ano": [n for _, _, _, n in linhas],
        }
    )


CONF, DESC = config.SINAN_CONFIRMADO, config.SINAN_DESCARTADO
SEM, FICHA = config.SINAN_SEM_CLASSIFICACAO, config.SINAN_FICHA_SEM_CLASSI


class TestPerfilNotificacoes:
    @pytest.mark.usefixtures("periodo_um_ano")
    def test_confirmados_e_maximo_possivel(self):
        """Decisão 0001, 100.000 pessoas-ano (Garwood por 100 mil).

        Chikungunya: 6 notificações = 3 confirmados + 2 descartados + 1 sem
          classificação. Casos = 3 → 3,00 (IC 0,62–8,77); máximo = 3 + 1 = 4
          → 4,00 (IC 1,09–10,24).
        Zika: 1 confirmado → 1,00 (IC 0,03–5,57), com ressalva do código.
        Animal peçonhento: sem CLASSI_FIN, 2 notificações contam como casos
          → 2,00 (IC 0,24–7,22); máximo = 2.
        """
        g_arb, g_cli = "Arboviroses fora do DRSAI", "Contexto climático"
        sinan = _sinan(
            [(g_arb, "Chikungunya", CONF, 2025)] * 3
            + [(g_arb, "Chikungunya", DESC, 2025)] * 2
            + [(g_arb, "Chikungunya", SEM, 2025)]
            + [(g_arb, "Zika", CONF, 2025)]
            + [(g_cli, "Acidente por animal peçonhento", FICHA, 2025)] * 2
        )
        resumo = perfil_notificacoes(sinan).set_index("agravo")

        chik = resumo.loc["Chikungunya"]
        assert (chik["notificacoes"], chik["confirmados"], chik["descartados"]) == (6, 3, 2)
        assert chik["sem_classificacao"] == 1
        assert chik["casos"] == 3
        assert (chik["taxa_100mil"], chik["taxa_ic_inferior"], chik["taxa_ic_superior"]) == (
            3.0,
            0.62,
            8.77,
        )
        assert chik["casos_maximo"] == 4
        assert (chik["taxa_maximo"], chik["maximo_ic_inferior"], chik["maximo_ic_superior"]) == (
            4.0,
            1.09,
            10.24,
        )
        assert not chik["amostra_suficiente"]
        assert not chik["a_conferir"]

        zika = resumo.loc["Zika"]
        assert (zika["casos"], zika["taxa_ic_inferior"], zika["taxa_ic_superior"]) == (
            1,
            0.03,
            5.57,
        )
        assert zika["a_conferir"]

        anim = resumo.loc["Acidente por animal peçonhento"]
        assert not anim["tem_classi_fin"]
        assert (anim["casos"], anim["casos_maximo"], anim["confirmados"]) == (2, 2, 0)
        assert (anim["taxa_100mil"], anim["taxa_ic_inferior"], anim["taxa_ic_superior"]) == (
            2.0,
            0.24,
            7.22,
        )

    def test_vazio_volta_colunas(self):
        resumo = perfil_notificacoes(pd.DataFrame())
        assert resumo.empty
        assert "taxa_100mil" in resumo.columns


class TestNotificacoesPorAno:
    def test_so_contagens_por_ano(self):
        """Chikungunya 2023: 1 confirmado e 1 descartado; 2024: 1 confirmado e 1 sem
        classificação. Esquistossomose 2024: 1 notificação, sem CLASSI_FIN."""
        g_arb, g_agua = "Arboviroses fora do DRSAI", "Contato com água"
        sinan = _sinan(
            [
                (g_arb, "Chikungunya", CONF, 2023),
                (g_arb, "Chikungunya", DESC, 2023),
                (g_arb, "Chikungunya", CONF, 2024),
                (g_arb, "Chikungunya", SEM, 2024),
                (g_agua, "Esquistossomose", FICHA, 2024),
            ]
        )
        tabela = notificacoes_por_ano(sinan).set_index(["agravo", "ano"])
        assert tuple(
            tabela.loc[("Chikungunya", 2023), ["notificacoes", "confirmados", "descartados"]]
        ) == (2, 1, 1)
        assert tuple(tabela.loc[("Chikungunya", 2024), ["confirmados", "sem_classificacao"]]) == (
            1,
            1,
        )
        assert tabela.loc[("Esquistossomose", 2024), "notificacoes"] == 1
        assert not tabela.loc[("Esquistossomose", 2024), "tem_classi_fin"]
        assert "taxa_100mil" not in tabela.columns


class TestCruzarNotificacoesInternacoes:
    def test_casos_ao_lado_das_notificacoes(self):
        """Contato com água: leptospirose confirmada, leptospirose descartada e
        esquistossomose (sem CLASSI_FIN, conta como caso) → 3 notificações, 2 casos."""
        g = "Contato com água"
        sinan = _sinan(
            [
                (g, "Leptospirose", CONF, 2025),
                (g, "Leptospirose", DESC, 2025),
                (g, "Esquistossomose", FICHA, 2025),
            ]
        )
        sih = pd.DataFrame({"grupo_agravo": ["Feco-oral"]})
        contato = next(r for r in cruzar_notificacoes_internacoes(sinan, sih) if r.grupo == g)
        assert (contato.notificacoes, contato.casos) == (3, 2)

    def test_leitura_por_grupo(self):
        """SINAN: 2 contato, 1 feco. SIH: 3 feco, 1 higiene. Ordem por internações."""
        sinan = pd.DataFrame({"grupo_agravo": ["Contato com água"] * 2 + ["Feco-oral"]})
        sih = pd.DataFrame({"grupo_agravo": ["Feco-oral"] * 3 + ["Higiene"]})
        resultado = cruzar_notificacoes_internacoes(sinan, sih)
        assert [(r.grupo, r.notificacoes, r.internacoes, r.leitura) for r in resultado] == [
            ("Feco-oral", 1, 3, "presente nas duas fontes"),
            ("Higiene", 0, 1, "registrado apenas no SIH no período"),
            ("Contato com água", 2, 0, "registrado apenas no SINAN no período"),
        ]

    def test_sinan_vazio(self):
        sih = pd.DataFrame({"grupo_agravo": ["Feco-oral"]})
        resultado = cruzar_notificacoes_internacoes(pd.DataFrame(), sih)
        assert [(r.notificacoes, r.internacoes) for r in resultado] == [(0, 1)]
