# STROBE e RECORD item a item

Onde cada item do STROBE (von Elm et al., 2007) e cada item próprio do RECORD (Benchimol et al., 2015) é atendido neste projeto, e o que ainda falta. As referências completas estão em `docs/metodos.md`.

Siglas dos lugares citados:

- **Métodos:** `docs/metodos.md`, pelo título da seção;
- **Relatório:** `relatorio.txt`, gerado por `main.py`, pelo número da seção;
- **Decisão NNNN:** `docs/decisoes/NNNN-*.md`.

Ainda não há manuscrito. Os itens de título, resumo e discussão ficam marcados como pendentes até ele existir.

## Título e resumo

| Item | Onde está atendido | O que falta |
|---|---|---|
| 1a. Desenho indicado no título ou no resumo | — | Manuscrito: título com "estudo ecológico descritivo". |
| 1b. Resumo informativo e equilibrado | — | Manuscrito: resumo. |
| RECORD 1.1. Tipo de dado e nomes das bases no título ou no resumo | Cabeçalho do relatório, com todas as fontes: SIH/SUS, SINAN, SIM, CNES, SISAGUA, SINISA, Censo 2022 e precipitação (Open-Meteo) | Manuscrito: nomear as bases no título ou no resumo. |
| RECORD 1.2. Região geográfica e período no resumo | Cabeçalho do relatório (município, código IBGE, período) | Manuscrito: repetir no resumo. |
| RECORD 1.3. Ligação entre bases indicada no título ou no resumo | — | Manuscrito: dizer no resumo que a única ligação é a amostra–cadastro dentro do SISAGUA (decisão 0005). |

## Introdução

| Item | Onde está atendido | O que falta |
|---|---|---|
| 2. Contexto científico e justificativa | Métodos, "Pergunta (itens 2 e 3)" | Manuscrito: revisão da literatura sobre DRSAI e qualidade da água (`docs/referencias.md`). |
| 3. Objetivos | Métodos, "Pergunta (itens 2 e 3)" | — |

## Métodos

| Item | Onde está atendido | O que falta |
|---|---|---|
| 4. Desenho do estudo | Métodos, "Desenho (item 4)" | — |
| 5. Contexto: local, período, datas de coleta | Métodos, "Contexto e período (item 5)"; data de extração no JSON de proveniência e na seção 25 do relatório | — |
| 6. Participantes: critérios de seleção | Métodos, "Participantes (item 6 e RECORD 6.1 a 6.3)"; decisões 0001, 0003 e 0009 | Conferir no dicionário nacional o código de `CLASSI_FIN` de zika (decisão 0001). |
| RECORD 6.1. Códigos e algoritmos de seleção | Métodos, "Variáveis", tabela CID gerada de `src/config.py` e conferida por `tests/test_documentacao.py`; decisão 0004 | Conferência na fonte (responsável: Rosival): código de `CLASSI_FIN` de zika no dicionário nacional; os demais foram conferidos (decisão 0001). |
| RECORD 6.2. Estudos de validação dos códigos | Métodos, "Participantes": nenhum código foi validado contra prontuário em Parauapebas | Citar estudos brasileiros de validação da CID no SIH para os grupos DRSAI, se existirem. |
| RECORD 6.3. Ligação entre bases | Métodos, "Participantes"; decisão 0005 | — |
| 7. Variáveis: desfechos, exposições, covariáveis | Métodos, "Variáveis (item 7 e RECORD 7.1)" e "Critérios da Portaria GM/MS nº 888/2021" | — |
| RECORD 7.1. Lista completa dos códigos | Métodos, tabela entre os marcadores `cid:inicio` e `cid:fim` | Conferência na fonte (responsável: Rosival): códigos de geo-helmintos e teníases no documento da FUNASA (2010) (Métodos, "Limitações"). |
| 8. Fontes de dados e medição | Métodos, "Fontes e medição (item 8)" e "Critérios da Portaria GM/MS nº 888/2021"; proveniência em `src/proveniencia.py` | — |
| 9. Viés | Métodos, "Viés (item 9)" | — |
| 10. Tamanho do estudo | Métodos, "Tamanho do estudo (item 10)" | — |
| 11. Variáveis quantitativas | Métodos, "Variáveis quantitativas (item 11)" | Conferência na fonte (responsável: Rosival): significado de `COD_IDADE` nos dicionários de dados do DATASUS (Métodos, "Limitações"). |
| 12a. Métodos estatísticos | Métodos, "Métodos estatísticos (item 12 e RECORD 12.1 a 12.3)"; decisões 0002, 0006, 0008, 0018 e 0020 | — |
| 12b. Subgrupos e interações | Métodos, "Variáveis" (grupo, faixa etária, sexo, área, tipo de solução) | Não há análise de interação, e o desenho descritivo não a prevê. |
| 12c. Dados ausentes | Métodos, "Critérios da Portaria" (amostras sem resultado saem do denominador) e "Fontes e medição" (completitude); relatório, seção 23 | — |
| 12d. Estratégia de amostragem | Não se aplica: o estudo usa todos os registros do período (Métodos, "Tamanho do estudo") | — |
| 12e. Análises de sensibilidade | Métodos, "Análise de sensibilidade (item 12e)"; relatório, seção 24 | — |
| RECORD 12.1. Acesso à base | Métodos, "Métodos estatísticos": só dados públicos e anonimizados | — |
| RECORD 12.2. Limpeza dos dados | `src/transformacoes.py` (`registrar_etapa`); cada filtro na proveniência e no relatório, seção 25 ("Todas as etapas de filtro, inclusive as que removeram 0 linhas"), com descarte separado de recorte | — |
| RECORD 12.3. Ligação: método e qualidade | Métodos, "Métodos estatísticos"; decisão 0005; contagens da ligação no relatório, seções 12 (divergência de desinfecção) e 14 (origem da captação) | — |

