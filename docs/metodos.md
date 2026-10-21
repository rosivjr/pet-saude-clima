# Métodos

Plano de análise do PET-Saúde CLIMA, Eixo II, em Parauapebas (PA). As seções seguem a ordem dos itens do STROBE (von Elm et al., 2007), com os itens do RECORD (Benchimol et al., 2015) para dados de rotina dos sistemas de saúde. O número de cada item aparece entre parênteses no título da seção. A tabela item a item, que mostra onde cada item é atendido e o que ainda falta, está em `docs/strobe_record.md`. As escolhas que exigem justificativa têm registro próprio em `docs/decisoes/`, citado pelo número.

Os valores fixos (código do município, período, população, códigos CID-10 e limites da Portaria) estão em `src/config.py`, que é a única fonte deles. Este documento descreve as regras e cita o nome da constante. A exceção é a tabela de códigos CID-10 da seção Variáveis, que um teste gera e confere.

## Pergunta (itens 2 e 3)

Parauapebas cresceu rápido por causa da mineração (Souza, 2024), e esse crescimento formou periferias sem rede de esgoto e com abastecimento de água desigual. A pergunta do estudo é descritiva: qual foi, entre 2023 e 2026, a ocorrência dos agravos relacionados a saneamento ambiental inadequado (DRSAI) entre os residentes do município, e qual foi a qualidade da água para consumo humano medida pela vigilância no mesmo período e no mesmo território?

O estudo descreve as duas séries lado a lado. Ele não testa se uma explica a outra.

## Desenho (item 4)

É um estudo ecológico e descritivo, com o município como unidade de análise e séries mensais e anuais. Os dados de saúde e os de água são agregados que nunca se referem às mesmas pessoas. Por isso, uma coincidência entre água fora do padrão e aumento de internações, no tempo ou no território, é tratada como hipótese para a gestão local. Ela não é lida como efeito da água sobre os agravos e não permite conclusões sobre indivíduos, que seriam falácia ecológica (Morgenstern, 1995). O estudo não estima associação e não usa modelo de regressão. Se o plano incluir a relação entre chuva e agravo, o método terá de entrar antes neste documento.

## Contexto e período (item 5)

O município é Parauapebas, código IBGE de 7 dígitos `MUNICIPIO_IBGE_7` e código DATASUS de 6 dígitos `MUNICIPIO_IBGE_6`. O período vai de `PERIODO_INICIO` (1º de janeiro de 2023) a `PERIODO_FIM` (30 de junho de 2026), inclusive nas duas pontas. Esse é o último dia do mês anterior à última competência do SIH publicada (2026-07; ver `docs/dados.md`). Os meses finais podem estar incompletos, porque a AIH pode ser faturada meses depois da alta.

Os dados de 2025 e 2026 do SIH e do SINAN são preliminares, e o arquivo de origem pode mudar a cada atualização do DATASUS. Todo relatório informa a data de extração, registrada no JSON de proveniência de cada arquivo em `outputs/proveniencia/`.

## Participantes (item 6 e RECORD 6.1 a 6.3)

A população de estudo são os residentes de Parauapebas. Em cada fonte de saúde, a seleção usa o município de residência, e não o de atendimento: `MUNIC_RES` no SIH, `ID_MN_RESI` no SINAN e os seis primeiros dígitos de `CODMUNRES` no SIM. Com isso, numerador e denominador se referem à mesma população. Uma internação de residente em hospital de outro município conta, e a de não residente atendido em Parauapebas não conta.

No SIH entram só as AIH do tipo 1 (`SIH_IDENT_NORMAL`). A AIH do tipo 5, de longa permanência, continua uma internação já contada e a contaria duas vezes (Bittencourt, Camacho e Leal, 2006, p. 26; decisão 0009). A internação entra no período pela data de internação, `DT_INTER`, e não pela competência do arquivo (decisão 0003). O grupo de agravo vem do diagnóstico principal, `DIAG_PRINC`. No SIM, o grupo vem da causa básica, `CAUSABAS`, e o período é contado por `DTOBITO`.

