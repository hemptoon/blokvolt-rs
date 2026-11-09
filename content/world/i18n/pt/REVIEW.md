# R-PT — revisão do pt-PT (10.11.2026)

Base: `origin/l-pt` (fa138e3). Ramo: `r-pt`. `check.py`: 0 erros.

## Resultado

O texto da L-PT está bom: pt-PT consistente (AO1990), impessoal, sem «nós», «você» ou brasileirismos; plurais CLDR corretos. As correções são pontuais.

## Cadeias — 403 lidas, 8 alteradas

- `strings_shell.search_none`: «Abrir o mapa em alternativa.» (infinitivo solto) → «Em alternativa, abra o mapa.»
- `strings_shell.home_desc`: «de dados abertos com fonte e data» → «a partir de dados abertos, com fonte e data».
- `strings_shell.region_h`: «Sérvia e Balcãs» → «Sérvia e os Balcãs».
- `strings_pages.ft_region`: «Sérvia e região» → «Sérvia e a região».
- `strings_prices.h_n_compare`: «…e com casa» → «…e com o carregamento em casa».
- `strings_prices.h_profiles`: vírgula → dois pontos.
- `strings_prices.profiles_note`: «Partes do carregamento» → «Repartição do carregamento».
- `strings_map.acc_all`: «Mostrar também os restantes» (27 car., > EN × 1,4) → «Incluir não públicos» (20).

Comprimento: os restantes rótulos acima de EN × 1,4 são palavras únicas sem alternativa mais curta (Potência, Partilhar, Cidade…) — mantidos.

## Países — 150 lidos, 9 alterados

- Sem artigo em pt-PT: «em Espanha», «em França», «em Itália», «em Mianmar».
- «no Botsuana» (masculino em pt-PT).
- Formas da imprensa em vez de CLDR raro: Liechtenstein, Sri Lanka, Ilhas Åland, Guernsey (slugs atualizados: `liechtenstein`, `sri-lanka`, `ilhas-aland`, `guernsey`). Koweit mantido (forma corrente em Portugal).

## Cidades — 107 de PT/BR lidas uma a uma; restantes `month`/`quarter` com nome diferente do local ou com artigo (268) verificadas

- 4 freguesias portuguesas: «na localidade de X» → «em Vilar», «em Eiras», «em Bougado», «em Vilar de Andorinho», `decl_ok = 1`.
- Erro de mapeamento: 17 cidades dos EUA/Canadá recebiam o exónimo da homónima europeia (Athens GA → «Atenas», Venice → «Veneza», London ON → «Londres», Naples, Rome, Florence, Hanover, Syracuse, Amsterdam, Rotterdam, Sparta, Corinth, Valencia). Repostos os nomes locais. Mantidos Nova Iorque, São Francisco, Filadélfia, Nova Orleães, Quebeque.
- Grécia: Tripoli → Trípoli.
- Restantes cidades estrangeiras: nome local + «em X» — gramaticalmente sempre correto em pt-PT.

## Slugs

ASCII, naturais (`/pt/postos-de-carregamento/`, `rede`, `sobre-os-dados`, `descarregar`…). Não há `content/com/local/pt/`; prefixo `/pt/` não colide com EN/SR/RU. Nenhum slug de cidade coincide com `rede`/`sobre-os-dados`/`descarregar`; slugs de países sem duplicados.

## Retrotradução

Agente independente retraduziu as 15 alterações (cadeias + grupos de países/cidades): sentido preservado. Aceites as suas sugestões: «Itinerário» mantido (não «Direções»), «a partir de 50 kW» mantido no cabeçalho da tabela, `acc_all` explícito.

## Em aberto

- `about_p` diz «independente», como EN; o CONTENT_STYLE evita a palavra nos guias SR — decisão no EN.
- `pct` = `{x}%` sem espaço, enquanto as notas usam «10 %»: a norma portuguesa admite ambos; uniformizar no motor (K8).
- «Kiev» vs «Kyiv»: mantido Kiev (uso da imprensa portuguesa).
