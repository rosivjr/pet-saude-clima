"""
Baixa do Zenodo (config.DDA_ZENODO_REGISTRO) os parquets do Sivep-DDA dos anos
de config.DDA_ANOS e o dicionário das colunas, cada um com o JSON de
proveniência ao lado, em data/raw.
"""

import json
from pathlib import Path

import requests

from dda import comum
from src import config, proveniencia


def baixar(arquivo_deposito: dict) -> Path:
    """Baixa um arquivo do depósito e grava a proveniência no momento do download."""
    url = arquivo_deposito["links"]["self"]
    resposta = requests.get(url, timeout=300)
    resposta.raise_for_status()
    caminho = comum.BRUTOS / arquivo_deposito["key"]
    caminho.write_bytes(resposta.content)
    # Linhas de um Parquet pelos metadados, sem carregar os dados; o zip fica sem contagem.
    registro = proveniencia.registro_download(caminho, config.DDA_ZENODO_DOI, url)
    (comum.BRUTOS / f"{caminho.stem}_proveniencia.json").write_text(
        json.dumps(registro, indent=2, ensure_ascii=False)
    )
    print("baixado:", arquivo_deposito["key"])
    return caminho


def main() -> None:
    deposito = requests.get(config.DDA_ZENODO_REGISTRO, timeout=60).json()

    print("Arquivos no depósito:")
    for arquivo_deposito in deposito["files"]:
        print(arquivo_deposito["key"], arquivo_deposito["size"])

    comum.BRUTOS.mkdir(parents=True, exist_ok=True)

    for arquivo_deposito in deposito["files"]:
        nome = arquivo_deposito["key"]
        if nome.endswith(".parquet") and any(str(ano) in nome for ano in config.DDA_ANOS):
            baixar(arquivo_deposito)

    # Dicionário das colunas: o zip fica em data/raw e o conteúdo vai para data/interim
    for arquivo_deposito in deposito["files"]:
        if arquivo_deposito["key"] == comum.ZIP_DICIONARIO.name:
            baixar(arquivo_deposito)
            print("Arquivos do dicionário:", comum.extrair_dicionario())


if __name__ == "__main__":
    main()
