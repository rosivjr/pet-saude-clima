"""
Registro de proveniência de cada execução.

Anota de onde veio cada dado lido, o que ficou indisponível e as linhas
antes e depois de cada filtro, e grava tudo num JSON por execução, para que duas execuções
com resultados diferentes possam ser comparadas arquivo por arquivo
(nome, tamanho, data de modificação, SHA-256, origem e data do download).
"""

import hashlib
import json
import logging
import platform
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import NamedTuple
from zoneinfo import ZoneInfo

import pyarrow.dataset as pads

from src import config

logger = logging.getLogger(__name__)

TAMANHO_BLOCO = 1024 * 1024  # leitura de 1 MB por vez no cálculo do hash
FUSO = ZoneInfo(config.FUSO_HORARIO)
# Valor gravado quando a origem ou a data do download não são conhecidas.
# A data da leitura nunca substitui a do download.
NAO_REGISTRADO = "não registrado"


def _agora() -> str:
    """Data e hora atuais no fuso do município, em ISO 8601 com o deslocamento."""
    return datetime.now(FUSO).isoformat(timespec="seconds")


@dataclass
class Registro:
    """Tudo o que uma execução leu, não encontrou e filtrou."""

    inicio: str = field(default_factory=_agora)
    arquivos: list[dict] = field(default_factory=list)
    indisponiveis: list[dict] = field(default_factory=list)
    etapas: list[dict] = field(default_factory=list)


class Extracao(NamedTuple):
    """Primeira e última data de extração dos arquivos de uma fonte."""

    primeira: date
    ultima: date
    do_download: bool  # False: ao menos uma data é a do arquivo, não a da extração


REGISTRO = Registro()


def reiniciar() -> None:
    """Começa um registro novo (uma execução do main.py)."""
    global REGISTRO  # noqa: PLW0603
    REGISTRO = Registro()


def sha256(caminho: Path) -> str:
    """
    SHA-256 de um arquivo ou de uma pasta, em hexadecimal.

    O PySUS pode devolver um Parquet como pasta com vários arquivos. Nesse
    caso, o hash combina nome relativo e conteúdo de cada arquivo, em
    ordem alfabética, para que o resultado não dependa da ordem de leitura.
    """
    caminho = Path(caminho)
    h = hashlib.sha256()

    arquivos = (
        [caminho] if caminho.is_file() else sorted(p for p in caminho.rglob("*") if p.is_file())
    )
    for arquivo in arquivos:
        if caminho.is_dir():
            h.update(str(arquivo.relative_to(caminho)).encode())
        with open(arquivo, "rb") as f:
            for bloco in iter(lambda: f.read(TAMANHO_BLOCO), b""):
                h.update(bloco)
    return h.hexdigest()


def _tamanho(caminho: Path) -> int:
    """Tamanho em bytes de um arquivo ou da soma de uma pasta."""
    if caminho.is_file():
        return caminho.stat().st_size
    return sum(p.stat().st_size for p in caminho.rglob("*") if p.is_file())


def data_do_arquivo(caminho: str | Path) -> str:
    """Data de modificação de um arquivo ou pasta, no fuso do município, em ISO 8601."""
    return datetime.fromtimestamp(Path(caminho).stat().st_mtime, FUSO).isoformat(timespec="seconds")


def registro_download(
    caminho: str | Path,
    fonte: str,
    origem: str,
    baixado_em: str | None = None,
    linhas: int | None = None,
) -> dict:
    """
    Monta o registro de proveniência de um arquivo baixado; quem chama grava o JSON.

    Devolve as chaves comuns a todos os scripts de download: arquivo (nome),
    fonte, origem (URL ou consulta), baixado_em, linhas e sha256; quem chama
    pode acrescentar as suas (ex.: cache_pysus no SIH, modelo na chuva). Sem
    baixado_em, vale a hora atual (download feito agora); para um arquivo do
    cache do PySUS, passe data_do_arquivo, que é a do download. Sem linhas, um
    Parquet (arquivo ou pasta) é contado pelos metadados; outro formato
    fica sem contagem (None).
    """
    caminho = Path(caminho)
    if linhas is None and caminho.suffix == ".parquet":
        linhas = pads.dataset(caminho, format="parquet").count_rows()
    return {
        "arquivo": caminho.name,
        "fonte": fonte,
        "origem": origem,
        "baixado_em": baixado_em or _agora(),
        "linhas": linhas,
        "sha256": sha256(caminho),
    }


