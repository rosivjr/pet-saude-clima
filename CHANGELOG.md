# Changelog

Mudanças nos números, no método, no código ou no CI, com a decisão que as sustenta.

Os números de seção de cada entrada são os do relatório na data da entrada.

Os hashes de commit citados nos documentos deste repositório referem-se ao histórico do repositório privado anterior, que não foi publicado.

## 2026-10-21 — Preparação para a publicação do repositório

### Documentação, sem mudar números

- Novo `CONTRIBUTING.md`, com os comandos, a arquitetura e as regras do projeto, e o fluxo de contribuição: abrir um PR, com o CI passando, depois de rodar `uv run pytest`, `uv run ruff check .` e `uv run ruff format --check .`. As referências às regras do projeto no CHANGELOG, nas decisões 0002, 0006, 0007 e 0008, em `docs/seguranca.md` e em `exploracao/README.md` passam a apontar para ele.
- Arquivos de configuração de ferramentas locais de edição saem do versionamento, e o `.gitignore` perde a linha que tratava deles.
- README: a seção "Uso de inteligência artificial" foi reescrita, e "Como citar" diz que o repositório é público e foi publicado sem o histórico anterior (ainda sem DOI). `docs/seguranca.md` registra o mesmo. O aviso de `docs/referencias.md` foi encurtado.

## 2026-10-21 — Registro único das etapas de filtro, corte fixo da extração do SIH e limpeza do código

### Mudou o relatório

- Seção 25 (proveniência): sai a subseção "Registros descartados na limpeza". Cada filtro passava por dois registros, `proveniencia.registrar_descarte` (só a quantidade removida) e `proveniencia.registrar_etapa` (linhas antes e depois), e o log saía duas vezes. Agora há um registro único: `transformacoes.registrar_etapa` anota cada filtro na proveniência e no log, uma vez só (WARNING quando um descarte remove linhas, INFO nos demais). As mesmas contagens continuam na tabela "Todas as etapas de filtro, inclusive as que removeram 0 linhas"; a chave `descartes` sai do JSON de proveniência.
- Seção 7 (lacunas de dados): sai a subseção "Competências do SIH após o fim do período", que listava como indisponíveis as competências de 2026-08 a 2026-12, e entra a linha "SIH extraído até a competência 2026-07", lida de `config.SIH_ULTIMA_COMPETENCIA`. O RECORD pede que o relatório diga até onde vai a extração, e a linha diz isso melhor que a lista de meses que faltam.
- Comparado ao relatório do commit 6b747bb (`rascunhos/relatorio_bloco11.txt`, sem as linhas "Início" e "Registro completo"), essas três mudanças são as únicas: nenhum número mudou, e as figuras de `figuras/` saíram com o mesmo SHA-256.

### Mudou a execução: corte fixo da extração do SIH

- `config.SIH_ULTIMA_COMPETENCIA = (2026, 7)`. Nem `carregadores.carregar_sih` nem `sih/baixar_sih.py` (`make baixar-sih`) pedem ao PySUS competência posterior. Antes, `carregar_sih` pedia os 12 meses de cada ano de `ANOS`, e os meses ainda não publicados faziam o pipeline depender do servidor (pendência da entrada anterior). O corte muda só trocando a constante e rodando `make baixar-sih` (`docs/dados.md`). `config.SIH_COMPETENCIAS_NACIONAIS`, dos scripts do DDA, fica separada do corte para não mudar os números do DDA; a unificação fica para a reescrita do relatório DDA.

### Mudou o código, sem mudar números

- Saem as checagens de coluna que o `usecols` e o pandera já garantem (`territorio`, `abastecimento.divergencia_desinfeccao`, `filtrar_aih_normal`) e os parâmetros que só os testes passavam (`conformidade_por_area(minimo_amostras)`, `proveniencia.salvar(pasta)`, `grafico_ecoli_por_area(limite)`, `configurar_log(verboso)`, `codigo_municipio`/`codigo_ibge7` nos carregadores e em `filtrar_municipio_sih`); os testes usam monkeypatch em `config`. `graficos.gerar_todos` deixa de capturar `KeyError`.
- Para o `config.py`: `DDA_SE_ATRASO_INICIO`, `DDA_ZENODO_REGISTRO`, `DDA_ZENODO_DOI`, `CRITERIO_PORTARIA_888`, `FIGURA_ECOLI_MAX_AREAS`, a paleta das figuras e `COR_EIXOS`. `PYSUS_PASTA_CACHE` passa a depender de `PYSUS_SOURCE`, com erro claro para origem sem cache conhecido.
- Nomes: `positividade_por_area` → `ecoli_por_area`; `secao_ecoli_por_categoria` → `secao_ecoli`; `sih/comum.filtrar_anos` → `filtrar_anos_dda`; `DDA_SIH_COMPETENCIAS` → `SIH_COMPETENCIAS_NACIONAIS`; `DDA_SIH_MESES_COMPARACAO` → `SIH_MESES_COMPARACAO`; `DDA_SE_MAX_2026` → `DDA_SE_MAX`; uma só `rotulo_meses` em `sih/comum.py`; `sih_pará_mensal.csv` → `sih_para_mensal.csv`.
- `sih/completar_download_sih.py`: `source=config.PYSUS_SOURCE`, nome do arquivo de `sih/comum.nome_rd` e proveniência em `data/raw/sih/proveniencia_sih_nacional.json` (`comum.registro_sih`, que sai de `baixar_sih.py`). Sai a conferência com números fixos de `sih/sih_nacional.py`.
- Docstrings de módulo em `dda/`, Args/Returns de `transformacoes.py` e `carregadores.py` só com o que a assinatura não diz, `.gitignore` sem entradas sem uso.

