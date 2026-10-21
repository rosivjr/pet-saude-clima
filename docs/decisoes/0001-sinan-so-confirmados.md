# 0001. Só casos confirmados no SINAN, com o total notificado ao lado

**Status:** Aceita (aplicada em 2026-10-19)
**Registro:** 2026-10-18

## Contexto

O SINAN recebe notificações de casos suspeitos. A classificação final de cada caso fica em `CLASSI_FIN`, preenchida depois da investigação. Uma notificação pode terminar confirmada, descartada ou inconclusiva, ou ficar sem classificação.

Até esta decisão, `perfil_notificacoes` (`src/indicadores/notificacoes.py`) contava todas as notificações de residentes no período, sem olhar `CLASSI_FIN`. A constante `SINAN_CLASSI_CONFIRMADO` existia em `src/config.py`, mas nenhum módulo a usava. Contar suspeitos descartados superestima a ocorrência, principalmente nas arboviroses (chikungunya e zika), em que a notificação por suspeita clínica é a regra.

Dois fatos já observados limitam a regra:

- o arquivo do agravo "Acidente por animal peçonhento" (ANIM) não traz `CLASSI_FIN` (`SINAN_SEM_CLASSI_FIN`);
- os códigos de `CLASSI_FIN` não são os mesmos em todas as fichas. A ficha de chikungunya, por exemplo, segue a de dengue e não usa o código 1 para confirmado.

Os códigos foram conferidos nas fontes oficiais de cada ficha de `SINAN_AGRAVOS`:

| Agravo | Confirmado | Descartado | Fonte |
|---|---|---|---|
| Chikungunya (CHIK) | 13 | 5 | Dicionário de Dados SINAN Online, Dengue/Chikungunya, MS/SVS, revisão de 21/10/2015 |
| Leptospirose (LEPT) | 1 | 2 | Dicionário de Dados SINAN NET v4.0, Leptospirose, MS/SVS, jan. 2010 |
| Cólera (COLE) | 1 | 2 | Dicionário de Dados SINAN NET v4.0, Cólera, MS/SVS, jan. 2010 |
| Febre tifoide (FTIF) | 1 | 2 | Ficha de Investigação Febre Tifoide, SINAN, SVS, 12/05/2006 |
| Zika (ZIKA) | 1 | 2 | Ficha de notificação e conclusão do e-SUS VS do Espírito Santo (estadual); **a conferir no dicionário nacional** |
| Esquistossomose (ESQU) | — | — | A ficha não tem `CLASSI_FIN` (SVS, 08/10/2009); o caso só é confirmado com ovos nas fezes ou na biópsia |
| Animal peçonhento (ANIM) | — | — | O arquivo não traz `CLASSI_FIN` |

Esquistossomose recebe o mesmo tratamento do ANIM: contada pelas notificações e marcada no relatório. A execução de 19/10/2026 confirmou que os arquivos ESQUBR23 a ESQUBR26 vêm sem a coluna. A distribuição observada dos códigos foi conferida por uma contagem dos valores de `CLASSI_FIN` por agravo e por ano, com o mesmo recorte do pipeline (residentes, notificações no período), cada código com o rótulo de `padronizar_sinan` e os vazios e códigos fora da lista à parte; a contagem mostrou só agregados, nenhum registro.

A contagem de 19/10/2026 (residentes, 2023 a junho de 2026) não achou nenhum código fora da lista. Ela mostrou dois fatos que pesam na regra:

- os casos sem classificação não são só os recentes, ainda em investigação: os 5 de chikungunya sem classificação são todos de 2024;
- as contagens são pequenas. Dos 30 notificados nos agravos com `CLASSI_FIN`, os confirmados são 9 de chikungunya; leptospirose e zika, menos de 5 cada. Os confirmados de zika dependem do código ainda não conferido no dicionário nacional.

## Decisão

Contar como caso só a notificação com classificação final de confirmado. Os códigos de cada ficha ficam em `SINAN_CLASSI_FIN` (`src/config.py`), e `padronizar_sinan` grava o rótulo na coluna `classificacao`.

- O relatório mostra quatro contagens por agravo: notificados, confirmados, descartados e sem classificação. Um código fora da lista aparece à parte e gera aviso no log.
- A contagem principal é a de confirmados, com taxa e IC de Garwood.
- Como análise de sensibilidade, o relatório mostra o máximo possível, que soma confirmados e sem classificação, também com taxa e IC. Assim, os casos sem classificação aparecem como limite superior.
- Com contagens de 0 a 9 por ano, uma taxa anual seria instável. Para o SINAN, o relatório mostra só contagens por ano (`notificacoes_por_ano`) e uma única taxa, a do período inteiro. Agravos com menos de `LIMIAR_AMOSTRA_MINIMA` casos são marcados como instáveis.
- Os agravos sem `CLASSI_FIN` (`SINAN_SEM_CLASSI_FIN`: animal peçonhento e esquistossomose) continuam contados pelas notificações e ficam marcados no relatório como "ficha sem CLASSI_FIN".
- A taxa de zika leva a ressalva de que o código vem de ficha estadual (`SINAN_CLASSI_A_CONFERIR`).
- Na tabela de cobertura por fonte, a coluna de casos fica ao lado do total notificado.

## Alternativas

- **Manter todas as notificações (situação atual).** É mais simples, mas mistura suspeitos descartados com casos e torna a taxa pouco comparável com outros estudos.
- **Contar confirmados e inconclusivos.** Reduz a perda de casos não investigados até o fim, mas a categoria "inconclusivo" não é igual em todas as fichas e ficaria difícil de explicar.
- **Mostrar só os confirmados, sem o total.** Esconde quanto da notificação foi descartado, que é informação útil para a vigilância local.

## Consequências

- As taxas do SINAN vão diminuir. A diferença entre notificados e confirmados passa a aparecer no relatório e mostra a proporção de casos descartados ou sem classificação.
- Como o código muda entre fichas, `SINAN_CLASSI_CONFIRMADO` deixou de ser um valor único e virou o mapeamento por agravo `SINAN_CLASSI_FIN`. `tests/test_config.py` falha se um agravo de `SINAN_AGRAVOS` ficar sem regra.
- Notificações recentes ainda em investigação ficam sem classificação. Por isso, os confirmados de 2025 e 2026 tendem a crescer nas próximas extrações, além do que já acontece com as notificações. Casos antigos sem classificação, como os 5 de chikungunya de 2024, indicam investigação não encerrada e só entram no máximo possível.
- Contagens de 1 ou 2 casos por ano, num município, podem identificar uma pessoa. O relatório interno mostra essas contagens. No README público e nos textos, elas entram agregadas no período ou como "menos de 5" (feita nos documentos versionados em 21/10/2026).
- A aplicação muda números já entregues. Ela exige teste com valor feito à mão e uma linha no `CHANGELOG.md`, como prevê a etapa de correções de método.

## Fonte

- Ministério da Saúde. Dicionários de dados e fichas do SINAN, por agravo (campo `CLASSI_FIN`), listados na tabela do contexto. O de zika ainda depende do dicionário nacional.
- Benchimol, E. I. et al. (2015). RECORD statement, item 6.1 (critérios de seleção da população em dados de rotina).
