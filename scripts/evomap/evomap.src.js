/* Evolako — mapa javnih punjača (www.evolako.rs/mapa-punjaca), 29.09.2026; „Najbliži punjač“ 30.09.2026.
   Stanice: otvoreni podaci (OpenStreetMap ODbL, Open Charge Map CC BY 4.0), spiskovi mreža i JP „Putevi Srbije“;
   cene po mreži sa datumom i izvorom. Sve to čita se iz otvorenog fida blokvolt.rs (CORS), isti tim ga vodi.
   Mapa: MapLibre GL 5 (jsDelivr, SRI) + OpenFreeMap. Ništa se ne šalje i ne čuva; lokacija („Blizu mene“, „Najbliži punjač“)
   ostaje na uređaju. Skripta se od 30.09.2026 učitava kao fajl sa blokvolt.rs (/assets/embed/, SRI), ne iz footer koda stranice.
   Jezik: document.documentElement.lang (sr | en | ru) — prekidač jezika na sajtu menja ga, mapa se odmah precrta.
   Boje pinova kao u aplikaciji Evolako: DC — tamni, AC — plavi, ne radi / samo Tesla — sivi, nepotvrđeni — bledi. */
(function () {
  'use strict';
  var d = document, root = d.getElementById('evm');
  if (!root) {
    // the page keeps a native container; if it is ever lost, the map still appears right under the page header
    var ph = d.querySelector('.v3-ph');
    if (!ph) return;
    var sec = d.createElement('div');
    sec.className = 'evm-sec';
    sec.innerHTML = '<div class="evm-wrap"><div id="evm" class="evm"></div></div>';
    ph.parentNode.insertBefore(sec, ph.nextSibling);
    root = d.getElementById('evm');
  }
  if (root.getAttribute('data-ready')) return;
  root.setAttribute('data-ready', '1');
  root.classList.add('evm');

  var FEED = 'https://www.blokvolt.rs';
  // kućna struja noću, sa svim naknadama — ista stopa kao u kalkulatoru na sajtu i u aplikaciji (RSD po kWh)
  var HOME_KWH = 6;
  var ML = 'https://cdn.jsdelivr.net/npm/maplibre-gl@5.24.0/dist/maplibre-gl';
  var ML_JS = 'sha384-5+cfbwT0iiub6VsQAdn6yz16nr6sDiQoHx6tm4O8OVYXHYOxcffFmCJBL0dgdvGp';
  var ML_CSS = 'sha384-uTttxo/aOKbdE5RlD/SPzSDoDmNvGlUYPjONi2MN/b7c9HPSvW07OIuyP7uL6jxK';
  var STYLE = 'https://tiles.openfreemap.org/styles/positron', FONT = ['Noto Sans Bold'];
  var SRB = [[18.82, 42.23], [23.01, 46.19]];
  var MOB = 900; // the same breakpoint as the CSS
  var INK = '#0B1220', BLUE = '#2E6BFF', DEEP = '#2358E0', SLATE = '#828DA3';

  var S = {
    sr: {
      search: 'Grad, adresa ili mreža', search_l: 'Pretraga punjača', near: 'Blizu mene', loading: 'Učitavam punjače…',
      load_err: 'Mapa trenutno ne može da se učita. Pokušaj ponovo za minut.', no_map: 'Mapa ne može da se prikaže u ovom pregledaču — lista punjača je ispod.',
      ok: 'Potvrđeni', all: 'Sve', fast: 'Brzi (DC ≥ 50 kW)', free_c: 'Besplatni', filters: 'Filteri',
      count_all: 'Punjača: {n}', count: 'Prikazano {n} od {all}', in_view: 'U ovom delu mape: {n}', all_serbia: 'Cela Srbija',
      sorted_near: 'najbliži prvi', more: 'Prikaži još ({n})', none: 'Nema punjača za ovaj izbor.', no_location: 'Lokacija nije dostupna.',
      l_dc: 'Brzi DC', l_ac: 'AC', l_off: 'Ne radi ili samo Tesla', l_nep: 'Nije potvrđeno', list_l: 'Lista punjača',
      fs_on: 'Mapa preko celog ekrana', fs_off: 'Zatvori prikaz preko celog ekrana', zin: 'Uvećaj', zout: 'Umanji',
      coop_w: 'Za zumiranje mape drži Ctrl i skroluj', coop_m: 'Za zumiranje mape drži ⌘ i skroluj', coop_t: 'Mapu pomeraš sa dva prsta',
      close: 'Zatvori', price: 'Cena', conn: 'Priključci', where: 'Gde tačno', access: 'Pristup', customers: 'Samo za goste ili kupce',
      navigate: 'Navigacija', nav_in: 'Otvori u:', share: 'Podeli', copied: 'Link je kopiran', copy: 'Kopiraj', copied_ll: 'Kopirano',
      report: 'Prijavi grešku', site: 'Sajt mreže', net_known: 'Mreža', operator: 'Operater', net_unknown: 'Mreža nije poznata', data: 'Podaci', map_w: 'Mapa',
      v_ok: 'Potvrđeno', v_nep: 'Nije potvrđeno', v_prob_t: 'Prijavljen kvar', v_checked: 'Provereno {d}',
      v_cg: 'na spisku lokacija mreže Charge&GO', v_rm: 'na roming mapi Charge&GO', v_te: 'na zvaničnom spisku Tesla',
      v_ps: 'na spisku JP „Putevi Srbije“', v_g: 'skorašnje ocene vozača na Google mapama', v_own: 'na sajtu vlasnika lokacije',
      v_none: 'Punjač je samo u otvorenim bazama: nema ga ni na spisku mreža ni na Google mapama. Možda više ne postoji ili nije javan. Proveri pre polaska.',
      v_old: 'Punjač je u otvorenim bazama i na Google mapama, ali bez skorijih potvrda: nijedna ocena vozača iz poslednjih godinu dana. Proveri pre polaska.',
      v_prob: 'Vozači u skorašnjim recenzijama pišu da punjač ne radi. Proveri pre polaska.',
      v_test: 'Po spisku mreže punjač je u probnom radu i još nije otvoren za sve. Proveri u aplikaciji pre polaska.',
      status: 'Stanje punjača', st_ok: 'radi', st_off: 'ne radi', st_kw60: 'do 60 kW', st_dc_only: 'samo DC konektor', st_toll: 'do otvaranja naplatne stanice',
      st_src: 'Po spisku JP „Putevi Srbije“ od {d}',
      per_min: 'RSD/min', per_kwh: 'RSD/kWh', free: 'Besplatno', off: 'Ne radi', tesla_only: 'Samo Tesla',
      p_unknown: 'Cena nije poznata. Proveri u aplikaciji mreže.', p_free: 'Besplatno', p_exact: 'Cena na ovom punjaču',
      p_tier: 'Cena mreže za {c}', p_receipt: 'Račun: {l}, {k} RSD po kWh', p_range: 'Između cena za {a} i {b}',
      p_seen: 'Zabeležene cene ove mreže:', p_old: 'Cena je starija od godinu dana. Proveri u aplikaciji mreže.',
      p_list: 'Cenovnik mreže, {d}', p_est: '≈ {k} RSD po kWh ako auto puni sa {w} kW', p_by_receipt: 'Po računima sa ovog punjača ({d})',
      idle: 'Zauzeće posle punjenja: {x}', p_tesla_only: 'Samo za Tesla vozila', p_tesla_fee: '{t} — {s}.',
      home_t: 'Kod kuće, noću: ≈ {k} RSD po kWh', home_s: 'sa svim naknadama, kao u kalkulatoru na sajtu', home_a: 'Pogledaj pakete',
      promo_t: 'Najjeftinije je kod kuće', promo_s: 'Noću ≈ {k} RSD po kWh, sa svim naknadama. Punjač u garaži tvoje zgrade, ugradnja za jedan dan.',
      promo_a: 'Proveri svoju garažu', near_t: 'okolina: {t}', charger: 'Punjač', schuko: 'Šuko', other: 'Ostalo',
      addr_none: 'Adresa nije poznata — koristi koordinate.', q_net: 'Tačka je sa spiska mreže.', q_osm: 'Tačka je iz OpenStreetMap-a.',
      q_ocm: 'Tačka je iz Open Charge Map-a i može odstupati nekoliko desetina metara.', q_site: 'Približna tačka: parking ili objekat, ne sam punjač.',
      q_field: 'Tačka je proverena na licu mesta.', mail_s: 'Greška na mapi: {id}', mail_b: 'Šta nije tačno:', src_rm: 'Charge&GO roming',
      map_l: 'Mapa javnih punjača', updated: 'provereno {d}', base: 'baza: {b}',
      nr_btn: 'Najbliži punjač', nr_title: 'Najbliži punjači', nr_sub: 'Potvrđeni punjači koji rade · udaljenost vazdušnom linijom',
      nr_sub_all: 'Uključeni su i nepotvrđeni · udaljenost vazdušnom linijom', nr_fast: 'Samo brzi (DC)', nr_nav_to: 'Navigacija do {t}, {d}',
      nr_opens: 'Otvara se u: {a}', nr_change: 'Promeni', nr_nep: 'Prikaži i nepotvrđene', nr_unfilter: 'Ukloni filter',
      nr_wait: 'Tražim tvoju lokaciju…', nr_denied: 'Pregledač nema dozvolu za lokaciju. Dozvoli je za ovaj sajt u podešavanjima pregledača, pa pokušaj ponovo.',
      nr_unavail: 'Lokacija trenutno nije dostupna. Pokušaj ponovo za minut.', nr_retry: 'Pokušaj ponovo', nr_privacy: 'Lokacija ostaje na tvom uređaju.',
      nr_far: 'Na mapi su punjači u Srbiji.', nr_find: 'Pronađi najbliže',
      nr_ask: 'Za najbliže punjače treba tvoja lokacija. Pregledač je traži tek kad pritisneš dugme i ne šalje je sajtu.',
      // 06.10.2026: „Moj auto“ (cena po km), cena po priključku, „Kako se puni ovde“, radno vreme, kabl
      car_btn_l: 'Moj auto:', car_pick: 'izaberi — cena po km', car_title: 'Moj auto',
      car_intro: 'Izaberi auto i mapa pokazuje koliko te košta kilometar na svakom punjaču. Izbor važi dok je stranica otvorena.',
      car_make: 'Marka', car_model: 'Model', car_cons: 'Potrošnja (kWh na 100 km)', car_cons_ph: 'npr. {x}', car_cab: 'Imam svoj Tip 2 kabl',
      car_opt: 'Auto ima opcioni punjač od {k} kW', car_save: 'Primeni', car_clear: 'Bez auta', car_none: '— izaberi —',
      car_load_err: 'Spisak auta trenutno ne može da se učita. Pokušaj ponovo za minut.', car_src: 'Podaci o autima: Open EV Data, Chargeprice, P3, ADAC i proizvođači; potrošnja je procena.',
      per_km: 'RSD/km', cheap: 'Najjeftinije za moj auto', sorted_cheap: 'najjeftinije za tvoj auto prvo',
      cost_t: 'Za tvoj {car}: ≈ {x} RSD/km', cost_100: '100 km ≈ {x} RSD', cost_kw: 'auto ovde prima ≈ {w} kW, ≈ {k} RSD po kWh',
      cost_start: 'sa naknadom za pokretanje {s} RSD, raspoređenom na pola baterije', cost_winter: 'zimi je potrošnja veća ≈ {p} %',
      cost_alt: 'Jeftinije ovde: {c} — ≈ {x} RSD/km', cost_near: 'Jeftinije u blizini: {t}, {d} — ≈ {x} RSD/km',
      cost_near_free: 'Besplatno u blizini: {t}, {d}.', cost_cmp: 'Benzin ≈ {b} RSD/km · kod kuće noću ≈ {h} RSD/km',
      cost_na: 'Za {car} ovde nema cene po kilometru.', cost_no_dc: '{car} ne može da puni na DC priključku ovog punjača.',
      cost_pick: 'Izaberi auto — cena po kilometru', home_km: 'Kod kuće, noću: ≈ {h} RSD/km za tvoj auto',
      promo_km: 'Noću ≈ {h} RSD/km za tvoj auto, sa svim naknadama. Punjač u garaži tvoje zgrade, ugradnja za jedan dan.',
      p_station: 'Cena ovog punjača u aplikaciji mreže · {d} · {s}',
      kako_t: 'Kako se puni ovde — {n}', kako_pay: 'Plaćanje:', kako_guest: 'Bez registracije:', kako_after: 'Posle punjenja:',
      kako_refund: 'Povraćaj:', kako_apps: 'Aplikacija:', kako_checked: 'Provereno {d}',
      oh_open: 'sada radi do {t}', oh_closed: 'sada zatvoreno, otvara u {t}', closed_now: 'sada zatvoreno',
      cab_own: 'Ponesi svoj Tip 2 kabl', src_cga: 'aplikacija Charge&GO'
    },
    en: {
      search: 'City, address or network', search_l: 'Search chargers', near: 'Near me', loading: 'Loading chargers…',
      load_err: 'The map can’t load right now. Try again in a minute.', no_map: 'The map can’t be shown in this browser — the charger list is below.',
      ok: 'Confirmed', all: 'All', fast: 'Fast (DC ≥ 50 kW)', free_c: 'Free', filters: 'Filters',
      count_all: 'Chargers: {n}', count: 'Showing {n} of {all}', in_view: 'In this part of the map: {n}', all_serbia: 'All of Serbia',
      sorted_near: 'nearest first', more: 'Show more ({n})', none: 'No chargers for this selection.', no_location: 'Location is not available.',
      l_dc: 'Fast DC', l_ac: 'AC', l_off: 'Not working or Tesla only', l_nep: 'Not confirmed', list_l: 'Charger list',
      fs_on: 'Full-screen map', fs_off: 'Close full-screen map', zin: 'Zoom in', zout: 'Zoom out',
      coop_w: 'Hold Ctrl and scroll to zoom the map', coop_m: 'Hold ⌘ and scroll to zoom the map', coop_t: 'Use two fingers to move the map',
      close: 'Close', price: 'Price', conn: 'Connectors', where: 'Where exactly', access: 'Access', customers: 'Guests or customers only',
      navigate: 'Directions', nav_in: 'Open in:', share: 'Share', copied: 'Link copied', copy: 'Copy', copied_ll: 'Copied',
      report: 'Report an error', site: 'Network website', net_known: 'Network', operator: 'Operator', net_unknown: 'Network unknown', data: 'Data', map_w: 'Map',
      v_ok: 'Confirmed', v_nep: 'Not confirmed', v_prob_t: 'Reported broken', v_checked: 'Checked {d}',
      v_cg: 'on the Charge&GO list of locations', v_rm: 'on the Charge&GO roaming map', v_te: 'on Tesla’s official list',
      v_ps: 'on the JP “Putevi Srbije” list', v_g: 'recent driver ratings on Google Maps', v_own: 'on the location owner’s website',
      v_none: 'This charger is only in the open databases: it is neither on the networks’ lists nor on Google Maps. It may no longer exist or may not be public. Check before you set off.',
      v_old: 'This charger is in the open databases and on Google Maps, but without recent confirmation: no driver rating from the past year. Check before you set off.',
      v_prob: 'Drivers say in recent reviews that this charger doesn’t work. Check before you set off.',
      v_test: 'According to the network’s list, this charger is in trial operation and not yet open to everyone. Check the app before you set off.',
      status: 'Charger status', st_ok: 'working', st_off: 'not working', st_kw60: 'up to 60 kW', st_dc_only: 'DC connector only', st_toll: 'until the toll station opens',
      st_src: 'According to the JP “Putevi Srbije” list of {d}',
      per_min: 'RSD/min', per_kwh: 'RSD/kWh', free: 'Free', off: 'Not working', tesla_only: 'Tesla only',
      p_unknown: 'Price unknown. Check the network’s app.', p_free: 'Free', p_exact: 'Price at this charger',
      p_tier: 'Network price for {c}', p_receipt: 'Receipt: {l}, {k} RSD per kWh', p_range: 'Between the prices for {a} and {b}',
      p_seen: 'Recorded prices of this network:', p_old: 'This price is more than a year old. Check it in the network’s app.',
      p_list: 'Network price list, {d}', p_est: '≈ {k} RSD per kWh if the car charges at {w} kW', p_by_receipt: 'From receipts at this charger ({d})',
      idle: 'Idle fee after charging: {x}', p_tesla_only: 'Tesla vehicles only', p_tesla_fee: '{t} — {s}.',
      home_t: 'At home, at night: ≈ {k} RSD per kWh', home_s: 'all fees included, as in the calculator on this site', home_a: 'See the kits',
      promo_t: 'Charging at home is cheapest', promo_s: 'At night ≈ {k} RSD per kWh, all fees included. A charger in your building’s garage, installed in one day.',
      promo_a: 'Check your garage', near_t: 'near {t}', charger: 'Charger', schuko: 'Schuko', other: 'Other',
      addr_none: 'Address unknown — use the coordinates.', q_net: 'The point is from the network’s list.', q_osm: 'The point is from OpenStreetMap.',
      q_ocm: 'The point is from Open Charge Map and may be off by a few dozen metres.', q_site: 'Approximate point: the car park or building, not the charger itself.',
      q_field: 'The point was checked on site.', mail_s: 'Map error: {id}', mail_b: 'What is wrong:', src_rm: 'Charge&GO roaming',
      map_l: 'Map of public chargers', updated: 'checked {d}', base: 'database: {b}',
      nr_btn: 'Nearest charger', nr_title: 'Nearest chargers', nr_sub: 'Confirmed chargers that work · straight-line distance',
      nr_sub_all: 'Unconfirmed ones included · straight-line distance', nr_fast: 'Fast only (DC)', nr_nav_to: 'Directions to {t}, {d}',
      nr_opens: 'Opens in: {a}', nr_change: 'Change', nr_nep: 'Show unconfirmed too', nr_unfilter: 'Remove filter',
      nr_wait: 'Finding your location…', nr_denied: 'Your browser doesn’t have permission to use your location. Allow it for this site in your browser settings, then try again.',
      nr_unavail: 'Your location isn’t available right now. Try again in a minute.', nr_retry: 'Try again', nr_privacy: 'Your location stays on your device.',
      nr_far: 'The map shows chargers in Serbia.', nr_find: 'Find the nearest',
      nr_ask: 'To find the nearest chargers, the map needs your location. Your browser asks for it only when you press the button and doesn’t send it to this site.',
      car_btn_l: 'My car:', car_pick: 'choose — price per km', car_title: 'My car',
      car_intro: 'Choose your car and the map shows what a kilometre costs at every charger. The choice lasts while this page is open.',
      car_make: 'Make', car_model: 'Model', car_cons: 'Consumption (kWh per 100 km)', car_cons_ph: 'e.g. {x}', car_cab: 'I have my own Type 2 cable',
      car_opt: 'The car has the optional {k} kW on-board charger', car_save: 'Apply', car_clear: 'No car', car_none: '— choose —',
      car_load_err: 'The car list can’t load right now. Try again in a minute.', car_src: 'Car data: Open EV Data, Chargeprice, P3, ADAC and the makers; consumption is an estimate.',
      per_km: 'RSD/km', cheap: 'Cheapest for my car', sorted_cheap: 'cheapest for your car first',
      cost_t: 'For your {car}: ≈ {x} RSD/km', cost_100: '100 km ≈ {x} RSD', cost_kw: 'the car takes ≈ {w} kW here, ≈ {k} RSD per kWh',
      cost_start: 'with the {s} RSD start fee spread over half the battery', cost_winter: 'in winter consumption is ≈ {p} % higher',
      cost_alt: 'Cheaper here: {c} — ≈ {x} RSD/km', cost_near: 'Cheaper nearby: {t}, {d} — ≈ {x} RSD/km',
      cost_near_free: 'Free nearby: {t}, {d}.', cost_cmp: 'Petrol ≈ {b} RSD/km · at home at night ≈ {h} RSD/km',
      cost_na: 'No price per kilometre for {car} here.', cost_no_dc: '{car} can’t charge at this charger’s DC connector.',
      cost_pick: 'Choose your car — price per kilometre', home_km: 'At home, at night: ≈ {h} RSD/km for your car',
      promo_km: 'At night ≈ {h} RSD/km for your car, all fees included. A charger in your building’s garage, installed in one day.',
      p_station: 'Price at this charger in the network’s app · {d} · {s}',
      kako_t: 'How to charge here — {n}', kako_pay: 'Payment:', kako_guest: 'Without registration:', kako_after: 'After charging:',
      kako_refund: 'Refund:', kako_apps: 'App:', kako_checked: 'Checked {d}',
      oh_open: 'open now until {t}', oh_closed: 'closed now, opens at {t}', closed_now: 'closed now',
      cab_own: 'Bring your own Type 2 cable', src_cga: 'Charge&GO app'
    },
    ru: {
      search: 'Город, адрес или сеть', search_l: 'Поиск зарядок', near: 'Рядом со мной', loading: 'Загружаю зарядки…',
      load_err: 'Карта сейчас не загружается. Попробуй ещё раз через минуту.', no_map: 'В этом браузере карту показать не получится — список зарядок ниже.',
      ok: 'Подтверждённые', all: 'Все', fast: 'Быстрые (DC ≥ 50 кВт)', free_c: 'Бесплатные', filters: 'Фильтры',
      count_all: 'Зарядок: {n}', count: 'Показано {n} из {all}', in_view: 'В этой части карты: {n}', all_serbia: 'Вся Сербия',
      sorted_near: 'сначала ближайшие', more: 'Показать ещё ({n})', none: 'Нет зарядок для этого выбора.', no_location: 'Местоположение недоступно.',
      l_dc: 'Быстрая DC', l_ac: 'AC', l_off: 'Не работает или только Tesla', l_nep: 'Не подтверждено', list_l: 'Список зарядок',
      fs_on: 'Карта на весь экран', fs_off: 'Закрыть карту на весь экран', zin: 'Приблизить', zout: 'Отдалить',
      coop_w: 'Чтобы изменить масштаб, зажми Ctrl и прокрути', coop_m: 'Чтобы изменить масштаб, зажми ⌘ и прокрути', coop_t: 'Двигай карту двумя пальцами',
      close: 'Закрыть', price: 'Цена', conn: 'Разъёмы', where: 'Где именно', access: 'Доступ', customers: 'Только для гостей или покупателей',
      navigate: 'Маршрут', nav_in: 'Открыть в:', share: 'Поделиться', copied: 'Ссылка скопирована', copy: 'Скопировать', copied_ll: 'Скопировано',
      report: 'Сообщить об ошибке', site: 'Сайт сети', net_known: 'Сеть', operator: 'Оператор', net_unknown: 'Сеть неизвестна', data: 'Данные', map_w: 'Карта',
      v_ok: 'Подтверждено', v_nep: 'Не подтверждено', v_prob_t: 'Сообщают о поломке', v_checked: 'Проверено {d}',
      v_cg: 'в списке локаций сети Charge&GO', v_rm: 'на роуминговой карте Charge&GO', v_te: 'в официальном списке Tesla',
      v_ps: 'в списке JP «Putevi Srbije»', v_g: 'свежие оценки водителей на Google Картах', v_own: 'на сайте владельца локации',
      v_none: 'Эта зарядка есть только в открытых базах: её нет ни в списках сетей, ни на Google Картах. Возможно, её уже нет или она не публичная. Проверь перед поездкой.',
      v_old: 'Эта зарядка есть в открытых базах и на Google Картах, но без свежих подтверждений: ни одной оценки водителей за последний год. Проверь перед поездкой.',
      v_prob: 'Водители в недавних отзывах пишут, что зарядка не работает. Проверь перед поездкой.',
      v_test: 'По списку сети зарядка в тестовом режиме и открыта ещё не для всех. Проверь в приложении перед поездкой.',
      status: 'Состояние зарядки', st_ok: 'работает', st_off: 'не работает', st_kw60: 'до 60 кВт', st_dc_only: 'только разъём DC', st_toll: 'до открытия пункта оплаты',
      st_src: 'По списку JP «Putevi Srbije» от {d}',
      per_min: 'RSD/мин', per_kwh: 'RSD/кВт·ч', free: 'Бесплатно', off: 'Не работает', tesla_only: 'Только Tesla',
      p_unknown: 'Цена неизвестна. Проверь в приложении сети.', p_free: 'Бесплатно', p_exact: 'Цена на этой зарядке',
      p_tier: 'Цена сети для {c}', p_receipt: 'Чек: {l}, {k} RSD за кВт·ч', p_range: 'Между ценами для {a} и {b}',
      p_seen: 'Записанные цены этой сети:', p_old: 'Цене больше года. Проверь её в приложении сети.',
      p_list: 'Прайс-лист сети, {d}', p_est: '≈ {k} RSD за кВт·ч, если машина заряжается на {w} кВт', p_by_receipt: 'По чекам с этой зарядки ({d})',
      idle: 'Плата за простой после зарядки: {x}', p_tesla_only: 'Только для автомобилей Tesla', p_tesla_fee: '{t} — {s}.',
      home_t: 'Дома ночью: ≈ {k} RSD за кВт·ч', home_s: 'со всеми сборами, как в калькуляторе на сайте', home_a: 'Посмотреть комплекты',
      promo_t: 'Дешевле всего — дома', promo_s: 'Ночью ≈ {k} RSD за кВт·ч, со всеми сборами. Зарядка в гараже твоего дома, монтаж за один день.',
      promo_a: 'Проверь свой гараж', near_t: 'рядом: {t}', charger: 'Зарядка', schuko: 'Шуко', other: 'Другое',
      addr_none: 'Адрес неизвестен — используй координаты.', q_net: 'Точка — из списка сети.', q_osm: 'Точка — из OpenStreetMap.',
      q_ocm: 'Точка взята из Open Charge Map и может отклоняться на несколько десятков метров.', q_site: 'Примерная точка: парковка или здание, а не сама зарядка.',
      q_field: 'Точка проверена на месте.', mail_s: 'Ошибка на карте: {id}', mail_b: 'Что не так:', src_rm: 'роуминг Charge&GO',
      map_l: 'Карта публичных зарядок', updated: 'проверено {d}', base: 'база: {b}',
      nr_btn: 'Ближайшая зарядка', nr_title: 'Ближайшие зарядки', nr_sub: 'Подтверждённые и работающие · расстояние по прямой',
      nr_sub_all: 'Включая неподтверждённые · расстояние по прямой', nr_fast: 'Только быстрые (DC)', nr_nav_to: 'Маршрут до {t}, {d}',
      nr_opens: 'Откроется в: {a}', nr_change: 'Изменить', nr_nep: 'Показать и неподтверждённые', nr_unfilter: 'Убрать фильтр',
      nr_wait: 'Определяю, где ты…', nr_denied: 'У браузера нет доступа к геолокации. Разреши его для этого сайта в настройках браузера и попробуй ещё раз.',
      nr_unavail: 'Местоположение сейчас недоступно. Попробуй ещё раз через минуту.', nr_retry: 'Попробовать ещё раз', nr_privacy: 'Местоположение остаётся на твоём устройстве.',
      nr_far: 'На карте — зарядки в Сербии.', nr_find: 'Найти ближайшие',
      nr_ask: 'Чтобы найти ближайшие зарядки, нужна твоя геолокация. Браузер запросит её, только когда ты нажмёшь кнопку, и сайту её не передаст.',
      car_btn_l: 'Моя машина:', car_pick: 'выбери — цена за км', car_title: 'Моя машина',
      car_intro: 'Выбери машину, и карта покажет, сколько стоит километр на каждой зарядке. Выбор действует, пока страница открыта.',
      car_make: 'Марка', car_model: 'Модель', car_cons: 'Расход (кВт·ч на 100 км)', car_cons_ph: 'напр. {x}', car_cab: 'У меня есть свой кабель Type 2',
      car_opt: 'У машины опциональное бортовое зарядное устройство на {k} кВт', car_save: 'Применить', car_clear: 'Без машины', car_none: '— выбери —',
      car_load_err: 'Список машин сейчас не загружается. Попробуй ещё раз через минуту.', car_src: 'Данные о машинах: Open EV Data, Chargeprice, P3, ADAC и производители; расход — оценка.',
      per_km: 'RSD/км', cheap: 'Дешевле всего для моей машины', sorted_cheap: 'сначала самые дешёвые для твоей машины',
      cost_t: 'Для твоей машины {car}: ≈ {x} RSD/км', cost_100: '100 км ≈ {x} RSD', cost_kw: 'машина берёт здесь ≈ {w} кВт, ≈ {k} RSD за кВт·ч',
      cost_start: 'с платой за старт {s} RSD, распределённой на половину батареи', cost_winter: 'зимой расход выше ≈ на {p} %',
      cost_alt: 'Дешевле здесь: {c} — ≈ {x} RSD/км', cost_near: 'Дешевле рядом: {t}, {d} — ≈ {x} RSD/км',
      cost_near_free: 'Бесплатно рядом: {t}, {d}.', cost_cmp: 'Бензин ≈ {b} RSD/км · дома ночью ≈ {h} RSD/км',
      cost_na: 'Для машины {car} здесь нет цены за километр.', cost_no_dc: 'Машина {car} не может заряжаться от DC-разъёма этой зарядки.',
      cost_pick: 'Выбери машину — цена за километр', home_km: 'Дома ночью: ≈ {h} RSD/км для твоей машины',
      promo_km: 'Ночью ≈ {h} RSD/км для твоей машины, со всеми сборами. Зарядка в гараже твоего дома, монтаж за один день.',
      p_station: 'Цена этой зарядки в приложении сети · {d} · {s}',
      kako_t: 'Как здесь заряжаться — {n}', kako_pay: 'Оплата:', kako_guest: 'Без регистрации:', kako_after: 'После зарядки:',
      kako_refund: 'Возврат:', kako_apps: 'Приложение:', kako_checked: 'Проверено {d}',
      oh_open: 'сейчас открыто до {t}', oh_closed: 'сейчас закрыто, откроется в {t}', closed_now: 'сейчас закрыто',
      cab_own: 'Возьми свой кабель Type 2', src_cga: 'приложение Charge&GO'
    }
  };
  // notes that come with the price data (Serbian), translated once from the same source; newer ones stay Serbian
  var TX = window.EVM_TX || { en: {}, ru: {} };

  function lang() { var l = (d.documentElement.lang || 'sr').slice(0, 2); return S[l] ? l : 'sr'; }
  function T(k) { var l = lang(); return (S[l][k] != null ? S[l][k] : S.sr[k]) || ''; }
  // units inside data labels („101,67 RSD/min“, „DC 110–120 kW“) follow the page language, as the rest of the card
  function unit(s) { return lang() === 'ru' && s ? String(s).replace(/\bkWh\b/g, 'кВт·ч').replace(/\bkW\b/g, 'кВт').replace(/\bmin\b/g, 'мин') : s; }
  function tr(s) { if (!s) return s; var l = lang(); return (l !== 'sr' && TX[l] && TX[l][s]) || unit(s); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function fold(s) { return (s || '').toLowerCase().replace(/đ/g, 'd').normalize('NFD').replace(/[̀-ͯ]/g, ''); }
  var CYR = { 'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'ѓ': 'g', 'ђ': 'd', 'е': 'e', 'ж': 'z', 'з': 'z', 'ѕ': 'dz', 'и': 'i', 'ј': 'j', 'к': 'k', 'ќ': 'k',
    'л': 'l', 'љ': 'lj', 'м': 'm', 'н': 'n', 'њ': 'nj', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'ћ': 'c', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'c',
    'џ': 'dz', 'ш': 's', 'й': 'j', 'ы': 'y', 'э': 'e', 'ю': 'ju', 'я': 'ja', 'ё': 'e', 'щ': 's', 'ь': '', 'ъ': '' };
  // search folds Serbian Latin, Cyrillic and plain ASCII to the same key: „Niš“, „Ниш“ and „nis“ find the same chargers
  function sfold(s) {
    return fold(String(s || '').toLowerCase().replace(/[Ѐ-ӿ]/g, function (c) { return c in CYR ? CYR[c] : c; }))
      .replace(/([szc])h/g, '$1').replace(/([gk])j/g, '$1').replace(/dj/g, 'd');
  }
  // Serbian number format on every language, as the rest of the site: 59.000 · 0,35
  function fmt(n, dg) {
    dg = dg || 0;
    var x = Number(n), p = Math.abs(x).toFixed(dg).split('.');
    return (x < 0 && +p.join('.') > 0 ? '−' : '') + p[0].replace(/\B(?=(\d{3})+(?!\d))/g, '.') + (p[1] ? ',' + p[1] : '');
  }
  function fill(s, o) { return String(s).replace(/\{(\w+)\}/g, function (m, k) { return o[k] != null ? o[k] : m; }); }
  function kWu() { return lang() === 'ru' ? 'кВт' : 'kW'; }
  function kmU(m) { return lang() === 'ru' ? (m ? 'м' : 'км') : (m ? 'm' : 'km'); }
  function mobile() { return window.innerWidth <= MOB; }

  function svg(p) { return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + p + '</svg>'; }
  var IC = {
    x: svg('<path d="M6 6l12 12M18 6 6 18"/>'), nav: svg('<path d="M3.5 11 20.5 3.5 13 20.5l-2-7.5-7.5-2Z"/>'),
    ext: svg('<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>'),
    flag: svg('<path d="M5 21V4M5 4h11l-2 4 2 4H5"/>'), ok: svg('<path d="M20 6 9 17l-5-5"/>'),
    warn: svg('<path d="M12 3 2 20h20L12 3Z"/><path d="M12 10v4M12 17.5v.01"/>'),
    share: svg('<path d="M12 3v12M7 8l5-5 5 5"/><path d="M5 12v7a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-7"/>'),
    copy: svg('<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3"/>'),
    clock: svg('<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>'),
    pin: svg('<path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11Z"/><circle cx="12" cy="10" r="2.3"/>'),
    info: svg('<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5M12 8v.01"/>'),
    home: svg('<path d="M4 11.5 12 5l8 6.5"/><path d="M6.5 10v9h11v-9"/><path d="M12.8 12.5 11 15.5h2l-1.8 3"/>'),
    loc: svg('<circle cx="12" cy="12" r="3.2"/><path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3"/><circle cx="12" cy="12" r="7"/>'),
    search: svg('<circle cx="11" cy="11" r="6.5"/><path d="m20 20-4.2-4.2"/>'),
    bolt: svg('<path d="M13 2.5 5 13.5h6l-1 8 8-11h-6l1-8Z"/>'),
    full: svg('<path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/>'),
    unfull: svg('<path d="M9 4v5H4M15 4v5h5M9 20v-5H4M15 20v-5h5"/>'),
    car: svg('<path d="M5 16.5h14M6.5 16.5V19M17.5 16.5V19M4.5 16.5v-4l2-5.2A1.5 1.5 0 0 1 7.9 6.3h8.2a1.5 1.5 0 0 1 1.4 1l2 5.2v4"/><path d="M4.5 12.5h15"/><circle cx="8" cy="14.3" r=".6"/><circle cx="16" cy="14.3" r=".6"/>'),
    cable: svg('<path d="M7 3v4M11 3v4M5.5 7h7v3a3.5 3.5 0 0 1-7 0V7Z"/><path d="M9 13.5V16a4 4 0 0 0 4 4h1a4 4 0 0 0 4-4V8"/>'),
    park: svg('<rect x="4" y="4" width="16" height="16" rx="3"/><path d="M10 16V8h3a2.5 2.5 0 0 1 0 5h-3"/>'),
    coins: svg('<ellipse cx="12" cy="6.5" rx="6.5" ry="2.5"/><path d="M5.5 6.5v5c0 1.4 2.9 2.5 6.5 2.5s6.5-1.1 6.5-2.5v-5M5.5 11.5v5c0 1.4 2.9 2.5 6.5 2.5s6.5-1.1 6.5-2.5v-5"/>')
  };
  var CONN = { ccs2: 'CCS2', ccs1: 'CCS1', chademo: 'CHAdeMO', type2: 'Type 2', type1: 'Type 1', tesla: 'Tesla', gbt: 'GB/T', cee: 'CEE' };
  // directions: Apple Maps first on Apple devices, Google Maps elsewhere (dir_action=navigate: turn-by-turn at once in the Maps app on
  // a phone), Waze always; coordinates only, no API key. The app the visitor opens a route in comes first for the rest of the visit
  // (kept in memory only: the privacy policy of evolako.rs names no other browser storage)
  var IS_APPLE = /iPhone|iPad|iPod|Macintosh/.test(navigator.userAgent) && !/Android/.test(navigator.userAgent);
  var NAV_NAME = { google: 'Google Maps', apple: 'Apple Maps', waze: 'Waze' }, NAV_PREF = '';
  function navApps() { return IS_APPLE ? ['apple', 'google', 'waze'] : ['google', 'waze']; }
  function navPref() { return navApps().indexOf(NAV_PREF) >= 0 ? NAV_PREF : navApps()[0]; }
  function navUrl(a, s) {
    var ll = s.lat + ',' + s.lon;
    if (a === 'apple') return 'https://maps.apple.com/?daddr=' + ll + '&dirflg=d';
    if (a === 'waze') return 'https://waze.com/ul?ll=' + ll + '&navigate=yes&utm_source=evolako';
    return 'https://www.google.com/maps/dir/?api=1&destination=' + ll + '&travelmode=driving&dir_action=navigate';
  }
  function navLinks(s) {
    var p = navPref();
    return [p].concat(navApps().filter(function (a) { return a !== p; })).map(function (a) { return [NAV_NAME[a], navUrl(a, s), a]; });
  }
  var MONTHS_SR = ['januar', 'februar', 'mart', 'april', 'maj', 'jun', 'jul', 'avgust', 'septembar', 'oktobar', 'novembar', 'decembar'];
  function ageDays(ds) {
    if (!ds) return Infinity;
    var t = 0, re = /(?:(\d{1,2})\.(\d{1,2})\.|([a-zčćšžđ]+)\s+)?(\d{4})/gi, m;
    while ((m = re.exec(ds))) {
      var y = +m[4], mi = m[2] ? +m[2] - 1 : m[3] ? MONTHS_SR.indexOf(m[3].toLowerCase()) : -1;
      var dt = m[1] ? new Date(y, mi, +m[1]) : mi >= 0 ? new Date(y, mi + 1, 0) : new Date(y, 11, 31);
      t = Math.max(t, dt.getTime());
    }
    return t > 0 ? (Date.now() - t) / 86400000 : Infinity;
  }
  function stale(ds) { var a = ageDays(ds); return a !== Infinity && a > 365; }
  var MONTHS = { en: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
    ru: ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь', 'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь'] };
  // dates in the data are Serbian („septembar 2026“, „22.09.2026“): month names follow the page language
  function dt(ds) {
    var l = lang(), s = String(ds || '').replace(/\b(\d{4})-(\d{2})-(\d{2})\b/g, '$3.$2.$1');
    if (!s || !MONTHS[l]) return s;
    return s.replace(/\b(januar|februar|mart|april|maj|jun|jul|avgust|septembar|oktobar|novembar|decembar)\b/gi, function (m) { return MONTHS[l][MONTHS_SR.indexOf(m.toLowerCase())]; });
  }

  // ---------- data ----------
  var ST = [], BYID = {}, NETS = {}, CHECKED = '', map = null, mlReady = false, dataReady = false, dataErr = false, me = null, sel = null, userMove = false;
  // „Najbliži punjač“: the last search (point, rows) and whether its panel is open; cardNear — the open card came from that panel
  var NEAR = null, nearOpen = false, cardNear = false;
  var state = { q: '', f: 'all', ok: false, cheap: false, bounds: null, lim: 20 };
  function teslaOnly(s) { return !!(s.ax && s.ax.who === 'tesla'); }
  // a Tesla chosen in „Moj auto“ may use the Superchargers (on blokvolt.rs: „Imam Teslu“)
  function teslaCar() { var c = carSpec(); return !!(c && c.mk === 'Tesla'); }
  function isFree(s) {
    var f = s.fee && s.fee.free;
    if (f) return f === 'all' || f === 'limited' || (f === 'tesla' && teslaCar());
    var n = NETS[s.net];
    if (!n || !n.free) return false;
    if (!n.free_where) return true;
    var hay = fold([s.n, s.a, s.t].join(' '));
    return n.free_where.some(function (w) { return hay.indexOf(w) >= 0; });
  }
  function ver(s) { return (s.v && s.v.s) || 'nep'; }
  function isOff(s) { return (!!s.ps && !s.ps.l.some(function (l) { return l[2] === 1; })) || ver(s) === 'prob'; }
  // the pin colour, as in the Evolako app: DC dark, AC blue, grey when it does not work or is only for Tesla
  function kind(s) {
    if (isOff(s)) return 'off';
    if (teslaOnly(s) && !teslaCar()) return 'tesla';
    return (s.dc || 0) > 0 ? 'dc' : 'ac';
  }
  function netOf(s) { return NETS[s.net] || null; }
  function netName(s) { var n = netOf(s); return n ? n.name : (s.opn || ''); }
  function cleanName(n) { return (n || '').replace(/^charge\s*&\s*go\s*[-–:,]?\s*/i, '').replace(/^BS\s+(?=gazprom|nis|evoil)/i, '').trim(); }
  function title(s) { return cleanName(s.n) || netName(s) || (s.a ? s.a.split(',')[0] : T('charger')); }
  function hayOf(s) { return fold([s.n, s.a].concat(s.al || []).join(' ')); }
  function place(s) {
    var near = s.t ? fill(T('near_t'), { t: s.t }) : '';
    if (!s.n && !netName(s) && s.a) return s.a.split(',').slice(1).join(',').trim() || near;
    return s.a || near;
  }
  function power(s) { return s.dc || s.ac || 0; }
  // what a typical car really takes from a DC charger of a given power (kW); AC — the car's 11 kW on-board charger
  var REAL_KW = [[30, 30], [50, 45], [60, 50], [115, 90], [165, 100], [240, 130]];
  function realKw(P, cur) {
    if (!P) return null;
    if (cur !== 'dc') return Math.min(P, 11);
    if (P <= 30) return P;
    for (var i = 1; i < REAL_KW.length; i++) {
      var a = REAL_KW[i - 1], b = REAL_KW[i];
      if (P <= b[0]) return a[1] + (b[1] - a[1]) * (P - a[0]) / (b[0] - a[0]);
    }
    return 130;
  }
  function perKwh(v, s) { var k = realKw(power(s), s.dc ? 'dc' : 'ac'); return v && k ? v * 60 / k : null; }
  function kwhSpan(list, dash) {
    var v = list.map(function (t) { return t.v; }).filter(function (x) { return x != null; });
    if (!v.length) return '?';
    var lo = Math.min.apply(null, v), hi = Math.max.apply(null, v);
    return lo === hi ? fmt(lo, 2) : fmt(lo, 2) + dash + fmt(hi, 2);
  }
  function freshReceipts(p, dash) {
    var rc = (p.receipt || []).filter(function (r) { return ageDays(r.date) <= 90; });
    if (!rc.length) return '';
    var ks = rc.map(function (r) { return r.kwh; }), lo = Math.min.apply(null, ks), hi = Math.max.apply(null, ks);
    return lo === hi ? fmt(lo) : fmt(lo) + (dash || '–') + fmt(hi);
  }
  // one price line: v = RSD/min, k = RSD/kWh, h = RSD/hour, st = start or connection fee, ut + pm = Spectra "units" + RSD/min
  function stationLines(s) {
    var P = s.pr, unitT = P.u === 'kwh' ? T('per_kwh') : T('per_min');
    return P.l.map(function (l) {
      return { cur: l[0], kw: l[1], n: l[3], v: P.u === 'min' ? l[2] : null, k: P.u === 'kwh' ? l[2] : null, st: P.st || 0,
        label: fmt(l[2], 2) + ' ' + unitT, date: P.d, src: P.src, charger: String(l[0]).toUpperCase() + ' ' + fmt(l[1], l[1] % 1 ? 1 : 0) + ' ' + kWu() };
    });
  }
  // the price as blokvolt.rs/mapa shows it (the same data): the network's app per connector (s.pr), a price recorded at this
  // place, the network's tariff for the power, a range between two tariffs, or the prices seen in the network
  function price(s) {
    var fee = s.fee;
    if (fee && fee.free) {
      var lbl = { label: tr(fee.t), src: tr(fee.src), note: tr(fee.note) };
      if (isFree(s)) return Object.assign({ kind: 'free', date: '' }, lbl);
      if (fee.free === 'tesla') return Object.assign({ kind: 'tesla' }, lbl);
    }
    var n = netOf(s);
    if (!n) return { kind: 'none', text: T('p_unknown') };
    if (n.via && NETS[n.via]) n = NETS[n.via];
    if (n.free && isFree(s)) return { kind: 'free', note: tr(n.free_note) || '', date: n.date || '' };
    var hay = hayOf(s);
    var receipt = (n.receipts || []).filter(function (r) { return (r.where || []).some(function (w) { return hay.indexOf(w) >= 0; }); });
    if (s.pr && s.pr.l && s.pr.l.length) { var ls = stationLines(s); return { kind: 'station', t: ls[0], lines: ls, receipt: receipt, note: tr(n.note) }; }
    if (n.free && !(n.tiers || []).length && !(n.places || []).length) return { kind: 'none', text: tr(n.note) || T('p_unknown') };
    var cur = s.dc ? 'dc' : 'ac', P = power(s);
    var fits = function (t) { return t.cur === cur && (t.lo == null || (P >= t.lo - 5 && P <= t.hi + 5)); };
    // 'guard' copies in cene.json keep older map code right; this one never takes a price of the other current
    var all = (n.tiers || []).concat(n.places || []).filter(function (t) { return !t.guard; });
    var exact = all.filter(function (t) { return (t.where || []).some(function (w) { return hay.indexOf(w) >= 0; }); });
    var ex = exact.filter(fits)[0] || (exact.length === 1 && exact[0].cur === cur ? exact[0] : null);
    if (ex) return { kind: 'exact', t: ex, receipt: receipt, note: tr(n.note) };
    if (n.kwh) {
      var fit = (n.tiers || []).filter(function (t) { return t.cur === cur && fits(t); });
      return fit.length ? { kind: 'kwh', list: fit, note: tr(n.note) } : { kind: 'none', text: tr(n.note) || T('p_unknown') };
    }
    var tiers = (n.tiers || []).filter(function (t) { return t.cur === cur; });
    var t1 = tiers.filter(fits)[0];
    if (t1) return { kind: 'tier', t: t1, receipt: receipt, note: tr(n.note) };
    if (cur === 'dc' && tiers.length && P && tiers.every(function (x) { return x.v != null; })) {
      var lower = tiers.filter(function (x) { return x.hi <= P; }).pop(), upper = tiers.filter(function (x) { return x.lo >= P; })[0];
      if (lower && upper) return { kind: 'range', lo: lower, hi: upper, note: tr(n.note) };
    }
    var same = all.filter(function (x) { return x.cur === cur; });
    if (same.length) return { kind: 'seen', list: same, note: tr(n.note) };
    return { kind: 'none', text: tr(n.note) || T('p_unknown') };
  }

  // ---------- cost per kWh and per km („Moj auto“) — the same engine as blokvolt.rs/mapa ----------
  // What a car really takes: AC — the car's on-board charger, the post's phases and current (22 kW = 3 × 32 A, 11 kW = 3 × 16 A,
  // 7,4 kW = 1 × 32 A); DC — the car's 10–80 % average, at most 88 % of the station's power. Without a car: a typical car
  // (REAL_KW, AC 11 kW). Losses from the charger to the battery: DC 4 %, AC 8–16 % by power (ADAC 08/2026). A start fee is
  // spread over half the battery (25 kWh without a car). Winter: the car's winter factor in December–February, half in
  // November and March. The car is chosen for this visit only: evolako.rs keeps nothing in the browser but the language.
  var CAR = null, CARS = null, CARS_P = null, COSTV = 0, CARS_URL = '', FUEL = null;
  var ETA_DC = 0.96;
  function etaAc(kw) { return kw >= 10 ? 0.92 : kw >= 6 ? 0.9 : kw >= 3.3 ? 0.88 : 0.84; }
  function acPost(kw) { return kw >= 21 ? [3, 32] : kw >= 10.5 ? [3, 16] : kw >= 7 ? [1, 32] : [1, 16]; }
  function winterShare() { var m = new Date().getMonth(); return m === 11 || m <= 1 ? 1 : m === 10 || m === 2 ? 0.5 : 0; }
  function loadCars() {
    if (CARS) return Promise.resolve(CARS);
    if (!CARS_P) {
      CARS_P = (CARS_URL ? fetch(FEED + CARS_URL).then(function (r) { if (!r.ok) throw new Error('cars'); return r.json(); }) : Promise.reject(new Error('cars')))
        .then(function (j) { CARS = j.cars || []; return CARS; }, function () { CARS_P = null; return null; });
    }
    return CARS_P;
  }
  function carSpec() {
    if (!CAR || !CARS) return null;
    var c = null;
    for (var i = 0; i < CARS.length; i++) if (CARS[i].id === CAR.id) { c = CARS[i]; break; }
    if (!c) return null;
    var o = CAR.opt && c.opt ? c.opt : c;
    return Object.assign({}, c, { ac: o.ac, ph: o.ph, a: o.a, cons: CAR.cons && CAR.cons >= 8 && CAR.cons <= 40 ? CAR.cons : c.cons, cab: CAR.cab });
  }
  function carName(c) { return c ? c.mk + ' ' + c.md.replace(/\s*\(.*?\)\s*/g, ' ').trim() : ''; }
  function carKw(car, cur, kw) {
    if (!kw) return null;
    if (cur === 'dc') return Math.min(car.dc, 0.88 * kw);
    var pa = acPost(kw);
    return Math.min(car.ac, kw, 0.23 * Math.min(pa[1], car.a) * Math.min(pa[0], car.ph));
  }
  // one tariff at one connector → {kw: what the car takes, kwh: RSD per kWh from the charger, km: RSD per km (with a car)}
  function lineCost(t, cur, kw) {
    var car = carSpec();
    var P = car ? carKw(car, cur, kw) : realKw(kw, cur);
    if (!P || t.ut || (t.v == null && t.k == null && t.h == null)) return null;   // Spectra "units" are not kWh
    var eta = cur === 'dc' ? ETA_DC : etaAc(P);
    var sess = car ? car.kwh * 0.5 / eta : 25;
    var kwh = (t.k || 0) + (t.v ? t.v * 60 / P : 0) + (t.h ? t.h / P : 0) + (t.pm ? t.pm * 60 / P : 0) + (t.st ? t.st / sess : 0);
    var cons = car ? car.cons * (1 + (car.wf - 1) * winterShare()) : null;
    return { kw: P, kwh: kwh, km: car ? kwh * cons / 100 / eta : null, eta: eta };
  }
  // a CHAdeMO car needs a CHAdeMO plug for DC, a CCS car a CCS one (Tesla stalls: Teslas only)
  function dcUsable(s, car) {
    if (!car || !s.c.length) return true;
    if (car.pl === 'chademo') return s.c.some(function (c) { return c[0] === 'chademo'; });
    return s.c.some(function (c) { return c[1] === 'dc' && c[0] !== 'chademo' && (c[0] !== 'tesla' || car.mk === 'Tesla'); });
  }
  function acUsable(s) { return !s.c.length || s.c.some(function (c) { return c[1] !== 'dc'; }) || (!s.dc && s.ac); }
  function costLines(s, p) {
    var car = carSpec(), ls = [];
    if (p.kind === 'station') ls = p.lines.map(function (t) { return { t: t, cur: t.cur, kw: t.kw }; });
    else if (p.kind === 'exact' || p.kind === 'tier') {
      ls = [{ t: p.t, cur: s.dc ? 'dc' : 'ac', kw: power(s) }];
      var n = netOf(s);
      if (s.dc && s.ac && n && p.kind === 'tier') {
        var at = (n.tiers || []).filter(function (x) { return x.cur === 'ac' && (x.lo == null || (s.ac >= x.lo - 5 && s.ac <= x.hi + 5)); })[0];
        if (at) ls.push({ t: at, cur: 'ac', kw: s.ac });
      }
    } else return [];
    return ls.filter(function (l) { return !car || (l.cur === 'dc' ? dcUsable(s, car) : acUsable(s)); })
      .map(function (l) { l.c = lineCost(l.t, l.cur, l.kw); return l; }).filter(function (l) { return l.c; });
  }
  // the line a driver most likely uses (the most powerful one the car can use) and a cheaper one at the same station
  function costOf(s) {
    if (s._cv === COSTV) return s._co;
    var out = null;
    if (!isOff(s)) {
      var p = price(s);
      var ls = p.kind === 'free' || p.kind === 'tesla' ? [] : costLines(s, p);
      if (ls.length) {
        var main = ls.slice().sort(function (a, b) { return b.c.kw - a.c.kw; })[0];
        var cheap = ls.slice().sort(function (a, b) { return a.c.kwh - b.c.kwh; })[0];
        out = { p: p, main: main, alt: cheap !== main && cheap.c.kwh < main.c.kwh * 0.8 ? cheap : null };
      }
    }
    s._cv = COSTV; s._co = out;
    return out;
  }
  function fmtKm(x) { return fmt(x, x < 10 ? 1 : 0); }
  function homeKm(car) { return HOME_KWH * car.cons / 100 / 0.92; }
  function fuelKm() { return FUEL && FUEL.b && FUEL.l ? FUEL.b * FUEL.l / 100 : null; }
  function priceShort(s) {
    if (isOff(s)) return { t: ver(s) === 'prob' ? T('v_prob_t') : T('off'), cls: 'off' };
    var p = price(s);
    if (p.kind === 'free') return { t: T('free'), cls: 'free' };
    if (p.kind === 'tesla') return { t: T('tesla_only'), cls: 'off' };
    if (carSpec()) { var c0 = costOf(s); if (c0 && c0.main.c.km != null) return { t: '≈ ' + fmtKm(c0.main.c.km) + ' ' + T('per_km'), cls: '' }; }
    var rc = freshReceipts(p);
    if (rc) return { t: rc + ' ' + T('per_kwh'), cls: '' };
    if (p.kind === 'station' || p.kind === 'exact' || p.kind === 'tier') {
      var co = costOf(s);
      if (co && (co.main.t.v || co.main.t.h || co.main.t.st)) return { t: '≈ ' + fmt(Math.round(co.main.c.kwh)) + ' ' + T('per_kwh'), cls: '' };
      return { t: unit(tr(p.t.label)), cls: '' };
    }
    if (p.kind === 'range') return { t: fmt(p.lo.v, 2) + '–' + fmt(p.hi.v, 2) + ' ' + T('per_min'), cls: '' };
    if (p.kind === 'kwh') return { t: kwhSpan(p.list, '–') + ' ' + T('per_kwh'), cls: '' };
    return { t: '', cls: '' };
  }
  // the label under a pin (zoom 12+): ASCII only, the map font has no other glyphs everywhere; no label when the price is unknown
  function pinPrice(s) {
    if (isOff(s)) return { t: '', c: '' };
    var p = price(s);
    if (p.kind === 'free') return { t: '0 RSD', c: 'free' };
    if (p.kind === 'tesla') return { t: '', c: '' };
    var old = function (dd) { return stale(dd) ? 'old' : ''; };
    if (carSpec()) { var c0 = costOf(s); if (c0 && c0.main.c.km != null) return { t: '~' + fmtKm(c0.main.c.km) + ' RSD/km', c: old(c0.main.t.date) }; }
    var rc = freshReceipts(p, '-');
    if (rc) return { t: rc + ' RSD/kWh', c: '' };
    if (p.kind === 'station' || p.kind === 'exact' || p.kind === 'tier') {
      var co = costOf(s);
      if (co) {
        var exact = co.main.t.k != null && !co.main.t.v && !co.main.t.h && !co.main.t.st;
        return { t: (exact ? '' : '~') + Math.round(co.main.c.kwh) + ' RSD/kWh', c: old(co.main.t.date) };
      }
    }
    if (p.kind === 'range') {
      var a = perKwh(p.lo.v, s), b = perKwh(p.hi.v, s);
      if (a && b) return { t: '~' + Math.round(Math.min(a, b)) + '-' + Math.round(Math.max(a, b)) + ' RSD/kWh', c: old(p.lo.date) };
    }
    if (p.kind === 'kwh') { var sp = kwhSpan(p.list, '-'); return sp === '?' ? { t: '', c: '' } : { t: sp + ' RSD/kWh', c: old(p.list[0].date) }; }
    return { t: '', c: '' };
  }

  // ---------- hours: „sada radi“ in Serbia's time, whatever the visitor's time zone (oh.w = open windows in minutes) ----------
  function nowMin() {
    try {
      var parts = new Intl.DateTimeFormat('en-GB', { timeZone: 'Europe/Belgrade', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).formatToParts(new Date());
      var h = 0, mi = 0;
      parts.forEach(function (x) { if (x.type === 'hour') h = +x.value % 24; if (x.type === 'minute') mi = +x.value; });
      return h * 60 + mi;
    } catch (e) { var n = new Date(); return n.getHours() * 60 + n.getMinutes(); }
  }
  function hhmm(x) { return String(Math.floor(x / 60) % 24).padStart(2, '0') + ':' + String(x % 60).padStart(2, '0'); }
  function openState(s, t) {
    var oh = s.oh;
    if (!oh) return null;
    if (oh.h24) return { open: true, h24: true };
    if (!oh.w || !oh.w.length) return null;
    var m = t == null ? nowMin() : t, i, next = null;
    for (i = 0; i < oh.w.length; i++) { var a = oh.w[i][0], b = oh.w[i][1]; if ((m >= a && m < b) || (m + 1440 >= a && m + 1440 < b)) return { open: true, until: b % 1440 }; }
    for (i = 0; i < oh.w.length; i++) { var dl = ((oh.w[i][0] - m) % 1440 + 1440) % 1440; if (!next || dl < next.d) next = { d: dl, at: oh.w[i][0] % 1440 }; }
    return { open: false, at: next ? next.at : null };
  }
  function closedNow(s) { var o = openState(s); return !!o && !o.open; }

  // ---------- filters ----------
  function matchChip(s, f) {
    if (f === 'fast' && !((s.dc || 0) >= 50)) return false;
    if (f === 'ac' && !(s.ac || s.c.some(function (c) { return c[1] !== 'dc'; }))) return false;
    if (f === 'free' && (isOff(s) || !isFree(s))) return false;
    if (f === 'chademo' && !s.c.some(function (c) { return c[0] === 'chademo'; })) return false;
    if (f.indexOf('net:') === 0 && s.net !== f.slice(4)) return false;
    return true;
  }
  function match(s) {
    if (!matchChip(s, state.f)) return false;
    if (state.ok && ver(s) !== 'ok') return false;
    if (state.q) {
      var hay = s._q || (s._q = sfold([s.n, s.a, s.t, netName(s), s.opn].concat(s.al || []).join(' ')));
      var ws = sfold(state.q).split(/\s+/).filter(Boolean);
      for (var i = 0; i < ws.length; i++) if (hay.indexOf(ws[i]) < 0) return false;
    }
    return true;
  }
  function visible() { return ST.filter(match); }
  function inView(s) { var b = state.bounds; return !b || (s.lat >= b.s && s.lat <= b.n && s.lon >= b.w && s.lon <= b.e); }
  function distKm(a, b) {
    var r = Math.PI / 180, dLa = (b.lat - a.lat) * r, dLo = (b.lon - a.lon) * r;
    var h = Math.pow(Math.sin(dLa / 2), 2) + Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.pow(Math.sin(dLo / 2), 2);
    return 12742 * Math.asin(Math.sqrt(h));
  }

  // ---------- skeleton ----------
  function $(q) { return root.querySelector(q); }
  root.innerHTML = '<div class="evm-app">' +
    '<div class="evm-top"><div class="evm-srow"><div class="evm-search">' + IC.search +
    '<label class="evm-sr" for="evm-q"></label><input id="evm-q" type="search" autocomplete="off" autocapitalize="off" spellcheck="false" enterkeyhint="search"></div>' +
    '<button class="evm-me" type="button">' + IC.loc + '<span></span></button></div>' +
    '<button class="evm-car" type="button" aria-haspopup="dialog">' + IC.car + '<span class="evm-car-l"></span> <span class="evm-car-v"></span></button>' +
    '<div class="evm-chips" role="group"></div></div>' +
    '<div class="evm-count" aria-live="polite"></div><div class="evm-list" role="region"></div>' +
    '<div class="evm-mapw"><div class="evm-mapbox"><div class="evm-map" role="region"></div>' +
    '<button class="evm-fs" type="button"></button><button class="evm-near" type="button">' + IC.nav + '<span></span></button></div>' +
    '<div class="evm-legend" aria-hidden="true"></div><div class="evm-attr"></div></div>' +
    '<div class="evm-card" hidden></div></div>';
  var $q = $('#evm-q'), $chips = $('.evm-chips'), $count = $('.evm-count'), $list = $('.evm-list'), $card = $('.evm-card'), $me = $('.evm-me'), $fs = $('.evm-fs');
  var $near = $('.evm-near'), $car = $('.evm-car');
  var CHIP_NETS = ['chargego', 'orion-emobility', 'putevi-srbije', 'tesla'];

  function count(net) { var n = 0; ST.forEach(function (s) { if (s.net === net) n++; }); return n; }
  function renderStatic() {
    $q.placeholder = T('search');
    $('label[for="evm-q"]').textContent = T('search_l');
    $me.querySelector('span').textContent = T('near');
    $me.setAttribute('aria-label', T('near'));
    $near.querySelector('span').textContent = T('nr_btn');
    $('.evm-map').setAttribute('aria-label', T('map_l'));
    $list.setAttribute('aria-label', T('list_l'));
    $chips.setAttribute('aria-label', T('filters'));
    paintFs();
    var chips = [['ok', IC.ok + esc(T('ok'))], ['all', esc(T('all'))], ['fast', IC.bolt + esc(T('fast'))], ['ac', 'AC'], ['free', esc(T('free_c'))], ['chademo', 'CHAdeMO']];
    if (carSpec()) chips.splice(2, 0, ['cheap', IC.coins + esc(T('cheap'))]);
    CHIP_NETS.forEach(function (k) { if (NETS[k] && count(k) >= 4) chips.push(['net:' + k, esc(NETS[k].name) + ' <span class="n">' + count(k) + '</span>']); });
    $chips.innerHTML = chips.map(function (c) { return '<button class="evm-chip" type="button" data-f="' + c[0] + '" aria-pressed="false">' + c[1] + '</button>'; }).join('');
    paintChips();
    paintCar();
    $('.evm-legend').innerHTML = [['dc', 'l_dc'], ['ac', 'l_ac'], ['off', 'l_off'], ['nep', 'l_nep']]
      .map(function (x) { return '<span><i class="lg-' + x[0] + '"></i>' + esc(T(x[1])) + '</span>'; }).join('');
    $('.evm-attr').innerHTML = esc(T('map_w')) + ': <a href="https://openfreemap.org" target="_blank" rel="noopener">OpenFreeMap</a> © <a href="https://www.openmaptiles.org/" target="_blank" rel="noopener">OpenMapTiles</a> · ' +
      esc(T('data')) + ': © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>, <a href="https://openchargemap.org" target="_blank" rel="noopener">Open Charge Map</a>, JP Putevi Srbije · ' +
      esc(fill(T('base'), { b: '' })) + '<a href="https://www.blokvolt.rs/mapa/" target="_blank" rel="noopener">blokvolt.rs</a>' +
      (CHECKED ? ' · ' + esc(fill(T('updated'), { d: CHECKED })) : '');
    var zi = root.querySelector('.maplibregl-ctrl-zoom-in'), zo = root.querySelector('.maplibregl-ctrl-zoom-out');
    if (zi) { zi.title = T('zin'); zi.setAttribute('aria-label', T('zin')); }
    if (zo) { zo.title = T('zout'); zo.setAttribute('aria-label', T('zout')); }
    var cm = root.querySelector('.maplibregl-desktop-message');
    if (cm) cm.textContent = T(/Mac/.test(navigator.platform) ? 'coop_m' : 'coop_w');
    var tm = root.querySelector('.maplibregl-mobile-message');
    if (tm) tm.textContent = T('coop_t');
    labelLang();
  }
  // place and street names in the page language: Serbian Latin on the Serbian page, English or Russian names where OSM has them
  var LBL = null;
  function labelLang() {
    if (!map || !map.isStyleLoaded || !LBL) return;
    var l = lang(), f = l === 'en' ? ['coalesce', ['get', 'name:en'], ['get', 'name:latin'], ['get', 'name']]
      : l === 'ru' ? ['coalesce', ['get', 'name:ru'], ['get', 'name:sr'], ['get', 'name:latin'], ['get', 'name']]
      : ['coalesce', ['get', 'name:sr-Latn'], ['get', 'name:latin'], ['get', 'name']];
    LBL.forEach(function (id) { if (map.getLayer(id)) map.setLayoutProperty(id, 'text-field', f); });
  }
  function paintChips() {
    [].forEach.call($chips.querySelectorAll('.evm-chip'), function (c) {
      var f = c.getAttribute('data-f');
      c.setAttribute('aria-pressed', (f === 'ok' ? state.ok : f === 'cheap' ? state.cheap : f === state.f) ? 'true' : 'false');
    });
  }
  function paintFs() {
    var on = root.classList.contains('evm-full');
    $fs.innerHTML = on ? IC.unfull : IC.full;
    $fs.setAttribute('aria-label', T(on ? 'fs_off' : 'fs_on'));
    $fs.title = T(on ? 'fs_off' : 'fs_on');
  }

  // ---------- list ----------
  function promoHtml() {
    var car = carSpec();
    return '<a class="evm-promo" href="/proveri-svoju-garazu"><span class="evm-promo-ic">' + IC.home + '</span><span><b>' + esc(T('promo_t')) + '</b>' +
      '<small>' + esc(car ? fill(T('promo_km'), { h: fmt(homeKm(car), 1) }) : fill(T('promo_s'), { k: fmt(HOME_KWH) })) + '</small><em>' + esc(T('promo_a')) + ' →</em></span></a>';
  }
  function renderList() {
    if (!dataReady) return;
    var rows = visible().filter(inView), ref = me;
    if (ref) rows = rows.map(function (s) { s._d = distKm(ref, s); return s; }).sort(function (a, b) { return a._d - b._d; });
    var cheap = state.cheap && !!carSpec() && !ref;
    if (cheap) {
      var ck = function (s) { if (isOff(s)) return Infinity; if (isFree(s)) return 0; var co = costOf(s); return co && co.main.c.km != null ? co.main.c.km : Infinity; };
      rows = rows.map(function (s) { s._k = ck(s); return s; }).sort(function (a, b) { return a._k - b._k; });
    }
    var txt = state.bounds ? fill(T('in_view'), { n: rows.length }) : fill(rows.length === ST.length ? T('count_all') : T('count'), { n: rows.length, all: ST.length });
    $count.innerHTML = '<span>' + esc(txt + (ref ? ' · ' + T('sorted_near') : cheap ? ' · ' + T('sorted_cheap') : '')) + '</span>' +
      (state.bounds || ref ? '<button class="evm-lnk" type="button" data-all>' + esc(T('all_serbia')) + '</button>' : '');
    var lim = mobile() ? state.lim : Infinity, more = rows.length - lim;
    var html = rows.slice(0, lim).map(function (s) {
      var k = kind(s), ps = priceShort(s), pw = power(s), v = ver(s);
      var sub = [netName(s), place(s), closedNow(s) ? T('closed_now') : ''].filter(Boolean).join(' · ');
      var dist = ref ? '<span>' + fmt(s._d, s._d < 10 ? 1 : 0) + ' ' + kmU() + '</span>' : '';
      var q = v === 'nep' ? ' <i class="evm-q" title="' + esc(T('v_nep')) + '">?</i>' : v === 'prob' ? ' <i class="evm-q no" title="' + esc(T('v_prob_t')) + '">!</i>' : '';
      return '<button class="evm-st' + (sel === s ? ' is-on' : '') + (v === 'nep' ? ' is-nep' : '') + '" type="button" data-id="' + esc(s.id) + '">' +
        '<span class="evm-dot ' + k + '">' + (k === 'tesla' ? 'T' : pw ? Math.round(pw) : '') + '</span>' +
        '<span class="evm-nm"><b>' + esc(title(s)) + q + '</b><span>' + esc(sub) + '</span></span>' +
        '<span class="evm-pr ' + ps.cls + '">' + esc(ps.t) + dist + '</span></button>';
    }).join('');
    $list.innerHTML = promoHtml() + (html || '<p class="evm-empty">' + esc(T('none')) + '</p>') +
      (more > 0 ? '<div class="evm-more"><button class="evm-btn" type="button" data-more>' + esc(fill(T('more'), { n: more })) + '</button></div>' : '');
  }

  // ---------- card ----------
  function connLine(c) {
    var nm = CONN[c[0]] || (c[0] === 'schuko' ? T('schuko') : T('other'));
    return nm + ' · ' + String(c[1]).toUpperCase() + (c[2] ? ' · ' + fmt(c[2], c[2] % 1 ? 1 : 0) + ' ' + kWu() : '') + (c[3] > 1 ? ' × ' + c[3] : '');
  }
  function estHtml(v, s) {
    var e = perKwh(v, s);
    return e ? '<small class="evm-est">' + esc(fill(T('p_est'), { k: fmt(Math.round(e)), w: fmt(Math.round(realKw(power(s), s.dc ? 'dc' : 'ac'))) })) + '</small>' : '';
  }
  function homeHtml(s) {
    if (isOff(s) || isFree(s)) return '';
    var car = carSpec();
    return '<a class="evm-home" href="/paketi-i-cene">' + IC.home + '<span><b>' + esc(car ? fill(T('home_km'), { h: fmt(homeKm(car), 1) }) : fill(T('home_t'), { k: fmt(HOME_KWH) })) + '</b><small>' +
      esc(T('home_s')) + ' · <u>' + esc(T('home_a')) + ' →</u></small></span></a>';
  }
  var IDLE = { chargego: '5 RSD/min posle 15 min', 'orion-emobility': '5 RSD/min posle 15 min', 'emobility-spectra': '10,20 RSD/min posle 10 min (ECO)' };
  function priceHtml(s) {
    var p = price(s), h = '<div class="evm-box"><span class="evm-lbl">' + esc(T('price')) + '</span>', t, rc, tariff;
    if (p.kind === 'free') {
      h += '<div class="evm-price free">' + esc(p.label || T('p_free')) + '</div>' + (p.src ? '<small>' + esc(p.src) + '</small>' : '') + (p.note ? '<small>' + esc(p.note) + '</small>' : '');
    } else if (p.kind === 'tesla') {
      h += '<div class="evm-price">' + esc(T('p_tesla_only')) + '</div>' + (p.label ? '<small>' + esc(fill(T('p_tesla_fee'), { t: p.label, s: p.src || '' })) + '</small>' : '') + (p.note ? '<small>' + esc(p.note) + '</small>' : '');
    } else if (p.kind === 'station') {
      // the network's app, connector by connector: the most powerful first
      t = p.t; rc = freshReceipts(p);
      if (rc) h += '<div class="evm-price">' + esc(rc + ' ' + T('per_kwh')) + '</div><small>' + esc(fill(T('p_by_receipt'), { d: p.receipt.map(function (r) { return dt(r.date); }).filter(function (x, i, a) { return a.indexOf(x) === i; }).join(', ') })) + '</small>';
      else h += '<div class="evm-price">' + esc(t.label) + (p.lines.length > 1 ? ' <span class="evm-pc">' + esc(t.charger) + '</span>' : '') + '</div>' +
        (carSpec() ? '' : estHtml(t.v, Object.assign({}, s, { dc: t.cur === 'dc' ? t.kw : null, ac: t.cur === 'ac' ? t.kw : null })));
      if (p.lines.length > 1 || rc) h += '<ul class="evm-plines">' + p.lines.map(function (l) { return '<li><span>' + esc(l.charger) + (l.n > 1 ? ' × ' + l.n : '') + '</span><b>' + esc(l.label) + '</b></li>'; }).join('') + '</ul>';
      h += '<small>' + esc(fill(T('p_station'), { d: dt(t.date), s: tr(t.src) })) + '</small>';
    } else if (p.kind === 'exact' || p.kind === 'tier') {
      t = p.t; rc = freshReceipts(p);
      tariff = (p.kind === 'exact' ? T('p_exact') : fill(T('p_tier'), { c: unit(t.charger) })) + ' · ' + dt(t.date) + (t.src ? ' · ' + tr(t.src) : '');
      if (rc) {
        h += '<div class="evm-price">' + esc(rc + ' ' + T('per_kwh')) + '</div><small>' + esc(fill(T('p_by_receipt'), { d: p.receipt.map(function (r) { return dt(r.date); }).filter(function (x, i, a) { return a.indexOf(x) === i; }).join(', ') })) + '</small>';
        h += '<small>' + esc(tariff + ': ' + tr(t.label)) + '</small>';
      } else {
        h += '<div class="evm-price">' + esc(unit(tr(t.label))) + '</div>' + (carSpec() ? '' : estHtml(t.v, s)) + '<small>' + esc(tariff) + '</small>';
      }
      if (t.extra) h += '<small>' + esc(tr(t.extra)) + '</small>';
    } else if (p.kind === 'range') {
      h += '<div class="evm-price">' + fmt(p.lo.v, 2) + '–' + fmt(p.hi.v, 2) + ' ' + esc(T('per_min')) + '</div>';
      var a = perKwh(p.lo.v, s), b = perKwh(p.hi.v, s);
      if (a && b) h += '<small class="evm-est">' + esc(fill(T('p_est'), { k: fmt(Math.round(Math.min(a, b))) + '–' + fmt(Math.round(Math.max(a, b))), w: fmt(Math.round(realKw(power(s), 'dc'))) })) + '</small>';
      h += '<small>' + esc(fill(T('p_range'), { a: unit(p.lo.charger), b: unit(p.hi.charger) })) + ' · ' + esc(dt(p.lo.date)) + '</small>';
    } else if (p.kind === 'kwh') {
      var t0 = p.list[0];
      h += '<div class="evm-price">' + esc(kwhSpan(p.list, '–') + ' ' + T('per_kwh')) + '</div>';
      if (p.list.length > 1 || t0.extra) h += '<ul>' + p.list.map(function (x) { return '<li><b>' + esc(tr(x.label)) + '</b>' + (x.extra ? ' — ' + esc(tr(x.extra)) : '') + '</li>'; }).join('') + '</ul>';
      h += '<small>' + esc(fill(T('p_list'), { d: dt(t0.date) })) + (t0.src ? ' · ' + esc(tr(t0.src)) : '') + '</small>';
    } else if (p.kind === 'seen') {
      h += '<div>' + esc(T('p_seen')) + '</div><ul>' + p.list.slice(0, 3).map(function (x) { return '<li><b>' + esc(tr(x.label)) + '</b> — ' + esc(unit(x.charger)) + (x.extra ? ', ' + esc(tr(x.extra)) : '') + '</li>'; }).join('') + '</ul>';
      h += '<small>' + esc(p.note || '') + ' · ' + esc(dt(p.list[0].date)) + '</small>';
    } else {
      h += '<div class="evm-pnone">' + esc(p.text) + '</div>';
    }
    if (p.note && (p.kind === 'exact' || p.kind === 'tier' || p.kind === 'range' || p.kind === 'kwh' || p.kind === 'station')) h += '<small>' + esc(p.note) + '</small>';
    var pd = p.kind === 'exact' || p.kind === 'tier' || p.kind === 'station' ? p.t.date : p.kind === 'range' ? p.lo.date : p.kind === 'seen' || p.kind === 'kwh' ? p.list[0].date : p.kind === 'free' ? p.date : '';
    if (stale(pd)) h += '<small class="evm-stale">' + esc(T('p_old')) + '</small>';
    var idle = IDLE[(netOf(s) && netOf(s).via) || s.net];
    if (idle && p.kind !== 'free' && p.kind !== 'none') h += '<small>' + esc(fill(T('idle'), { x: tr(idle) })) + '</small>';
    return h + costHtml(s, p) + homeHtml(s) + '</div>';
  }
  // „Za tvoj auto“: RSD/km for the chosen car, 100 km, what the car takes here; petrol and home at night beside it; a cheaper
  // connector here or a much cheaper charger within 10 km. Without a car: a link that opens the car picker.
  function costHtml(s, p) {
    if (p.kind === 'free' || p.kind === 'tesla' || p.kind === 'none' || isOff(s)) return '';
    var car = carSpec(), has = p.kind === 'station' || p.kind === 'exact' || p.kind === 'tier';
    if (!car) return has && CARS_URL ? '<p class="evm-cost-pick"><button class="evm-lnk" type="button" data-car-open>' + IC.car + '<span>' + esc(T('cost_pick')) + '</span></button></p>' : '';
    var co = costOf(s);
    if (!co) return has ? '<div class="evm-cost na">' + IC.car + '<div><small>' + esc(fill(car.pl === 'chademo' && !dcUsable(s, car) ? T('cost_no_dc') : T('cost_na'), { car: carName(car) })) + '</small></div></div>' : '';
    var m = co.main, km = m.c.km;
    var h = '<div class="evm-cost">' + IC.car + '<div><b>' + esc(fill(T('cost_t'), { car: carName(car), x: fmtKm(km) })) + '</b>' +
      '<small>' + esc(fill(T('cost_100'), { x: fmt(Math.round(km * 100)) })) + ' · ' + esc(fill(T('cost_kw'), { w: fmt(Math.round(m.c.kw)), k: fmt(Math.round(m.c.kwh)) })) +
      (co.p.kind === 'station' && co.p.lines.length > 1 ? ' (' + esc(m.t.charger) + ')' : '') + '</small>';
    if (m.t.st) h += '<small>' + esc(fill(T('cost_start'), { s: fmt(m.t.st) })) + '</small>';
    if (winterShare()) h += '<small>' + esc(fill(T('cost_winter'), { p: fmt(Math.round((car.wf - 1) * winterShare() * 100)) })) + '</small>';
    if (co.alt && co.alt.c.km != null) h += '<small class="evm-tip">' + esc(fill(T('cost_alt'), { c: co.alt.t.charger || (String(co.alt.cur).toUpperCase() + ' ' + fmt(co.alt.kw) + ' ' + kWu()), x: fmtKm(co.alt.c.km) })) + '</small>';
    var nb = nearCheaper(s, km);
    if (nb) {
      var what = title(nb.s) + ' (' + (nb.s.dc ? 'DC ' + Math.round(nb.s.dc) : 'AC ' + Math.round(nb.s.ac || 0)) + ' ' + kWu() + ')';
      h += '<small class="evm-tip">' + esc(fill(nb.km ? T('cost_near') : T('cost_near_free'), { t: what, d: fmtDist(nb.d), x: fmtKm(nb.km) })) + '</small>';
    }
    var fb = fuelKm();
    h += '<small class="evm-cmp">' + esc(fb ? fill(T('cost_cmp'), { b: fmtKm(fb), h: fmt(homeKm(car), 1) }) : fill(T('home_km'), { h: fmt(homeKm(car), 1) })) + '</small>';
    return h + '</div></div>';
  }
  // a charger within 10 km that costs at least 40 % less per km for the chosen car (confirmed, works, open now, usable by the car)
  function nearCheaper(s, km) {
    if (!km) return null;
    var best = null;
    ST.forEach(function (x) {
      if (x === s || ver(x) !== 'ok' || !nearUsable(x)) return;
      if (Math.abs(x.lat - s.lat) > 0.1 || Math.abs(x.lon - s.lon) > 0.14) return;
      var dkm = distKm(s, x);
      if (dkm > 10) return;
      var co = isFree(x) ? null : costOf(x), c = isFree(x) ? 0 : co && co.main.c.km;
      if (c == null || c === false || c > km * 0.6) return;
      if (!best || c < best.km || (c === best.km && dkm < best.d)) best = { s: x, km: c, d: dkm };
    });
    return best;
  }
  // „Kako se puni ovde“: the network's steps, payment, without registration, after charging (cene.json: kako) — folded
  function kakoHtml(s) {
    var n = netOf(s), k = n && n.kako;
    if (!k) return '';
    var row = function (lbl, x) { return x ? '<p><b>' + esc(lbl) + '</b> ' + esc(tr(x)) + '</p>' : ''; };
    var links = (k.apps || []).map(function (a) { return '<a href="' + esc(a.u) + '" target="_blank" rel="noopener nofollow">' + esc(tr(a.l)) + '</a>'; }).join(' · ');
    var src = (k.src || []).map(function (a) { return '<a href="' + esc(a.u) + '" target="_blank" rel="noopener nofollow">' + esc(tr(a.l)) + '</a>'; }).join(' · ');
    return '<details class="evm-box evm-kako"><summary>' + esc(fill(T('kako_t'), { n: n.name })) + '</summary>' +
      (k.start && k.start.length ? '<ol>' + k.start.map(function (x) { return '<li>' + esc(tr(x)) + '</li>'; }).join('') + '</ol>' : '') +
      row(T('kako_pay'), k.pay) + row(T('kako_guest'), k.guest) + row(T('kako_after'), k.after) + row(T('kako_refund'), k.refund) +
      (links ? '<p class="evm-kako-apps">' + esc(T('kako_apps')) + ' ' + links + '</p>' : '') +
      '<small>' + esc(fill(T('kako_checked'), { d: dt(k.checked || '') })) + (src ? ' · ' + src : '') + '</small></details>';
  }
  function statusHtml(s) {
    if (!s.ps) return '';
    var li = s.ps.l.map(function (l) {
      return '<li class="' + (l[2] === 1 ? 'ok' : 'no') + '"><i></i><span>' + esc(unit([l[0], l[1]].filter(Boolean).join(' · '))) + ' · <b>' + esc(l[2] === 1 ? T('st_ok') : T('st_off')) + '</b>' +
        (l[3] && T('st_' + l[3]) ? ' (' + esc(T('st_' + l[3])) + ')' : '') + '</span></li>';
    }).join('');
    return '<div class="evm-box"><span class="evm-lbl">' + esc(T('status')) + '</span><ul class="evm-stl">' + li + '</ul><small>' + esc(fill(T('st_src'), { d: dt(s.ps.d) })) + '</small></div>';
  }
  function tagsHtml(s) {
    var t = [];
    if (s.oh && s.oh.t) {
      var o = openState(s);
      var now = o && !o.h24 ? (o.open ? fill(T('oh_open'), { t: hhmm(o.until) }) : fill(T('oh_closed'), { t: o.at != null ? hhmm(o.at) : '?' })) : '';
      t.push('<span class="evm-tag' + (s.oh.h24 ? ' ok' : o && !o.open ? ' warn' : '') + '">' + IC.clock + esc(tr(s.oh.t)) + (now ? ' · ' + esc(now) : '') + '</span>');
    }
    if (s.cab && s.cab.own) { var car = carSpec(); t.push('<span class="evm-tag' + (car && !car.cab ? ' warn' : '') + '">' + IC.cable + esc(T('cab_own')) + '</span>'); }
    if (s.park && s.park.t) t.push('<span class="evm-tag">' + IC.park + esc(tr(s.park.t)) + '</span>');
    if (s.ax && s.ax.t) t.push('<span class="evm-tag' + (s.ax.who === 'tesla' ? ' warn' : '') + '">' + esc(tr(s.ax.t)) + '</span>');
    if (s.ax && s.ax.limit) t.push('<span class="evm-tag">' + esc(tr(s.ax.limit)) + '</span>');
    return t.length ? '<div class="evm-tags">' + t.join('') + '</div>' : '';
  }
  function verHtml(s) {
    var v = s.v || { s: 'nep', g: 'g_none' };
    if (v.s === 'ok') {
      var VBY = { cg: 'v_cg', rm: 'v_rm', te: 'v_te', ps: 'v_ps', g: 'v_g', own: 'v_own' };
      var by = (v.by || []).map(function (b) { return VBY[b] ? T(VBY[b]) : ''; }).filter(Boolean).join('; ');
      return '<p class="evm-vf">' + IC.ok + '<span><b>' + esc(T('v_ok')) + '</b> ' + esc(by) + (v.d ? ' · ' + esc(dt(v.d)) : '') + '</span></p>';
    }
    var why = v.s === 'prob' ? T('v_prob') : (v.g === 'test' ? T('v_test') : v.g === 'g_old' ? T('v_old') : T('v_none'));
    return '<div class="evm-vw' + (v.s === 'prob' ? ' no' : '') + '"><b>' + IC.warn + esc(v.s === 'prob' ? T('v_prob_t') : T('v_nep')) + '</b><p>' + esc(why) + '</p>' +
      (v.d ? '<small>' + esc(fill(T('v_checked'), { d: dt(v.d) })) + '</small>' : '') + '</div>';
  }
  function dms(v, pos, neg) {
    var a = Math.abs(v), dg = Math.floor(a), m = Math.floor((a - dg) * 60), sc = Math.round(((a - dg) * 60 - m) * 600) / 10;
    if (sc >= 60) { sc = 0; m += 1; }
    if (m >= 60) { m = 0; dg += 1; }
    return dg + '°' + String(m).padStart(2, '0') + '′' + sc.toFixed(1).padStart(4, '0') + '″' + (v >= 0 ? pos : neg);
  }
  var OLC = '23456789CFGHJMPQRVWX';
  function plusCode(lat, lon) {
    var la = Math.floor((Math.min(Math.max(lat, -90), 89.9999999) + 90) * 8000 + 1e-7), lo = Math.floor(((((lon + 180) % 360) + 360) % 360) * 8000 + 1e-7), c = '';
    for (var i = 0; i < 5; i++) { c = OLC[la % 20] + OLC[lo % 20] + c; la = Math.floor(la / 20); lo = Math.floor(lo / 20); }
    return c.slice(0, 8) + '+' + c.slice(8);
  }
  function pointQ(s) {
    if (s.loc && s.loc.q) return s.loc.q;
    return { cg: 'net', rm: 'net', te: 'net', ps: 'site', osm: 'osm', ocm: 'ocm' }[s.id.split('-')[0]] || '';
  }
  function whereHtml(s) {
    var L0 = s.loc || {}, ll = (+s.lat).toFixed(5) + ', ' + (+s.lon).toFixed(5), q = pointQ(s);
    return '<div class="evm-box evm-where"><span class="evm-lbl">' + esc(T('where')) + '</span>' +
      '<p class="evm-adr">' + (s.a ? esc(s.a) : '<i>' + esc(T('addr_none')) + '</i>') + (L0.venue ? '<small>' + esc(tr(L0.venue)) + '</small>' : '') + '</p>' +
      (L0.find ? '<p class="evm-find">' + IC.pin + '<span>' + esc(tr(L0.find)) + '</span></p>' : '') +
      '<div class="evm-ll"><code translate="no">' + ll + '</code><button class="evm-btn sm" type="button" data-copy="' + ll + '">' + IC.copy + '<span>' + esc(T('copy')) + '</span></button></div>' +
      '<small translate="no">' + dms(+s.lat, 'N', 'S') + ' ' + dms(+s.lon, 'E', 'W') + ' · Plus Code ' + plusCode(+s.lat, +s.lon) + '</small>' +
      (q ? '<small>' + esc(T('q_' + q)) + '</small>' : '') + '</div>';
  }
  function lock(on) { d.documentElement.classList.toggle('evm-lock', !!on); }
  function openCard(s, fly, fromNear) {
    var wasOpen = !!sel || nearOpen || carOpen;
    carOpen = false;
    sel = s;
    nearOpen = false;
    cardNear = !!(fromNear && NEAR);
    var n = netOf(s), navs = navLinks(s);
    var logo = n && n.logo ? '<span class="evm-lg' + (n.logo_dark ? ' dark' : '') + '"><img src="' + esc(FEED + n.logo) + '" alt="" loading="lazy"></span>' : '<span class="evm-lg mono" aria-hidden="true">' + esc((netName(s) || '?').slice(0, 2).toUpperCase()) + '</span>';
    var netLine = netName(s) ? '<div class="evm-net">' + logo + '<div><b>' + esc(netName(s)) + '</b><span>' + esc(n ? T('net_known') : (s.opn ? T('operator') : T('net_unknown'))) + '</span></div></div>' : '';
    var conns = s.c.length ? '<div class="evm-box"><span class="evm-lbl">' + esc(T('conn')) + '</span><ul class="evm-cl">' + s.c.map(function (c) { return '<li>' + esc(connLine(c)) + '</li>'; }).join('') + '</ul></div>' : '';
    var acc = s.acc === 'customers' ? '<div class="evm-box"><span class="evm-lbl">' + esc(T('access')) + '</span><div>' + esc(T('customers')) + '</div></div>' : '';
    var site = n && n.site ? n.site : '';
    var mail = 'mailto:hello@evolako.com?subject=' + encodeURIComponent(fill(T('mail_s'), { id: s.id })) + '&body=' + encodeURIComponent(title(s) + ' — ' + location.origin + location.pathname + '#' + s.id + '\n\n' + T('mail_b') + '\n');
    var SRC = { ocm: 'Open Charge Map', osm: 'OpenStreetMap', ps: 'JP Putevi Srbije', cg: 'Charge&GO', rm: T('src_rm'), te: 'Tesla', cga: T('src_cga') };
    var srcs = s.src.filter(function (x) { return x.u; }).map(function (x) { return '<a href="' + esc(x.u) + '" target="_blank" rel="noopener nofollow">' + esc(tr(x.l) || SRC[x.d] || x.d) + '</a>' + (x.upd ? ' (' + esc(dt(x.upd)) + ')' : ''); }).join(' · ');
    $card.innerHTML = '<div class="evm-cc" role="dialog" aria-label="' + esc(title(s)) + '"><span class="evm-grab" aria-hidden="true"></span>' +
      '<button class="evm-x" type="button" aria-label="' + esc(T('close')) + '">' + IC.x + '</button>' +
      (cardNear ? '<button class="evm-lnk evm-nr-back" type="button" data-nr="back">← ' + esc(T('nr_title')) + '</button>' : '') +
      '<h2>' + esc(title(s)) + '</h2><p class="evm-addr">' + esc(place(s)) + '</p>' + verHtml(s) + tagsHtml(s) + netLine + priceHtml(s) + kakoHtml(s) +
      (s.note ? '<p class="evm-note">' + IC.info + '<span>' + esc(tr(s.note)) + '</span></p>' : '') + statusHtml(s) + conns + acc + whereHtml(s) +
      '<div class="evm-acts"><a class="evm-btn pri full" href="' + navs[0][1] + '" target="_blank" rel="noopener" data-nav="' + navs[0][2] + '">' + IC.nav + '<span>' + esc(T('navigate')) + '</span></a>' +
      '<p class="evm-navalt">' + esc(T('nav_in')) + ' ' + navs.slice(1).map(function (x) { return '<a href="' + x[1] + '" target="_blank" rel="noopener" data-nav="' + x[2] + '">' + x[0] + '</a>'; }).join(' · ') + '</p>' +
      '<button class="evm-btn" type="button" data-share>' + IC.share + '<span>' + esc(T('share')) + '</span></button>' +
      '<a class="evm-btn" href="' + mail + '">' + IC.flag + '<span>' + esc(T('report')) + '</span></a>' +
      (site ? '<a class="evm-btn full" href="' + esc(site) + '" target="_blank" rel="noopener">' + IC.ext + '<span>' + esc(T('site')) + '</span></a>' : '') + '</div>' +
      (srcs ? '<p class="evm-src">' + esc(T('data')) + ': ' + srcs + '</p>' : '') + '</div>';
    $card.hidden = false;
    $card.scrollTop = 0;
    var cc = $card.querySelector('.evm-cc');
    if (cc) cc.scrollTop = 0;
    root.classList.add('evm-open');
    if (mobile()) lock(true);
    if (map && map.getSource('sel')) map.getSource('sel').setData({ type: 'FeatureCollection', features: [feat(s)] });
    if (fly && map) map.flyTo({ center: [s.lon, s.lat], zoom: Math.max(map.getZoom(), 13), speed: 1.4 });
    try { history.replaceState(null, '', location.pathname + location.search + '#' + s.id); } catch (e) { /* ignore */ }
    if (!wasOpen) { var x = $card.querySelector('.evm-x'); if (x && x.focus) x.focus({ preventScroll: true }); }
    renderList();
  }
  function closeCard() {
    if (carOpen) { closeCar(); return; }
    if (nearOpen && !sel) { closeNear(); return; }
    if (!sel) return;
    var id = sel.id;
    sel = null;
    $card.hidden = true;
    $card.innerHTML = '';
    root.classList.remove('evm-open');
    if (!root.classList.contains('evm-full')) lock(false);
    if (map && map.getSource('sel')) map.getSource('sel').setData({ type: 'FeatureCollection', features: [] });
    try { history.replaceState(null, '', location.pathname + location.search); } catch (e) { /* ignore */ }
    renderList();
    var b = $list.querySelector('[data-id="' + (window.CSS && CSS.escape ? CSS.escape(id) : id) + '"]');
    if (b && !mobile()) b.focus({ preventScroll: false });
  }
  function share(s, b) {
    var url = location.origin + location.pathname + '#' + encodeURIComponent(s.id);
    if (navigator.share) { navigator.share({ title: title(s), text: [title(s), place(s)].filter(Boolean).join(' — '), url: url }).catch(function () {}); return; }
    var ok = function () { var sp = b.querySelector('span'); sp.textContent = T('copied'); setTimeout(function () { if (b.isConnected) sp.textContent = T('share'); }, 2500); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(url).then(ok, function () { window.prompt(T('share'), url); });
    else window.prompt(T('share'), url);
  }

  // ---------- „Najbliži punjač“: the three nearest chargers a driver can really use, and a route in a navigation app ----------
  // The same rules as the Evolako and BlokVolt apps and blokvolt.rs/mapa: the chip filter counts, the search text and the visible
  // part of the map do not; never a charger that does not work or is only for Tesla vehicles; only confirmed ones unless the
  // visitor asks for the rest (or there is no confirmed one at all); the order is the straight-line distance and nothing else —
  // no network or firm is ever put first. The location stays in the browser: nothing is sent and nothing is stored.
  function nearUsable(s) { return !isOff(s) && (!teslaOnly(s) || teslaCar()) && !closedNow(s) && typeof s.lat === 'number' && typeof s.lon === 'number' && isFinite(s.lat) && isFinite(s.lon); }
  function nearestList(pt, withNep) {
    var all = ST.filter(function (s) { return nearUsable(s) && matchChip(s, state.f); })
      .map(function (s) { return { s: s, d: distKm(pt, s) }; })
      .sort(function (a, b) { return a.d - b.d || (((b.s.dc || 0) >= 50) - ((a.s.dc || 0) >= 50)) || fold(title(a.s)).localeCompare(fold(title(b.s))); });
    var ok = all.filter(function (x) { return ver(x.s) === 'ok'; });
    // „Potvrđeni“ switched on means confirmed only, even when none is left
    var every = !state.ok && (withNep || !ok.length);
    var rows = (every ? all : ok).slice(0, 3);
    var last = rows.length ? rows[rows.length - 1].d : Infinity;
    var more = !every && !state.ok && all.some(function (x) { return ver(x.s) !== 'ok' && (rows.length < 3 || x.d < last); });
    return { rows: rows, every: every, more: more };
  }
  // 230 m · 2,4 km · 17 km (metres rounded to ten)
  function fmtDist(km) { var m = Math.round(km * 100) * 10; return m < 1000 ? m + ' ' + kmU(1) : fmt(km, km < 10 ? 1 : 0) + ' ' + kmU(); }
  function chipLabel(f) {
    var el = $chips.querySelector('[data-f="' + (window.CSS && CSS.escape ? CSS.escape(f) : f) + '"]');
    if (!el) return f;
    var c = el.cloneNode(true);
    [].forEach.call(c.querySelectorAll('.n, svg'), function (x) { x.parentNode.removeChild(x); });
    return c.textContent.trim();
  }
  function setF(f) { state.f = f; paintChips(); refresh(); }
  function nearRow(x, i) {
    var s = x.s, k = kind(s), pw = power(s), ps = priceShort(s), a = navPref(), dist = fmtDist(x.d), tags = [];
    if (ver(s) !== 'ok') tags.push('<span class="evm-tag warn">' + IC.warn + esc(T('v_nep')) + '</span>');
    if (s.oh && s.oh.t && !s.oh.h24) tags.push('<span class="evm-tag">' + IC.clock + esc(tr(s.oh.t)) + '</span>');
    if (s.ax && s.ax.t) tags.push('<span class="evm-tag">' + esc(tr(s.ax.t)) + '</span>');
    else if (s.acc === 'customers') tags.push('<span class="evm-tag">' + esc(T('customers')) + '</span>');
    return '<li class="evm-nr' + (i ? '' : ' first') + '">' +
      '<button class="evm-nr-main" type="button" data-open="' + esc(s.id) + '"><span class="evm-dot ' + k + (ver(s) === 'nep' ? ' nep' : '') + '">' + (pw ? Math.round(pw) : '') + '</span>' +
      '<span class="evm-nr-nm"><b>' + esc(title(s)) + '</b><span class="evm-nr-sb">' + esc([netName(s), place(s)].filter(Boolean).join(' · ')) + '</span>' +
      '<span class="evm-nr-meta"><b>' + esc(dist) + '</b>' + (ps.t ? ' · ' + esc(ps.t) : '') + '</span></span></button>' +
      '<a class="evm-btn ' + (i ? 'sm' : 'pri') + ' evm-nr-go" href="' + esc(navUrl(a, s)) + '" target="_blank" rel="noopener" data-nav="' + a + '" aria-label="' +
      esc(fill(T('nr_nav_to'), { t: title(s), d: dist })) + '">' + IC.nav + '<span>' + esc(T('navigate')) + '</span></a>' +
      (tags.length ? '<div class="evm-tags evm-nr-tags">' + tags.slice(0, 2).join('') + '</div>' : '') + '</li>';
  }
  function nearChips() {
    var f = state.f, other = f !== 'all' && f !== 'fast';
    return '<div class="evm-nr-chips"><button class="evm-chip" type="button" data-nr="fast" aria-pressed="' + (f === 'fast') + '">' + IC.bolt + esc(T('nr_fast')) + '</button>' +
      (other ? '<button class="evm-chip" type="button" data-nr="all" aria-pressed="true">' + esc(chipLabel(f)) + ' <span aria-hidden="true">✕</span><span class="evm-sr">' + esc(T('nr_unfilter')) + '</span></button>' : '') + '</div>';
  }
  // the visitor and the chargers in the panel on one screen, clear of the button, the legend and the full-screen top bar
  function nearFit(pt, rows) {
    if (!map || !pt || !window.maplibregl) return;
    var b = new window.maplibregl.LngLatBounds([pt.lon, pt.lat], [pt.lon, pt.lat]);
    rows.forEach(function (x) { b.extend([x.s.lon, x.s.lat]); });
    var pad = !mobile() ? { top: 76, bottom: 76, left: 56, right: 64 } : root.classList.contains('evm-full') ? { top: 150, bottom: 140, left: 40, right: 40 } : { top: 60, bottom: 76, left: 40, right: 40 };
    map.fitBounds(b, { padding: pad, maxZoom: 15, duration: 900 });
  }
  function showMe() {
    if (!map || !map.getSource('me')) return;
    map.getSource('me').setData({ type: 'FeatureCollection', features: me ? [{ type: 'Feature', geometry: { type: 'Point', coordinates: [me.lon, me.lat] }, properties: {} }] : [] });
  }
  function nearPanel(o, fit) {
    var was = nearOpen || !!sel || carOpen, body;
    carOpen = false;
    if (sel) { sel = null; try { history.replaceState(null, '', location.pathname + location.search); } catch (e) { /* ignore */ } renderList(); }
    nearOpen = true;
    if (o.pt && !dataReady && dataErr) body = '<p class="evm-nr-msg" role="alert">' + esc(T('load_err')) + '</p>';
    else if (o.wait || (o.pt && !dataReady)) body = '<p class="evm-nr-wait" role="status"><span class="evm-nr-spin" aria-hidden="true"></span>' + esc(T(o.wait ? 'nr_wait' : 'loading')) + '</p>';
    else if (o.ask) body = '<p class="evm-nr-msg">' + esc(T('nr_ask')) + '</p><button class="evm-btn pri evm-nr-cta" type="button" data-nr="go">' + IC.nav + '<span>' + esc(T('nr_find')) + '</span></button>';
    else if (o.err) body = '<p class="evm-nr-msg" role="alert">' + esc(T(o.err === 'denied' ? 'nr_denied' : 'nr_unavail')) + '</p><button class="evm-btn evm-nr-cta" type="button" data-nr="go">' + esc(T('nr_retry')) + '</button>';
    else {
      var r = nearestList(o.pt, o.withNep), a = navPref(), apps = navApps();
      o.rows = r.rows;
      body = '<p class="evm-addr">' + esc(T(r.every ? 'nr_sub_all' : 'nr_sub')) + '</p>' + nearChips() +
        (r.rows.length
          ? '<ol class="evm-nrl">' + r.rows.map(nearRow).join('') + '</ol>' + (r.rows[0].d > 100 ? '<p class="evm-nr-msg">' + esc(T('nr_far')) + '</p>' : '')
          : '<p class="evm-nr-msg">' + esc(T('none')) + '</p>' + (state.f !== 'all' ? '<button class="evm-btn sm" type="button" data-nr="all">' + esc(T('nr_unfilter')) + '</button>' : '')) +
        (r.more ? '<p class="evm-nr-more"><button class="evm-lnk" type="button" data-nr="nep">' + esc(T('nr_nep')) + '</button></p>' : '') +
        (r.rows.length && apps.length > 1
          ? '<p class="evm-nr-app">' + esc(fill(T('nr_opens'), { a: NAV_NAME[a] })) + ' · <button class="evm-lnk" type="button" data-nr="apps" aria-expanded="false">' + esc(T('nr_change')) + '</button></p>' +
            '<div class="evm-nr-apps" hidden>' + apps.map(function (x) { return '<button class="evm-chip" type="button" data-app="' + x + '" aria-pressed="' + (x === a) + '">' + NAV_NAME[x] + '</button>'; }).join('') + '</div>'
          : '') +
        '<p class="evm-nr-note">' + esc(T('nr_privacy')) + '</p>';
      if (map && map.getSource('sel')) map.getSource('sel').setData({ type: 'FeatureCollection', features: r.rows.length ? [feat(r.rows[0].s)] : [] });
      if (fit) nearFit(o.pt, r.rows);
    }
    $card.innerHTML = '<div class="evm-cc evm-nrp" role="dialog" aria-label="' + esc(T('nr_title')) + '"><span class="evm-grab" aria-hidden="true"></span>' +
      '<button class="evm-x" type="button" aria-label="' + esc(T('close')) + '">' + IC.x + '</button><h2>' + esc(T('nr_title')) + '</h2>' + body + '</div>';
    $card.hidden = false;
    root.classList.add('evm-open');
    if (mobile()) lock(true);
    if (!was) {
      $card.scrollTop = 0;
      var x = $card.querySelector('.evm-x');
      if (x && x.focus) x.focus({ preventScroll: true });
    }
  }
  function nearGo(source) {
    var o = NEAR = { pt: null, withNep: false, source: source };
    if (!navigator.geolocation) { o.err = 'unavail'; nearPanel(o); return; }
    o.wait = true;
    nearPanel(o);
    $near.disabled = true;
    navigator.geolocation.getCurrentPosition(function (pos) {
      $near.disabled = false;
      if (NEAR !== o) return;
      o.wait = false;
      me = o.pt = { lat: pos.coords.latitude, lon: pos.coords.longitude };
      state.bounds = null;
      state.lim = 20;
      showMe();
      renderList();
      if (nearOpen) nearPanel(o, true);   // not when the panel was closed while the browser was looking for the location
    }, function (err) {
      $near.disabled = false;
      if (NEAR !== o) return;
      o.wait = false;
      o.err = err && err.code === 1 ? 'denied' : 'unavail';
      if (nearOpen) nearPanel(o);
    }, { enableHighAccuracy: false, timeout: 10000, maximumAge: 120000 });
  }
  function closeNear() {
    nearOpen = false;
    $card.hidden = true;
    $card.innerHTML = '';
    root.classList.remove('evm-open');
    if (!root.classList.contains('evm-full')) lock(false);
    if (map && map.getSource('sel')) map.getSource('sel').setData({ type: 'FeatureCollection', features: [] });
    if (!mobile() && $near.focus) $near.focus({ preventScroll: true });
  }
  // clicks inside the panel (its HTML is rebuilt on every change) and the „back“ link of a card opened from it
  function nearClick(t) {
    if (!NEAR) return false;
    if (!nearOpen) {
      if (sel && t.closest('[data-nr="back"]')) { nearPanel(NEAR, false); return true; }
      return false;
    }
    var op = t.closest('[data-open]');
    if (op) { var s = BYID[op.getAttribute('data-open')]; if (s) openCard(s, true, true); return true; }
    var ap = t.closest('[data-app]');
    if (ap) { NAV_PREF = ap.getAttribute('data-app'); nearPanel(NEAR, false); return true; }
    var b = t.closest('[data-nr]');
    if (!b) return false;
    var k = b.getAttribute('data-nr');
    if (k === 'go') nearGo(NEAR.source || 'button');
    else if (k === 'fast') { setF(state.f === 'fast' ? 'all' : 'fast'); nearPanel(NEAR, true); }
    else if (k === 'all') { setF('all'); nearPanel(NEAR, true); }
    else if (k === 'nep') { NEAR.withNep = true; nearPanel(NEAR, true); }
    else if (k === 'apps') {
      var box = $card.querySelector('.evm-nr-apps');
      if (box) { box.hidden = !box.hidden; b.setAttribute('aria-expanded', String(!box.hidden)); }
    }
    return true;
  }
  $card.addEventListener('click', function (e) {
    var t = e.target;
    if (t === $card || t.closest('.evm-x')) { closeCard(); return; }
    var nv = t.closest('a[data-nav]');
    if (nv) { NAV_PREF = nv.getAttribute('data-nav'); return; }
    if (nearClick(t)) return;
    if (t.closest('[data-car-open]')) { openCar(); return; }
    var cb = t.closest('button[data-car]');
    if (cb && carOpen) {
      var k = cb.getAttribute('data-car');
      if (k === 'save') {
        var md = $card.querySelector('[data-car="md"]'), cons = $card.querySelector('[data-car="cons"]'), cab = $card.querySelector('[data-car="cab"]'), opt = $card.querySelector('[data-car="opt"]');
        if (!md || !md.value) return;
        var cv = parseFloat(String((cons && cons.value) || '').replace(',', '.'));
        CAR = { id: md.value, cons: cv >= 8 && cv <= 40 ? cv : null, cab: !!(cab && cab.checked), opt: !!(opt && opt.checked) };
        carChanged();
        closeCar();
      } else if (k === 'clear') { CAR = null; state.cheap = false; carChanged(); closeCar(); }
      return;
    }
    var b = t.closest('[data-copy]');
    if (b) {
      var txt = b.getAttribute('data-copy'), lbl = b.querySelector('span');
      var ok = function () { lbl.textContent = T('copied_ll'); setTimeout(function () { if (b.isConnected) lbl.textContent = T('copy'); }, 2500); };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(txt).then(ok, function () { window.prompt(T('copy'), txt); }); else window.prompt(T('copy'), txt);
      return;
    }
    var sh = t.closest('[data-share]');
    if (sh && sel) share(sel, sh);
  });

  // ---------- map ----------
  function feat(s) {
    var v = ver(s), k = kind(s), p = k === 'tesla' ? 'T' : (Math.round(power(s)) || ''), pp = pinPrice(s);
    return { type: 'Feature', geometry: { type: 'Point', coordinates: [s.lon, s.lat] },
      properties: { id: s.id, k: k, v: v, p: String(p), pl: pp.t, pc: pp.c, cl: closedNow(s) ? 1 : 0 } };
  }
  function data() { return { type: 'FeatureCollection', features: visible().map(feat) }; }
  function refresh() { state.lim = 20; if (map && map.getSource('st')) map.getSource('st').setData(data()); renderList(); }
  // the price capsule under a pin, as in the app: a rounded box that stretches around the text
  function capsule(color) {
    var r = 2, w = 32 * r, c = d.createElement('canvas'), x;
    c.width = w; c.height = w;
    x = c.getContext('2d');
    x.fillStyle = color;
    x.beginPath();
    if (x.roundRect) x.roundRect(0, 0, w, w, 8 * r); else x.rect(0, 0, w, w);
    x.fill();
    return { img: x.getImageData(0, 0, w, w), opt: { pixelRatio: r, stretchX: [[8 * r, 24 * r]], stretchY: [[8 * r, 24 * r]] } };
  }
  function srbBounds() { return new window.maplibregl.LngLatBounds(SRB[0], SRB[1]); }
  function initMap() {
    var ml = window.maplibregl;
    if (!ml || (ml.supported && ml.supported() === false)) throw new Error('no webgl');
    // on a computer the page scrolls over the map and Ctrl/⌘ + wheel (or a trackpad pinch) zooms; on a phone one finger moves the map
    map = new ml.Map({ container: $('.evm-map'), style: STYLE, bounds: SRB, fitBoundsOptions: { padding: 16 }, minZoom: 5, maxZoom: 18, attributionControl: false,
      dragRotate: false, pitchWithRotate: false, touchPitch: false, cooperativeGestures: !mobile() && !('ontouchstart' in window),
      locale: { 'NavigationControl.ZoomIn': T('zin'), 'NavigationControl.ZoomOut': T('zout'), 'CooperativeGesturesHandler.WindowsHelpText': T('coop_w'),
        'CooperativeGesturesHandler.MacHelpText': T('coop_m'), 'CooperativeGesturesHandler.MobileHelpText': T('coop_t') } });
    if (/[?&]qa=1\b/.test(location.search)) window.evmMap = map;
    map.touchZoomRotate.disableRotation();
    map.keyboard.disableRotation();
    map.addControl(new ml.NavigationControl({ showCompass: false }), 'top-right');
    renderStatic();
    map.on('load', function () {
      LBL = map.getStyle().layers.filter(function (y) {
        var tf = y.type === 'symbol' && y.layout && y.layout['text-field'];
        return tf && /name/.test(JSON.stringify(tf)) && !/"ref"|\{ref\}|housenumber/.test(JSON.stringify(tf));
      }).map(function (y) { return y.id; });
      labelLang();
      var ck = capsule(INK), cb = capsule(DEEP);
      if (!map.hasImage('evm-cap-k')) map.addImage('evm-cap-k', ck.img, ck.opt);
      if (!map.hasImage('evm-cap-b')) map.addImage('evm-cap-b', cb.img, cb.opt);
      map.addSource('st', { type: 'geojson', data: data(), cluster: true, clusterRadius: 44, clusterMaxZoom: 11 });
      map.addSource('sel', { type: 'geojson', data: { type: 'FeatureCollection', features: sel ? [feat(sel)] : [] } });
      map.addSource('me', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
      var nep = ['==', ['get', 'v'], 'nep'], pt = ['!', ['has', 'point_count']];
      map.addLayer({ id: 'me-halo', type: 'circle', source: 'me', paint: { 'circle-radius': 24, 'circle-color': 'rgba(46,107,255,.16)' } });
      map.addLayer({ id: 'cl', type: 'circle', source: 'st', filter: ['has', 'point_count'],
        paint: { 'circle-color': INK, 'circle-radius': ['step', ['get', 'point_count'], 15, 10, 19, 30, 23], 'circle-stroke-width': 2.5, 'circle-stroke-color': '#FFFFFF' } });
      map.addLayer({ id: 'cl-n', type: 'symbol', source: 'st', filter: ['has', 'point_count'],
        layout: { 'text-field': ['get', 'point_count_abbreviated'], 'text-font': FONT, 'text-size': 13, 'text-allow-overlap': true }, paint: { 'text-color': '#FFFFFF' } });
      map.addLayer({ id: 'sel', type: 'circle', source: 'sel', paint: { 'circle-radius': 21, 'circle-color': 'rgba(46,107,255,.22)', 'circle-stroke-width': 2.5, 'circle-stroke-color': BLUE } });
      // an invisible, larger circle takes the taps: small pins are hard to hit with a finger
      map.addLayer({ id: 'pt-hit', type: 'circle', source: 'st', filter: pt, paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 6, 12, 12, 18, 16, 21], 'circle-opacity': 0 } });
      map.addLayer({ id: 'pt', type: 'circle', source: 'st', filter: pt,
        paint: {
          'circle-radius': ['interpolate', ['linear'], ['zoom'], 6, 6, 11, 9, 12, 11.5, 16, 13.5],
          'circle-color': ['match', ['get', 'k'], 'dc', INK, 'ac', BLUE, SLATE],
          'circle-opacity': ['case', ['==', ['get', 'cl'], 1], 0.45, nep, 0.5, 1],
          'circle-stroke-width': ['interpolate', ['linear'], ['zoom'], 6, 1.5, 12, 2.5],
          'circle-stroke-color': '#FFFFFF', 'circle-stroke-opacity': ['case', nep, 0.8, 1]
        } });
      map.addLayer({ id: 'pt-kw', type: 'symbol', source: 'st', filter: pt, minzoom: 11,
        layout: { 'text-field': ['get', 'p'], 'text-font': FONT, 'text-size': ['interpolate', ['linear'], ['zoom'], 11, 9, 16, 11], 'text-allow-overlap': true, 'text-ignore-placement': true },
        paint: { 'text-color': '#FFFFFF' } });
      map.addLayer({ id: 'pt-pr', type: 'symbol', source: 'st', filter: ['all', pt, ['!=', ['get', 'pl'], '']], minzoom: 12,
        layout: { 'text-field': ['get', 'pl'], 'text-font': FONT, 'text-size': 11, 'text-anchor': 'top', 'text-offset': [0, 1.45], 'text-padding': 3,
          'icon-image': ['match', ['get', 'pc'], 'free', 'evm-cap-b', 'evm-cap-k'], 'icon-text-fit': 'both', 'icon-text-fit-padding': [3, 7, 2, 7] },
        paint: { 'text-color': ['match', ['get', 'pc'], 'old', 'rgba(255,255,255,0.62)', '#FFFFFF'] } });
      map.addLayer({ id: 'me-dot', type: 'circle', source: 'me', paint: { 'circle-radius': 7, 'circle-color': '#FFFFFF', 'circle-stroke-width': 4, 'circle-stroke-color': BLUE } });
      map.on('movestart', function (e) { if (e.originalEvent) userMove = true; });
      map.on('moveend', function () {
        if (!userMove) return;
        userMove = false;
        if (map.getZoom() >= 8) { var b = map.getBounds(); state.bounds = { s: b.getSouth(), n: b.getNorth(), w: b.getWest(), e: b.getEast() }; } else state.bounds = null;
        state.lim = 20;
        renderList();
      });
      map.on('click', function (e) {
        var hit = map.queryRenderedFeatures(e.point, { layers: ['cl', 'pt-hit'] });
        if (!hit.length) { if (sel && !mobile()) closeCard(); return; }
        var f = hit.filter(function (x) { return x.layer.id === 'pt-hit'; })[0] || hit[0];
        if (f.layer.id === 'cl') {
          userMove = true;
          var src = map.getSource('st'), done = function (z) { map.easeTo({ center: f.geometry.coordinates, zoom: z + 0.3 }); };
          var r = src.getClusterExpansionZoom(f.properties.cluster_id, function (err, z) { if (!err) done(z); });
          if (r && r.then) r.then(done, function () {});
          return;
        }
        var s = BYID[f.properties.id];
        if (s) openCard(s, false);
      });
      ['cl', 'pt-hit'].forEach(function (l) {
        map.on('mouseenter', l, function () { map.getCanvas().style.cursor = 'pointer'; });
        map.on('mouseleave', l, function () { map.getCanvas().style.cursor = ''; });
      });
      if (sel) map.jumpTo({ center: [sel.lon, sel.lat], zoom: 13 });
      showMe();
      if (nearOpen && NEAR && NEAR.rows) {
        map.getSource('sel').setData({ type: 'FeatureCollection', features: NEAR.rows.length ? [feat(NEAR.rows[0].s)] : [] });
        nearFit(NEAR.pt, NEAR.rows);
      }
    });
  }
  function startMap() {
    if (map || !mlReady || !dataReady) return;
    try { initMap(); } catch (e) { noMap(); }
  }
  function noMap() {
    root.classList.add('evm-nomap');
    $('.evm-map').innerHTML = '<p class="evm-nomap-t">' + esc(T('no_map')) + '</p>';
  }
  function loadMaplibre() {
    if (window.maplibregl) { mlReady = true; return; }
    var l = d.createElement('link');
    l.rel = 'stylesheet'; l.href = ML + '.css'; l.integrity = ML_CSS; l.crossOrigin = 'anonymous';
    d.head.appendChild(l);
    var sc = d.createElement('script');
    sc.src = ML + '.js'; sc.integrity = ML_JS; sc.crossOrigin = 'anonymous'; sc.async = true;
    sc.onload = function () { mlReady = true; startMap(); };
    sc.onerror = function () { if (dataReady) noMap(); else mlReady = 'err'; };
    d.head.appendChild(sc);
  }
  function fitTo(rows) {
    if (!map || !rows.length || rows.length > 60) return;
    if (rows.length === 1) { map.flyTo({ center: [rows[0].lon, rows[0].lat], zoom: 13 }); return; }
    var b = new window.maplibregl.LngLatBounds();
    rows.forEach(function (s) { b.extend([s.lon, s.lat]); });
    map.fitBounds(b, { padding: 48, maxZoom: 13, duration: 700 });
  }
  function setFull(on) {
    root.classList.toggle('evm-full', on);
    lock(on || ((!!sel || nearOpen) && mobile()));
    paintFs();
    if (map) setTimeout(function () { map.resize(); }, 30);
  }

  // ---------- „Moj auto“: the car for this visit only (evolako.rs keeps nothing in the browser but the language) ----------
  var carOpen = false, carBack = null;
  function paintCar() {
    var c = carSpec();
    $car.querySelector('.evm-car-l').textContent = T('car_btn_l');
    $car.querySelector('.evm-car-v').textContent = c ? carName(c) : T('car_pick');
    $car.classList.toggle('on', !!c);
    $car.hidden = !CARS_URL && dataReady;
  }
  function modelOpts(list, mk, id) {
    return list.filter(function (c) { return c.mk === mk; }).map(function (c) {
      return '<option value="' + esc(c.id) + '"' + (c.id === id ? ' selected' : '') + '>' + esc(c.md + ' (' + c.y + ')') + '</option>';
    }).join('');
  }
  function openCar() {
    if (!carOpen) carBack = sel ? { s: sel, near: cardNear } : nearOpen ? { near: true } : null;
    var was = !!sel || nearOpen || carOpen;
    if (sel) { sel = null; try { history.replaceState(null, '', location.pathname + location.search); } catch (e) { /* ignore */ } renderList(); }
    nearOpen = false;
    carOpen = true;
    $card.innerHTML = '<div class="evm-cc evm-carp" role="dialog" aria-label="' + esc(T('car_title')) + '"><span class="evm-grab" aria-hidden="true"></span>' +
      '<button class="evm-x" type="button" aria-label="' + esc(T('close')) + '">' + IC.x + '</button><h2>' + esc(T('car_title')) + '</h2>' +
      '<p class="evm-addr">' + esc(T('car_intro')) + '</p><div class="evm-carf"><p class="evm-nr-wait" role="status"><span class="evm-nr-spin" aria-hidden="true"></span>' +
      esc(T('loading')) + '</p></div></div>';
    $card.hidden = false;
    root.classList.add('evm-open');
    if (mobile()) lock(true);
    if (!was) { var x = $card.querySelector('.evm-x'); if (x && x.focus) x.focus({ preventScroll: true }); }
    loadCars().then(function (list) { if (carOpen) carForm(list); });
  }
  function carForm(list) {
    var box = $card.querySelector('.evm-carf');
    if (!box) return;
    if (!list || !list.length) { box.innerHTML = '<p class="evm-nr-msg" role="alert">' + esc(T('car_load_err')) + '</p>'; return; }
    var cur = CAR ? list.filter(function (c) { return c.id === CAR.id; })[0] : null, mk = cur ? cur.mk : '', makes = [];
    list.forEach(function (c) { if (makes.indexOf(c.mk) < 0) makes.push(c.mk); });
    box.innerHTML = '<label class="evm-fl"><span>' + esc(T('car_make')) + '</span><select data-car="mk"><option value="">' + esc(T('car_none')) + '</option>' +
      makes.map(function (m) { return '<option' + (m === mk ? ' selected' : '') + '>' + esc(m) + '</option>'; }).join('') + '</select></label>' +
      '<label class="evm-fl"><span>' + esc(T('car_model')) + '</span><select data-car="md"' + (mk ? '' : ' disabled') + '>' +
      (mk ? modelOpts(list, mk, cur && cur.id) : '<option value="">' + esc(T('car_none')) + '</option>') + '</select></label>' +
      '<label class="evm-fl"><span>' + esc(T('car_cons')) + '</span><input data-car="cons" type="number" inputmode="decimal" min="8" max="40" step="0.1" value="' +
      (CAR && CAR.cons ? CAR.cons : '') + '"></label><div data-car="optw"></div>' +
      '<label class="evm-fc"><input data-car="cab" type="checkbox"' + (CAR && CAR.cab ? ' checked' : '') + '> <span>' + esc(T('car_cab')) + '</span></label>' +
      '<div class="evm-fbtn"><button class="evm-btn pri" type="button" data-car="save">' + esc(T('car_save')) + '</button>' +
      (CAR ? '<button class="evm-btn" type="button" data-car="clear">' + esc(T('car_clear')) + '</button>' : '') + '</div>' +
      '<p class="evm-nr-note">' + esc(T('car_src')) + '</p>';
    carOpt(list);
  }
  // the selected model: its consumption as the placeholder, and its optional on-board charger
  function carOpt(list) {
    var md = $card.querySelector('[data-car="md"]'), c = md ? list.filter(function (x) { return x.id === md.value; })[0] : null;
    var cons = $card.querySelector('[data-car="cons"]'), w = $card.querySelector('[data-car="optw"]');
    if (cons) cons.placeholder = c ? fill(T('car_cons_ph'), { x: fmt(c.cons, 1) }) : '';
    if (w) w.innerHTML = c && c.opt ? '<label class="evm-fc"><input data-car="opt" type="checkbox"' + (CAR && CAR.id === c.id && CAR.opt ? ' checked' : '') + '> <span>' +
      esc(fill(T('car_opt'), { k: fmt(c.opt.ac, c.opt.ac % 1 ? 1 : 0) })) + '</span></label>' : '';
  }
  function closeCar() {
    carOpen = false;
    var back = carBack;
    carBack = null;
    if (back && back.s) { openCard(back.s, false, back.near); return; }
    if (back && back.near && NEAR) { nearPanel(NEAR, false); return; }
    $card.hidden = true;
    $card.innerHTML = '';
    root.classList.remove('evm-open');
    if (!root.classList.contains('evm-full')) lock(false);
    if (!mobile() && $car.focus) $car.focus({ preventScroll: true });
  }
  function carChanged() {
    COSTV++;
    if (!carSpec()) state.cheap = false;
    renderStatic();
    if (map && map.getSource('st')) map.getSource('st').setData(data());
    renderList();
  }
  $car.addEventListener('click', function () { openCar(); });
  $card.addEventListener('change', function (e) {
    var t = e.target, k = t.getAttribute ? t.getAttribute('data-car') : null;
    if (!carOpen || !k || !CARS) return;
    if (k === 'mk') {
      var md = $card.querySelector('[data-car="md"]');
      md.innerHTML = t.value ? modelOpts(CARS, t.value, '') : '<option value="">' + esc(T('car_none')) + '</option>';
      md.disabled = !t.value;
      carOpt(CARS);
    } else if (k === 'md') carOpt(CARS);
  });

  // ---------- controls ----------
  $chips.addEventListener('click', function (e) {
    var c = e.target.closest('.evm-chip');
    if (!c) return;
    var f = c.getAttribute('data-f');
    if (f === 'cheap') { state.cheap = !state.cheap; paintChips(); renderList(); return; }
    if (f === 'ok') state.ok = !state.ok; else state.f = f;
    paintChips();
    refresh();
  });
  $count.addEventListener('click', function (e) {
    if (!e.target.closest('[data-all]')) return;
    state.bounds = null; me = null;
    if (map) { map.getSource('me').setData({ type: 'FeatureCollection', features: [] }); map.fitBounds(SRB, { padding: 16 }); }
    renderList();
  });
  var qt, qf;
  $q.addEventListener('input', function () {
    clearTimeout(qt); clearTimeout(qf);
    qt = setTimeout(function () {
      state.q = $q.value.trim(); state.bounds = null;
      refresh();
      if (state.q) qf = setTimeout(function () { fitTo(visible()); }, 500);
    }, 140);
  });
  $q.addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); $q.blur(); fitTo(visible()); } });
  $list.addEventListener('click', function (e) {
    if (e.target.closest('[data-more]')) { state.lim += 30; renderList(); return; }
    var b = e.target.closest('.evm-st');
    if (b) { var s = BYID[b.getAttribute('data-id')]; if (s) openCard(s, true); }
  });
  $fs.addEventListener('click', function () { setFull(!root.classList.contains('evm-full')); });
  $near.addEventListener('click', function () { nearGo('button'); });
  d.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    if (carOpen) closeCar(); else if (sel || nearOpen) closeCard(); else if (root.classList.contains('evm-full')) setFull(false);
  });
  $me.addEventListener('click', function () {
    if (!navigator.geolocation) { $count.textContent = T('no_location'); return; }
    $me.disabled = true;
    navigator.geolocation.getCurrentPosition(function (pos) {
      me = { lat: pos.coords.latitude, lon: pos.coords.longitude };
      state.bounds = null; state.lim = 20; $me.disabled = false;
      if (map) {
        map.getSource('me').setData({ type: 'FeatureCollection', features: [{ type: 'Feature', geometry: { type: 'Point', coordinates: [me.lon, me.lat] }, properties: {} }] });
        map.flyTo({ center: [me.lon, me.lat], zoom: 11 });
      }
      renderList();
      if (mobile()) $count.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }, function () { $me.disabled = false; $count.textContent = T('no_location'); }, { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 });
  });
  var rt;
  window.addEventListener('resize', function () {
    clearTimeout(rt);
    rt = setTimeout(function () { if (!mobile() && root.classList.contains('evm-full')) setFull(false); lock(root.classList.contains('evm-full') || ((!!sel || nearOpen) && mobile())); renderList(); }, 150);
  });
  // the site's language switch changes <html lang>: redraw everything in the new language
  new MutationObserver(function () {
    renderStatic(); renderList();
    if (carOpen) { var b = carBack; openCar(); carBack = b; } else if (sel) openCard(sel, false, cardNear); else if (nearOpen && NEAR) nearPanel(NEAR, false);
  }).observe(d.documentElement, { attributes: true, attributeFilter: ['lang'] });

  // ---------- start ----------
  renderStatic();
  $count.textContent = T('loading');
  loadMaplibre();
  function getJson(u) { return fetch(u).then(function (r) { if (!r.ok) throw new Error(u); return r.json(); }); }
  getJson(FEED + '/app/v1/manifest.json').then(function (man) {
    var f = man.files.map;
    CARS_URL = f.auta || '';
    if (man.files.data) getJson(FEED + man.files.data).then(function (dj) {
      var c = dj.calculator || {};
      if (c.fuel && c.fuel.benzin && c.defaults && c.defaults.l100_benzin) { FUEL = { b: c.fuel.benzin, l: c.defaults.l100_benzin }; if (sel && !carOpen) openCard(sel, false, cardNear); }
    }, function () { /* without it the per-km block compares with home only */ });
    return Promise.all([getJson(FEED + f.punjaci), f.mreze ? getJson(FEED + f.mreze).catch(function () { return { upd: {}, add: [] }; }) : { upd: {}, add: [] },
      getJson(FEED + f.cene), f.dopune ? getJson(FEED + f.dopune).catch(function () { return { upd: {} }; }) : { upd: {} },
      f.tx ? getJson(FEED + f.tx).catch(function () { return null; }) : null]);
  }).then(function (r) {
    var a = r[0], m = r[1], b = r[2], x = r[3];
    if (r[4] && r[4].en) TX = r[4];
    ST = a.stations;
    CHECKED = a.checked || '';
    var join = function (layer, list) {
      list.forEach(function (s) {
        var u = layer.upd && layer.upd[s.id];
        if (!u) return;
        Object.keys(u).forEach(function (k) { if (k !== 'src') s[k] = u[k]; });
        s.src = (s.src || []).concat(u.src || []);
      });
    };
    // the networks' own lists first (their names and connectors, and the stations the open data lacks), then the checked facts
    join(m, ST);
    ST = ST.concat(m.add || []);
    join(x, ST);
    ST.forEach(function (s) { s.c = s.c || []; s.src = s.src || []; BYID[s.id] = s; });
    // confirmed and network stations first, the ones that are only in the open databases after them; then by name
    ST.sort(function (p, q) { return ((ver(p) === 'nep') - (ver(q) === 'nep')) || (!p.n - !q.n) || fold(p.n).localeCompare(fold(q.n)) || (p.id < q.id ? -1 : 1); });
    NETS = b.nets || {};
    dataReady = true;
    var qs = new URLSearchParams(location.search), q0 = qs.get('q');
    if (q0) { $q.value = q0; state.q = q0; }
    var id = decodeURIComponent(location.hash.slice(1));
    renderStatic();
    renderList();
    if (id && BYID[id]) openCard(BYID[id], false);
    if (nearOpen && NEAR && NEAR.pt) nearPanel(NEAR, true);
    // ?najblizi=1 (=brzi: fast only) opens „Najbliži punjač“: at once when the browser already allows the location, otherwise
    // the panel asks first — the page never asks for the location by itself
    var nz = qs.get('najblizi');
    if (nz && !sel && !NEAR) {
      if (nz === 'brzi') setF('fast');
      var ask = function () { NEAR = { pt: null, withNep: false, source: 'link', ask: true }; nearPanel(NEAR); };
      if (navigator.permissions && navigator.permissions.query) navigator.permissions.query({ name: 'geolocation' }).then(function (p) { if (p.state === 'granted') nearGo('link'); else ask(); }, ask);
      else ask();
    }
    // „Najbliži punjač“ for a given point, as the panel would list it (only with ?qa=1: the apps and blokvolt.rs are compared with it)
    if (/[?&]qa=1\b/.test(location.search)) {
      window.evmNearQa = function (lat, lon, nep) { return nearestList({ lat: lat, lon: lon }, !!nep).rows.map(function (x) { return { id: x.s.id, t: title(x.s), m: Math.round(x.d * 1000) }; }); };
      // the cost engine for one station (blokvolt.rs has the same: window.bvCostQa)
      window.evmCostQa = function (id) { var s0 = BYID[id], co = s0 && costOf(s0); return co ? { kw: co.main.c.kw, kwh: co.main.c.kwh, km: co.main.c.km } : null; };
    }
    if (mlReady === 'err') noMap(); else startMap();
  }).catch(function () { dataErr = true; $count.textContent = T('load_err'); if (nearOpen && NEAR && NEAR.pt) nearPanel(NEAR); });
})();
