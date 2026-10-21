"""
Testes da camada de transformação.

Cobre conversão decimal, idade no SIH e no SINAN, tipo de AIH e recorte temporal.
"""

from datetime import date

import pandas as pd
import pytest

from src import config, proveniencia
from src.transformacoes import (
    converter_decimal_brasileiro,
    filtrar_agravos,
    filtrar_aih_normal,
    filtrar_anos,
    filtrar_drsai,
    filtrar_municipio_cnes,
    filtrar_municipio_sih,
    filtrar_periodo,
    idade_sih_em_anos,
    idade_sim_em_anos,
    idade_sinan_em_anos,
    padronizar_cnes,
    padronizar_populacao,
    padronizar_sih,
    padronizar_sim,
    padronizar_sinan,
    padronizar_sisagua,
    registrar_etapa,
)


class TestConverterDecimalBrasileiro:
    """Testes da conversão de texto com vírgula decimal para número."""

    def test_converte_virgula_decimal(self):
        """Vírgula deve virar ponto decimal."""
        entrada = pd.Series(["0,00", "2,24", "1,66"])
        esperado = pd.Series([0.00, 2.24, 1.66])
        resultado = converter_decimal_brasileiro(entrada)
        pd.testing.assert_series_equal(resultado, esperado)

    def test_remove_separador_de_milhar(self):
        """Ponto de milhar deve ser removido antes da conversão."""
        entrada = pd.Series(["1.234,56", "10.000,00"])
        esperado = pd.Series([1234.56, 10000.00])
        resultado = converter_decimal_brasileiro(entrada)
        pd.testing.assert_series_equal(resultado, esperado)

    def test_texto_nao_numerico_vira_nan(self):
        """Valores qualitativos não devem causar erro, apenas NaN."""
        entrada = pd.Series(["PRESENTE", "AUSENTE", "1,5"])
        resultado = converter_decimal_brasileiro(entrada)

        assert pd.isna(resultado[0])
        assert pd.isna(resultado[1])
        assert resultado[2] == 1.5

    def test_ignora_espacos_em_branco(self):
        """Espaços ao redor do valor não devem impedir a conversão."""
        entrada = pd.Series(["  2,50  ", "3,00 "])
        resultado = converter_decimal_brasileiro(entrada)

        assert resultado[0] == 2.50
        assert resultado[1] == 3.00

    def test_inteiro_sem_virgula(self):
        """Valores inteiros sem vírgula devem converter normalmente."""
        entrada = pd.Series(["6", "7"])
        resultado = converter_decimal_brasileiro(entrada)

        assert resultado[0] == 6.0
        assert resultado[1] == 7.0

    # O caso "0.5" (ponto como decimal) está em TestFormatoDecimal.


class TestFiltrarAnos:
    """Testes do recorte temporal."""

    def test_mantem_apenas_anos_configurados(self, monkeypatch):
        """Registros fora de config.ANOS devem ser removidos.

        O monkeypatch fixa ANOS só durante o teste, para ele não depender
        do período configurado no projeto.
        """
        monkeypatch.setattr(config, "ANOS", [2025, 2026])
        df = pd.DataFrame({"ano": [2023, 2024, 2025, 2026], "valor": [1, 2, 3, 4]})
        resultado = filtrar_anos(df)

        assert set(resultado["ano"]) == {2025, 2026}
        assert len(resultado) == 2

    def test_nao_modifica_original(self, monkeypatch):
        """A função não deve alterar o DataFrame recebido."""
        monkeypatch.setattr(config, "ANOS", [2025])
        df = pd.DataFrame({"ano": [2023, 2025], "valor": [1, 2]})
        copia = df.copy()
        filtrar_anos(df)

        pd.testing.assert_frame_equal(df, copia)


