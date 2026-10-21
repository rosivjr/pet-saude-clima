"""
Testes da camada de relatório.

Cada seção recebe resultados sintéticos e a saída é comparada, caractere
por caractere, com o texto esperado escrito no próprio teste. Os números
dos resultados são casos conferidos à mão (ver tests/indicadores/):
3 casos em 100.000 pessoas-ano → 3,00 (IC 0,62–8,77); 1/3 → 33,3%
(IC 6,1–79,2); 2/3 → 66,7% (IC 20,8–93,9); 1/4 → 25,0% (IC 4,6–69,9).
"""

from datetime import date

import pandas as pd

from src import config
from src.indicadores import CruzamentoFontes, PerfilAgravo, PerfilRede, ResultadoConformidade
from src.relatorio import (
    cabecalho,
    milhar,
    numero,
    rodape,
    rodape_figura,
    secao_cobertura_fontes,
    secao_conformidade,
    secao_drsai,
    secao_lacunas,
    secao_mortalidade,
    secao_notificacoes,
    secao_proveniencia,
    secao_rede,
    secao_serie_anual_internacoes,
)

LINHA = "=" * 78


def test_numero_com_virgula_decimal():
    assert numero(0.2) == "0,2"
    assert numero(5.0) == "5,0"
    assert numero(2.456, 2) == "2,46"


def test_milhar_com_ponto():
    assert milhar(999) == "999"
    assert milhar(13015) == "13.015"
    assert milhar(1234567) == "1.234.567"


def test_secao_conformidade():
    resultados = [
        ResultadoConformidade(
            "Cloro residual livre (mg/L)", 0.2, None, "mg/L", 3, 2, 66.7, 20.8, 93.9
        ),
        ResultadoConformidade("Turbidez (uT)", None, 5.0, "uT", 5, 0, 0.0, 0.0, 43.4),
        ResultadoConformidade("pH", 6.0, 9.5, "", 4, 1, 25.0, 4.6, 69.9),
    ]
    esperado = (
        f"\n{LINHA}\n"
        "8. QUALIDADE DA ÁGUA — PARÂMETROS FÍSICO-QUÍMICOS\n"
        f"{LINHA}\n"
        "Critério: Portaria GM/MS nº 888, de 04/05/2021\n"
        "\n"
        "  Cloro residual livre (mg/L)\n"
        "    Limite legal .......... mínimo 0,2 mg/L\n"
        "    Amostras .............. 3\n"
        "    Fora do padrão ........ 2 (66,7%, IC95% 20,8–93,9)\n"
        "\n"
        "  Turbidez (uT)\n"
        "    Limite legal .......... máximo 5,0 uT\n"
        "    Amostras .............. 5\n"
        "    Fora do padrão ........ 0 (0,0%, IC95% 0,0–43,4)\n"
        "\n"
        "  pH\n"
        "    Limite legal .......... entre 6,0 e 9,5\n"
        "    Amostras .............. 4\n"
        "    Fora do padrão ........ 1 (25,0%, IC95% 4,6–69,9)\n"
    )
    assert secao_conformidade(resultados) == esperado


def test_secao_drsai():
    indicador = PerfilAgravo(
        grupo="DRSAI",
        internacoes=3,
        taxa_100mil=3.0,
        obitos=1,
        letalidade=33.3,
        permanencia_media=4.5,
        amostra_suficiente=False,
        taxa_ic_inferior=0.62,
        taxa_ic_superior=8.77,
        letalidade_ic_inferior=6.1,
        letalidade_ic_superior=79.2,
    )
    esperado = (
        f"\n{LINHA}\n"
        "1. INTERNAÇÕES POR DRSAI — INDICADOR AGREGADO\n"
        f"{LINHA}\n"
        "Doenças Relacionadas ao Saneamento Ambiental Inadequado\n"
        "Classificação FUNASA (2010); indicador 33 dos Indicadores de\n"
        "Desenvolvimento Sustentável do IBGE (IDS Brasil 2015).\n"
        "\n"
        "  Internações ............. 3\n"
        "  Taxa/100 mil pessoas-ano  3,00 (IC95% 0,62–8,77)\n"
        "  Óbitos .................. 1\n"
        "  Letalidade .............. 33,3% (IC95% 6,1–79,2)\n"
        "  Permanência média ....... 4,5 dias\n"
    )
    assert secao_drsai(indicador) == esperado


