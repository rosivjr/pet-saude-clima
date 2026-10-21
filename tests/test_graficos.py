"""
Testes da camada de visualização.

Cada figura é gerada a partir de resultados sintéticos numa pasta
temporária (tmp_path); o teste confere o nome e se o arquivo é um PNG.
"""

import pandas as pd
import pytest

from src import config, graficos
from src.indicadores import PerfilAgravo, ResultadoConformidade

ASSINATURA_PNG = b"\x89PNG\r\n\x1a\n"


@pytest.fixture(autouse=True)
def pasta_temporaria(tmp_path, monkeypatch):
    """Salva as figuras em tmp_path, nunca em figuras/ do projeto."""
    pasta = tmp_path / "figuras"
    monkeypatch.setattr(graficos, "PASTA_FIGURAS", pasta)
    return pasta


def _confere_png(caminho, pasta, nome):
    assert caminho == pasta / f"{nome}.png"
    assert caminho.read_bytes()[:8] == ASSINATURA_PNG


def _perfil(grupo: str, internacoes: int) -> PerfilAgravo:
    return PerfilAgravo(grupo, internacoes, 10.0, 0, 0.0, 3.0, True)


def _microbiologico() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "PARAMETRO": ["Escherichia coli"],
            "total": [8],
            "presentes": [1],
            "percentual_presenca": [12.5],
            "ic_inferior": [3.5],
            "ic_superior": [36.0],
        }
    )


def _ecoli_area() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "area": ["CENTRO", "RIO VERDE"],
            "amostras": [40, 40],
            "percentual_positivo": [45.0, 5.0],
            "ic_inferior": [30.7, 1.4],
            "ic_superior": [60.2, 16.5],
        }
    )


def _sazonal() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ano": [2024, 2024],
            "mes": [2, 1],
            "percentual_positivo": [10.0, 30.0],
            "ic_inferior": [1.8, 10.8],
            "ic_superior": [40.4, 60.3],
        }
    )


def _hospitais() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "nome": ["Hospital com um nome bem comprido demais", "Clínica"],
            "leitos": [111, 10],
            "internacoes": [500, 3],
        }
    )


def _etario(percentuais: dict[str, float]) -> pd.DataFrame:
    return pd.DataFrame(
        {"faixa_etaria": list(percentuais), "percentual": list(percentuais.values())}
    )


def _serie_cloro() -> pd.DataFrame:
    return pd.DataFrame({"ano": [2024, 2024], "mes": [1, 2], "media": [0.15, 0.4]})


def _captacao() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "origem": ["Subterrânea", "Superficial"],
            "amostras": [30, 12],
            "percentual_positivo": [10.0, 35.0],
            "ic_inferior": [3.5, 14.1],
            "ic_superior": [25.6, 63.7],
        }
    )


def test_conformidade_agua(pasta_temporaria):
    resultados = [
        ResultadoConformidade(config.PARAMETRO_CLORO, 0.2, None, "mg/L", 4, 1, 25.0, 4.6, 69.9)
    ]
    caminho = graficos.grafico_conformidade_agua(resultados, _microbiologico())
    _confere_png(caminho, pasta_temporaria, "01_conformidade_agua")


def test_conformidade_agua_com_rodape(pasta_temporaria):
    resultados = [
        ResultadoConformidade(config.PARAMETRO_CLORO, 0.2, None, "mg/L", 4, 1, 25.0, 4.6, 69.9)
    ]
    caminho = graficos.grafico_conformidade_agua(
        resultados, _microbiologico(), rodape="Fonte: SISAGUA. Extração: 18/09/2026."
    )
    _confere_png(caminho, pasta_temporaria, "01_conformidade_agua")


def test_desenhar_rodape_escreve_o_texto_na_figura():
    fig, _ = graficos._preparar_eixos("Título")
    graficos.desenhar_rodape(fig, "Fonte: SIH/SUS; extraído em 18/09/2026.")
    assert [t.get_text() for t in fig.texts] == ["Fonte: SIH/SUS; extraído em 18/09/2026."]
    graficos.plt.close(fig)