class TestFormatoDecimal:
    """Ponto fora do padrão de milhar para a conversão (decisão 0010)."""

    def test_formato_decimal_do_sisagua(self):
        """Sem a regra, "0.5" viraria 5 (ponto lido como milhar)."""
        entrada = pd.Series(["0,5", "0.5"])
        with pytest.raises(ValueError, match="1 valor"):
            converter_decimal_brasileiro(entrada)

    @pytest.mark.parametrize("ambiguo", ["1.234", "<0.5", "0.123,5", "1.23,4"])
    def test_ponto_ambiguo_para_com_erro(self, ambiguo):
        with pytest.raises(ValueError):
            converter_decimal_brasileiro(pd.Series([ambiguo]))

    def test_erro_nao_mostra_o_valor(self):
        with pytest.raises(ValueError) as erro:
            converter_decimal_brasileiro(pd.Series(["0.5", "7.25", "1,0"]))
        assert "2 valores" in str(erro.value)
        assert "0.5" not in str(erro.value)
        assert "7.25" not in str(erro.value)

    def test_milhar_negativo_continua_aceito(self):
        assert list(converter_decimal_brasileiro(pd.Series(["-1.234,5"]))) == [-1234.5]


class TestIdadeSih:
    def _converter(self, idades, codigos):
        return idade_sih_em_anos(pd.Series(idades), pd.Series(codigos))

    def test_dias_e_meses_viram_zero(self):
        assert list(self._converter(["15", "6"], ["2", "3"])) == [0, 0]

    def test_anos(self):
        assert list(self._converter(["34"], ["4"])) == [34]

    def test_cem_anos_ou_mais(self):
        """Código 5: idade = 100 + valor."""
        assert list(self._converter(["2"], ["5"])) == [102]

    def test_codigo_desconhecido_vira_nan(self):
        assert pd.isna(self._converter(["10"], ["9"]).iloc[0])

    def test_menor_de_um_ano_entra_na_faixa_menor_1(self):
        """Antes da etapa 2, dias e meses ficavam fora de todas as faixas."""
        df = pd.DataFrame(
            {
                "DT_INTER": ["20240110", "20240110"],
                "DT_SAIDA": ["20240112", "20240112"],
                "IDADE": ["20", "3"],
                "COD_IDADE": ["2", "4"],
                "SEXO": ["1", "3"],
                "DIAG_PRINC": ["A09", "A09"],
                "MORTE": [0, 0],
                "DIAS_PERM": [2, 2],
            }
        )
        resultado = padronizar_sih(df)
        assert list(resultado["faixa_etaria"].astype(str)) == ["<1", "1-4"]


class TestIdadeSinan:
    def test_decodifica_unidades(self):
        """4025 = 25 anos; 3006 = 6 meses -> 0; 2010 = 10 dias -> 0."""
        entrada = pd.Series(["4025", "3006", "2010"])
        assert list(idade_sinan_em_anos(entrada)) == [25, 0, 0]

    def test_aceita_numero_float(self):
        assert list(idade_sinan_em_anos(pd.Series([4025.0]))) == [25]


class TestFiltroAih:
    def test_mantem_so_tipo_1(self):
        df = pd.DataFrame({"IDENT": ["1", "5", "1"], "N_AIH": [1, 2, 3]})
        assert list(filtrar_aih_normal(df)["N_AIH"]) == [1, 3]


class TestFiltrarMunicipioSih:
    def test_usa_codigo_do_config_e_ignora_espacos(self):
        """150553 e ' 150553 ' são Parauapebas; 150010 fica fora: 2 de 3."""
        df = pd.DataFrame({"MUNIC_RES": ["150553", " 150553 ", "150010"], "N_AIH": [1, 2, 3]})
        assert list(filtrar_municipio_sih(df)["N_AIH"]) == [1, 2]

    def test_segue_o_codigo_do_config(self, monkeypatch):
        monkeypatch.setattr(config, "MUNICIPIO_IBGE_6_STR", "150010")
        df = pd.DataFrame({"MUNIC_RES": ["150553", "150010"], "N_AIH": [1, 2]})
        assert list(filtrar_municipio_sih(df)["N_AIH"]) == [2]