## 2026-10-21 — IC dos residentes internados fora do Pará, sensibilidade do Sivep-DDA por coluna e revisão da documentação

### Mudou o relatório

- Ressalvas sobre as fontes: o percentual de residentes internados em hospitais de outras UFs passa a ter IC 95% de Wilson, calculado em `indicadores.residentes_fora_do_para` (colunas `ic_inferior` e `ic_superior`): 192 de 13.207 em 2025 (1,5%; IC95% 1,3–1,7) e 67 de 5.930 em 2026 (1,1%; IC95% 0,9–1,4). Antes, o `metodos.md` dizia que esses percentuais não tinham IC por serem contagem completa, mas eles são proporções de eventos de saúde, como as demais que levam Wilson. A quebra de linha não separa mais o IC dos números.
- Seção 11, bloco "menor positividade" de E. coli: "Apenas áreas com base amostral suficiente." passa a "Só áreas com 30 amostras ou mais." (`config.LIMIAR_AMOSTRAS_PROPORCAO`, decisão 0020).
- Ressalvas sobre a interpretação: linha nova, "Percentuais de amostras de água com menos de 30 amostras levam [!]."
- Comparado ao relatório do commit bb43bbb (`rascunhos/relatorio_bloco10.txt`, sem as linhas "Início" e "Registro completo"), não há outra diferença: nenhum número existente mudou, e as 8 figuras saíram com o mesmo SHA-256. O SIH foi lido do cache até a competência 2026-07, como na referência.

### Mudou o método: sensibilidade da limpeza do Sivep-DDA (decisão 0021)

- `dda/sensibilidade_limpeza.py` conta os registros corrigidos em `nu_unidades_inf` (informantes) e em `nu_usaude_sem` (existentes), separados. Antes contava só a primeira coluna. Com 100×, a regra corrige em 2025 1 registro de informantes e 5 de existentes; em 2026, 0 e 3. As 3 correções de 2026 mudam só a completude (82,4% sem correção, 82,8% com ela), não a razão casos por unidade-semana. A 0021 dizia "nenhum registro em 2026"; a tabela e as frases foram refeitas.
- Busca por critério oficial, feita em 21/10/2026 no Instrutivo do Sivep-DDA, no Guia de Vigilância em Saúde (6ª ed. rev., 2024, v. 1) e no PubMed: nenhuma fonte traz critério para valores implausíveis. A 0021 segue como critério do projeto, e o `CONTRIBUTING.md` passa a registrá-la como a única exceção aprovada à regra dos critérios oficiais.

### Documentação

- Decisão 0020: o NCHS usa o tamanho efetivo de amostra e o IC de Korn-Graubard (derivado do de Clopper-Pearson); aqui o tamanho efetivo é o número de amostras, porque não há desenho complexo. Decisão 0018: fecho da decisão reescrito.
- `docs/referencias.md`: autores e DOI de Parker et al. (2023), conferidos no PDF do NCHS (`sr02-200.pdf`); entram o Instrutivo do Sivep-DDA, as Notas técnicas do SIH/SUS e o Guia de Vigilância em Saúde.
- `docs/metodos.md`, `README.md`, `docs/dados.md`, `docs/strobe_record.md` e `Makefile`: decisões 0018, 0020 e 0021 citadas onde faltavam, ligação amostra–cadastro descrita por inteiro, `IDADE` do SIM marcada como conferida, `dda/sensibilidade_limpeza.py` no lugar de `dda/sensibilidade_dda.py`.
- Este CHANGELOG: "HEAD" e "deste bloco" trocados pelos commits de referência (4f11c23 e 65f417d).

### Pendente para o próximo bloco

- `carregar_sih` pede os 12 meses de cada ano de `ANOS`, inclusive competências ainda não publicadas. Com o servidor do PySUS fora do ar, o pipeline parou em `httpx.ConnectTimeout` (duas tentativas nesta data); se o DATASUS publicar uma competência nova, ela seria baixada e mudaria os números. A correção é a constante `SIH_ULTIMA_COMPETENCIA`, que fixa o corte da extração.

## 2026-10-21 — Limiar de 30 amostras para proporções de amostras de água (decisão 0020)

### Mudou o relatório

As proporções de amostras de água por área, ponto de coleta e mês passam a usar `config.LIMIAR_AMOSTRAS_PROPORCAO = 30` (NCHS, Vital Health Stat 2(175), 2017, critério "Sample size") em vez de `LIMIAR_AMOSTRA_MINIMA = 10`, que continua valendo para contagens de eventos (decisão 0018). O limiar decide quais áreas têm base suficiente para entrar no resumo e no ranking: uma área com 10 amostras e 0% de positividade no bloco de "menor positividade" leva o leitor a uma conclusão que a amostra não sustenta. Amostras, positivos, percentuais e IC de Wilson de cada área, ponto e mês não mudam; a proporção marcada não é suprimida.

