"""
Testes dos carregadores com o PySUS substituído por arquivos locais.

Nenhum download real: cada teste cria um Parquet pequeno em tmp_path e
faz o fetcher do PySUS devolver esse caminho.
"""

import hashlib
import json

import pandas as pd
import pytest

from src import carregadores, config, proveniencia


@pytest.fixture(autouse=True)
def registro_limpo(tmp_path, monkeypatch):
    """Registro novo e cache do PySUS vazio, para não ler o cache real da máquina."""
    proveniencia.reiniciar()
    monkeypatch.setattr(config, "PYSUS_PASTA_CACHE", tmp_path / "cache_pysus")


def _parquet(tmp_path, nome, dados):
    caminho = tmp_path / nome
    pd.DataFrame(dados).to_parquet(caminho)
    return str(caminho)


def test_sih_filtra_residentes_e_registra(tmp_path, monkeypatch):
    rd = _parquet(
        tmp_path,
        "RDPA2401.parquet",
        {
            "MUNIC_RES": ["150553", "150420", "150553"],
            "DIAG_PRINC": ["A09", "A09", "J18"],
            "IDENT": ["1", "1", "1"],
        },
    )
    monkeypatch.setattr(carregadores.pysus_ftp, "sih", lambda **k: [rd])

    df = carregadores.carregar_sih(uf="PA", anos=[2024])

    # 12 meses devolvem o mesmo arquivo de teste: 2 residentes por mês
    assert len(df) == 24
    assert set(df["MUNIC_RES"]) == {"150553"}
    assert proveniencia.resumo()["arquivos_por_fonte"]["SIH"] == 12
    entrada = proveniencia.REGISTRO.arquivos[0]
    assert entrada["origem"].startswith(config.PYSUS_ENDERECOS[config.PYSUS_SOURCE])
    assert "pysus.ftp.sih(state=PA, year=2024, month=1)" in entrada["origem"]
    assert entrada["baixado_em"] == proveniencia.data_do_arquivo(rd)


def test_baixar_tenta_sem_group_quando_group_falha(tmp_path, monkeypatch):
    st = _parquet(tmp_path, "STPA2606.parquet", {"CNES": ["1"]})
    chamadas = []

    def falso_cnes(**k):
        chamadas.append("group" in k)
        if "group" in k:
            raise TypeError("group não aceito")
        return [str(tmp_path / "LTPA2606.parquet"), st]

    caminho = carregadores._baixar(falso_cnes, "ST", "teste", state="PA", year=2026, month=6)
    assert caminho == st
    assert chamadas == [True, False]


def test_baixar_nao_engole_typeerror_sem_group():
    """Fora da tentativa com group=, um TypeError é erro de programação e sobe."""

    def falso_cnes(**k):
        if "group" in k:
            return []
        raise TypeError("erro de programação")

    with pytest.raises(TypeError):
        carregadores._baixar(falso_cnes, "ST", "teste", state="PA", year=2026, month=6)


def test_sinan_sem_arquivo_fica_indisponivel(monkeypatch):
    monkeypatch.setattr(carregadores.pysus_ftp, "sinan", lambda **k: [])
    df = carregadores.carregar_sinan(agravos={"COLE": ("Cólera", "Feco-oral")}, anos=[2023])

    assert df.empty
    itens = [i["item"] for i in proveniencia.resumo()["indisponiveis"]]
    assert itens == ["COLE 2023"]


def test_cnes_periodo_continua_se_um_ano_falhar(tmp_path, monkeypatch):
    st = _parquet(
        tmp_path,
        "STPA2506.parquet",
        {
            "CNES": ["2615746"],
            "CODUFMUN": ["150553"],
            "TP_UNID": ["05"],
        },
    )

    def falso_cnes(state, year, month, **k):
        return [] if year == 2024 else [st]

    monkeypatch.setattr(carregadores.pysus_ftp, "cnes", falso_cnes)
    monkeypatch.setattr(config, "CNES_COMPETENCIA_MES", 6)

    df = carregadores.carregar_cnes_periodo(anos=[2024, 2025])

    assert list(df["competencia_ano"]) == [2025]
    assert proveniencia.resumo()["indisponiveis"][0]["item"] == "PA 2024-06 ST"