class TestFiltrarAgravos:
    def _df(self):
        return pd.DataFrame({"grupo_agravo": ["Feco-oral", "Contexto climático", None]})

    def test_remove_sem_grupo(self):
        """Feco-oral e Contexto climático têm grupo; None sai: 2 de 3."""
        resultado = filtrar_agravos(self._df())
        assert list(resultado["grupo_agravo"]) == ["Feco-oral", "Contexto climático"]


class TestFiltrarDrsai:
    def test_tira_grupos_fora_do_drsai_e_registra_recorte(self):
        """4 internações; Contexto climático e Sensibilidade saem: 4 → 2."""
        proveniencia.reiniciar()
        df = pd.DataFrame(
            {"grupo_agravo": ["Feco-oral", "Contexto climático", "Higiene", "Sensibilidade"]}
        )
        resultado = filtrar_drsai(df)
        assert list(resultado["grupo_agravo"]) == ["Feco-oral", "Higiene"]
        etapas = [
            (e["etapa"], e["tipo"], e["antes"], e["depois"])
            for e in proveniencia.resumo()["etapas"]
        ]
        assert etapas == [("SIH: DRSAI", "recorte", 4, 2)]


class TestFiltrarMunicipioCnes:
    def test_mantem_so_o_municipio(self):
        df = pd.DataFrame({"CODUFMUN": ["150553", "150010", "150553"], "CNES": ["A", "B", "C"]})
        assert list(filtrar_municipio_cnes(df)["CNES"]) == ["A", "C"]


class TestClassificarGrupo:
    def test_cid_curto_ou_ausente_fica_sem_grupo(self):
        df = pd.DataFrame(
            {
                "DT_INTER": ["20240110"] * 3,
                "DT_SAIDA": ["20240112"] * 3,
                "IDADE": ["30"] * 3,
                "COD_IDADE": ["4"] * 3,
                "SEXO": ["1"] * 3,
                "DIAG_PRINC": ["A0", None, "a090"],
                "MORTE": [0] * 3,
                "DIAS_PERM": [2] * 3,
            }
        )
        grupos = padronizar_sih(df)["grupo_agravo"]
        assert pd.isna(grupos.iloc[0])
        assert pd.isna(grupos.iloc[1])
        assert grupos.iloc[2] == "Feco-oral"


class TestPadronizarSisagua:
    def _df(self):
        return pd.DataFrame(
            {
                "DT_COLETA": ["2024-03-15", "2024-04-02", "data ruim"],
                "PARAMETRO": [
                    "Cloro residual livre (mg/L)",
                    "Escherichia coli",
                    "Cor Aparente (uH)",
                ],
                "RESULTADO": ["0,15", " presente ", "5"],
                "NO_AREA": [" rio verde ", "CENTRO", ""],
            }
        )

    def test_separa_numero_de_texto(self):
        resultado = padronizar_sisagua(self._df())
        assert resultado["resultado_numerico"].iloc[0] == 0.15
        assert pd.isna(resultado["resultado_numerico"].iloc[1])
        assert resultado["resultado_numerico"].iloc[2] == 5.0
        assert resultado["resultado_texto"].iloc[1] == "PRESENTE"

    def test_tipo_de_parametro(self):
        resultado = padronizar_sisagua(self._df())
        assert list(resultado["tipo_parametro"]) == ["numerico", "microbiologico", "outro"]

    def test_data_ano_mes_e_area(self):
        resultado = padronizar_sisagua(self._df())
        assert list(resultado["ano"].iloc[:2]) == [2024, 2024]
        assert list(resultado["mes"].iloc[:2]) == [3, 4]
        assert pd.isna(resultado["DT_COLETA"].iloc[2])
        assert list(resultado["NO_AREA"].iloc[:2]) == ["RIO VERDE", "CENTRO"]
        assert pd.isna(resultado["NO_AREA"].iloc[2])

    def test_nao_modifica_original(self):
        df = self._df()
        copia = df.copy()
        padronizar_sisagua(df)
        pd.testing.assert_frame_equal(df, copia)