| Onde | Antes (10) | Depois (30) |
|---|---|---|
| Seção 11, texto de abertura | "Áreas com menos de 10 amostras…" | "Áreas com menos de 30 amostras…" |
| Seção 11, resumo do cloro: áreas com base suficiente | 19 | 12 |
| Seção 11, resumo do cloro: suficientes com 100% abaixo do mínimo | 6 | 2 |
| Seção 11, tabela do cloro por área: linhas com `[!]` | 6 | 10 |
| Seção 11, tabela de E. coli por área: linhas com `[!]` | 1 | 6 |
| Seção 11, E. coli, bloco "menor positividade" | MARANHAO (31 amostras, 0%), BELA VISTA I (17), PRIMAVERA (16), MINERIOS (13), CASAS POPULARES II (10) e VILA RICA (10), todas com 0% | MARANHAO (31 amostras, 0%), LIBERDADE I (63; 6,3%), CIDADE NOVA (249; 6,8%), UNIAO (55; 9,1%), BETANIA (46; 10,9%) e DA PAZ (84; 16,7%) |
| Seção 14, E. coli por mês: meses com `[!]` | 0 | 14 dos 35 meses com coleta |
| Seção 14, E. coli por ponto de coleta: linhas com `[!]` | 4 | 4 |
| Figura 02 (E. coli por área) | áreas com 10 ou mais amostras | só as com 30 ou mais |

Comparado ao relatório do commit 4f11c23 (sem as linhas "Início" e "Registro completo"), não há outra diferença; das 8 figuras, só a 02 mudou de SHA-256. Os nomes das áreas estão como saem no relatório e no SISAGUA.

### Mudou o código: figura 02 sem área suficiente

- Com o limiar de 30, ficou mais provável que nenhuma área tenha base suficiente. Nesse caso `grafico_ecoli_por_area` quebrava ao definir o eixo (`ValueError`), e o log dizia só "Falha ao gerar o gráfico de E. coli por área: ValueError". Agora a figura não é gerada, o log diz "Figura 02 não gerada: nenhuma área com 30 amostras de E. coli ou mais" e o pipeline segue. Com os dados atuais a figura é gerada normalmente.

### Decisões

- **0020** passa de proposta a aceita.

## 2026-10-21 — Cache do PySUS, limiares com fonte, limitação do SIH fora do Pará e estrutura

### Mudou o relatório

- Ressalvas sobre as fontes: novo item com as internações de residentes em hospitais de outras UFs, que o relatório não lê. Medido à parte com `sih/sih_nacional.py`: 192 de 13.207 em 2025 (1,5%) e 67 de 5.930 em 2026 (1,1%). Os números do relatório não mudaram. Contagens em `config.SIH_RESIDENTES_FORA_DO_PARA`, percentual em `indicadores.residentes_fora_do_para`, texto também em `docs/metodos.md` (Limitações). A leitura das 27 UFs é a proposta da **decisão 0019**.
- Fora esse item, o relatório saiu idêntico ao do commit 65f417d (sem as linhas "Início" e "Registro completo"), e as 8 figuras saíram com o mesmo SHA-256.

### Mudou a execução: cache do PySUS primeiro

- O pipeline esperava o servidor do PySUS mesmo com os arquivos baixados. Toda chamada `pysus.ftp.*` consulta o catálogo remoto para listar os arquivos e compara o tamanho do arquivo local com o do remoto, e baixa de novo se diferirem. Na referência, gerada no commit 65f417d, o PySUS baixou de novo `CHIKBR24` e o CNES de 2023 a 2025.
- `carregar_sih`, `carregar_sinan`, `carregar_sim` e `carregar_cnes` leem direto do cache (`config.PYSUS_PASTA_CACHE`) quando o arquivo existe; só o que falta vai ao PySUS. Cada arquivo leva na proveniência o campo `leitura`, que diz se veio do cache ou do servidor. Na execução final, os 75 arquivos do PySUS vieram do cache. Dados preliminares só se atualizam pelos alvos `make baixar-*` (`docs/dados.md`).

### Decisões novas

- **0018** (aceita): taxa ou grupo com menos de 10 eventos leva o aviso de estimativa instável, pelo padrão atual do NCHS (Vital Health Stat 2(200), 2023; a regra dos 20 óbitos valeu até os dados de 2022). Com o IC de Garwood, o critério do NCHS de largura relativa até 160% vale para toda contagem de 10 ou mais. O relatório não muda.
- **0019** (proposta): ler o SIH de todas as UFs.
- **0020** (proposta, não aplicada): limiar de 30 amostras para proporções de amostras de água (NCHS, Vital Health Stat 2(175), 2017), com o efeito medido no relatório.
- **0021** (aceita): no Sivep-DDA, número de unidades acima de 100 vezes a mediana do município é erro de digitação. Critério do projeto, sem fonte oficial, justificado pela sensibilidade de 10 a 1000×. O múltiplo foi para `config.DDA_LIMITE_MEDIANA_UNIDADES`.

### Notas a conferir do config.py

- Conferidas: a `IDADE` do SIM (unidade no 1º dígito, "000" = idade ignorada), os códigos de ignorado do SIM (SEXO 0, LOCOCOR 9) e os tipos de estabelecimento 20, 21 e 61 do CNES. Fontes em `docs/referencias.md`.
- Correção de código: `idade_sim_em_anos` tratava "000" (idade ignorada) como menor de 1 ano. Passa a dar NaN. Nenhum óbito de residente de 2023 ou 2024 tem "000", e o relatório não muda.
- Continuam pendentes, com o que falta:
  - lista FUNASA (2010) e grupo de geo-helmintos e teníases: o PDF original não foi localizado;
  - A97 no SIM: falta fonte para a troca da versão da CID-10 no fim de 2024;
  - `COD_IDADE` do SIH: o dicionário da AIH reduzida não foi localizado;
  - `CLASSI_FIN` da zika: falta o dicionário nacional da ficha;
  - `CS_SEXO` e `EVOLUCAO` do SINAN: falta o dicionário da notificação individual; a `EVOLUCAO` muda de ficha para ficha;
  - arredondamento do plano de amostragem: depende do plano aprovado pela SEMSA/SESPA.

