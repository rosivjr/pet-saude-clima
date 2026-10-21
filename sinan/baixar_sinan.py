"""Copia o Sinan hepatites (HEPA) do cache do PySUS para data/raw/sinan, com proveniência.

Para localizar o arquivo, o script chama o PySUS, que pode baixá-lo de novo
para o cache mesmo quando ele já está lá (aconteceu com o HEPABR22).
"""

import json
import shutil
import sys
from datetime import datetime
from importlib.metadata import version
from pathlib import Path

import pysus

from src import config, proveniencia

DESTINO = config.DADOS_BRUTOS / "sinan"


def _json(arquivo: Path) -> Path:
    return DESTINO / f"{arquivo.stem}_proveniencia.json"


def conferir(arquivo: Path) -> bool:
    """Confere o SHA-256 de um arquivo já em data/raw com o registrado no JSON."""
    caminho_json = _json(arquivo)
    if not caminho_json.exists():
        print(f"ATENÇÃO: {arquivo.name} existe sem {caminho_json.name}; nada foi alterado.")
        return False
    registrado = json.loads(caminho_json.read_text())["sha256"]
    if proveniencia.sha256(arquivo) != registrado:
        print(f"ATENÇÃO: {arquivo.name} difere do SHA-256 registrado; nada foi alterado.")
        return False
    print(f"já existe, SHA-256 confere: {arquivo.name}")
    return True


def salvar(origem: Path, ano: int) -> bool:
    """Copia o arquivo do cache do PySUS para data/raw e grava a proveniência ao lado."""
    arquivo = DESTINO / origem.name
    if arquivo.exists():
        # data/raw não muda: para trocar a versão, apague o arquivo e o JSON à mão.
        return conferir(arquivo)
    (shutil.copytree if origem.is_dir() else shutil.copy2)(origem, arquivo)
    # O PySUS grava o arquivo no cache quando o baixa: a data do arquivo é a do download.
    registro = proveniencia.registro_download(
        arquivo,
        f"DATASUS, Sinan hepatites virais (HEPA), via PySUS {version('pysus')}",
        (
            f"{config.PYSUS_ENDERECOS[config.PYSUS_SOURCE]}; "
            f"pysus.ftp.sinan(disease=HEPA, year={ano})"
        ),
        baixado_em=proveniencia.data_do_arquivo(origem),
    )
    registro |= {
        "obtencao": (
            "Copiado do cache local do PySUS. Para localizar o arquivo, o script chama "
            "pysus.ftp.sinan, que pode baixá-lo de novo da origem abaixo mesmo quando "
            "ele já está no cache; baixado_em é a data do arquivo no cache depois "
            "dessa chamada."
        ),
        "cache_pysus": str(origem),
        "copiado_em": datetime.now(proveniencia.FUSO).isoformat(timespec="seconds"),
    }
    _json(arquivo).write_text(json.dumps(registro, indent=2, ensure_ascii=False))
    print(
        f"copiado: {arquivo.name}, {registro['linhas']} linhas, baixado em {registro['baixado_em']}"
    )
    return True


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    tudo_certo = True
    for ano in config.SINAN_HEPATITE_ANOS:
        for caminho in pysus.ftp.sinan(disease="HEPA", year=ano, source=config.PYSUS_SOURCE):
            tudo_certo &= salvar(Path(caminho), ano)
    if not tudo_certo:
        sys.exit(1)


if __name__ == "__main__":
    main()