def _serie_anual() -> pd.DataFrame:
    """Valores de TestSerieAnualInternacoes.test_razao_de_taxas_nos_meses_comuns.

    2025: 20 internações em 100.000 p-a (20,00), 10 delas em jan-jun
    (49.589 p-a, 20,17). 2026: 20 em 181.000 p-a (11,05), todas em jan-jun.
    RT jan-jun = 0,55 (IC 0,26–1,17). Os IC das taxas são de Garwood:
    n=20 → χ²(0,025; 40)/2 = 12,22 e χ²(0,975; 42)/2 = 30,89 casos.
    """
    serie = pd.DataFrame(
        {
            "indicador": ["DRSAI (agregado)"] * 2,
            "ano": [2025, 2026],
            "ano_parcial": [False, True],
            "internacoes": [20, 20],
            "pessoa_ano": [100_000, 181_000],
            "taxa": [20.0, 11.05],
            "taxa_ic_inferior": [12.22, 6.75],
            "taxa_ic_superior": [30.89, 17.07],
            "internacoes_mc": [10, 20],
            "pessoa_ano_mc": [49_589, 181_000],
            "taxa_mc": [20.17, 11.05],
            "taxa_mc_ic_inferior": [9.67, 6.75],
            "taxa_mc_ic_superior": [37.09, 17.07],
            "razao_taxas": [None, 0.55],
            "rt_ic_inferior": [None, 0.26],
            "rt_ic_superior": [None, 1.17],
        }
    )
    serie.attrs["meses_comuns"] = [1, 2, 3, 4, 5, 6]
    return serie


def test_secao_serie_anual_separa_descricao_e_comparacao():
    texto = secao_serie_anual_internacoes(_serie_anual())
    esperado_descricao = (
        "  Ano        n      Taxa  IC95%\n"
        "  2025      20     20,00  12,22–30,89\n"
        "  2026*     20     11,05  6,75–17,07\n"
    )
    esperado_comparacao = (
        "  Ano        n      Taxa  IC95%                RT  IC95% RT\n"
        "  2025      10     20,17  9,67–37,09         ref.\n"
        "  2026*     20     11,05  6,75–17,07         0,55  0,26–1,17\n"
    )
    assert "meses comuns a todos os anos (jan–jun)" in texto
    assert esperado_descricao in texto
    assert esperado_comparacao in texto


def test_secao_rede_usa_percentual_calculado():
    perfil = PerfilRede(3, 2, {"Hospital geral": 2}, 1, 1, 66.7, 33.3)
    texto = secao_rede(perfil, {})
    assert "Com vínculo SUS ................ 2 (66,7%)" in texto
    assert "Sem vínculo SUS ................ 1 (33,3%)" in texto


def test_secao_rede_local_de_internacao_com_ic():
    """35 de 40 no município (87,5%) e 5 fora (12,5%); IC de Wilson dado à mão."""
    perfil = PerfilRede(3, 2, {"Hospital geral": 2}, 1, 1, 66.7, 33.3)
    local = {
        "total": 40,
        "dentro": 35,
        "fora": 5,
        "percentual_dentro": 87.5,
        "ic_dentro": (73.9, 94.5),
        "percentual_fora": 12.5,
        "ic_fora": (5.5, 26.1),
        "estabelecimentos_distintos": 4,
        "principal_cnes": "0000001",
        "principal_internacoes": 30,
        "principal_percentual": 75.0,
        "ic_principal": (59.8, 85.8),
        "principal_leitos": 0,
    }
    texto = secao_rede(perfil, local)
    assert "Em estabelecimento do município  35 (87,5%, IC95% 73,9–94,5)" in texto
    assert "Fora do município .............. 5 (12,5%, IC95% 5,5–26,1)" in texto
    assert "30 (75,0% do total, IC95% 59,8–85,8)" in texto