ESGOTO_SIDRA = (
    '\ufeff"Tabela 6805 - Domicílios particulares permanentes ocupados, '
    'por tipo de esgotamento sanitário"\n'
    '"Variável - Domicílios particulares permanentes ocupados (Unidades)"\n'
    '"Nível";"Cód.";"Município";"Ano x Tipo de esgotamento sanitário"\n'
    '"Nível";"Cód.";"Município";"2022"\n'
    '"Nível";"Cód.";"Município";"Total";"Rede geral, rede pluvial ou fossa ligada à rede";'
    '"Rede geral ou pluvial";"Fossa séptica ou fossa filtro ligada à rede"\n'
    '"MU";"1505536";"Parauapebas (PA)";"87667";"24842";"19623";"5219"\n'
    '"Fonte: IBGE - Censo Demográfico"\n'
    "\n"
    '"Variável - Domicílios particulares permanentes ocupados - percentual do total geral"\n'
    '"Nível";"Cód.";"Município";"Total";"Rede geral, rede pluvial ou fossa ligada à rede";'
    '"Rede geral ou pluvial";"Fossa séptica ou fossa filtro ligada à rede"\n'
    '"MU";"1505536";"Parauapebas (PA)";"100,00";"28,34";"22,38";"5,95"\n'
)


def test_censo_le_so_o_bloco_de_contagens(tmp_path, monkeypatch):
    """Formato real do download do SIDRA (tabela 6805, recorte de colunas)."""
    (tmp_path / "censo2022_6805_esgoto.csv").write_text(ESGOTO_SIDRA, encoding="utf-8")
    monkeypatch.setattr(config, "DADOS_BRUTOS", tmp_path)

    tabela = carregadores.carregar_censo_sidra("esgoto")

    assert list(tabela["domicilios"]) == [87667, 24842, 19623, 5219]
    assert tabela["categoria"].iloc[0] == "Total"