## Resultados

| Item | Onde está atendido | O que falta |
|---|---|---|
| 13. Participantes: números em cada etapa | Relatório, seção 25 (arquivos lidos, indisponíveis e tabela de todas as etapas de filtro, com linhas antes e depois e descarte separado de recorte) e seção 7 (lacunas de dados e competência final da extração do SIH) | Manuscrito: desenhar o fluxograma a partir da tabela de etapas, que vai até o recorte do DRSAI. |
| RECORD 13.1. Seleção detalhada da população, com fluxograma | Relatório, seção 25, tabela de todas as etapas de filtro, por base (SIH, SINAN, SIM, SISAGUA, cadastro do SISAGUA e CNES) | Manuscrito: o mesmo fluxograma do item 13, por base. |
| 14. Dados descritivos | Relatório, seções 3 e 15 (idade), 12 (soluções de abastecimento), 13 (rede de atenção), 18 e 19 (saneamento) | Manuscrito: tabela descritiva única. |
| 15. Dados de desfecho | Relatório, seções 1, 2, 4, 5, 8 a 11, 16, 17 e 22 | — |
| 16. Principais resultados, com IC | Relatório, seções 1 e 16 (taxas com IC de Garwood e razão de taxas), 8 e 9 (proporções com IC de Wilson) | — (a comparação com o Pará padronizada por idade foi rejeitada para o relatório principal, decisão 0007). |
| 17. Outras análises | Relatório, seção 24 (sem o ano parcial); grupo "Sensibilidade" mostrado à parte nas seções 2 e 6 | — |

## Discussão

| Item | Onde está atendido | O que falta |
|---|---|---|
| 18. Resultados principais | — | Manuscrito. |
| 19. Limitações | Métodos, "Limitações (item 19 e RECORD 19.1)"; README, "O que o desenho permite e não permite concluir"; relatório, nota sobre as fontes | — |
| RECORD 19.1. Limitações do uso de dados não coletados para pesquisa | Métodos, "Limitações": sub-registro, uso de serviço em vez de ocorrência, cobertura só do SUS, dados preliminares, codificação de faturamento | — |
| 20. Interpretação | Métodos, "Desenho": coincidências são hipóteses, sem inferência causal nem conclusão sobre indivíduos | Manuscrito. |
| 21. Generalização | — | Manuscrito: discutir até onde os achados de um município minerador valem para outros contextos. |

## Outras informações

| Item | Onde está atendido | O que falta |
|---|---|---|
| 22. Financiamento | README, "Financiamento": o projeto foi submetido ao edital SGTES/MS nº 23/2026, do Programa de Educação pelo Trabalho para a Saúde (PET-Saúde) do Ministério da Saúde | Atualizar se o resultado do edital mudar a situação (o texto da proposta diz "submetido"). |
| RECORD 22.1. Acesso a protocolo, dados brutos e código | README, "Fontes", "Arquivos a baixar manualmente" e "Como rodar"; Métodos (plano de análise); `uv.lock` com as versões exatas | DOI do Zenodo para o código, na publicação em repositório novo (`docs/seguranca.md`). |
