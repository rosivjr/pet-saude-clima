# Como contribuir

PET-Saúde CLIMA, Eixo II: análise descritiva e ecológica de agravos
relacionados à água (DRSAI) e da qualidade da água para consumo humano em
Parauapebas (PA), com dados públicos do SUS. O estudo não estabelece
causalidade; achados são coincidências temporais/territoriais, nunca
conclusões sobre indivíduos. Código, nomes e mensagens são em português.

## Fluxo

Abra um PR; o CI precisa passar. Antes, rode:

```
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## Comandos

- Testes: `uv run pytest`
- Um teste: `uv run pytest tests/indicadores/test_agua.py::nome_do_teste`
- Pipeline completo: `uv run python main.py > relatorio.txt`
  (o relatório vai para stdout e o log para stderr; figuras saem em `figuras/`)

Lint: `uv run ruff check .` (formatação: `uv run ruff format .`). Não há build configurado.

## Arquitetura

Pipeline linear orquestrado por `main.py`: carregar → transformar → calcular
→ apresentar. Cada módulo de `src/` tem uma única responsabilidade e eles só
se comunicam pelos DataFrames/dataclasses que passam de um para o outro:

- `config.py` — única fonte de constantes: município (código IBGE em 7
  dígitos e DATASUS em 6, como int e como texto), `ANOS`, população,
  listas CID-10 por grupo DRSAI, agravos do SINAN, tipos CNES, limites da
  Portaria GM/MS nº 888/2021, faixas etárias e caminhos `data/raw|interim|processed`.
- `carregadores.py` — acessa as fontes (SIH, SINAN, SIM e CNES via PySUS;
  SISAGUA, Censo 2022 do SIDRA e SINISA em arquivos baixados à mão para
  `data/raw/`; chuva pela API do Open-Meteo), sem filtrar conteúdo. CSVs
  grandes são lidos em blocos com filtro de município durante a leitura.
- `proveniencia.py` — registra, por execução, cada arquivo lido (origem, data,
  linhas, SHA-256), o que ficou indisponível e as etapas de filtro.
- `transformacoes.py` — padroniza e filtra (`padronizar_*`, `filtrar_*`), não calcula.
- `validacao.py` — valida com pandera a estrutura das tabelas padronizadas.
- `qualidade.py` — avalia completitude, consistência e duplicidade, sem
  alterar registros.
- `estatistica.py` — funções estatísticas: pessoa-tempo, taxa, IC exato de
  Garwood, IC de Wilson e razão de taxas.
- `indicadores/` — calcula; não acessa fontes. Retorna DataFrames ou
  dataclasses (`PerfilAgravo`, `ResultadoConformidade`, etc.). Um submódulo
  por assunto: `agua`, `internacoes`, `notificacoes`, `territorio`,
  `abastecimento`, `rede`, `saneamento`, `sazonalidade`, `mortalidade`,
  `sensibilidade`; o que é usado por vários fica em `_comum` (pessoa-tempo
  do período e dos meses comuns, anos parciais, percentuais com IC de Wilson
  sobre `estatistica.ic_wilson`). Constantes, como `ROTULO_DRSAI` e
  `PARAMETRO_CLORO`, vêm direto do `config`.
- `relatorio/` — só formata texto (`secao_*`), não calcula. Os mesmos
  assuntos de `indicadores/`, mais `geral` (cabeçalho, lacunas, qualidade
  dos dados, proveniência, rodapé) e `_formato` (números, IC, datas, títulos).
- `graficos.py` — só gera figuras a partir de resultados já calculados.

Nos dois pacotes, o `__init__.py` só reexporta: o `__all__` lista os nomes
públicos, e quem usa importa do pacote (`from src.indicadores import ...`).
Os submódulos importam uns dos outros pelo caminho relativo (`from ._comum
import ...`), nunca pelo pacote, para não criar import circular.

Detalhes de domínio que exigem ler vários arquivos para entender:
- CIDs são comparados pelos 3 primeiros caracteres (o SIH grava `A090` para A09.0).
  Cada internação recebe um único grupo; só os grupos de `GRUPOS_DRSAI` entram
  no indicador DRSAI.
- O recorte temporal do SIH é por `DT_INTER`, não pela competência do arquivo.
- Comparações entre anos usam só os meses comuns a todos os anos
  (`meses_comuns`), com a pessoa-tempo desses meses e a razão de taxas
  contra o primeiro ano (`razao_taxas`); a taxa anualizada de cada ano
  (`pessoa_tempo_por_ano`) fica só como descrição, com o ano parcial
  marcado. A sensibilidade refaz os indicadores sem o ano parcial
  (`sensibilidade_sem_ano_parcial`), passando o fim do período como
  argumento, sem alterar `config.PERIODO_FIM`. Ver decisões 0006 e 0008.
- No SISAGUA, `RESULTADO` mistura números com vírgula decimal e texto
  (PRESENTE/AUSENTE); a transformação separa em `resultado_numerico` e
  `resultado_texto`. Qualidade e cadastro se ligam por `NU_SOLUCAO_ABASTECIMENTO`.

## Regras obrigatórias

- Nunca alterar nada em `data/raw`.
- Nunca imprimir registros individuais; scripts mostram só agregados.
- Nunca carregar arquivos nacionais inteiros (limite de 24 GB de RAM): ler só
  as colunas e o município necessários.
- `config.py` é a única fonte de constantes e códigos CID; não repetir valores em outro lugar.
- Respeitar a responsabilidade de cada módulo descrita acima.
- Toda função de cálculo nova precisa de teste com valor feito à mão.
- Critérios vêm de normas oficiais (FUNASA, Portaria 888/2021, Portaria SAS/MS
  221/2008); não inventar critérios novos; a única exceção aprovada é a decisão
  0021, justificada por análise de sensibilidade.

## Regras de dados e estatística

- Testes usam apenas dados sintéticos criados no próprio teste; nunca arquivos de `data/`.
- Toda taxa leva intervalo de confiança exato de Poisson (Garwood). O denominador é a
  população do IBGE do ano; se o período não for um ano completo, usar pessoa-tempo.
- Toda proporção leva intervalo de confiança de Wilson (`ic_wilson`), exceto contagens
  completas de cadastro ou estrutura, justificadas no metodos.md.
- Dados de 2025 e 2026 do SINAN e do SIH são preliminares: todo relatório informa a
  data de extração.
- Código novo de download salva o arquivo em `data/raw/` com um JSON de proveniência
  (fonte, origem no PySUS — espelho ou servidor original —, data, número de linhas e SHA-256).
- Método estatístico novo só entra se estiver no plano de análise; na dúvida, abra uma
  issue antes.