### pip-audit: checagem adiada

- Em 21/10/2026 nenhuma correção tinha os 7 dias de espera: `pillow` 13.0.0 é de 16/10/2026, não há `pillow` 12.x nova, e `certifi` 2026.10.19 é de 20/10/2026. Os 9 `--ignore-vuln` continuam.
- Datas: um PR só do `pillow` em 23/10/2026 e um só do `certifi` em 27/10/2026. Cada um precisa mudar a trava do pacote em `constraint-dependencies`; sem isso, o `uv lock` não atualiza (`docs/seguranca.md`).

### Mudou o código, sem mudar números

- Exceções: `graficos.gerar_todos` captura só `KeyError`, `ValueError` e `OSError`. `ERROS_PYSUS` passa a ser `(PySUSError, OSError)`: parâmetro recusado já é `ValidationError` do PySUS. O `TypeError` de `group=` só é aceito na primeira tentativa de `_baixar`.
- Parâmetros usados só em teste saíram: `filtrar_agravos(apenas_drsai=)`, `carregar_cnes(uf=)` e `filtrar_municipio_cnes(codigo_municipio=)`.
- `.copy()` saiu dos filtros de `transformacoes.py` que só fatiam. Os testes rodam com `SettingWithCopyWarning` como erro, e o log da execução não tem o aviso.
- `indicadores/rede.py` não confere mais colunas que o pandera garante. O esquema do CNES passou a exigir `QTLEITP1` a `QTLEITP3`.
- `proveniencia.registro_download` grava as mesmas chaves (`arquivo`, `fonte`, `origem`, `baixado_em` em America/Belem, `linhas`, `sha256`) em `dda/baixar_dda.py` (antes em UTC), `sih/baixar_sih.py` e `sinan/baixar_sinan.py`. O SIH guarda o caminho do cache em `cache_pysus`, e `sih/comum.arquivos_rdpa` ainda lê o JSON antigo. O JSON da chuva passa a ter a URL (`config.CLIMA_API`) em `origem`.
- `main.executar` foi dividido em funções com nome (`carregar_bases`, `validar_bases`, `calcular_indicadores`, `gerar_figuras`, `imprimir_relatorio` e outras), no lugar dos comentários-título.
- `figuras_complementares.py` virou `sih/figuras_sih.py` (`make sih` roda `python -m sih.figuras_sih`). `tests/test_indicadores.py` foi dividido em `tests/indicadores/`, um arquivo por submódulo, com os mesmos 86 testes. A fixture de período virou `usefixtures`.
- `relatorio/_formato`: `_ic`, `_data`, `_titulo`, `_subtitulo` e `_extracao` perderam o sublinhado. O parâmetro `extracao` de `rodape_figura` virou `datas_extracao`.
- Testes de texto novos para `relatorio/mortalidade.py` e `relatorio/rede.py`, incluindo o formato do IC.
- Limpeza: `pytest.ini` foi para `[tool.pytest.ini_options]`. Saíram as constraints de seaborn e pandas-stubs, que não estão no lock (nenhum pacote mudou). O comentário do `openpyxl` diz que ele serve ao `read_excel` do SINISA.

## 2026-10-21 — AIH tipo 1 nos scripts do SIH, leitura comum do SIH-RD e nomes

### Mudou o método nos scripts de sih/, com efeito na Figura 4

- `sih/sih_nacional.py` e `sih/verificar_sih.py` passam a contar só a AIH do tipo 1, como manda a **decisão 0009** e como `sih/contar_sih.py` já fazia. Os três usam `transformacoes.filtrar_aih_normal`, com `config.SIH_IDENT_NORMAL`, no lugar do `== "1"` escrito no script.
- Em `verificar_sih.py` a saída não mudou: as 867.062 AIH dos arquivos RD do Pará de 2025 e 2026 são todas do tipo 1.
- Em `sih_nacional.py`, Parauapebas não mudou. No Pará saíram 23 AIH de outros tipos em 2025 e 4 em 2026 (residentes internados em arquivos de outras UFs). No Brasil saíram 85.546 em 2025 e 30.695 em 2026. Todas as internações no Brasil: 12.489.594 → 12.404.048 (2025) e 5.989.382 → 5.958.687 (2026); por diarreia (A00–A09): 120.115 → 120.107 e 58.262 → 58.258.
- Figura 4 de `figuras_complementares.py`: só as barras do Brasil mudam, +0,01 ponto percentual em cada período (0,96 → 0,97 em 2025; 1,14 → 1,15 em jan.–abr. de 2025; 1,06 → 1,07 em jan.–abr. de 2026).

### Mudou o código, sem mudar números

