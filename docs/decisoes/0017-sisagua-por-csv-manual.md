# 0017. SISAGUA baixado manualmente em CSV, não pelo PySUS

**Status:** Aceita
**Registro:** 2026-10-20

## Contexto

O SIH, o SINAN e o CNES são baixados pelo PySUS, que também registra a origem de cada arquivo. O PySUS tem acesso ao SISAGUA, mas, nos testes do projeto, esse acesso se mostrou instável: os índices dos arquivos mudavam e o cache ficava em /tmp, apagado ao reiniciar a máquina (registro no antigo `docs/estado_projeto.md`, commit `169139c`). O Portal de Dados Abertos do Ministério da Saúde publica o SISAGUA em CSV, um arquivo por ano.

## Decisão

Os arquivos do SISAGUA são baixados à mão de dadosabertos.saude.gov.br e salvos em `data/raw/` com nomes fixos:

- qualidade: `sisagua_2023.csv` a `sisagua_2026.csv` (dataset "SISAGUA - Vigilância Parâmetros Básicos");
- cadastro das soluções de abastecimento: `sisagua_populacao.csv`.

`carregar_sisagua` e o carregador do cadastro (`src/carregadores.py`) leem esses arquivos em blocos, só com as colunas usadas e só as linhas do município, e registram cada arquivo na proveniência da execução.

## Alternativas

- **PySUS.** Automatiza o download, mas foi instável nos testes.
- **Download automático direto do portal.** Possível no futuro; exige fixar o endereço de cada arquivo e gravar a proveniência do download.

## Consequências

- Quem for reproduzir o estudo precisa baixar esses arquivos à mão (RECORD 12.1). O README lista os nomes em "Arquivos a baixar manualmente".
- Sem um arquivo de ano, a execução para com erro de arquivo ausente, porque o SISAGUA é a base do perfil sanitário.
- A data do download não fica registrada automaticamente; a proveniência de cada execução registra o arquivo no momento da leitura. O registro manual em "Arquivos usados" guarda o SHA-256 e a data de modificação de cada CSV, que é a do download se o arquivo não foi alterado depois.

## Arquivos usados

Versão dos CSVs em `data/raw/` usada nas análises, com a data de modificação de cada arquivo (registro de 20/10/2026):

| Arquivo | Data do arquivo | SHA-256 |
|---|---|---|
| `sisagua_2023.csv` | 18/09/2026 | `93b929c938b4e92bc468de550d20a24dc48761c292ceb93532e604583e9a5c64` |
| `sisagua_2024.csv` | 18/09/2026 | `7806fb940af9075cba4b474e550bbd0c64566b55838fb401c881a7cb842579ec` |
| `sisagua_2025.csv` | 04/09/2026 | `a10c1031d142d53254b2ea40d7fc7b0fd3b61ff665a19133071da184373ce82f` |
| `sisagua_2026.csv` | 04/09/2026 | `a1a09d5381483714f5d3175b0364018a75e1a09c9ef24e64eff2186e2657dead` |
| `sisagua_populacao.csv` | 15/09/2026 | `c8c283f0c5f407f483078ce1a2510718514eb40cc52092f643893ad80eb785fa` |

Quem baixar os arquivos de novo pode conferir com `sha256sum`. Um hash diferente indica outra versão publicada pelo portal, e os números podem mudar.

## Fonte

- Ministério da Saúde. Portal de Dados Abertos (dadosabertos.saude.gov.br), dataset SISAGUA.
- Benchimol EI et al. The REporting of studies Conducted using Observational Routinely-collected health Data (RECORD) statement. PLoS Med. 2015;12(10):e1001885 (item 12.1).
- Registro sobre o PySUS: `docs/estado_projeto.md` no commit `169139c`; o arquivo foi removido no commit `0d88e24`.