No SINAN, o período é contado pela data de notificação, `DT_NOTIFIC`. Os agravos lidos estão em `SINAN_AGRAVOS`. O caso é a notificação com classificação final de confirmado, pelos códigos de cada ficha em `SINAN_CLASSI_FIN` (decisão 0001). O relatório mostra notificados, confirmados, descartados e sem classificação; a taxa do período inteiro usa os confirmados, e o máximo possível (confirmados mais sem classificação) é a análise de sensibilidade. Por ano, o SINAN tem só contagens, porque com tão poucos casos uma taxa anual seria instável. Os agravos sem `CLASSI_FIN` (`SINAN_SEM_CLASSI_FIN`) são contados pelas notificações. O código de zika vem de ficha estadual e aguarda conferência no dicionário nacional. A diarreia aguda não é agravo do SINAN: ela é vigiada pelas unidades sentinela do Sivep-DDA e é tratada em análise separada, em `dda/`.

Os códigos usados para selecionar a população (RECORD 6.1) são os da tabela da seção Variáveis. Nenhum desses códigos foi validado contra prontuário em Parauapebas (RECORD 6.2), e o estudo depende da qualidade da codificação feita no faturamento.

A ligação entre bases (RECORD 6.3) é feita só dentro do SISAGUA: cada amostra do arquivo de qualidade se liga ao cadastro da solução de abastecimento pela chave `NU_SOLUCAO_ABASTECIMENTO`, depois de conferir que a chave não se repete no mesmo ano do cadastro, nesta ordem: o cadastro do ano da coleta; se não houver, o do ano anterior mais próximo; se não houver nenhum anterior, o do ano seguinte mais próximo (decisão 0005). Uma amostra de solução sem cadastro em nenhum ano fica sem par. SIH, SINAN, SIM e SISAGUA não são ligados por pessoa. Eles só se encontram no mesmo mês e no mesmo município.

## Variáveis (item 7 e RECORD 7.1)

O desfecho principal é a internação por DRSAI de residente, na classificação da FUNASA (2010), que segue Cairncross e Feachem (1993). Cada internação recebe um único grupo, e o código CID-10 é comparado pelos três primeiros caracteres, porque o SIH grava `A090` para A09.0 (decisão 0004). O indicador DRSAI soma os cinco grupos de `GRUPOS_DRSAI`. Os grupos fora do DRSAI são apresentados em blocos separados e nunca entram no total: as arboviroses que a lista da FUNASA não traz, os códigos de listas locais usados só na sensibilidade e os agravos do contexto climático.

A tabela abaixo é gerada a partir de `GRUPOS_AGRAVO` e `GRUPOS_DRSAI` em `src/config.py`. O teste `tests/test_documentacao.py` falha se ela divergir do config.

<!-- cid:inicio (gerado por tests/test_documentacao.py; não editar à mão) -->
| Grupo | Entra no indicador DRSAI | Códigos CID-10 (3 primeiros caracteres) |
|---|---|---|
| Feco-oral | sim | A00, A02, A03, A04, A06, A07, A08, A09, A01, B15 |
| Inseto vetor | sim | A90, A91, A97, A95, B55, B74, B50, B51, B52, B53, B54, B57 |
| Contato com água | sim | B65, A27 |
| Higiene | sim | A71, H10, B35, B36 |
| Geo-helmintos e teníases | sim | B68, B69, B70, B71, B76, B77, B78, B79, B80, B81, B82, B83 |
| Arboviroses fora do DRSAI | não | A92 |
| Sensibilidade | não | A05, E86, L00, L01, L02, L03, L04, L05, L06, L07, L08 |
| Contexto climático | não | J00, J01, J02, J03, J04, J05, J06, J07, J08, J09, J10, J11, J12, J13, J14, J15, J16, J17, J18, J19, J20, J21, J22, J40, J41, J42, J43, J44, J45, J46, J47, T63 |
<!-- cid:fim -->

A dengue inclui A97, da versão 2019 da CID-10, junto com A90 e A91. Na tabela unificada do SIGTAP da competência 03/2026 (`TabelaUnificada_202603_v2605181534.zip`, FTP do DATASUS, `ftp2.datasus.gov.br/pub/sistemas/tup/downloads/`, consultada em 20/10/2026), a tabela de CID (`tb_cid`) traz A90 e A91 e não traz A97. Sem os três códigos, parte dos casos se perderia.

