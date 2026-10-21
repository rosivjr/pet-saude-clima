# Segurança do repositório

Modelagem STRIDE das três ameaças que mais pesam neste projeto: vazamento de microdados, alteração de dado bruto e dependência maliciosa. Para cada uma, o que já mitiga e o que falta.

## Ameaças

| Ameaça | STRIDE | O que mitiga hoje | O que falta |
|---|---|---|---|
| Vazamento de microdados | Information disclosure | `data/`, `outputs/`, `figuras/`, `relatorio.txt` e as extensões de dado (`*.csv`, `*.parquet`, `*.dbc`, `*.xlsx`) estão no `.gitignore`. Os scripts imprimem só agregados (regra do `CONTRIBUTING.md`). Os testes usam só dados sintéticos. O repositório é público e foi publicado sem o histórico do repositório privado anterior. | Contagens de 1 ou 2 casos por ano podem identificar uma pessoa. A supressão (contagens de 1 a 4 viram "menos de 5") foi feita nos documentos versionados; o relatório gerado continua fora do repositório. A regra de contagens pequenas precisa valer também para as taxas: taxa e população juntas revelam a contagem (0,10 por 100 mil em cerca de 1 milhão de pessoas-ano é 1 caso). Ou a contagem e a taxa são suprimidas juntas, ou o período é agregado até a contagem passar do limite. O `.gitignore` não impede um `git add -f`. O `relatorio.txt` de 09/09/2026 estava no histórico do repositório privado, do commit `bd079e9` ao `5f85520`; por isso, o repositório público foi publicado sem esse histórico. |
| Alteração de dado bruto | Tampering | O pipeline só escreve em `data/raw/` ao baixar a série de chuva (`clima/precipitacao_diaria.csv`, com um JSON ao lado), e só quando o arquivo ainda não existe; os demais arquivos são apenas lidos. Cada execução grava, em `outputs/proveniencia/`, o SHA-256 de cada arquivo lido. A decisão 0017 registra o SHA-256 dos CSVs do SISAGUA. `sinan/baixar_sinan.py` não sobrescreve e confere o SHA-256 do arquivo que já existe. | `dda/baixar_dda.py` e `sih/baixar_sih.py` sobrescrevem o arquivo se rodados de novo. Nada confere, antes de uma execução, se os hashes ainda batem com os registrados. |
| Dependência maliciosa | Tampering, Elevation of privilege | `uv.lock` com o hash de cada pacote, instalado com `uv sync --locked`. `pip-audit` no CI. Dependabot semanal com 7 dias de espera para versões novas. Actions fixadas pelo SHA completo, com `permissions: contents: read` e `persist-credentials: false`. O binário do Gitleaks é conferido contra o `checksums.txt` e contra um hash fixo no workflow. | O `pip-audit` acusa só vulnerabilidades já publicadas; um pacote malicioso ainda sem alerta passa. |

O Gitleaks procura segredos (senhas, tokens, chaves), não microdados. Ele não protege contra a primeira ameaça.

## Vulnerabilidades ignoradas temporariamente no CI

Desde 20/10/2026, o passo "Vulnerabilidades conhecidas" do CI ignora 9 IDs (`--ignore-vuln`). As versões corrigidas saíram há menos de 7 dias, e o projeto espera esse prazo (o cooldown do Dependabot) antes de adotar uma versão nova, para não pegar uma release comprometida no dia em que sai. Cada ID, a data da correção e a data limite para remover a exceção estão no comentário do passo, em `.github/workflows/ci.yml`.

| Pacote | IDs | Correção (publicada no PyPI) | Remover até | Por que o risco é baixo até lá |
|---|---|---|---|---|
| `pillow` 12.3.0 | 8 CVEs (CVE-2026-112395, -112397, -112400, -112404, -112895, -112896, -112897, -112899) | 13.0.0 (16/10/2026) | 23/10/2026 | O projeto só usa o Pillow pelo matplotlib, para gravar em PNG as próprias figuras. As falhas estão na leitura de PDF, GIF, TIFF e EPS, no encoder de TIFF e no ImageMorph, que o projeto não usa: nenhuma imagem de fora é aberta. |
| `certifi` 2026.7.22 | GHSA-6q48-6c7w-9gw2 | 2026.10.19 (20/10/2026) | 27/10/2026 | A falha é uma autoridade certificadora comprometida, que permitiria interceptar conexões HTTPS. O `certifi` só valida os downloads: PySUS (espelho S3 do projeto PySUS, `PYSUS_SOURCE = "catalog"`), Open-Meteo (precipitação) e Zenodo (`dda/baixar_dda.py`). Até a atualização, não rodar os alvos de download (`make baixar-*`). Os arquivos já baixados têm o SHA-256 registrado na proveniência. |

Em 20/10/2026 não havia `pillow` 12.x corrigido: a última 12.x é a 12.3.0, afetada. Se sair uma 12.x corrigida, a atualização deve preferi-la à 13, que é versão maior e pode mudar os bytes dos PNG gerados.

Checagem de 21/10/2026, na API JSON do PyPI: nenhuma das duas correções tinha 7 dias. Não saiu `pillow` 12.x nova (a última 12.x continua a 12.3.0, de 01/07/2026), e a `certifi` mais nova continua a 2026.10.19, de 20/10/2026. A atualização fica em dois PRs separados, cada um na sua data:

- **23/10/2026: `pillow` 13.0.0**, ou uma 12.x corrigida que tenha saído até lá e tenha 7 dias;
- **27/10/2026: `certifi` 2026.10.19** ou posterior com 7 dias.

Cada PR precisa também mudar a trava do pacote em `constraint-dependencies` (`pyproject.toml`: `pillow==12.3.0` e `certifi==2026.7.22`). Sem isso, `uv lock --upgrade-package` não sai da versão travada. O PR tira os `--ignore-vuln` do pacote no `ci.yml`, roda testes e relatório e compara os hashes das figuras (o Pillow grava os PNG).

Desde 21/10/2026 o `main.py` lê do cache local os arquivos do PySUS que já existem (`docs/dados.md`), mas ainda consulta o espelho do PySUS por HTTPS para os arquivos que faltam (por exemplo, meses do SIH ainda não publicados). Até a atualização do `certifi`, essa consulta passa pela cadeia de certificados afetada. Os arquivos já baixados continuam conferidos pelo SHA-256.

## Incidente

Em caso de vazamento de microdados ou de outro incidente com dados (por exemplo, um arquivo de `data/` enviado ao GitHub), Rosival avisa a coordenação do projeto assim que perceber. A coordenação decide se e como o incidente é comunicado à Autoridade Nacional de Proteção de Dados (ANPD).

## Manutenção manual

O Dependabot atualiza o `uv.lock` (e, com ele, o Ruff do pre-commit e o `pip-audit` do CI) e as actions. Ele não atualiza o Gitleaks, que tem versão fixa em dois lugares: no `rev` do `.pre-commit-config.yaml` e no passo "Gitleaks" do `.github/workflows/ci.yml`, junto com o SHA-256 do tarball. Ao trocar de versão, mude os dois e tire o novo hash do `checksums.txt` da release.

## Dados brutos

**A implantar.** Os dados brutos são públicos, mas mudam com as atualizações do DATASUS e do SISAGUA. Uma cópia de `data/raw/` é guardada fora do computador de trabalho antes de cada entrega com números novos; o SHA-256 de cada arquivo, nos JSONs de proveniência e na decisão 0017, identifica a versão usada.