class TestPadronizarSinan:
    def test_data_idade_e_sexo(self):
        df = pd.DataFrame(
            {
                "DT_NOTIFIC": ["2024-05-10", "data ruim"],
                "DT_SIN_PRI": ["2024-05-08", "2024-05-01"],
                "NU_IDADE_N": ["4034", "3006"],
                "CS_SEXO": ["m", "F"],
            }
        )
        resultado = padronizar_sinan(df)
        assert resultado["ano"].iloc[0] == 2024
        assert resultado["mes"].iloc[0] == 5
        assert pd.isna(resultado["DT_NOTIFIC"].iloc[1])
        assert list(resultado["idade_anos"]) == [34, 0]
        assert list(resultado["faixa_etaria"].astype(str)) == ["30-39", "<1"]
        assert list(resultado["sexo"]) == ["Masculino", "Feminino"]

    def test_vazio_volta_vazio(self):
        assert padronizar_sinan(pd.DataFrame()).empty

    def test_classificacao_final_por_ficha(self):
        """Cada ficha com seus códigos (decisão 0001).

        CHIK 13 → confirmado; CHIK 1 → outro código (1 não é código da ficha);
        CHIK 5 → descartado; LEPT 1.0 (lido como float) → confirmado;
        LEPT vazio → sem classificação; ESQU e ANIM → ficha sem CLASSI_FIN.
        """
        df = pd.DataFrame(
            {
                "DT_NOTIFIC": ["2024-05-10"] * 7,
                "DT_SIN_PRI": ["2024-05-08"] * 7,
                "NU_IDADE_N": ["4034"] * 7,
                "CS_SEXO": ["M"] * 7,
                "agravo": ["Chikungunya"] * 3
                + ["Leptospirose"] * 2
                + ["Esquistossomose", "Acidente por animal peçonhento"],
                "CLASSI_FIN": ["13", "1", "5", 1.0, None, None, None],
            }
        )
        resultado = padronizar_sinan(df)
        assert list(resultado["classificacao"]) == [
            config.SINAN_CONFIRMADO,
            config.SINAN_OUTRO_CODIGO,
            config.SINAN_DESCARTADO,
            config.SINAN_CONFIRMADO,
            config.SINAN_SEM_CLASSIFICACAO,
            config.SINAN_FICHA_SEM_CLASSI,
            config.SINAN_FICHA_SEM_CLASSI,
        ]


class TestPadronizarPopulacao:
    def test_booleanos_numeros_e_ultima_linha_do_ano(self, monkeypatch):
        """Solução 1 tem duas linhas em 2024: fica a última (DESINFECCAO NÃO, 300).

        A linha de 2020 sai por estar fora de config.ANOS.
        """
        monkeypatch.setattr(config, "ANOS", [2023, 2024])
        df = pd.DataFrame(
            {
                "NU_ANO": ["2024", "2024", "2023", "2020"],
                "NU_SOLUCAO_ABASTECIMENTO": [" 1 ", "1", "2", "3"],
                "DESINFECCAO": ["SIM", "NÃO", "nao", "SIM"],
                "NU_VALOR_POPULACAO_ESTIMADA": ["100", "300", "x", "50"],
            }
        )
        resultado = padronizar_populacao(df)
        assert list(resultado["NU_SOLUCAO_ABASTECIMENTO"]) == ["1", "2"]
        assert list(resultado["ano"]) == [2024, 2023]
        assert list(resultado["DESINFECCAO"]) == [False, False]
        assert resultado["NU_VALOR_POPULACAO_ESTIMADA"].iloc[0] == 300
        assert pd.isna(resultado["NU_VALOR_POPULACAO_ESTIMADA"].iloc[1])

    def test_vazio_volta_vazio(self):
        assert padronizar_populacao(pd.DataFrame()).empty

    def test_registra_a_deduplicacao(self, monkeypatch):
        """3 linhas em 2023, a solução 1 repetida: 3 → 2, descarte."""
        monkeypatch.setattr(config, "ANOS", [2023])
        proveniencia.reiniciar()
        df = pd.DataFrame({"NU_ANO": ["2023"] * 3, "NU_SOLUCAO_ABASTECIMENTO": ["1", "1", "2"]})
        padronizar_populacao(df)
        dedup = [
            (e["tipo"], e["motivo"], e["antes"], e["depois"])
            for e in proveniencia.resumo()["etapas"]
            if e["etapa"] == "SISAGUA cadastro: dedup"
        ]
        assert dedup == [("descarte", "deduplicação: última linha por solução e ano", 3, 2)]