def test_secao_mortalidade_formata_ic_e_marca_poucos_obitos():
    """4 óbitos levam [!] (abaixo de 10); 12 não. IC com vírgula e travessão."""
    por_grupo = pd.DataFrame(
        {
            "grupo": ["Feco-oral", "Inseto vetor"],
            "obitos": [4, 12],
            "taxa_100mil": [0.69, 2.07],
            "taxa_ic_inferior": [0.19, 1.07],
            "taxa_ic_superior": [1.76, 3.62],
        }
    )
    serie = pd.DataFrame(
        {
            "ano": [2024],
            "obitos_total": [1200],
            "obitos_drsai": [8],
            "taxa_drsai": [2.68],
            "taxa_ic_inferior": [1.16],
            "taxa_ic_superior": [5.28],
            "proporcao_drsai": [0.67],
            "proporcao_ic_inferior": [0.34],
            "proporcao_ic_superior": [1.31],
        }
    )
    por_faixa = pd.DataFrame(
        {
            "faixa_etaria": ["30-39"],
            "obitos": [4],
            "percentual": [28.6],
            "ic_inferior": [11.7],
            "ic_superior": [54.6],
        }
    )
    texto = secao_mortalidade(por_grupo, serie, por_faixa, [2023, 2024])

    linhas = texto.splitlines()
    feco = next(linha for linha in linhas if "Feco-oral" in linha)
    vetor = next(linha for linha in linhas if "Inseto vetor" in linha)
    assert feco.endswith("0,69  0,19–1,76  [!]")
    assert vetor.endswith("2,07  1,07–3,62")
    assert "1,16–5,28" in texto
    assert "0,67% (0,34–1,31)" in texto
    assert "28,6%  11,7–54,6%" in texto
    assert "Sem arquivo carregado: 2025, 2026" in texto


def test_secao_mortalidade_sem_anos():
    vazio = pd.DataFrame()
    assert "Nenhum ano do SIM disponível" in secao_mortalidade(vazio, vazio, vazio, [])


def _perfil_sinan() -> pd.DataFrame:
    """Valores de TestPerfilNotificacoes (100.000 pessoas-ano, Garwood)."""
    return pd.DataFrame(
        {
            "grupo_agravo": ["Arboviroses fora do DRSAI"] * 2 + ["Contexto climático"],
            "agravo": ["Chikungunya", "Zika", "Acidente por animal peçonhento"],
            "notificacoes": [6, 1, 2],
            "confirmados": [3, 1, 0],
            "descartados": [2, 0, 0],
            "sem_classificacao": [1, 0, 0],
            "outros_codigos": [0, 0, 0],
            "tem_classi_fin": [True, True, False],
            "casos": [3, 1, 2],
            "taxa_100mil": [3.0, 1.0, 2.0],
            "taxa_ic_inferior": [0.62, 0.03, 0.24],
            "taxa_ic_superior": [8.77, 5.57, 7.22],
            "casos_maximo": [4, 1, 2],
            "taxa_maximo": [4.0, 1.0, 2.0],
            "maximo_ic_inferior": [1.09, 0.03, 0.24],
            "maximo_ic_superior": [10.24, 5.57, 7.22],
            "amostra_suficiente": [False, False, False],
            "a_conferir": [False, True, False],
        }
    )


def _sinan_por_ano() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "grupo_agravo": ["Arboviroses fora do DRSAI"] * 2,
            "agravo": ["Chikungunya"] * 2,
            "ano": [2024, 2025],
            "notificacoes": [4, 2],
            "confirmados": [2, 1],
            "descartados": [1, 1],
            "sem_classificacao": [1, 0],
            "outros_codigos": [0, 0],
            "tem_classi_fin": [True, True],
        }
    )


def test_secao_notificacoes_quatro_contagens_e_maximo():
    texto = secao_notificacoes(_perfil_sinan(), _sinan_por_ano())
    esperado_chik = (
        "  Chikungunya (Arboviroses fora do DRSAI)\n"
        "    Notificados ........... 6\n"
        "    Confirmados ........... 3\n"
        "    Descartados ........... 2\n"
        "    Sem classificação ..... 1\n"
        "    Taxa/100 mil p-a ...... 3,00 (IC95% 0,62–8,77)\n"
        "    [!] menos de 10 casos: estimativa instável\n"
        "    Máximo possível ....... 4 casos, 4,00 (IC95% 1,09–10,24)\n"
    )
    assert esperado_chik in texto
    assert "Ressalva: código de CLASSI_FIN de ficha estadual" in texto
    assert "    Notificados ........... 2 (ficha sem CLASSI_FIN; casos = notificações)\n" in texto
    assert "  Chikungunya                     2024        4      2      1        1" in texto
    assert "Taxa/100 mil p-a ...... 2,00" in texto