- `sih/comum.py` (com `tests/test_sih_comum.py`) junta a leitura dos arquivos RD que estava repetida em três scripts: lista da proveniência, limpeza dos campos, data da internação, ano, mês e CID de 3 caracteres.
- Anos fixos trocados por `config.DDA_ANOS` (primeiro e último ano) em `sih/`, `dda/` e `figuras_complementares.py`. O "Janeiro a abril" de `sih_nacional.py` sai de `DDA_SIH_MESES_COMPARACAO` e da nova `config.MESES_NOME`.
- Hepatite A (`sinan/hepatite_a_sinan.py`): o critério (`SINAN_HEPATITE_CONFIRMADO`, `SINAN_HAV_VIRUS_A`) e os números do boletim (`SINAN_HEPATITE_A_BOLETIM`) foram para o `config.py`, com a fonte: Boletim Epidemiológico de Hepatites Virais, número especial de julho de 2025, Tabela 3, p. 40, e o Dicionário de Dados Sinan NET 5.0, campos 48 e 50 (`docs/referencias.md`). `HAV` não é a sorologia anti-HAV IgM, que está em `ANTIHAVIGM`. Ela marca o vírus A: aparece só com `CLASSI_FIN` 1 ou 2, inclusive em casos confirmados por critério clínico-epidemiológico. O dicionário não documenta que `HAV` desdobra a `CLAS_ETIOL`, e essa pendência ficou registrada no `config.py`.
- `ROTULO_DRSAI` foi para o `config.py`, e o apelido `CLORO` deu lugar a `config.PARAMETRO_CLORO`.
- `ResultadoConformidade` guarda o limite legal como número (`limite_minimo`, `limite_maximo`, `unidade`), e o texto "mínimo 0,2 mg/L" é montado em `relatorio/agua.py`.
- Uma paleta só (`graficos.CORES_LOCAL` e as cores Okabe-Ito) e uma formatação só: `relatorio.numero` (antes `_num`) e o novo `relatorio.milhar`, usados no relatório, em `graficos.py`, em `dda/figuras_dda.py` e em `figuras_complementares.py`.
- Funções renomeadas com "ecoli": `ecoli_por_captacao`, `ecoli_por_ponto`, `sazonalidade_ecoli` e `grafico_ecoli_por_area`.
- Nomes nos scripts: saem os apelidos de constantes do config e as abreviações (`out`, `RAW`, `cb`, `r`, `f`, `s`, `sub`, `dup`, `cols` e outras).
- Docstrings: as de módulo de `carregadores`, `transformacoes`, `graficos`, `config` e `main` dizem o que o módulo cobre. Os `Args:`/`Returns:` que repetiam nome ou tipo viraram frase.
- `exploracao/sinan/colunas_sinan.py`, que lia o arquivo nacional inteiro, foi apagado; ele continua no histórico do git.

## 2026-10-20 — Coliformes, rodapé das figuras, IC por faixa etária e texto

### Mudou o texto e as figuras, sem mudar números

- Coliformes totais e *E. coli* descritos como "amostras com presença", não como "fora do padrão" ou "contaminação" (Portaria GM/MS nº 888/2021, Anexo 1): título da figura 01, títulos das figuras 02, 03 e 08 ("Amostras com E. coli presente"), coluna da **seção 17** ("Fora do padrão ou com presença"), docstrings, README, `docs/dados.md` e **decisões 0005, 0006 e 0013**. Os arquivos 02 e 03 passam a se chamar `02_ecoli_por_area.png` e `03_sazonalidade_ecoli.png`; `secao_fatores_contaminacao` passa a `secao_ecoli_por_categoria`. `docs/img/conformidade_agua.png` foi gerada de novo.
- Rodapé único nas figuras: `relatorio.rodape_figura` (fonte, período, data de extração e, quando há, critério) substitui `rodape_figura_agua`, e `graficos.desenhar_rodape` o desenha em todas as figuras de `src/graficos.py`, `dda/figuras_dda.py` e `figuras_complementares.py`. A data segue a regra da **decisão 0017**: no Sivep-DDA é a data do arquivo, com o aviso "data do arquivo, não da extração", porque os JSONs antigos guardam a data da inspeção; na Figura 4 sai "data de extração não registrada" enquanto `proveniencia_sih.json` estiver no formato anterior. `datas_de_extracao` aceita mais de uma fonte (figura 05: CNES e SIH).
- Figura 4 de `figuras_complementares.py`: os meses comparados vêm de `DDA_SIH_MESES_COMPARACAO` (janeiro a abril), com o rótulo gerado a partir dela, e os valores não mudaram. A Figura 4 compara janeiro a abril, enquanto o relatório principal compara janeiro a junho (**decisão 0008**). A escolha veio com o script no commit `840863d`, sem justificativa escrita, e volta a ser decidida na reescrita do relatório DDA.
- Rótulos: "Perdas na distribuição (%)" (Figura 3) e "Escala logarítmica simétrica (linear perto de zero)" (figura 05). Na figura 2 do DDA, a legenda subiu para não encostar no rodapé.
- Título único do projeto em `config.TITULO_PROJETO`, usado no cabeçalho do relatório (sem "INTEGRADO") e conferido por teste em README, `CITATION.cff` e `pyproject.toml`.
- Aviso de contagem pequena com redação única, "menos de 10 casos: estimativa instável" (**seções 2, 5 e 22** e ressalvas; na **seção 22**, a nota que explica o `[!]`). Na **seção 5** o aviso passou para uma linha própria, para caber em 78 colunas.
- **Seção 1**: cita o indicador 33 do IDS Brasil 2015 (IBGE). **Seção 19**: o SINISA substituiu o SNIS a partir da coleta de 2024, ano de referência 2023 (Nota Informativa SEI/MIDR nº 5886717); o texto anterior dizia 2024. Frases das **seções 16, 21 e 24** reescritas.
- Documentos: `docs/metodos.md` (Souza, 2024; caminhos de `dda/`; fonte da tabela CID do SIGTAP, sem a frase sem fonte sobre o SIM, que ficou como pendência no comentário do `config.py`; construções ", e não" reescritas), **decisão 0007** (padronização não aplicada; volta se outro documento comparar locais), **decisões 0002 e 0006** (a taxa de 2026 é só descrição), README, `docs/referencias.md` (Morgenstern, von Elm, Benchimol, Fay e Feuer, Diretriz Vigiagua, IDS, SINISA e SIGTAP). Os números de etapa e de bloco saíram do CHANGELOG, de `docs/seguranca.md`, de `docs/strobe_record.md` e da **decisão 0001**, e o negrito do CHANGELOG ficou só nos nomes de decisão e de seção.