Na água, os desfechos são o percentual de amostras fora do padrão em cada parâmetro físico-químico (cloro residual livre, turbidez e pH) e o percentual de amostras com coliformes totais ou *Escherichia coli* presentes. As covariáveis descritivas são sexo, faixa etária (`FAIXA_ETARIA_LIMITES` e `FAIXA_ETARIA_ROTULOS`), grupo de agravo, mês, ano, área e tipo da solução de abastecimento.

## Fontes e medição (item 8)

As internações vêm do SIH/SUS (AIH reduzida), as notificações do SINAN, os óbitos do SIM e a rede de estabelecimentos do CNES. As quatro bases são baixadas pelo PySUS. A origem, o espelho do projeto PySUS ou o servidor do DATASUS, fica em `PYSUS_SOURCE` e é registrada na proveniência. A qualidade da água e o cadastro das soluções de abastecimento vêm do SISAGUA, em arquivos CSV baixados à mão do portal de dados abertos do Ministério da Saúde e guardados em `data/raw/`. Os arquivos nacionais são lidos em blocos, só com as colunas necessárias e com o filtro de município aplicado durante a leitura.

O contexto sanitário vem do Censo 2022 (tabelas do SIDRA em `CENSO_2022_TABELAS`) e do SINISA (`SINISA_ARQUIVOS`). A chuva diária vem da reanálise ERA5 (Hersbach et al., 2020) pela API do Open-Meteo (`CLIMA_MODELO`). A reanálise descreve o padrão sazonal do município e não substitui uma estação local.

Cada arquivo lido tem um JSON de proveniência com fonte, origem, data do download, número de linhas e SHA-256 (`src/proveniencia.py`). Nos arquivos do PySUS, que devolve só o caminho local, a origem é o endereço do espelho ou do servidor (`PYSUS_ENDERECOS`) com os parâmetros da consulta, e a data do download é a da gravação do arquivo no cache. Quando a data do download não é conhecida, o registro diz "não registrado", e nunca a data da leitura. A completitude, a consistência e as duplicidades são avaliadas em `src/qualidade.py`, com a escala de incompletude de Romero e Cunha (2006) (`ESCALA_INCOMPLETUDE`). A estrutura de cada base é validada com pandera em `src/validacao.py`.

## Critérios da Portaria GM/MS nº 888/2021

Os limites seguem a Portaria GM/MS nº 888, de 4 de maio de 2021. O cloro residual livre tem mínimo de 0,2 mg/L (`CLORO_RESIDUAL_MINIMO`, art. 32). A turbidez tem máximo de 5 uT (`TURBIDEZ_MAXIMA`). O pH deve ficar entre 6,0 e 9,5 (`PH_MINIMO` e `PH_MAXIMO`). Para coliformes totais, a Portaria (Anexo 1) avalia o conjunto das amostras examinadas no mês pelo responsável pelo sistema: no sistema de distribuição, ausência em 100 mL em 95% das amostras nos sistemas que abastecem 20 mil habitantes ou mais, e no máximo uma amostra positiva no mês nos que abastecem menos de 20 mil; na saída do tratamento, ausência em 100 mL. Para *E. coli*, exige ausência em 100 mL, inclusive no sistema de distribuição. As amostras do SISAGUA usadas aqui são da vigilância; o critério mensal da Portaria vale para o controle feito pelo responsável pelo sistema. Por isso, o indicador microbiológico é o percentual de amostras com presença, sem aplicar o critério mensal da Portaria.

No SISAGUA, a coluna `RESULTADO` mistura números com vírgula decimal e texto (PRESENTE ou AUSENTE). A padronização separa os dois em `resultado_numerico` e `resultado_texto`. O ponto só é aceito como separador de milhar seguido de vírgula decimal ("1.234,56"); qualquer outro ponto interrompe a leitura, e a contagem de 18/10/2026 não achou nenhum ponto nos 6.539 valores (decisão 0010). Amostras sem resultado numérico válido saem do denominador do parâmetro, e o número delas aparece no relatório.

