# TR back-translation QA (seed 42, 60 keys)

**Counts:** ok 57 / minor 3 / mismatch 0. Fixes applied to TR JSON: 9 (2 from sample, 7 from the {country_u} scan).

Summary: meaning matches EN in all 60 sampled strings; no first person (biz/mi), no informal sen-forms (imperatives use -in: indirin, düzeltin), placeholders intact, no suffixes glued to placeholders. One real grammar error (OSM attribution accusative). Main systemic problem was outside the sample: 7 strings put {country_u} (a ready locative, "Almanya'da") after a colon or as a bare label, giving "Endeks: Almanya'da" etc.

| file | key | TR (original) | back-EN (blind) | EN | verdict |
|---|---|---|---|---|---|
| prices | m2 | Sınıflar: AC; DC 50–149 kW; 150 kW'tan itibaren HPC. Tüm DC şarj için tek fiyat uygulayan bir şarj ağı hem DC hem HPC sınıfına girer. Bir ağın en yüksek sınıfı 50 veya 60 kW'tan başlıyorsa bu fiyat yalnızca DC olarak sayılır. | Classes: AC; DC 50–149 kW; HPC from 150 kW. A charging network that applies one price to all DC charging falls into both the DC and HPC classes. If a network's highest class starts at 50 or 60 kW, that price counts only as DC. | Classes: AC; DC 50–149 kW; HPC from 150 kW. A network that charges one price for all DC enters both DC and HPC. Where a network's top class starts at 50 or 60 kW, that price counts as DC only. | ok |
| map | c_pts | Şarj noktaları | Charging points | Charging points | ok |
| map | t_ac | AC, 22 kW'a kadar | AC, up to 22 kW | AC up to 22 kW | ok |
| prices | th_cindex | Ülke endeksi | Country index | Country index | ok |
| pages | download_link | Açık verileri indirin (ODbL) | Download the open data (ODbL) | Download the open data (ODbL) | ok |
| pages | balkan_note | Bu ülkelerin, kontrol edilmiş verilerle hazırlanmış ayrı BlokVolt sayfaları vardır. | These countries have separate BlokVolt pages prepared with checked data. | These countries have their own BlokVolt pages with checked data. | ok |
| map | ch_ft_data | Haritalar: © <a href="https://www.openstreetmap.org/copyright" rel="noopener">OpenStreetMap</a> katkıda bulunanları, <a href="https://openchargemap.org" rel="noopener">Open Charge Map</a> | Maps: © OpenStreetMap contributors (accusative form), Open Charge Map | Maps: © <a href="https://www.openstreetmap.org/copyright" rel="noopener">OpenStreetMap</a> contributors, <a href="https://openchargemap.org" rel="noopener">Open Charge Map</a> | minor - Turkish error: OSM attribution must be nominative "katkıda bulunanlar", not accusative "-ları". FIXED. |
| map | osm_fix | OpenStreetMap'te de düzeltin | Fix it on OpenStreetMap too | Correct it in OpenStreetMap too | ok |
| prices | h_n_compare | Ülke ve evde şarjla karşılaştırma | Comparison with country and home charging | Compared with the country and with home | minor - "Ülke ve evde şarj" is ambiguous ("country charging"); EN means the country average. FIXED to "Ülke ortalaması ve evde şarjla karşılaştırma". |
| map | c_unnamed | Elektrikli araç şarj istasyonu | Electric vehicle charging station | EV charging station | ok |
| prices | th_fees | Diğer ücretler | Other fees | Other fees | ok |
| prices | h1_hub | Avrupa Elektrikli Araç Şarj Fiyat Endeksi — {month} | European EV Charging Price Index — {month} | European EV Charging Price Index — {month} | ok |
| map | sources_btn | Kaynaklar ve lisanslar | Sources and licences | Sources and licences | ok |
| prices | h_table | Ülkelere göre fiyatlar | Prices by country | Prices by country | ok |
| pages | t_hub_month_na | Avrupa, ABD ve Kanada'daki elektrikli araç şarj istasyonları | Electric vehicle charging stations in Europe, the USA and Canada | EV charging stations in Europe, the US and Canada | ok |
| map | f_net | Şarj ağı | Charging network | Network | ok - "Şarj ağı" = network (explicit, fine). |
| map | t_unk | Güç bilinmiyor | Power unknown | Power unknown | ok |
| map | attr_map | Harita | Map | Map | ok |
| map | ch_ft_checked | kontrol edildi | checked | checked | ok |
| map | ch_nav_region | Bölge (İngilizce) | Region (English) | Region (English) | ok |
| shell | region_h | Sırbistan ve Balkanlar | Serbia and the Balkans | Serbia and the Balkans | ok |
| prices | th_ratio | DC / ev | DC / home | DC vs home | ok |
| map | t_dc | DC, 149 kW'a kadar | DC, up to 149 kW | DC up to 149 kW | ok |
| prices | cur_label | Para birimi | Currency | Currency | ok |
| map | r_ok | Teşekkürler. Bildirimler haftada bir incelenir; düzeltme bir sonraki veri güncellemesinden sonra görünür. | Thanks. Reports are reviewed once a week; the fix appears after the next data update. | Thank you. Reports are reviewed once a week; a correction appears after the next data update. | ok |
| prices | pay_sub | Abonelikler: {list}. | Subscriptions: {list}. | Plans: {list}. | minor - "Abonelikler" (subscriptions) vs EN "Plans"; consistent with "abonelikle" used for "with a plan" elsewhere, no fix. |
| prices | dl_index | Ülkelere göre endeks (CSV) | Index by country (CSV) | Index by country (CSV) | ok |
| prices | th_car | Araç | Car | Car | ok |
| pages | t_gnet | Ülkelere göre {net} şarj istasyonları | {net} charging stations by country | {net} charging stations by country | ok |
| map | ch_ft_charging | Şarj | Charging | Charging | ok |
| pages | th_name | Lokasyon | Location | Location | ok |
| prices | lg_home | Ev elektriği | Home electricity | Home electricity | ok |
| pages | fast_more | {total} hızlı şarj noktasından {shown} tanesi gösteriliyor; haritada tümü yer alır. | Showing {shown} of {total} fast charging points; the map has all of them. | Showing {shown} of {total} fast chargers; the map shows all. | ok |
| map | lead | Sırbistan ve bölge dışındaki halka açık şarj noktaları, açık verilerden. | Public charging points outside Serbia and the region, from open data. | Public chargers outside Serbia and the region, from open data. | ok |
| prices | per_100 | 100 km başına | Per 100 km | per 100 km | ok |
| map | acc_restricted_private | Özel | Private | Private | ok |
| prices | hpc_note | HPC sütunu: şarj ağının 150 kW'ın altında (50, 60 veya 100 kW'tan) başlayan en yüksek güç sınıfı; DC sütunu 50 kW altı bir sınıfı gösteriyorsa bu fiyat endeksin DC fiyatıdır | HPC column: the network's highest power class that starts below 150 kW (from 50, 60 or 100 kW); if the DC column shows a class below 50 kW, this price is the index's DC price | HPC column: the network's top power class, which starts below 150 kW (from 50, 60 or 100 kW); where the DC column is a class under 50 kW, this price is the DC price of the index | ok |
| pages | nav_hub | Şarj istasyonları | Charging stations | Charging stations | ok |
| map | acc_public_notice_required | Halka açık, önceden bildirimle | Public, with advance notice | Public, by prior notice | ok |
| map | ch_ft_claim | Sırbistan'da ve komşu ülkelerde elektrikli araç nerede şarj edilir, ne kadara mal olur ve kurallar nelerdir. | Where to charge an EV in Serbia and neighbouring countries, how much it costs and what the rules are. | Where to charge an electric car in Serbia and its neighbours, what it costs and what the rules are. | ok |
| prices | dash_none | fiyat yok | no price | no price | ok |
| pages | nav_about | Veriler hakkında | About the data | About the data | ok |
| pages | p_hub | Orta veya yüksek güvenilirlikte en az 100 halka açık lokasyonu olan her ülkenin bir sayfası vardır. Batı Balkanlar, her ülke için ayrı BlokVolt sayfalarında ele alınır. | Every country with at least 100 public locations of medium or high reliability has a page. The Western Balkans are covered on separate BlokVolt pages for each country. | Countries with at least 100 public locations of medium or high reliability have a page. The Western Balkans are covered by the BlokVolt pages of each country. | ok |
| map | close | Kapat | Close | Close | ok |
| pages | p1 | 7 kW'a kadar AC | AC up to 7 kW | AC up to 7 kW | ok |
| pages | net_page | şarj ağı sayfası | charging network page | network page | ok - as above |
| prices | th_nets | Şarj ağları | Charging networks | Networks | ok - as above |
| pages | d_network | Açık verilere göre {country_u} {net} şarj lokasyonları: güç, konnektörler ve şehirler, kaynaklarıyla birlikte. | {net} charging locations {country_u} according to open data: power, connectors and cities, with their sources. | {net} charging locations {country_u} from open data: power, connectors and cities, with sources. | ok - Reads "Açık verilere göre Almanya'da Tesla şarj lokasyonları" - natural. |
| map | net_remove | Filtreyi kaldır: {x} | Remove filter: {x} | Remove filter: {x} | ok |
| prices | more_local | Yerel bölüm | Local section | Local section | ok |
| pages | unknown_net | Şarj ağı bilinmiyor | Charging network unknown | Network not known | ok - as above |
| shell | method_p | Farklı kaynaklardan gelen ve aynı yeri tanımlayan kayıtlar tek kayıtta birleştirilir. Her lokasyona 0 ile 100 arasında bir veri güvenilirliği puanı verilir (kaynak türü, ikinci bir kaynak, güncellik). Bir ülke sayfası için güvenilirliği 50 veya üzeri olan en az 100 halka açık lokasyon, bir şehir sayfası için en az 20 lokasyon gerekir. Formül ve eşikler burada açıklanır: | Records from different sources describing the same place are merged into one. Each location gets a data reliability score from 0 to 100 (source type, a second source, recency). A country page needs at least 100 public locations with reliability 50 or higher; a city page needs at least 20 locations. The formula and thresholds are explained here: | Records from different sources that describe one place are merged into one. Each place gets a data reliability from 0 to 100 (source type, a second source, freshness). A country page needs at least 100 public places with reliability 50 or more, a city page at least 20. The formula and the thresholds are explained here: | ok |
| map | conf_hi | Yüksek | High | High | ok |
| pages | p_gnet | {net}, {n_countries} bulunuyor. | {net} is present {n_countries}. | {net} appears in {n_countries}. | ok - {n_countries} = pl_country_in ("12 ülkede"), so locative is supplied; reads "{net}, 12 ülkede bulunuyor." |
| map | lg_hpc | 150+ kW | 150+ kW | 150+ kW | ok |
| prices | t_country | {country_u} elektrikli araç şarj fiyatları | EV charging prices {country_u} | EV charging prices {country_u} | ok - "Almanya'da elektrikli araç şarj fiyatları" - natural. |
| pages | h_balkan | Batı Balkanlar | Western Balkans | Western Balkans | ok |
| prices | pr_street | Evde şarj cihazı yok | No home charger | No home charger | ok |
| prices | serbia_link | Sırbistan fiyat endeksi | Serbia price index | Price index of Serbia | ok |
| pages | p3 | 50 kW altı DC | DC below 50 kW | DC under 50 kW | ok |