def test_censo_arquivo_ausente(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DADOS_BRUTOS", tmp_path)
    with pytest.raises(FileNotFoundError):
        carregadores.carregar_censo_sidra("lixo")
    assert proveniencia.resumo()["indisponiveis"][0]["fonte"] == "Censo 2022"


def test_sinisa_valor_deslocado_do_cabecalho(tmp_path, monkeypatch):
    """No relatório real, valor e unidade ficam uma coluna à esquerda do cabeçalho."""
    linhas = [
        [None, "Relatório de Indicadores de Módulo de Abastecimento de Água", None, None, None],
        [None, "Ano atual: 2025 / Ano de referência: 2024", None, None, None],
        [None, "Parauapebas", None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
        ["Código", "Grupo de indicador", "Descrição", "Valor", "Unidade"],
        ["IAG0001", "Atendimento da população total com rede", "90,26", "Percentual", None],
        ["IAG0002", "Atendimento da população urbana com rede", "91,75", "Percentual", None],
    ]
    (tmp_path / "sinisa").mkdir()
    pd.DataFrame(linhas).to_excel(
        tmp_path / "sinisa" / "indicadores_de_abastecimento_de_agua.xlsx",
        header=False,
        index=False,
    )
    monkeypatch.setattr(config, "DADOS_BRUTOS", tmp_path)

    tabela, meta = carregadores.carregar_sinisa("agua")

    assert meta == {"ano_referencia": 2024, "municipio": "Parauapebas"}
    assert list(tabela["codigo"]) == ["IAG0001", "IAG0002"]
    assert list(tabela["valor"]) == [90.26, 91.75]
    assert list(tabela["unidade"]) == ["Percentual", "Percentual"]


class _RespostaFalsa:
    def __init__(self, corpo):
        self._corpo = corpo

    def raise_for_status(self):
        pass

    def json(self):
        return self._corpo


class _SessaoFalsa:
    """Responde ao geocodificador e à API de histórico sem rede."""

    def __init__(self):
        self.chamadas = []

    def get(self, url, params=None, timeout=None):
        self.chamadas.append((url, params))
        if url == config.CLIMA_GEOCODING_API:
            return _RespostaFalsa(
                {
                    "results": [
                        {
                            "name": "Parauapebas",
                            "country_code": "BR",
                            "admin1": "Goiás",
                            "latitude": 1.0,
                            "longitude": 1.0,
                        },
                        {
                            "name": "Parauapebas",
                            "country_code": "BR",
                            "admin1": "Pará",
                            "latitude": -6.0,
                            "longitude": -50.0,
                        },
                    ]
                }
            )
        return _RespostaFalsa(
            {
                "latitude": -6.05,
                "longitude": -49.95,
                "daily": {"time": ["2025-01-01", "2025-01-02"], "precipitation_sum": [10.5, None]},
            }
        )


def test_precipitacao_baixa_grava_copia_e_reusa(tmp_path, monkeypatch):
    from datetime import date

    monkeypatch.setattr(config, "DADOS_BRUTOS", tmp_path)
    monkeypatch.setattr(config, "PERIODO_INICIO", date(2025, 1, 1))
    monkeypatch.setattr(config, "PERIODO_FIM", date(2025, 1, 2))
    monkeypatch.setattr(config, "CLIMA_COORDENADAS", None)

    sessao = _SessaoFalsa()
    df = carregadores.carregar_precipitacao(sessao)

    # Escolhe o resultado do Pará, não o homônimo de outra UF
    assert sessao.chamadas[1][1]["latitude"] == -6.0
    assert df["precipitacao_mm"].iloc[0] == 10.5
    assert pd.isna(df["precipitacao_mm"].iloc[1])
    assert df.attrs["meta"]["latitude_grade"] == -6.05

    # JSON de proveniência: linhas e SHA-256 do CSV gravado, data no fuso de Belém
    copia = tmp_path / config.CLIMA_ARQUIVO
    meta = json.loads(copia.with_suffix(".json").read_text(encoding="utf-8"))
    assert meta["linhas"] == 2
    assert meta["sha256"] == hashlib.sha256(copia.read_bytes()).hexdigest()
    assert meta["baixado_em"].endswith("-03:00")
    assert meta["origem"] == config.CLIMA_API
    assert meta["arquivo"] == copia.name

    # Segunda chamada usa a cópia local, sem rede, e mantém a data do download
    outra = _SessaoFalsa()
    carregadores.carregar_precipitacao(outra)
    assert outra.chamadas == []
    baixado, reusado = proveniencia.REGISTRO.arquivos
    assert baixado["origem"] == reusado["origem"] == config.CLIMA_API
    assert reusado["baixado_em"] == df.attrs["meta"]["baixado_em"]


def test_precipitacao_sem_rede_fica_indisponivel(tmp_path, monkeypatch):
    class SessaoQuebrada:
        def get(self, *a, **k):
            raise ConnectionError("sem rede")

    monkeypatch.setattr(config, "DADOS_BRUTOS", tmp_path)
    monkeypatch.setattr(config, "CLIMA_COORDENADAS", (-6.0, -50.0))
    with pytest.raises(RuntimeError):
        carregadores.carregar_precipitacao(SessaoQuebrada())
    assert proveniencia.resumo()["indisponiveis"][0]["fonte"] == "Precipitação"


def test_precipitacao_so_nula_e_erro_e_nao_grava_copia(tmp_path, monkeypatch):
    """Resposta com precipitation_sum toda nula não pode virar 0 mm."""

    class SessaoNula:
        def get(self, url, params=None, timeout=None):
            return _RespostaFalsa(
                {
                    "latitude": -6.1,
                    "longitude": -49.9,
                    "daily": {"time": ["2025-01-01"], "precipitation_sum": [None]},
                }
            )

    monkeypatch.setattr(config, "DADOS_BRUTOS", tmp_path)
    monkeypatch.setattr(config, "CLIMA_COORDENADAS", (-6.0, -50.0))
    with pytest.raises(RuntimeError, match="não retornou precipitação"):
        carregadores.carregar_precipitacao(SessaoNula())
    assert not (tmp_path / config.CLIMA_ARQUIVO).exists()


def test_copia_local_toda_nula_e_ignorada(tmp_path, monkeypatch):
    from datetime import date

    monkeypatch.setattr(config, "DADOS_BRUTOS", tmp_path)
    monkeypatch.setattr(config, "PERIODO_INICIO", date(2025, 1, 1))
    monkeypatch.setattr(config, "PERIODO_FIM", date(2025, 1, 2))
    monkeypatch.setattr(config, "CLIMA_COORDENADAS", (-6.0, -50.0))
    copia = tmp_path / config.CLIMA_ARQUIVO
    copia.parent.mkdir(parents=True)
    copia.write_text("data,precipitacao_mm\n2025-01-01,\n2025-01-02,\n")
    copia.with_suffix(".json").write_text('{"modelo": "era5_land"}')

    sessao = _SessaoFalsa()
    df = carregadores.carregar_precipitacao(sessao)
    assert len(sessao.chamadas) == 1, "deveria baixar de novo"
    assert df["precipitacao_mm"].iloc[0] == 10.5


def test_sim_filtra_residentes_e_guarda_anos(tmp_path, monkeypatch):
    """CODMUNRES com 6 ou 7 dígitos; 2025 sem arquivo fica indisponível."""
    do = _parquet(
        tmp_path,
        "DOPA2023.parquet",
        {
            "CAUSABAS": ["A09", "I219", "A90"],
            "CODMUNRES": ["150553", "1505536", "150420"],
            "DTOBITO": ["15032023", "01012023", "10102023"],
            "IDADE": ["405", "470", "430"],
        },
    )

    def falso_sim(state, year, **k):
        return [do] if year == 2023 else []

    monkeypatch.setattr(carregadores.pysus_ftp, "sim", falso_sim)
    df = carregadores.carregar_sim(uf="PA", anos=[2023, 2025])

    assert len(df) == 2
    assert df.attrs["anos"] == [2023]
    assert proveniencia.resumo()["indisponiveis"][0]["item"] == "PA 2025 DO"


def _no_cache(sistema, nome, dados):
    pasta = config.PYSUS_PASTA_CACHE / sistema
    pasta.mkdir(parents=True, exist_ok=True)
    return _parquet(pasta, nome, dados)


def _sem_servidor(**k):
    raise AssertionError("o servidor não deveria ser consultado")


def test_sih_nao_pede_competencia_depois_do_corte(monkeypatch):
    """Corte em 2026-07: RDPA2601 vem do cache, 2 a 7 do servidor; 8 a 12 nunca são pedidos."""
    monkeypatch.setattr(config, "SIH_ULTIMA_COMPETENCIA", (2026, 7))
    _no_cache("sih", "RDPA2601.parquet", {"MUNIC_RES": ["150553"], "IDENT": ["1"]})
    chamadas = []
    monkeypatch.setattr(
        carregadores.pysus_ftp,
        "sih",
        lambda **k: chamadas.append((k["year"], k["month"])) or [],
    )

    carregadores.carregar_sih(anos=[2026])

    assert sorted(set(chamadas)) == [(2026, mes) for mes in range(2, 8)]


def test_sih_no_cache_nao_consulta_o_servidor(monkeypatch):
    """RDPA2401 no cache: lido dali; os outros 11 meses vêm do servidor (vazio aqui)."""
    rd = _no_cache("sih", "RDPA2401.parquet", {"MUNIC_RES": ["150553"], "IDENT": ["1"]})
    chamadas = []
    monkeypatch.setattr(
        carregadores.pysus_ftp, "sih", lambda **k: chamadas.append(k["month"]) or []
    )

    df = carregadores.carregar_sih(anos=[2024])

    assert len(df) == 1
    assert 1 not in chamadas and sorted(set(chamadas)) == list(range(2, 13))
    entrada = proveniencia.REGISTRO.arquivos[0]
    assert entrada["arquivo"] == "RDPA2401.parquet"
    assert entrada["leitura"] == carregadores.LEITURA_CACHE
    assert entrada["baixado_em"] == proveniencia.data_do_arquivo(rd)


def test_fora_do_cache_registra_consulta_ao_servidor(tmp_path, monkeypatch):
    st = _parquet(tmp_path, "STPA2606.parquet", {"CNES": ["1"]})
    monkeypatch.setattr(carregadores.pysus_ftp, "cnes", lambda **k: [st])

    carregadores.carregar_cnes(ano=2026, mes=6)

    assert proveniencia.REGISTRO.arquivos[0]["leitura"] == carregadores.LEITURA_SERVIDOR


def test_cache_de_sim_cnes_e_sinan(monkeypatch):
    """Nomes do cache: DOPA2024, STPA2606 e COLEBR23; nenhum vai ao servidor."""
    _no_cache("sim", "DOPA2024.parquet", {"CODMUNRES": ["150553"], "IDADE": ["430"]})
    _no_cache("cnes", "STPA2606.parquet", {"CNES": ["1"]})
    _no_cache("sinan", "COLEBR23.parquet", {"ID_MN_RESI": ["150553"]})
    for sistema in ("sim", "cnes", "sinan"):
        monkeypatch.setattr(carregadores.pysus_ftp, sistema, _sem_servidor)

    assert len(carregadores.carregar_sim(anos=[2024])) == 1
    assert len(carregadores.carregar_cnes(ano=2026, mes=6)) == 1
    assert (
        len(carregadores.carregar_sinan(agravos={"COLE": ("Cólera", "Feco-oral")}, anos=[2023]))
        == 1
    )
    leituras = {a["leitura"] for a in proveniencia.REGISTRO.arquivos}
    assert leituras == {carregadores.LEITURA_CACHE}