O número mínimo mensal de amostras segue a Diretriz Nacional do Plano de Amostragem do Vigiagua (Ministério da Saúde, 2016), pelas faixas de `PLANO_AMOSTRAGEM_FAIXAS`. A Diretriz não diz como arredondar a parcela variável. O projeto usa o arredondamento para cima (`PLANO_AMOSTRAGEM_ARREDONDAMENTO`) até a SEMSA ou a SESPA confirmarem a regra do plano municipal.

## Viés (item 9)

A principal fonte de viés é o sub-registro. O SIH só capta quem foi internado pelo SUS, e o SINAN só capta quem procurou atendimento e foi notificado. As duas bases medem universos diferentes e não são somadas nem divididas uma pela outra. O atraso de faturamento reduz as contagens dos últimos meses. A vigilância da água coleta mais em uns meses e lugares do que em outros, e por isso o número de amostras sempre aparece ao lado de cada percentual.

## Tamanho do estudo (item 10)

O estudo usa todos os registros do período, sem cálculo de tamanho de amostra. Quando um grupo tem menos de `LIMIAR_AMOSTRA_MINIMA` casos, o relatório avisa que a estimativa é instável (decisão 0018). Proporções de amostras de água com menos de `LIMIAR_AMOSTRAS_PROPORCAO` amostras são marcadas (decisão 0020).

## Variáveis quantitativas (item 11)

A idade é convertida para anos completos a partir do código de unidade de cada sistema (`SIH_COD_IDADE_*`, `SINAN_UNIDADE*` e `SIM_UNIDADE*`) e agrupada nas faixas do config. Os resultados de água são analisados na unidade da Portaria: mg/L, uT e escala de pH.

## Métodos estatísticos (item 12 e RECORD 12.1 a 12.3)

As taxas são dadas por 100 mil pessoas-ano. O denominador é a população do IBGE de cada ano (`POPULACAO_ANUAL`). Quando o período não cobre um ano inteiro, cada ano entra com a fração de dias observados, o que dá pessoa-tempo (`pessoa_tempo` em `src/estatistica.py`, decisão 0002). As estimativas de 2024 a 2026 são as publicadas pelo IBGE no Diário Oficial. O IBGE não publica estimativa municipal para 2023. Para esse ano, o projeto usa a média geométrica entre o Censo 2022 e a estimativa de 2024, valor calculado pelo projeto e não oficial.

Toda taxa leva intervalo de confiança de 95% exato de Poisson, pelo método de Garwood (1936) (`ic_garwood`): o limite inferior é χ²(0,025; 2k)/2, igual a zero quando k = 0, e o superior é χ²(0,975; 2k+2)/2, divididos pela pessoa-tempo. O método exato vale para contagens pequenas, comuns num município de 300 mil habitantes, em que a aproximação normal dá limites negativos ou estreitos demais.

As proporções (percentual de amostras fora do padrão, percentual de amostras com presença microbiológica, letalidade, proporção de óbitos por DRSAI, local das internações e residentes internados fora do Pará) levam intervalo de 95% de Wilson (1927) (`ic_wilson`). O intervalo de Wald falha quando a proporção fica perto de 0 ou de 100%, e isso acontece nesses indicadores. As proporções de cadastro ou estrutura (composição do cadastro do SISAGUA, estabelecimentos do CNES com e sem vínculo SUS, indicadores do SINISA e do Censo) não levam IC, porque são contagens completas. Como não são amostras nem eventos de saúde, não há variação aleatória para o intervalo medir.

Cada ano tem sua taxa anualizada por pessoa-tempo (decisão 0006), que aparece só como descrição, com o ano parcial marcado. A comparação entre anos usa só os meses do calendário cobertos em todos os anos (`meses_comuns`; com o período atual, janeiro a junho), com a pessoa-tempo desses meses (decisão 0008, que substitui em parte a 0006). A razão de taxas contra o primeiro ano da série é calculada nesses meses e tem IC pelo logaritmo, exp(ln RT ± 1,96 √(1/a + 1/b)) (`razao_taxas`; Rothman, Greenland e Lash, 2008). A razão não é calculada quando um dos anos tem zero casos. Os meses comuns não corrigem o atraso de faturamento: maio e junho de 2026 continuam incompletos. Nenhum p-valor é apresentado, e por isso não se aplica correção para comparações múltiplas.