def test_secao_cobertura_mostra_casos_e_notificacoes():
    cruz = [CruzamentoFontes("Contato com água", 3, 0, "registrado apenas no SINAN", 2)]
    texto = secao_cobertura_fontes(cruz)
    assert f"  {'Grupo':<28}{'Notificações':>14}{'Casos':>8}{'Internações':>14}" in texto
    assert f"  {'Contato com água':<28}{3:>14}{2:>8}{0:>14}" in texto


def test_rodape_figura_com_periodo_do_estudo_e_criterio():
    esperado = (
        "Fonte: SISAGUA, vigilância da qualidade da água, Parauapebas (PA), "
        "01/01/2023 a 30/06/2026; extraído de 04/09/2026 a 18/09/2026.\n"
        "Critério: Portaria GM/MS nº 888, de 04/05/2021. Unidade: amostra de água."
    )
    texto = rodape_figura(
        "SISAGUA, vigilância da qualidade da água, Parauapebas (PA)",
        (date(2026, 9, 4), date(2026, 9, 18), True),
        criterio="Portaria GM/MS nº 888, de 04/05/2021. Unidade: amostra de água.",
    )
    assert texto == esperado


def test_rodape_figura_com_periodo_proprio_sem_criterio():
    texto = rodape_figura("SINISA, Parauapebas (PA)", None, periodo="ano de referência 2024")
    assert texto == (
        "Fonte: SINISA, Parauapebas (PA), ano de referência 2024; data de extração não registrada."
    )


def test_rodape_figura_com_data_do_arquivo():
    """Sem data de download, a figura avisa que a data é a do arquivo."""
    texto = rodape_figura("Sivep-DDA", (date(2025, 9, 18), date(2025, 9, 18), False))
    assert "; 18/09/2025 (data do arquivo, não da extração)." in texto


def test_cabecalho_lista_todas_as_fontes():
    texto = cabecalho()
    for fonte in ("SIH/SUS", "SINAN", "SIM", "CNES", "SISAGUA", "SINISA", "Censo 2022"):
        assert f"  {fonte} ." in texto
    assert "(Portal de Dados Abertos)" in texto
    assert "Precipitação ...... chuva diária por reanálise (Open-Meteo)" in texto


def test_rodape_declara_microdados_anonimizados_e_agregados():
    assert (
        "  - Microdados públicos anonimizados, mostrados só em agregados; não\n"
        "    substituem a análise oficial da vigilância municipal.\n"
    ) in rodape()


def test_rodape_mede_internacoes_em_outras_ufs():
    """3 de 200 (1,5%) e 1 de 8 (12,5%), com IC, já calculados pelo indicador."""
    fora = pd.DataFrame(
        {
            "ano": [2025, 2026],
            "fora": [3, 1],
            "total": [200, 8],
            "percentual": [1.5, 12.5],
            "ic_inferior": [0.5, 2.2],
            "ic_superior": [4.3, 47.1],
        }
    )
    texto = " ".join(rodape(fora).split())
    assert "hospitais de outras UFs ficam fora" in texto
    assert (
        "3 de 200 em 2025 (1,5%; IC95% 0,5–4,3) e 1 de 8 em 2026 (12,5%; IC95% 2,2–47,1)."
    ) in texto
    assert "outras UFs" not in rodape()


def test_rodape_nao_separa_o_ic_dos_numeros():
    """Com estes valores, a quebra de linha cairia entre "IC95%" e "0,9–1,4"."""
    fora = pd.DataFrame(
        {
            "ano": [2025, 2026],
            "fora": [192, 67],
            "total": [13_207, 5_930],
            "percentual": [1.5, 1.1],
            "ic_inferior": [1.3, 0.9],
            "ic_superior": [1.7, 1.4],
        }
    )
    linhas = rodape(fora).splitlines()
    for parentese in ("(1,5%; IC95% 1,3–1,7)", "(1,1%; IC95% 0,9–1,4)"):
        assert any(parentese in linha for linha in linhas), f"{parentese} quebrado entre linhas"