### Fica para depois

- O "Janeiro a abril" fixo em `sih/sih_nacional.py` passa a usar `DDA_SIH_MESES_COMPARACAO`.
- `contaminacao_por_captacao`, `contaminacao_por_ponto`, `sazonalidade_contaminacao` e `grafico_contaminacao_por_area` passam a usar "ecoli" no nome, como os arquivos das figuras. A "não conformidade" do cloro residual em `indicadores/territorio.py` fica, porque ali o termo é técnico.

### Mudou o relatório: IC novos

- **Seções 3 e 15** (distribuição etária das internações DRSAI e feco-orais) e **seção 22** (óbitos DRSAI por faixa etária): percentual com IC de Wilson (`perfil_etario`, `mortalidade_por_faixa`), com teste de valor feito à mão. Os percentuais e as contagens não mudaram.

## 2026-10-20 — IC de Wilson nas seções de mortalidade e rede

### Mudou o relatório: IC novos, sem mudar números

- **Seção 22**: a proporção de óbitos DRSAI no total de óbitos, por ano, ganhou IC de Wilson (`serie_anual_mortalidade`).
- **Seção 13**: internações dentro e fora do município e no hospital principal ganharam IC de Wilson (`local_de_internacao`).
- **Seção 12**: o percentual de cada tipo de solução passou a ser calculado em `indicadores` (`percentual_por_tipo`), sem IC, porque o cadastro é contagem completa. O mesmo vale para o CNES com e sem vínculo SUS. A exceção está no `CONTRIBUTING.md` e em `docs/metodos.md`.
- Proveniência da chuva: o JSON grava linhas e SHA-256, e a data do download sai no fuso do município. Testes novos de pessoa-tempo em `tests/test_estatistica.py`.

## 2026-10-20 — Revisão de texto

### Mudou o texto, sem mudar números

- Coliformes totais (**seção 9**, `docs/metodos.md`, `docs/dados.md`). Conferido no Anexo 1 da Portaria GM/MS nº 888/2021: o padrão de coliformes totais na distribuição vale para o conjunto das amostras examinadas no mês pelo responsável pelo sistema (ausência em 95% a partir de 20 mil habitantes; no máximo uma positiva abaixo disso; ausência na saída do tratamento); *E. coli* exige ausência em 100 mL. As amostras do SISAGUA são da vigilância, e o indicador passa a ser descrito como "percentual de amostras com presença", não como não conformidade.
- **Decisão 0007** rejeitada para o relatório principal. O relatório não mostra taxa do Pará nem do Brasil; as comparações com o Brasil são de saneamento (SINISA). Saiu de `docs/metodos.md` o parágrafo da padronização, e entrou nas limitações que as taxas são brutas e não devem ser comparadas com outros locais sem padronização. Caminhos corrigidos para `exploracao/dda/`.
- Frases do relatório. Nota de completitude do SINAN gerada de `SINAN_SEM_CLASSI_FIN` (passa a citar esquistossomose); ressalva sobre microdados numa frase só; seção 15 sem a afirmação sobre o perfil etário, escrita antes dos dados; "Contexto climático" cita os acidentes por animais peçonhentos (T63); seção 16 diz que a taxa anualizada é só descrição (decisão 0008); nota da sazonalidade reescrita.
- Documentos. 0008 tratada como aceita nas decisões 0003, 0006 e 0008; 0016 (sem estimativa municipal do IBGE em 2022 e 2023); 0014 e 0017 (remoção de `docs/estado_projeto.md` no commit `0d88e24`); 0009 (execução de 20/10/2026); 0001 sem aforismos; `docs/strobe_record.md`, `docs/seguranca.md`, `README.md` e arquitetura do `CONTRIBUTING.md` alinhados ao código.

## 2026-10-20 — Vulnerabilidades ignoradas temporariamente no CI

### Mudou o CI, sem mudar números

- `pip-audit` ignora 9 IDs até o fim do cooldown de 7 dias. Oito são do `pillow` 12.3.0 (correção na 13.0.0, de 16/10/2026; remover até 23/10/2026) e um do `certifi` 2026.7.22 (GHSA-6q48-6c7w-9gw2; correção na 2026.10.19, de 20/10/2026; remover até 27/10/2026). Os IDs e as datas estão no comentário do passo em `.github/workflows/ci.yml`.
- Por quê, em resumo (detalhes em `docs/seguranca.md`): o projeto só usa o Pillow para gravar as próprias figuras em PNG, e as falhas são na leitura de outros formatos; o `certifi` só valida os downloads (PySUS, Open-Meteo e Zenodo).
- Não havia `pillow` 12.x corrigido em 20/10/2026. Se sair, a atualização deve preferi-lo à 13.

## 2026-10-20 — Proveniência do SIH e leitura do Sivep-DDA

### Mudou o código, sem mudar números