def test_desenhar_rodape_sem_texto_nao_escreve():
    fig, _ = graficos._preparar_eixos("Título")
    graficos.desenhar_rodape(fig, None)
    assert fig.texts == []
    graficos.plt.close(fig)


def test_ecoli_por_area(pasta_temporaria):
    caminho = graficos.grafico_ecoli_por_area(_ecoli_area())
    _confere_png(caminho, pasta_temporaria, "02_ecoli_por_area")


def test_ecoli_por_area_sem_area_suficiente(pasta_temporaria, caplog):
    """Áreas com 29 e 10 amostras: nenhuma chega a 30, a figura não é gerada."""
    dados = _ecoli_area().assign(amostras=[29, 10])
    with caplog.at_level("WARNING", logger=graficos.logger.name):
        caminho = graficos.grafico_ecoli_por_area(dados)
    assert caminho is None
    assert not (pasta_temporaria / "02_ecoli_por_area.png").exists()
    assert f"nenhuma área com {config.LIMIAR_AMOSTRAS_PROPORCAO}" in caplog.text


def test_sazonalidade(pasta_temporaria):
    caminho = graficos.grafico_sazonalidade(_sazonal())
    _confere_png(caminho, pasta_temporaria, "03_sazonalidade_ecoli")


def test_internacoes_por_grupo(pasta_temporaria):
    perfis = [_perfil("Feco-oral", 40), _perfil("Higiene", 5), _perfil("Contexto climático", 90)]
    caminho = graficos.grafico_internacoes_por_grupo(perfis)
    _confere_png(caminho, pasta_temporaria, "04_internacoes_por_grupo")


def test_capacidade_hospitalar(pasta_temporaria):
    caminho = graficos.grafico_capacidade_hospitalar(_hospitais())
    _confere_png(caminho, pasta_temporaria, "05_capacidade_hospitalar")


def test_perfil_etario_comparado(pasta_temporaria):
    caminho = graficos.grafico_perfil_etario_comparado(
        _etario({"<1": 20.0, "1-4": 80.0}), _etario({"<1": 60.0, "1-4": 40.0})
    )
    _confere_png(caminho, pasta_temporaria, "06_perfil_etario_comparado")


def test_serie_cloro(pasta_temporaria):
    caminho = graficos.grafico_serie_cloro(_serie_cloro())
    _confere_png(caminho, pasta_temporaria, "07_serie_cloro")


def test_origem_captacao(pasta_temporaria):
    caminho = graficos.grafico_origem_captacao(_captacao())
    _confere_png(caminho, pasta_temporaria, "08_origem_captacao")


def test_gerar_todos_segue_apos_falha(pasta_temporaria):
    """Sem área com base suficiente, a figura 02 falha (max de lista vazia); as outras 7 saem."""
    poucas_amostras = _ecoli_area().assign(amostras=[1, 1])
    gerados = graficos.gerar_todos(
        conformidade=[],
        microbiologico=_microbiologico(),
        ecoli_area=poucas_amostras,
        sazonal=_sazonal(),
        perfis=[_perfil("Feco-oral", 40)],
        hospitais=_hospitais(),
        etario_geral=_etario({"<1": 100.0}),
        etario_feco=_etario({"<1": 100.0}),
        serie_cloro=_serie_cloro(),
        captacao=_captacao(),
        rodapes={"agua": "Fonte: SISAGUA.", "internacoes": "Fonte: SIH/SUS."},
    )
    assert len(gerados) == 7
    assert pasta_temporaria / "02_ecoli_por_area.png" not in gerados
    assert sorted(p.name for p in pasta_temporaria.iterdir()) == sorted(p.name for p in gerados)


def test_erro_ic_distancia_ate_os_limites():
    """25,0% com IC 4,6–69,9: 20,4 abaixo e 44,9 acima."""
    erro = graficos._erro_ic([25.0], [4.6], [69.9])
    assert erro[0][0] == pytest.approx(20.4)
    assert erro[1][0] == pytest.approx(44.9)