class TestPadronizarCnes:
    def test_booleanos_e_tipo_de_unidade(self):
        df = pd.DataFrame(
            {
                "CNES": [" 001 ", "002"],
                "CODUFMUN": ["150553", "150553"],
                "TP_UNID": ["05", "99"],
                "VINC_SUS": ["1", "0"],
                "LEITHOSP": ["1", "0"],
                "URGEMERG": [1, 0],
            }
        )
        resultado = padronizar_cnes(df)
        assert list(resultado["CNES"]) == ["001", "002"]
        assert list(resultado["VINC_SUS"]) == [True, False]
        assert list(resultado["URGEMERG"]) == [True, False]
        assert list(resultado["tipo_unidade"]) == ["Hospital geral", "Tipo 99"]

    def test_vazio_volta_vazio(self):
        assert padronizar_cnes(pd.DataFrame()).empty


class TestFiltrarPeriodo:
    def test_inclui_as_duas_pontas(self, monkeypatch):
        monkeypatch.setattr(config, "PERIODO_INICIO", date(2023, 1, 1))
        monkeypatch.setattr(config, "PERIODO_FIM", date(2026, 6, 30))
        df = pd.DataFrame(
            {"data": pd.to_datetime(["2022-12-31", "2023-01-01", "2026-06-30", "2026-07-01"])}
        )
        resultado = filtrar_periodo(df, "data")
        assert list(resultado["data"].dt.strftime("%Y-%m-%d")) == ["2023-01-01", "2026-06-30"]

    def test_registra_data_invalida_separada_de_fora_do_periodo(self, monkeypatch):
        monkeypatch.setattr(config, "PERIODO_INICIO", date(2023, 1, 1))
        monkeypatch.setattr(config, "PERIODO_FIM", date(2026, 6, 30))
        proveniencia.reiniciar()
        df = pd.DataFrame({"data": pd.to_datetime(["2022-05-01", None, "2024-01-01"])})
        filtrar_periodo(df, "data", fonte="SINAN")
        removidas = {e["motivo"]: e["antes"] - e["depois"] for e in proveniencia.resumo()["etapas"]}
        assert removidas == {"data inválida": 1, "data fora do período": 1}

    def test_registra_antes_e_depois_de_cada_passo(self, monkeypatch):
        """5 linhas: 1 sem data (sai antes), 2 fora do período; ficam 2."""
        monkeypatch.setattr(config, "PERIODO_INICIO", date(2023, 1, 1))
        monkeypatch.setattr(config, "PERIODO_FIM", date(2026, 6, 30))
        proveniencia.reiniciar()
        df = pd.DataFrame(
            {"data": pd.to_datetime(["2022-05-01", None, "2024-01-01", "2026-07-01", "2025-03-15"])}
        )
        resultado = filtrar_periodo(df, "data", fonte="SIH")
        etapas = [
            (e["etapa"], e["tipo"], e["antes"], e["depois"])
            for e in proveniencia.resumo()["etapas"]
        ]
        assert etapas == [
            ("SIH: período", "descarte", 5, 4),
            ("SIH: período", "recorte", 4, 2),
        ]
        assert len(resultado) == 2