- Formato novo de `data/raw/sih/proveniencia_sih.json`. `sih/baixar_sih.py` passa a gravar, para cada arquivo, os campos do `sinan/baixar_sinan.py`: `fonte`, `origem` (endereço do PySUS e consulta), `baixado_em` (data do arquivo no cache do PySUS), `linhas` e `sha256`, também para Parquet em pasta. O campo `baixado_em` do topo, que era a hora da execução, passa a se chamar `gerado_em`.
  - O JSON que está em `data/raw/sih/` é do formato anterior: só `arquivo` e `sha256` por arquivo (`"pasta"` no lugar do hash quando o Parquet é uma pasta), e um `baixado_em` no topo que é a hora da execução, não a do download. Ele só muda no próximo `make baixar-sih`.
  - `contar_sih.py` e `verificar_sih.py` leem só `arquivos[].arquivo`, presente nos dois formatos.
- `dda/comum.ler_ano` lê só as colunas usadas (`DDA_COLUNAS`) e filtra o ano na leitura. Conferido nos arquivos de 2025 e 2026: `sem_epid_year` é inteiro, e os dados lidos são iguais aos da leitura anterior (264.350 e 102.628 linhas, 18 colunas).

## 2026-10-20 — Figuras 02 e 08 em cor única

### Mudou a figura, sem mudar números

- Sem faixas de cor. As barras tinham cores por faixa, com cortes que nenhuma norma define:
  - figura 02 (E. coli por área): vermelho a partir de 40%, verde-azulado de 10% a 40% e verde abaixo de 10%;
  - figura 08 (origem da captação): vermelho a partir de 30%, verde-azulado de 15% a 30% e verde abaixo de 15%.
- Agora as duas usam o azul da paleta Okabe-Ito, como a figura 01. Percentuais, n e IC de Wilson não mudaram; das figuras do relatório, só a 02 e a 08 mudaram de SHA-256.

## 2026-10-20 — Seção 12 e duas etapas novas na tabela de filtros

### Mudou o relatório, sem mudar números

- Nenhum número mudou. O diff contra o relatório anterior mostra só estas três mudanças.
- **Seção 12**, frase da ligação corrigida. Dizia que cada amostra foi ligada ao cadastro "no ano da coleta"; agora descreve a regra da decisão 0005: o ano da coleta ou, se não houver, o ano anterior mais próximo e, na falta dele, o seguinte.
- **Seção 25**, etapa "SIH: DRSAI" (recorte). A seleção dos grupos do DRSAI passou de uma linha do `main.py` para `filtrar_drsai` e aparece na tabela: 3.012 → 502 internações. A etapa termina nas 502 internações por DRSAI da seção 1.
- **Seção 25**, etapa "SISAGUA cadastro: dedup" (descarte). A deduplicação do cadastro (última linha por solução e ano) passou a ser registrada: 400 → 400 linhas, nenhuma repetida nesta extração.

## 2026-10-20 — Seções do relatório renumeradas

### Mudou o código, sem mudar números

- **Seções 19 a 26** passaram a 18 a 25. Não havia seção 18. Nas entradas abaixo, qualidade dos dados é a 24 (hoje 23), sensibilidade é a 25 (hoje 24) e proveniência é a 26 (hoje 25).
- Linhas novas no relatório, sem mudar as existentes: todas as fontes no cabeçalho; contagens da ligação amostra-cadastro na divergência de desinfecção (seção 12); data de extração por fonte e tabela de todas as etapas de filtro, com descarte e recorte separados (seção 25).

## 2026-10-20 — Figura 01 (conformidade da água)

### Mudou a figura, sem mudar números

- Uma cor só. As barras eram vermelhas a partir de 50% fora do padrão e verde-azuladas abaixo disso. Nenhuma norma define esse corte, e agora todas usam o azul da paleta Okabe-Ito, legível para as formas comuns de daltonismo.
- Número de amostras e rodapé. Cada barra mostra o percentual e o n; o rodapé traz fonte, período, critério (Portaria GM/MS nº 888/2021) e data de extração. As barras de IC de Wilson são as da correção do método (2026-10-19).
- A mesma figura foi copiada para `docs/img/conformidade_agua.png` e aparece no README.

## 2026-10-19 — SINAN só confirmados (decisão 0001)

### Mudou o método

- Caso do SINAN = notificação confirmada (**decisão 0001**, aceita).
  - Os códigos de `CLASSI_FIN` de cada ficha ficam em `SINAN_CLASSI_FIN`. Chikungunya usa 13; os demais agravos usam 1. `padronizar_sinan` grava o rótulo na coluna `classificacao`.
  - A seção 5 mostra notificados, confirmados, descartados e sem classificação. A taxa do período inteiro usa os confirmados.
  - Como sensibilidade, a seção mostra o máximo possível (confirmados + sem classificação). Por ano, mostra só contagens, sem taxa.
  - Agravos com menos de 10 casos são marcados como instáveis. Zika leva a ressalva de que o código ainda não foi conferido no dicionário nacional.
- Esquistossomose sem `CLASSI_FIN`. Entrou em `SINAN_SEM_CLASSI_FIN`, porque a ficha não tem o campo. Ela é contada pelas notificações, como o ANIM.

Números entregues que mudam:

- **Seção 5**, taxa por 100 mil pessoas-ano:
  - Chikungunya: 2,01 → 0,86 (9 de 21 notificações confirmadas; máximo 1,34).
  - Leptospirose: taxa com menos de 5 casos, antes e depois (menos de 5 confirmados em menos de 5 notificações; máximo: taxa com menos de 5 casos).
  - Zika: taxa com menos de 5 casos, antes e depois (menos de 5 confirmados em menos de 5 notificações; máximo: taxa com menos de 5 casos).
  - Febre tifoide: taxa com menos de 5 casos → 0,00 (as notificações, menos de 5, foram descartadas).
  - Esquistossomose e animal peçonhento não mudam.
