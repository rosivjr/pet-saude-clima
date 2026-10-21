"""
Testes de consistência do config.

Pegam erros de edição: código CID em dois grupos, faixa etária sem rótulo,
ano do período sem população.
"""

from collections import Counter
from datetime import date

from src import config


def test_nenhum_cid_em_dois_grupos():
    """_classificar_grupo_agravo pega o primeiro grupo que casar; duplicata
    faria a internação cair no grupo errado sem aviso."""
    contagem = Counter(c for codigos in config.GRUPOS_AGRAVO.values() for c in codigos)
    duplicados = [c for c, n in contagem.items() if n > 1]
    assert not duplicados, f"CID em mais de um grupo: {duplicados}"


def test_grupos_drsai_existem_no_mapa():
    assert set(config.GRUPOS_DRSAI) <= set(config.GRUPOS_AGRAVO)


def test_sensibilidade_fora_do_drsai():
    """L00-L08, E86 e A05 não podem entrar no total DRSAI."""
    drsai = {c for g in config.GRUPOS_DRSAI for c in config.GRUPOS_AGRAVO[g]}
    assert not drsai & set(config.CID_SENSIBILIDADE)


def test_dengue_inclui_a97():
    assert {"A90", "A91", "A97"} <= set(config.CID_VETOR)


def test_faixas_etarias_consistentes():
    assert len(config.FAIXA_ETARIA_ROTULOS) == len(config.FAIXA_ETARIA_LIMITES) - 1
    assert list(config.FAIXA_ETARIA_LIMITES) == sorted(config.FAIXA_ETARIA_LIMITES)


def test_grupos_do_sinan_existem_no_mapa():
    grupos = {grupo for _, grupo in config.SINAN_AGRAVOS.values()}
    assert grupos <= set(config.GRUPOS_AGRAVO)


def test_populacao_preenchida_para_todos_os_anos():
    """Todo ano do período precisa de denominador."""
    faltando = [a for a in config.ANOS if config.POPULACAO_ANUAL.get(a) is None]
    assert not faltando, f"Ano sem população em config.POPULACAO_ANUAL: {faltando}"


def test_toda_populacao_tem_fonte():
    assert set(config.POPULACAO_ANUAL) == set(config.POPULACAO_FONTE)


def test_2023_e_media_geometrica_censo_2024():
    """2023 fica entre o Censo 2022 e a estimativa 2024, pela fórmula declarada."""
    esperado = round((config.POPULACAO_CENSO_2022 * config.POPULACAO_IBGE_ESTIMATIVA[2024]) ** 0.5)
    assert config.POPULACAO_ANUAL[2023] == esperado
    assert (
        config.POPULACAO_CENSO_2022
        < config.POPULACAO_ANUAL[2023]
        < config.POPULACAO_IBGE_ESTIMATIVA[2024]
    )


def test_tipos_cnes_conforme_cnesweb():
    """83 é Polo de prevenção; Polo academia da saúde é 74 (lista do CnesWeb)."""
    assert config.CNES_TIPOS_UNIDADE["74"] == "Polo academia da saúde"
    assert config.CNES_TIPOS_UNIDADE["83"].startswith("Polo de prevenção")


def test_lacunas_separam_competencias_apos_o_periodo(monkeypatch):
    from src.relatorio.geral import _separar_por_periodo

    monkeypatch.setattr(config, "PERIODO_FIM", date(2026, 6, 30))
    itens = [
        {"fonte": "SIH", "item": "PA 2026-06 RD", "motivo": "x"},
        {"fonte": "SIH", "item": "PA 2026-07 RD", "motivo": "x"},
        {"fonte": "SINAN", "item": "COLE 2026", "motivo": "x"},
    ]
    dentro, depois = _separar_por_periodo(itens)
    assert [i["item"] for i in dentro] == ["PA 2026-06 RD", "COLE 2026"]
    assert [i["item"] for i in depois] == ["PA 2026-07 RD"]


def test_todo_agravo_do_sinan_tem_regra_de_classificacao():
    """Cada agravo tem códigos conferidos ou está entre os sem CLASSI_FIN, nunca os dois."""
    com_codigos = {config.SINAN_AGRAVOS[s][0] for s in config.SINAN_CLASSI_FIN}
    sem_classi = set(config.SINAN_SEM_CLASSI_FIN)
    todos = {nome for nome, _ in config.SINAN_AGRAVOS.values()}
    assert set(config.SINAN_CLASSI_FIN) <= set(config.SINAN_AGRAVOS)
    assert com_codigos | sem_classi == todos
    assert not com_codigos & sem_classi
    assert set(config.SINAN_CLASSI_A_CONFERIR) <= set(config.SINAN_CLASSI_FIN)


def test_27_ufs_sem_repeticao():
    assert len(config.UFS) == 27
    assert len(set(config.UFS)) == 27
    assert config.MUNICIPIO_UF in config.UFS


def test_cids_do_relatorio_dda_com_tres_caracteres():
    """O SIH é comparado pelos 3 primeiros caracteres; código maior nunca casaria."""
    codigos = [c for grupo in config.CID_RELATORIO_DDA.values() for c in grupo]
    assert all(len(c) == 3 for c in codigos)
    assert len(config.CID_RELATORIO_DDA["diarreia"]) == 10  # A00 a A09