class TestSim:
    def test_idade_sim(self):
        """405 = 5 anos; 310 = 10 meses -> 0; 215 = 15 dias -> 0; 502 = 102 anos."""
        entrada = pd.Series(["405", "310", "215", "502", "999"])
        resultado = list(idade_sim_em_anos(entrada))
        assert resultado[:4] == [5, 0, 0, 102]
        assert pd.isna(resultado[4])

    def test_idade_sim_000_e_ignorada_e_020_e_minuto(self):
        """000 = idade ignorada (NaN), não menor de 1 ano; 020 = 20 minutos -> 0."""
        resultado = list(idade_sim_em_anos(pd.Series(["000", "020"])))
        assert pd.isna(resultado[0])
        assert resultado[1] == 0

    def test_padronizar_data_e_grupo(self):
        df = pd.DataFrame(
            {
                "CAUSABAS": ["A090", "I219"],
                "CODMUNRES": ["150553", "150553"],
                "DTOBITO": ["5032024", "31122024"],
                "IDADE": ["301", "480"],
                "SEXO": ["1", "2"],
            }
        )
        df.attrs["anos"] = [2024]
        resultado = padronizar_sim(df)
        assert list(resultado["DTOBITO"].dt.strftime("%Y-%m-%d")) == ["2024-03-05", "2024-12-31"]
        assert resultado["grupo_agravo"].iloc[0] == "Feco-oral"
        assert pd.isna(resultado["grupo_agravo"].iloc[1])
        assert resultado["faixa_etaria"].astype(str).iloc[0] == "<1"
        assert resultado.attrs["anos"] == [2024]

    def test_vazio_mantem_anos(self):
        df = pd.DataFrame()
        df.attrs["anos"] = [2024]
        resultado = padronizar_sim(df)
        assert resultado.empty
        assert resultado.attrs["anos"] == [2024]


class TestRegistrarEtapa:
    def test_devolve_removidas_e_anota_antes_e_depois(self):
        """10 linhas entram, 7 saem: 3 removidas."""
        proveniencia.reiniciar()
        assert registrar_etapa("SIH: tipo de AIH", "AIH diferente do tipo 1", 10, 7) == 3
        assert proveniencia.resumo()["etapas"] == [
            {
                "etapa": "SIH: tipo de AIH",
                "tipo": "descarte",
                "motivo": "AIH diferente do tipo 1",
                "antes": 10,
                "depois": 7,
            }
        ]

    def test_etapa_sem_remocao_tambem_e_anotada(self):
        proveniencia.reiniciar()
        assert registrar_etapa("CNES: município", "outro município", 4, 4, "recorte") == 0
        assert len(proveniencia.resumo()["etapas"]) == 1

    @pytest.mark.parametrize(("antes", "depois"), [(3, 4), (3, -1)])
    def test_contagem_impossivel_para_com_erro(self, antes, depois):
        with pytest.raises(ValueError, match="depois"):
            registrar_etapa("SIH: período", "x", antes, depois)

    def test_tipo_desconhecido_para_com_erro(self):
        with pytest.raises(ValueError, match="Tipo"):
            registrar_etapa("SIH: período", "x", 3, 2, tipo="perda")

    def test_filtros_de_escopo_sao_recorte(self):
        """Município e grupo de agravo tiram linhas fora do escopo, não dado inválido."""
        proveniencia.reiniciar()
        sih = pd.DataFrame(
            {
                "MUNIC_RES": [config.MUNICIPIO_IBGE_6_STR, "150010", config.MUNICIPIO_IBGE_6_STR],
                "grupo_agravo": ["Diarreia", None, None],
            }
        )
        filtrar_agravos(filtrar_municipio_sih(sih))
        etapas = [
            (e["etapa"], e["tipo"], e["antes"], e["depois"])
            for e in proveniencia.resumo()["etapas"]
        ]
        assert etapas == [
            ("SIH: município", "recorte", 3, 2),
            ("SIH: grupo de agravo", "recorte", 2, 1),
        ]