## Fixes applied

| file | key | old TR | new TR |
|---|---|---|---|
| map | ch_ft_data | Haritalar: © <a href="https://www.openstreetmap.org/copyright" rel="noopener">OpenStreetMap</a> katkıda bulunanları, <a href="https://openchargemap.org" rel="noopener">Open Charge Map</a> | Haritalar: © <a href="https://www.openstreetmap.org/copyright" rel="noopener">OpenStreetMap</a> katkıda bulunanlar, <a href="https://openchargemap.org" rel="noopener">Open Charge Map</a> |
| prices | h_n_compare | Ülke ve evde şarjla karşılaştırma | Ülke ortalaması ve evde şarjla karşılaştırma |
| prices | d_country | {country_u}: şarj ağlarına göre halka açık elektrikli araç şarj fiyatları: AC, DC ve HPC, abonelik olmadan ve abonelikle, ev elektriği, 100 km'nin maliyeti. Her fiyat için kaynak ve tarih. | {country_u} şarj ağlarına göre halka açık elektrikli araç şarj fiyatları: AC, DC ve HPC, abonelik olmadan ve abonelikle, ev elektriği, 100 km'nin maliyeti. Her fiyat için kaynak ve tarih. |
| prices | d_net | {country_u} {net}: yayımlanan tarifeler, abonelik olmadan ve abonelikle, ücretler, 100 km'nin maliyeti ve ülke ortalaması ile evde şarjla karşılaştırma. | {country_u} {net} şarj fiyatları: yayımlanan tarifeler, abonelik olmadan ve abonelikle, ücretler, 100 km'nin maliyeti ve ülke ortalaması ile evde şarjla karşılaştırma. |
| prices | h_c_index | Endeks: {country_u} | {country_u} şarj fiyat endeksi |
| prices | h_more | Daha fazlası: {country_u} | {country_u} diğer sayfalar |
| prices | h_n_places | Şarj ağının şarj noktaları: {country_u} | Şarj ağının {country_u} bulunan şarj noktaları |
| prices | n_station_page | Tüm {net} şarj noktaları: {country_u} | {country_u} bulunan tüm {net} şarj noktaları |
| pages | dataset_desc | {country_u} elektrikli araçlar için halka açık şarj istasyonlarının lokasyonları; açık kaynaklardan (OpenStreetMap, Open Charge Map, ulusal kayıtlar ve diğerleri) birleştirilmiş, güç, konnektör, şarj ağı, kaynak ve güvenilirlik puanı bilgileriyle. | {country_u} bulunan halka açık elektrikli araç şarj istasyonlarının lokasyonları; açık kaynaklardan (OpenStreetMap, Open Charge Map, ulusal kayıtlar ve diğerleri) birleştirilmiş, güç, konnektör, şarj ağı, kaynak ve güvenilirlik puanı bilgileriyle. |