O acesso às bases (RECORD 12.1) foi dado só aos dados públicos e anonimizados do DATASUS e do portal de dados abertos, sem acesso à população completa identificada. A limpeza (RECORD 12.2) está em `src/transformacoes.py`, e cada registro descartado é contado na proveniência com o motivo. A seção 25 do relatório mostra todas as etapas de filtro de cada base, com as linhas antes e depois, inclusive as que não removeram nada, e separa o descarte (registro inválido) do recorte (registro fora do escopo do estudo). A ligação (RECORD 12.3) só existe dentro do SISAGUA, como descrito em Participantes, e o número de amostras ligadas no mesmo ano, no ano anterior, no ano seguinte ou sem par aparece no relatório, na seção 12 (divergência de desinfecção) e na seção 14 (origem da captação).

## Análise de sensibilidade (item 12e)

A primeira análise refaz os indicadores principais só com os anos completos e tira o primeiro semestre de 2026 (`sensibilidade_sem_ano_parcial`). Se o resultado pouco muda, a descrição não depende do ano parcial, que tem atraso de faturamento. Essa análise cobre só o indicador do período inteiro.

A segunda análise acrescenta os códigos do grupo "Sensibilidade" (intoxicação alimentar bacteriana, desidratação e infecções bacterianas de pele), que aparecem em listas locais mas não na da FUNASA. O resultado é mostrado à parte e nunca somado ao DRSAI.

Na análise do Sivep-DDA, a contagem é repetida com limites de 10 a 1000 vezes a mediana para corrigir valores implausíveis de unidades informantes (`dda/sensibilidade_limpeza.py`, decisão 0021).

## Limitações (item 19 e RECORD 19.1)

O desenho ecológico não permite atribuir os agravos à água nem tirar conclusão sobre quem foi internado. As bases de rotina medem uso de serviço e notificação, que são só uma parte da ocorrência real da doença. O SIH só cobre o SUS e não capta a rede privada. Os dados de 2025 e 2026 são preliminares, e as contagens dos últimos meses tendem a crescer nas próximas extrações.

O SIH do relatório é lido só nos arquivos do Pará, que são organizados pela UF do hospital. A internação de um residente de Parauapebas num hospital de outra UF fica fora. O tamanho dessa perda foi medido à parte com `sih/sih_nacional.py`, que lê os arquivos RD de todas as UFs com os mesmos critérios (AIH do tipo 1, ano por `DT_INTER`, residência por `MUNIC_RES`). Ficaram fora 192 de 13.207 internações de residentes em 2025 (1,5%) e 67 de 5.930 em 2026, até junho (1,1%) (`SIH_RESIDENTES_FORA_DO_PARA`). Os percentuais levam IC 95% de Wilson (`ic_wilson`), como as demais proporções de eventos de saúde: as internações de cada ano são tratadas como resultado de um processo sujeito a variação aleatória, e o IC mostra a incerteza do percentual como medida da perda. Todas as taxas de internação ficam, portanto, um pouco subestimadas. A leitura das 27 UFs é a proposta da decisão 0019, para a versão publicada. O relatório mostra essa limitação nas ressalvas sobre as fontes.

Vários pontos do config ainda dependem de conferência na fonte original. A lista do grupo de geo-helmintos e teníases foi montada a partir de reproduções secundárias do quadro da FUNASA. O significado de `COD_IDADE` no SIH foi inferido das faixas observadas e precisa ser conferido no dicionário de dados. Os códigos de "ignorado" do SINAN (`CODIGOS_IGNORADO`) também precisam de conferência; os do SIM, e a codificação da `IDADE` do SIM, foram conferidos na Estrutura do SIM do MS/SVS em 21/10/2026. A população de 2023 é calculada pelo projeto. A regra de arredondamento do plano de amostragem aguarda a SEMSA.

Na água, o SISAGUA registra as amostras da vigilância, e o volume de coleta varia entre anos e áreas. Quando falta o cadastro do ano da coleta, a ligação usa o de outro ano e pode atribuir a uma amostra características que a solução não tinha naquele ano (decisão 0005). A chuva de reanálise, numa grade de cerca de 25 km, não representa a chuva de um bairro.

