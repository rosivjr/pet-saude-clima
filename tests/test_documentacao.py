"""
Testes de consistência entre a documentação e o config.

A lista de códigos CID-10 de docs/metodos.md é gerada a partir de
config.GRUPOS_AGRAVO (item 7.1 do RECORD pede a lista no material
publicado). Se um código mudar no config, este teste falha e mostra a
tabela nova para colar entre os marcadores.
"""

from pathlib import Path

from src import config

METODOS = config.RAIZ / "docs" / "metodos.md"
INICIO = "<!-- cid:inicio (gerado por tests/test_documentacao.py; não editar à mão) -->"
FIM = "<!-- cid:fim -->"


def tabela_cid() -> str:
    """Tabela em Markdown com os grupos e códigos, na ordem do config."""
    linhas = [
        "| Grupo | Entra no indicador DRSAI | Códigos CID-10 (3 primeiros caracteres) |",
        "|---|---|---|",
    ]
    for grupo, codigos in config.GRUPOS_AGRAVO.items():
        drsai = "sim" if grupo in config.GRUPOS_DRSAI else "não"
        linhas.append(f"| {grupo} | {drsai} | {', '.join(codigos)} |")
    return "\n".join(linhas)


def _bloco_documentado(texto: str) -> str:
    assert INICIO in texto and FIM in texto, f"Marcadores da tabela CID ausentes em {METODOS}"
    return texto.split(INICIO, 1)[1].split(FIM, 1)[0].strip()


def test_tabela_cid_igual_ao_config():
    documentado = _bloco_documentado(Path(METODOS).read_text(encoding="utf-8"))
    esperado = tabela_cid()
    assert documentado == esperado, (
        "A tabela CID de docs/metodos.md difere do config.py. "
        f"Substitua o bloco entre os marcadores por:\n\n{esperado}"
    )


def test_tabela_cid_feita_a_mao():
    """Confere o gerador com um mapa pequeno, montado à mão."""
    original_grupos, original_drsai = config.GRUPOS_AGRAVO, config.GRUPOS_DRSAI
    try:
        config.GRUPOS_AGRAVO = {"G1": ("A00", "A01"), "G2": ("B65",)}
        config.GRUPOS_DRSAI = ("G1",)
        assert tabela_cid().splitlines()[2:] == [
            "| G1 | sim | A00, A01 |",
            "| G2 | não | B65 |",
        ]
    finally:
        config.GRUPOS_AGRAVO, config.GRUPOS_DRSAI = original_grupos, original_drsai


def test_titulo_unico_no_readme_citation_e_pyproject():
    """README, CITATION.cff e pyproject.toml usam o título de config.TITULO_PROJETO."""
    titulo = config.TITULO_PROJETO
    readme = (config.RAIZ / "README.md").read_text(encoding="utf-8")
    citation = (config.RAIZ / "CITATION.cff").read_text(encoding="utf-8")
    pyproject = (config.RAIZ / "pyproject.toml").read_text(encoding="utf-8")
    assert readme.splitlines()[0] == f"# {titulo}"
    assert f'title: "{titulo}"' in citation
    assert f'description = "{titulo}"' in pyproject