## {country_u} scan (strings_prices.json + strings_pages.json), test value "Almanya'da"

Note: scripts/world_pages.py country_u() and world_prices.py cu() have no 'tr' branch yet - TR needs a locative column (e.g. tr_u = "Almanya'da") before these strings render.

| file | key | rendered with Almanya'da (current) | status |
|---|---|---|---|
| prices | t_country | Almanya'da elektrikli araç şarj fiyatları | ok as is |
| prices | d_country | Almanya'da şarj ağlarına göre halka açık elektrikli araç şarj fiyatları: AC, DC ve HPC, abonelik olmadan ve abonelikle, ev elektriği, 100 km'nin maliyeti. Her fiyat için kaynak ve tarih. | FIXED |
| prices | t_net | Almanya'da {net} şarj fiyatları | ok as is |
| prices | d_net | Almanya'da {net} şarj fiyatları: yayımlanan tarifeler, abonelik olmadan ve abonelikle, ücretler, 100 km'nin maliyeti ve ülke ortalaması ile evde şarjla karşılaştırma. | FIXED |
| prices | h_c_index | Almanya'da şarj fiyat endeksi | FIXED |
| prices | h_more | Almanya'da diğer sayfalar | FIXED |
| prices | more_stations | Almanya'da şarj istasyonları | ok as is |
| prices | h_n_places | Şarj ağının Almanya'da bulunan şarj noktaları | FIXED |
| prices | n_station_page | Almanya'da bulunan tüm {net} şarj noktaları | FIXED |
| pages | d_country | Açık verilere göre Almanya'da halka açık şarj lokasyonları: hızlı DC şarj noktaları, şarj ağları, şehirler, konnektörler, kaynaklar ve lisanslar. | ok as is |
| pages | d_network | Açık verilere göre Almanya'da {net} şarj lokasyonları: güç, konnektörler ve şehirler, kaynaklarıyla birlikte. | ok as is |
| pages | dataset_desc | Almanya'da bulunan halka açık elektrikli araç şarj istasyonlarının lokasyonları; açık kaynaklardan (OpenStreetMap, Open Charge Map, ulusal kayıtlar ve diğerleri) birleştirilmiş, güç, konnektör, şarj ağı, kaynak ve güvenilirlik puanı bilgileriyle. | FIXED |
| pages | dataset_name | Almanya'da halka açık elektrikli araç şarj lokasyonları (açık veri, ODbL) | ok as is |
| pages | p_net_share | Şarj ağı Almanya'da {n_cities} bulunuyor; burada gösterilen ülkedeki halka açık lokasyonlar içindeki payı: {share}. | ok as is |
| pages | t_country | Almanya'da elektrikli araç şarj istasyonları | ok as is |
| pages | t_network | Almanya'da {net} şarj istasyonları | ok as is |
| pages | to_country | Almanya'da şarj istasyonları | ok as is |
