"""
Testes do registro de proveniência.
"""

import hashlib
import json
import os
import re
from datetime import date

import pandas as pd

from src import config, proveniencia


def test_sha256_de_arquivo_conhecido(tmp_path):
    """SHA-256 de b'abc' é um valor de referência da norma FIPS 180-2."""
    arquivo = tmp_path / "a.txt"
    arquivo.write_bytes(b"abc")
    assert proveniencia.sha256(arquivo) == hashlib.sha256(b"abc").hexdigest()


def test_sha256_de_pasta_muda_com_o_conteudo(tmp_path):
    pasta = tmp_path / "dados.parquet"
    pasta.mkdir()
    (pasta / "parte-0").write_bytes(b"x")
    antes = proveniencia.sha256(pasta)
    (pasta / "parte-0").write_bytes(b"y")
    assert proveniencia.sha256(pasta) != antes


def test_registro_e_json(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "PROVENIENCIA", tmp_path)
    proveniencia.reiniciar()
    arquivo = tmp_path / "RDPA2401.parquet"
    arquivo.write_bytes(b"123")

    proveniencia.registrar_arquivo("SIH", arquivo, "PA 2024-01 RD")
    proveniencia.registrar_indisponivel("SINAN", "COLE 2023", "sem arquivo publicado")

    resumo = proveniencia.resumo()
    assert resumo["arquivos_por_fonte"] == {"SIH": 1}
    assert "descartes" not in resumo

    destino = proveniencia.salvar()
    assert destino.parent == tmp_path
    conteudo = json.loads(destino.read_text(encoding="utf-8"))
    assert conteudo["arquivos"][0]["bytes"] == 3
    assert conteudo["indisponiveis"][0]["item"] == "COLE 2023"
    assert "periodo" in conteudo["execucao"]


def test_datas_no_fuso_de_belem_e_nome_sem_deslocamento(tmp_path, monkeypatch):
    """Belém é UTC-03:00 sem horário de verão; o nome do JSON não leva o deslocamento."""
    monkeypatch.setattr(config, "PROVENIENCIA", tmp_path)
    proveniencia.reiniciar()
    arquivo = tmp_path / "a.txt"
    arquivo.write_bytes(b"x")
    proveniencia.registrar_arquivo("SIH", arquivo)

    destino = proveniencia.salvar()
    conteudo = json.loads(destino.read_text(encoding="utf-8"))
    assert conteudo["execucao"]["inicio"].endswith("-03:00")
    assert conteudo["execucao"]["fim"].endswith("-03:00")
    assert conteudo["arquivos"][0]["modificado_em"].endswith("-03:00")
    assert re.fullmatch(r"proveniencia_\d{8}T\d{6}\.json", destino.name)


def test_registra_origem_e_data_do_download(tmp_path):
    proveniencia.reiniciar()
    arquivo = tmp_path / "a.csv"
    arquivo.write_bytes(b"x")
    proveniencia.registrar_arquivo(
        "Precipitação",
        arquivo,
        origem="https://exemplo.org/api?x=1",
        baixado_em="2026-10-01T10:00:00-03:00",
    )
    entrada = proveniencia.REGISTRO.arquivos[0]
    assert entrada["origem"] == "https://exemplo.org/api?x=1"
    assert entrada["baixado_em"] == "2026-10-01T10:00:00-03:00"
    assert entrada["sha256"] == hashlib.sha256(b"x").hexdigest()


def test_sem_data_de_download_nao_usa_a_data_da_leitura(tmp_path):
    proveniencia.reiniciar()
    arquivo = tmp_path / "a.csv"
    arquivo.write_bytes(b"x")
    proveniencia.registrar_arquivo("SISAGUA", arquivo)
    entrada = proveniencia.REGISTRO.arquivos[0]
    assert entrada["origem"] == proveniencia.NAO_REGISTRADO
    assert entrada["baixado_em"] == proveniencia.NAO_REGISTRADO


def test_datas_de_extracao_preferem_o_download_e_filtram_a_fonte(tmp_path):
    proveniencia.reiniciar()
    arquivo = tmp_path / "a.csv"
    arquivo.write_bytes(b"x")
    proveniencia.registrar_arquivo("SISAGUA", arquivo, baixado_em="2026-09-18T10:00:00-03:00")
    proveniencia.registrar_arquivo(
        "SISAGUA cadastro", arquivo, baixado_em="2026-09-04T08:00:00-03:00"
    )
    proveniencia.registrar_arquivo("SIH", arquivo, baixado_em="2026-01-01T08:00:00-03:00")
    assert proveniencia.datas_de_extracao("SISAGUA") == (
        date(2026, 9, 4),
        date(2026, 9, 18),
        True,
    )


def test_datas_de_extracao_juntam_varias_fontes(tmp_path):
    """CNES em 02/09 e SIH em 15/09: a figura de leitos e internações cobre as duas."""
    proveniencia.reiniciar()
    arquivo = tmp_path / "a.csv"
    arquivo.write_bytes(b"x")
    proveniencia.registrar_arquivo("CNES", arquivo, baixado_em="2026-09-02T08:00:00-03:00")
    proveniencia.registrar_arquivo("SIH", arquivo, baixado_em="2026-09-15T08:00:00-03:00")
    proveniencia.registrar_arquivo("SIM", arquivo, baixado_em="2026-10-01T08:00:00-03:00")
    assert proveniencia.datas_de_extracao("CNES", "SIH") == (
        date(2026, 9, 2),
        date(2026, 9, 15),
        True,
    )


