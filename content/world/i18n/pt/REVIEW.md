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

---

# L2-PT — delta de chaves e textos de dados (11.11.2026)

Ramo `l2-pt` a partir de `dev` (bb86f74). HOME2 ainda não está em `dev` — sem chaves novas da página inicial.

## Feito
- 274 chaves novas: `strings_map` +29 (28 `ci_*`, `emb_open`), ficheiros novos `strings_pay` 93, `strings_press` 54, `strings_b2b` 33, `strings_embed` 65.
- `texts.json`: secções `pay` (6 nós `afir.points[i]`) e `routes` (59 nós `routes[i].stops[j].city`, nomes de `cities.csv`: Belgrado, Budapeste, Salzburgo, Liubliana, Sófia…); `sources_pages` sincronizado com o novo `nobil`.
- `cities.csv`: Sofia → Sófia (exónimo pt-PT). Portugal: 56 cidades com página verificadas (nome, artigo, `in_phrase`) — sem alterações; 100/100 cidades PT presentes.
- `check.py`: 8 ficheiros + `texts.pay`/`texts.routes` (nó existe, placeholders e tags como EN) → 0 erros.
- Termos: portagem, vinheta, itinerário, paragem, troço, imprensa, widget, «Listado». Tom impessoal; mensagens de erro no imperativo de cortesia, como no mapa.

## Retrotradução (60 cadeias novas, agente às cegas)
60/60 com o sentido do EN. 14 notas; corrigido:
- «a até X km» → «num raio de X km» (lead_routes, lead_route, gap_line, method, stops_note);
- stops_note: «quando há dois próximos um do outro»;
- d_route: «três modelos de carro»; b2b.what_price: «moeda local e valor em EUR»;
- dv_p_lang: «definido pelo endereço do widget»; cf_view: «vista exata do mapa».
Mantido: `{cu}`/`{lo}`/`{hi}` já trazem preposição+artigo (`names.in_`, `world_pay.cu`); «Pontos» como cabeçalho curto ao lado de kW; «Listado».

## Em aberto
- 144 cidades novas NOBIL (SE 138, NO 6) não estão em `names/cities.csv` → não podem entrar em `cities.csv` (fora do mercado pt; motor usa EN).
- `dv_p_lang` diz «(EN, SR, RU)» como o EN — atualizar no EN quando o widget tiver mais idiomas.
- `world_press.py` tem cadeias `de` embutidas — assunto do LANG0.

## FIXL 11.11.2026

- Verificado: novo `strings_home.json` (71 chaves), `lang_hint`/`lang_hint_close`, D11 (`dv_p_lang`, `p_hub_na`), D14
  (`name_nom` em `countries.csv`; `afir_eu`, `afir_non`, `conn_txt`), 7 slugs novos, 49 cidades (48 NOBIL + Genebra).
- Retrotradução PT→EN, vaga 1: 20 chaves aleatórias de `strings_home` (as mesmas do NL) + as 8 cadeias alteradas.
- Divergências corrigidas:
  - `afir_non` (1.ª versão «…não abrange {name_nom}, que fica fora da UE») — concordância errada com nomes no plural
    («os Estados Unidos, que fica») → «…não se aplica fora dela, pelo que as regras abaixo podem não valer para {name_nom}»
    (preposição «para» não se contrai com o artigo).
  - `p_city_cmp` tinha «em média em {country_name}» → «em Alemanha» (falta o artigo). Agora «…em média no país ({country_name})».
- Regra D14 para pt: `{name_nom}` só em posição sem preposição contraível (sujeito/objeto direto ou depois de «para»);
  nunca depois de «de/em/a» (dariam «de a Alemanha»). Sujeitos com verbo evitados por causa do plural (Países Baixos, Filipinas).
- `name_nom`: derivado de `in_phrase` (no→o, na→a, nos→os, nas→as, em→sem artigo), com exceções: «a Espanha», «a França»,
  «a Itália», «o Essuatíni» (em pt-PT «em França», mas «a França» como sujeito).
- D12: nenhum exónimo histórico/irredentista encontrado (Escópia, Carcóvia, Kiev, Salónica são exónimos pt-PT correntes).
- Dúvidas: título 78 caracteres (EN 72); «Viagens de carro» para «Road trips».