As taxas são brutas, sem padronização por idade. Parauapebas tem estrutura etária própria, formada pela migração para a mineração, e as taxas não devem ser comparadas com as de outros locais sem padronização (decisão 0007).

## Referências

BENCHIMOL, E. I. et al. The REporting of studies Conducted using Observational Routinely-collected health Data (RECORD) statement. *PLOS Medicine*, v. 12, n. 10, e1001885, 2015.

BITTENCOURT, S. A.; CAMACHO, L. A. B.; LEAL, M. C. O Sistema de Informação Hospitalar e sua aplicação na saúde coletiva. *Cadernos de Saúde Pública*, Rio de Janeiro, v. 22, n. 1, p. 19-30, 2006.

BRASIL. Ministério da Saúde. Portaria GM/MS nº 888, de 4 de maio de 2021. Altera o Anexo XX da Portaria de Consolidação GM/MS nº 5, de 28 de setembro de 2017, para dispor sobre os procedimentos de controle e de vigilância da qualidade da água para consumo humano e seu padrão de potabilidade. *Diário Oficial da União*, Brasília, 7 maio 2021.

BRASIL. Ministério da Saúde. *Diretriz Nacional do Plano de Amostragem da Vigilância da Qualidade da Água para Consumo Humano*. Brasília: Ministério da Saúde, 2016.

CAIRNCROSS, S.; FEACHEM, R. *Environmental health engineering in the tropics*: an introductory text. 2. ed. Chichester: John Wiley & Sons, 1993.

FUNDAÇÃO NACIONAL DE SAÚDE (FUNASA). *Impactos na saúde e no Sistema Único de Saúde decorrentes de agravos relacionados a um saneamento ambiental inadequado*. Brasília: Funasa, 2010.

GARWOOD, F. Fiducial limits for the Poisson distribution. *Biometrika*, v. 28, n. 3-4, p. 437-442, 1936. DOI: 10.1093/biomet/28.3-4.437.

HERSBACH, H. et al. The ERA5 global reanalysis. *Quarterly Journal of the Royal Meteorological Society*, v. 146, n. 730, p. 1999-2049, 2020. DOI: 10.1002/qj.3803.

MORGENSTERN, H. Ecologic studies in epidemiology: concepts, principles, and methods. *Annual Review of Public Health*, v. 16, p. 61-81, 1995.

PARKER, J. D. et al. National Center for Health Statistics data presentation standards for proportions. *Vital and Health Statistics*, Series 2, n. 175. Hyattsville: National Center for Health Statistics, 2017.

PARKER, J. D. et al. National Center for Health Statistics data presentation standards for rates and counts. *Vital and Health Statistics*, Series 2, n. 200. Hyattsville: National Center for Health Statistics, 2023. DOI: 10.15620/cdc:124368.

ROMERO, D. E.; CUNHA, C. B. Avaliação da qualidade das variáveis sócio-econômicas e demográficas dos óbitos de crianças menores de um ano registrados no Sistema de Informações sobre Mortalidade do Brasil (1996/2001). *Cadernos de Saúde Pública*, v. 22, n. 3, p. 673-681, 2006. DOI: 10.1590/S0102-311X2006000300022.

ROTHMAN, K. J.; GREENLAND, S.; LASH, T. L. *Modern epidemiology*. 3. ed. Philadelphia: Wolters Kluwer Health/Lippincott Williams & Wilkins, 2008.

SOUZA, M. K. M. S. *A urbanização de Parauapebas/PA*: a cidade produzida pela mineração. Tese (Doutorado em Geografia) – Universidade Federal da Paraíba, João Pessoa, 2024. Disponível em: https://repositorio.ufpb.br/jspui/handle/123456789/34639.

VON ELM, E. et al. The Strengthening the Reporting of Observational Studies in Epidemiology (STROBE) statement. *The Lancet*, v. 370, n. 9596, p. 1453-1457, 2007.

WILSON, E. B. Probable inference, the law of succession, and statistical inference. *Journal of the American Statistical Association*, v. 22, n. 158, p. 209-212, 1927. DOI: 10.1080/01621459.1927.10502953.