def test_datas_de_extracao_usam_a_data_do_arquivo_sem_download(tmp_path):
    proveniencia.reiniciar()
    arquivo = tmp_path / "a.csv"
    arquivo.write_bytes(b"x")
    os.utime(arquivo, (1_758_200_000, 1_758_200_000))  # 18/09/2025 09:53 em Belém
    proveniencia.registrar_arquivo("SISAGUA", arquivo)
    assert proveniencia.datas_de_extracao("SISAGUA") == (
        date(2025, 9, 18),
        date(2025, 9, 18),
        False,
    )
    assert proveniencia.datas_de_extracao("SIM") is None


def test_extracao_mista_marca_data_do_arquivo(tmp_path):
    """Um arquivo sem download registrado basta para a data não ser só de extração."""
    proveniencia.reiniciar()
    arquivo = tmp_path / "a.csv"
    arquivo.write_bytes(b"x")
    os.utime(arquivo, (1_758_200_000, 1_758_200_000))  # 18/09/2025 em Belém
    proveniencia.registrar_arquivo("SIH", arquivo, baixado_em="2026-01-10T08:00:00-03:00")
    proveniencia.registrar_arquivo("SIH", arquivo)
    assert proveniencia.datas_de_extracao("SIH") == (
        date(2025, 9, 18),
        date(2026, 1, 10),
        False,
    )


def test_resumo_traz_extracao_por_fonte_exata(tmp_path):
    """No resumo, 'SISAGUA' e 'SISAGUA cadastro' ficam separados."""
    proveniencia.reiniciar()
    arquivo = tmp_path / "a.csv"
    arquivo.write_bytes(b"x")
    proveniencia.registrar_arquivo("SISAGUA", arquivo, baixado_em="2026-09-18T10:00:00-03:00")
    proveniencia.registrar_arquivo(
        "SISAGUA cadastro", arquivo, baixado_em="2026-09-04T08:00:00-03:00"
    )
    extracao = proveniencia.resumo()["extracao"]
    assert extracao["SISAGUA"] == (date(2026, 9, 18), date(2026, 9, 18), True)
    assert extracao["SISAGUA cadastro"] == (date(2026, 9, 4), date(2026, 9, 4), True)


def test_etapas_guardam_antes_e_depois_inclusive_zero(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "PROVENIENCIA", tmp_path)
    proveniencia.reiniciar()
    proveniencia.registrar_etapa("SIH, tipo de AIH", "descarte", "AIH diferente do tipo 1", 50, 50)
    proveniencia.registrar_etapa(
        "SIH, município", "recorte", "residência em outro município", 80, 50
    )

    etapas = proveniencia.resumo()["etapas"]
    assert [(e["antes"], e["depois"]) for e in etapas] == [(50, 50), (80, 50)]
    assert [e["tipo"] for e in etapas] == ["descarte", "recorte"]

    conteudo = json.loads(proveniencia.salvar().read_text(encoding="utf-8"))
    assert "descartes" not in conteudo
    assert conteudo["etapas"][1]["motivo"] == "residência em outro município"


CHAVES_DOWNLOAD = {"arquivo", "fonte", "origem", "baixado_em", "linhas", "sha256"}


def test_registro_download_de_parquet_conta_linhas(tmp_path):
    """3 linhas sintéticas; baixado_em passado é mantido; arquivo é só o nome."""
    arquivo = tmp_path / "RDPA2501.parquet"
    pd.DataFrame({"x": [1, 2, 3]}).to_parquet(arquivo)
    registro = proveniencia.registro_download(
        arquivo, "Fonte X", "https://exemplo/x", baixado_em="2026-10-01T10:00:00-03:00"
    )
    assert set(registro) == CHAVES_DOWNLOAD
    assert registro["arquivo"] == "RDPA2501.parquet"
    assert registro["linhas"] == 3
    assert registro["baixado_em"] == "2026-10-01T10:00:00-03:00"
    assert registro["sha256"] == proveniencia.sha256(arquivo)


def test_registro_download_sem_data_usa_agora_em_belem(tmp_path):
    """Sem baixado_em, vale a hora atual no fuso America/Belem (-03:00)."""
    arquivo = tmp_path / "dicionario.zip"
    arquivo.write_bytes(b"abc")
    registro = proveniencia.registro_download(arquivo, "Fonte X", "https://exemplo/z")
    assert registro["baixado_em"].endswith("-03:00")
    assert registro["linhas"] is None
    assert registro["sha256"] == hashlib.sha256(b"abc").hexdigest()


def test_registro_download_aceita_linhas_dadas(tmp_path):
    arquivo = tmp_path / "chuva.csv"
    arquivo.write_text("data,mm\n2023-01-01,1\n2023-01-02,0\n")
    registro = proveniencia.registro_download(arquivo, "F", "https://x", linhas=2)
    assert registro["linhas"] == 2
