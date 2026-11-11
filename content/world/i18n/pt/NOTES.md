# L-PT — notas (09.11.2026)

## Variante e tom

- **Português europeu (pt-PT)**, Acordo Ortográfico de 1990. Escolhido porque o mundo do BlokVolt é sobretudo a Europa e a MOBI.E é a referência terminológica em Portugal. Uma variante pt-BR pode reutilizar ~90 % do texto (diferenças: registo/registro, descarregar/baixar, ecrã/tela, nomes de países como Polónia/Polônia).
- hreflang sugerido: `pt-PT` (ou `pt` se não houver pt-BR). og: `pt_PT`.
- Tom impessoal: sem «nós», sem «a redação», sem «você». Botões no infinitivo («Abrir o mapa»); na prosa, construções impessoais («convém confirmar…», «é possível…»). Em 3–4 mensagens curtas de erro/ajuda do mapa ficou o imperativo de cortesia («Tente novamente», «Arraste», «aproxime») — equivalente ao «vi»/Sie.
- Números: separador decimal vírgula, milhares com espaço fino (norma portuguesa): `1 234,5`; percentagem `12 %`.

## Plurais (CLDR pt_PT, Babel 2.18)

- Categorias: `one` (só 1 inteiro), `many` (milhões redondos: «1 000 000 de locais»), `other` (0, 2, 1,5 …).
- Atenção: em pt_PT **0 é `other`** («0 cidades»), diferente de pt-BR (0 = one).
- `many` = «de » + forma `other` em todas as chaves `pl_*`.

## Terminologia (glossary.csv não tem coluna pt — proposta para acrescentar)

| EN | pt-PT |
|---|---|
| charging station | posto de carregamento |
| charger (rótulo curto) | carregador |
| charging point | ponto de carregamento |
| charging location | local de carregamento |
| charging network / operator | rede de carregamento / operador |
| connector | conector |
| power | potência |
| fast / HPC charging | carregamento rápido / ultrarrápido |
| open data | dados abertos |
| reliability | fiabilidade |
| registry | registo |
| download | descarregar |
| tariff / price | tarifário / preço |
| ad hoc | ad hoc |
| subscription / plan | assinatura / plano |
| idle fee | taxa de ocupação |
| VAT | IVA («com IVA» / «sem IVA») |
| report (problema no mapa) | comunicação |
| breadcrumbs | navegação estrutural |

## Plugs de frase

- `{country_u}`, `{city_u}` e `fallback_u` recebem a frase com preposição e artigo: `in_phrase` de `countries.csv`/`cities.csv` («na Alemanha», «nos Países Baixos», «no Porto», «em Berlim»).
- `d_city`, `t_city`, `t_city_cc` usam `{city_u}` em vez de `{city}`, como já faz o SR; `check.py` aceita os plugs de EN, SR ou RU.

## Países (`countries.csv`)

- Nome: CLDR **pt_PT** (Babel), não a coluna `name_pt` de `names/countries.csv`, que é pt-BR (Armênia, Polônia, Irã, Vietnã).
- Encurtados: Hong Kong, Macau, Mianmar, São Martinho. El Salvador em vez do CLDR «Salvador» (confusão com a cidade brasileira).
- Mantidas as formas oficiais pt-PT do CLDR, embora menos usadas na imprensa: Listenstaine, Sri Lanca, Koweit, Alanda, Guernesey — decisão em aberto (ver perguntas).
- Preposição: «em» sem artigo (Portugal, Andorra, Cuba, Chipre, Malta, Israel, Singapura, Macau, Hong Kong, Taiwan, Marrocos, Omã…), «no/na/nos/nas» com artigo para os restantes.

## Cidades (`cities.csv`)

- Todas as 5 605 cidades; ordem: países de língua oficial portuguesa → `stage = month` → resto.
- Nome: exónimo pt-PT quando consagrado (115: Munique, Colónia, Francoforte, Nuremberga, Amesterdão, Roterdão, Haia, Varsóvia, Moscovo, Atenas, Salónica, Nova Iorque…); nome EN para escrita não latina (158: grego, búlgaro, russo, chinês, coreano…); restante — nome local.
- `in_phrase`: «em X» para cidades estrangeiras (sem artigo em português); com artigo para as portuguesas/brasileiras que o exigem (no Porto, na Maia, nas Caldas da Rainha, no Funchal, no Rio de Janeiro, no Recife, na Haia, no Cairo, na Cidade do México…).
- `decl_ok = 0` e «na localidade de X» em 4 casos de artigo incerto: Vilar, Eiras, Bougado, Vilar de Andorinho.

## Verificação

- `python3 content/world/i18n/pt/check.py` → 0 erros.
- Retrotradução de 60 frases aleatórias para EN por um agente independente: ver secção abaixo.

## O que falta

- Revisão por um falante nativo de pt-PT (sobretudo títulos SEO e textos longos de `texts.json`).
- Acrescentar a coluna `pt` ao `glossary.csv` (proposta acima).
- Decidir se o site também precisa de pt-BR.

## Retrotradução (60 frases aleatórias, agente independente)

- 60/60 com o mesmo sentido do EN; nenhum brasileirismo, nenhum «você», nenhum «nós».
- Assinalado `strings_prices.t_country` («Preços de carregamento de VE {country_u}») — correto, porque `{country_u}` já traz «na Alemanha».
- `attribution` de fontes (AFDC, Overture, NSW, Luxemburgo) e «© OpenStreetMap contributors» ficaram na língua original de propósito: texto de atribuição exigido pela licença.
- `odbl_note` uniformizado para «ao abrigo da licença».

## FIXL (11.11.2026)

- D14: `countries.csv` tem a coluna `name_nom` (forma com artigo: «a Suíça», «os Países Baixos», «o Reino Unido», «Portugal»,
  «a França»). Usada em `strings_pay` `afir_eu`, `afir_non`, `conn_txt`; `conn_lnk` fica com `{name}`.
  Regra: nunca `{name_nom}` depois de «de/em/a/por» (contração); evitar `{name_nom}` como sujeito de verbo (concordância no plural).
- Slugs (F5): `/pt/como-pagar/`, `/pt/itinerarios/`, `/pt/imprensa/`, `/pt/dados-para-empresas/`, `/pt/embed/mapa/`,
  `/pt/mapa-para-o-seu-site/`, `/pt/programadores/`.
- Home (F3): «local de carregamento» para "charging place"; botões no infinitivo; Asia-Pacific = «Ásia-Pacífico».
- Cidades: 48 NOBIL (nome local, «em X») + Genebra (2660646, «em Genebra»).