- **Seção 6**: coluna nova "Casos" ao lado de "Notificações". Contato com água: menos de 5 casos; feco-oral: 0.
- **Seção 24**: completitude do SINAN recalculada sem a esquistossomose, que não tem `CLASSI_FIN` e saiu do denominador.

## 2026-10-19 — Correção do método

### Mudou o método

- Comparação entre anos nos meses comuns (**decisão 0008**, aceita). `serie_anual_internacoes` e `serie_anual_todas_causas` calculam a razão de taxas só nos meses cobertos em todos os anos (`meses_comuns`: janeiro a junho, com o período atual), com a pessoa-tempo desses meses. A taxa anualizada de cada ano continua como descrição, e o ano parcial é marcado na coluna `ano_parcial` e com `*` no relatório. A decisão 0006 passou a "Substituída em parte pela 0008".
  - Números entregues que mudam (seção 16, RT contra 2023):
    - DRSAI: 2024 2,85 → 2,44; 2025 2,58 → 3,39; 2026 1,69 → 1,51.
    - Feco-oral: 1,98 em 2024, 1,39 em 2025 e 1,22 em 2026.
    - Inseto vetor: 3,21 em 2024, 6,17 em 2025 e 1,93 em 2026.
    - Todas as causas: 1,13 em 2024, 1,22 em 2025 e 1,14 em 2026.
  - Os meses comuns não corrigem o atraso de faturamento: maio e junho de 2026 continuam incompletos.

### Mudou o código, sem mudar números

- `periodo_temporario` removido. O fim do período passa a ser argumento (`fim`) de `pessoa_ano_periodo`, `indicador_drsai`, `perfil_por_grupo` e `_indicadores_principais`, e a sensibilidade não altera mais `config.PERIODO_FIM`. A seção 25 (sensibilidade) ficou igual.
- `ligar_cadastro_por_ano` confere a chave. Lança `ValueError` se o cadastro repetir a mesma solução no mesmo ano, porque o `merge_asof` escolheria uma linha sem avisar. Grava também o número de soluções sem par em `attrs["ligacao"]` e avisa no log quando há amostras sem par. Na extração atual a chave é única, e a seção 14 ficou igual.
- Percentual da rede SUS calculado em `indicadores`. `PerfilRede` ganhou `percentual_sus` e `percentual_sem_sus`. `relatorio.py` só formata, e a seção 13 ficou igual.
- IC de Wilson nas figuras de percentual. As figuras 01 (conformidade), 02 (E. coli por área) e 08 (origem da captação) ganharam barras de IC. A figura 03 (série de E. coli) ganhou a faixa do IC.
- Proveniência com origem e data do download.
  - Cada arquivo do JSON agora traz `origem` e `baixado_em`, além do SHA-256.
  - PySUS: o PySUS não expõe a URL, então a origem registrada é o endereço do espelho ou do servidor (`PYSUS_ENDERECOS`) mais a consulta. A data do download é a da gravação no cache.
  - Precipitação: URL da API e data gravada no download.
  - Arquivos baixados à mão (SISAGUA, Censo, SINISA): "não registrado". A data da leitura nunca entra no lugar da data do download.
- `dda/`.
  - `baixar_dda.py` grava a proveniência (URL do arquivo, data do download, linhas e SHA-256) no momento do download, inclusive para o dicionário.
  - `inspecionar_dda.py` só lê essa proveniência. Ele não grava mais em `data/raw` e não imprime mais as três primeiras linhas, que eram registros individuais.
  - Os JSONs de proveniência que já existem continuam com a data da inspeção, porque `data/raw` não é alterado. Para corrigi-los, é preciso baixar os arquivos de novo.

### Não aplicado

- SINAN só confirmados (**decisão 0001**, continua proposta). Falta conferir no dicionário de cada ficha qual código de `CLASSI_FIN` significa confirmado, porque a de chikungunya não usa o 1. A execução de 19/10/2026 mostrou também que os arquivos de esquistossomose (ESQUBR23 a 26), e não só os de animais peçonhentos, vêm sem `CLASSI_FIN`.
- Padronização por idade (**decisão 0007**, continua proposta). O IC da taxa padronizada ainda não está no plano de análise.

## 2026-10-18 — Ponto no RESULTADO do SISAGUA (decisão 0010)

### Mudou o código, sem mudar números

- Ponto fora do padrão de milhar interrompe a leitura (**decisão 0010**, aceita). `converter_decimal_brasileiro` só aceita o ponto como separador de milhar seguido de vírgula decimal (`PADRAO_MILHAR_BRASILEIRO`). Qualquer outro ponto ("0.5", "1.234") lança `ValueError`, com a contagem e sem mostrar valores. Antes, todo ponto era apagado, e "0.5" viraria 5 sem aviso.
- A contagem de 18/10/2026 achou 6.539 valores de `RESULTADO` em Parauapebas, 2023-2026, nenhum com ponto. Nenhum resultado mudou.

## 2026-10-16 — População de referência (decisão 0016)

### Mudou o método

- Denominador ano a ano (**decisão 0016**, aceita). A população deixou de ser a do Censo 2022 em todos os anos. 2024 a 2026 usam as estimativas do IBGE publicadas no DOU; 2023, sem estimativa oficial, usa a interpolação geométrica entre o Censo 2022 e a estimativa de 2024 (`POPULACAO_ANUAL`, com a fonte de cada ano em `POPULACAO_FONTE`).
- A mudança entrou junto com a troca do período para 2023-2026 e foi registrada como decisão em 2026-10-20. Os números anteriores não são comparáveis com os atuais, porque o período também mudou, e não foram listados aqui.