def registrar_arquivo(
    fonte: str,
    caminho: str | Path,
    descricao: str = "",
    origem: str | None = None,
    baixado_em: str | None = None,
    leitura: str | None = None,
) -> None:
    """
    Anota um arquivo lido: nome, tamanho, data de modificação, SHA-256,
    origem e data do download.

    A fonte é o sistema de origem (SIH, SINAN, SISAGUA, CNES), e a descrição,
    um complemento livre (ex.: 'PA 2024-03 RD'). Sem origem (URL ou endereço)
    ou sem baixado_em (ISO 8601), o campo fica NAO_REGISTRADO. Falha ao
    calcular o hash não interrompe a análise; fica anotada. A leitura, quando
    dada, diz como o arquivo foi obtido nesta execução (ex.: do cache local,
    sem consulta ao servidor).
    """
    caminho = Path(caminho)
    entrada = {
        "fonte": fonte,
        "arquivo": caminho.name,
        "descricao": descricao,
        "origem": origem or NAO_REGISTRADO,
        "baixado_em": baixado_em or NAO_REGISTRADO,
    }
    if leitura:
        entrada["leitura"] = leitura
    try:
        entrada["bytes"] = _tamanho(caminho)
        entrada["modificado_em"] = data_do_arquivo(caminho)
        entrada["sha256"] = sha256(caminho)
    except OSError as erro:
        entrada["erro"] = type(erro).__name__
        logger.warning("Proveniência de %s incompleta: %s", caminho.name, erro)
    REGISTRO.arquivos.append(entrada)


def _extracao(arquivos: list[dict]) -> Extracao | None:
    """
    Regra única da data de extração, usada no relatório e nas figuras.

    Usa a data do download quando registrada e, se não, a data do arquivo.
    A data do arquivo muda quando ele é copiado, então o resultado marca
    do_download=False se alguma data usada for a do arquivo (decisão 0017).
    Recebe entradas de REGISTRO.arquivos; sem nenhuma data, devolve None.
    """
    datas, do_download = [], True
    for a in arquivos:
        if a["baixado_em"] != NAO_REGISTRADO:
            texto = a["baixado_em"]
        else:
            texto = a.get("modificado_em")
            do_download = False
        if texto:
            datas.append(datetime.fromisoformat(texto).date())
    return Extracao(min(datas), max(datas), do_download) if datas else None


def datas_de_extracao(*prefixos_fonte: str) -> Extracao | None:
    """
    Data de extração dos arquivos de uma ou mais fontes (regra em _extracao).

    Cada prefixo pega as fontes cujo nome começa com ele ('SISAGUA' pega
    também 'SISAGUA cadastro'); com mais de um, junta as datas de todas.
    Sem nenhuma data, devolve None.
    """
    return _extracao([a for a in REGISTRO.arquivos if a["fonte"].startswith(prefixos_fonte)])


def registrar_indisponivel(fonte: str, item: str, motivo: str) -> None:
    """Anota um arquivo esperado que não pôde ser obtido ou lido."""
    REGISTRO.indisponiveis.append({"fonte": fonte, "item": item, "motivo": motivo})


def registrar_etapa(etapa: str, tipo: str, motivo: str, antes: int, depois: int) -> None:
    """
    Anota as linhas antes e depois de um filtro, inclusive quando nada sai.

    Args:
        etapa: fonte e filtro (ex.: 'SIH, período').
        tipo: 'descarte' (dado inválido ou fora da regra) ou 'recorte'
              (fora do escopo do estudo, sem perda de dado).
        motivo: o que o filtro removeu.
        antes: linhas que entraram no filtro.
        depois: linhas que saíram dele.
    """
    REGISTRO.etapas.append(
        {
            "etapa": etapa,
            "tipo": tipo,
            "motivo": motivo,
            "antes": int(antes),
            "depois": int(depois),
        }
    )


def _versao(pacote: str) -> str:
    """Versão instalada de um pacote, ou 'não instalado'."""
    from importlib import metadata

    try:
        return metadata.version(pacote)
    except metadata.PackageNotFoundError:
        return "não instalado"


def resumo() -> dict:
    """Contagens do registro atual, para o relatório."""
    por_fonte: dict[str, int] = {}
    for a in REGISTRO.arquivos:
        por_fonte[a["fonte"]] = por_fonte.get(a["fonte"], 0) + 1
    extracao = {
        fonte: _extracao([a for a in REGISTRO.arquivos if a["fonte"] == fonte])
        for fonte in por_fonte
    }
    return {
        "inicio": REGISTRO.inicio,
        "arquivos_por_fonte": por_fonte,
        "extracao": extracao,
        "indisponiveis": list(REGISTRO.indisponiveis),
        "etapas": list(REGISTRO.etapas),
        "pysus": _versao("pysus"),
        "pysus_source": config.PYSUS_SOURCE,
    }


def salvar() -> Path:
    """Grava o registro da execução em JSON, em config.PROVENIENCIA."""
    pasta = config.PROVENIENCIA
    pasta.mkdir(parents=True, exist_ok=True)

    carimbo = datetime.fromisoformat(REGISTRO.inicio).strftime("%Y%m%dT%H%M%S")
    destino = pasta / f"proveniencia_{carimbo}.json"

    conteudo = {
        "execucao": {
            "inicio": REGISTRO.inicio,
            "fim": _agora(),
            "python": platform.python_version(),
            "pacotes": {p: _versao(p) for p in ("pysus", "pandas", "pyarrow", "scipy")},
            "pysus_source": config.PYSUS_SOURCE,
            "periodo": [str(config.PERIODO_INICIO), str(config.PERIODO_FIM)],
            "municipio_ibge": config.MUNICIPIO_IBGE_7,
        },
        **asdict(REGISTRO),
    }
    destino.write_text(json.dumps(conteudo, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Proveniência gravada em %s", destino)
    return destino
