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