def _resumo_proveniencia():
    return {
        "inicio": "2026-10-20T10:00:00-03:00",
        "pysus": "1.0",
        "pysus_source": "ftp",
        "arquivos_por_fonte": {"SIH": 2, "SISAGUA": 1, "SINISA": 1},
        "extracao": {
            "SIH": (date(2026, 9, 1), date(2026, 9, 3), True),
            "SISAGUA": (date(2025, 9, 18), date(2025, 9, 18), False),
            "SINISA": None,
        },
        "etapas": [
            {
                "etapa": "SIH: tipo de AIH",
                "tipo": "descarte",
                "motivo": "AIH diferente do tipo 1",
                "antes": 10,
                "depois": 7,
            },
            {
                "etapa": "CNES: município",
                "tipo": "recorte",
                "motivo": "estabelecimento em outro município",
                "antes": 4,
                "depois": 4,
            },
        ],
    }


def test_proveniencia_mostra_caminho_relativo_a_raiz():
    caminho = config.RAIZ / "outputs" / "proveniencia" / "proveniencia_20261020T100000.json"
    texto = secao_proveniencia(_resumo_proveniencia(), caminho)
    assert (
        "  Registro completo ....... outputs/proveniencia/proveniencia_20261020T100000.json\n"
        in texto
    )
    assert str(config.RAIZ) not in texto


def test_proveniencia_data_de_extracao_por_fonte():
    texto = secao_proveniencia(_resumo_proveniencia(), config.RAIZ / "p.json")
    assert f"  {'SIH':<18}extraído de 01/09/2026 a 03/09/2026" in texto
    assert f"  {'SISAGUA':<18}18/09/2025 (data do arquivo, não da extração)" in texto
    assert f"  {'SINISA':<18}data de extração não registrada" in texto


def test_proveniencia_mostra_todas_as_etapas_sem_a_tabela_antiga_de_descartes():
    """10 → 7 remove 3; 4 → 4 é recorte sem remoção e aparece mesmo assim."""
    texto = secao_proveniencia(_resumo_proveniencia(), config.RAIZ / "p.json")
    assert "Registros descartados na limpeza" not in texto
    assert "Todas as etapas de filtro, inclusive as que removeram 0 linhas" in texto
    assert f"  {'SIH: tipo de AIH':<24}{'descarte':<10}{10:>10}{7:>10}{3:>11}" in texto
    assert f"  {'CNES: município':<24}{'recorte':<10}{4:>10}{4:>10}{0:>11}" in texto
    assert "    estabelecimento em outro município" in texto


def test_lacunas_dizem_ate_onde_vai_a_extracao_do_sih(monkeypatch):
    monkeypatch.setattr(config, "SIH_ULTIMA_COMPETENCIA", (2026, 7))
    texto = secao_lacunas([])
    assert "  SIH extraído até a competência 2026-07\n" in texto
    assert "Competências do SIH após o fim do período" not in texto


def test_lacunas_marcam_competencia_do_corte_que_nao_veio(monkeypatch):
    """Fim em 30/06/2026: 2026-07 fica depois do período; 2026-03 entra na lista comum."""
    monkeypatch.setattr(config, "PERIODO_FIM", date(2026, 6, 30))
    monkeypatch.setattr(config, "SIH_ULTIMA_COMPETENCIA", (2026, 7))
    texto = secao_lacunas(
        [
            {"fonte": "SIH", "item": "PA 2026-03 RD", "motivo": "sem arquivo RD"},
            {"fonte": "SIH", "item": "PA 2026-07 RD", "motivo": "sem arquivo RD"},
        ]
    )
    assert f"  {'SIH':<18}{'PA 2026-03 RD':<22}sem arquivo RD" in texto
    assert "  SIH extraído até a competência 2026-07 (indisponíveis: 2026-07)\n" in texto
