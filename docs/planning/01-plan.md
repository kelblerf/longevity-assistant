# Longevity Assistant: ujasneny cil a plan

Datum: 2026-06-03

## 1. Co vlastne chceme vytvorit

Cil neni "jen chat", ale osobni AI asistenta, ktery:

- zna vas profil, priority, zvyky, zdravotni cile a kontext
- umi cerpat z vasich vlastnich zdroju dat
- umi si dohledat aktualni informace na internetu a dodat je se zdroji
- umi doporucovat dalsi kroky v oblasti zdraveho zivotniho stylu a longevity
- umi navazat na vase digitalni nastroje a casem i na automatizaci domacnosti, technologiich a medialni workflow

Pracovni definice produktu:

> "Osobni AI operacni system pro zdravi, rozhodovani a automatizaci, jehoz hlavni vstup je chat a jehoz sila je v personalizaci nad vasimi daty."

## 2. Doporucene vymezeni cile

### Hlavni produktovy cil

Vytvorit chat-first asistenta, ktery bude umet:

- odpovidat na otazky nad vasimi osobnimi daty
- davat personalizovana doporuceni ke zdravi, navykum a longevity
- vysvetlit, z ceho doporuceni vychazi
- odlisit fakta z vasich dat, internetovy vyzkum a vlastni odhad
- postupne spoustet akce v dalsich systemech

### Co ma byt prvni verze

Prvni verze by mela umet hlavne:

- profil uzivatele a dlouhodobou pamet
- cteni z Notion
- cteni z OneNote
- praci s nahranymi soubory
- internetovy vyzkum se zdroji
- personalizovany chat pro zdravi, navyky a rozhodovani
- zapis poznamek, ukolu a follow-upu

### Co do prvni verze nepatri

Tyto veci doporucuji neposouvat do MVP, ale az do navazujicich fazi:

- prime rizeni Tecomat Foxtrot
- prime rizeni Home Assistantu nad vice domenami
- automatizace DaVinci Resolve
- automaticke zpracovani videi z DJI Avatar 2
- viceagentni orchestrace pro vsechny use-cases najednou

Duvod:

- jinak bude projekt prilis siroky
- bude tezke overit hodnotu pro vas osobne
- integrace vas zpomali driv, nez overite, ze samotny asistent je uzitecny

## 3. Doporuceni: jedna app, nebo vice app?

Doporuceni:

Nevytvaret nekolik samostatnych aplikaci pro uzivatele. Vytvorit jednu hlavni aplikaci a pod ni oddelene backend moduly.

### Doporucena struktura

Jedna uzivatelska aplikace:

- webovy chat
- osobni dashboard
- profil a cile
- historie konverzaci
- zdroje, soubory a vysvetleni doporuceni

Vice internich sluzeb/modulu:

- memory/profile service
- knowledge ingestion service
- search/research service
- recommendation engine
- integration service
- automation/media service

To vam da:

- jednoduchy vstup pro uzivatele
- cistou architekturu
- moznost pridavat schopnosti bez prestavby cele aplikace

## 4. Doporucena architektura

## Vrstva A: Chat a UX

Frontend:

- web app
- pozdeji mobilni wrapper nebo PWA

Hlavni prvky:

- chat
- profil
- cile a zvyky
- timeline doporuceni
- zdroje a citace
- akce "vytvorit ukol", "ulozit do Notion", "spustit rutinu", "pridat do deniku"

## Vrstva B: Orchestrace asistenta

Serverova logika:

- rizeni konverzace
- rozhodovani, kdy sahnout do pameti
- rozhodovani, kdy pouzit web search
- rozhodovani, kdy pouzit integraci
- oddeleni osobnich dat od obecneho vyzkumu

Doporuceny princip:

- model nesmi tvarit internetove domnenky jako osobni fakta
- odpoved ma umet oznacit:
  - "z vaseho profilu"
  - "z Notion/OneNote"
  - "z webu"
  - "muj navrh/odhad"

## Vrstva C: Pamet a znalostni vrstva

Tato vrstva bude klicova.

Mela by obsahovat:

- osobni profil
- zdravotni cile
- preference
- omezeni a kontraindikace
- navyky
- timeline udalosti
- extrahovane znalosti z Notion a OneNote
- metadata o duveryhodnosti zdroje

Prakticky rozdelit na:

- structured memory
  - profil
  - cile
  - biometrie
  - navyky
  - rutiny
  - zarizeni
- unstructured memory
  - poznamky
  - deniky
  - dokumenty
  - web clanky
  - transkripty

## Vrstva D: Integrace

### Notion

Pouzitelne jako hlavni znalostni vrstva pro strukturovana data a projektove vedeni.

Overeno:

- Notion ma oficialni API pro pages, data sources, search a content queries.
- Aktualni docs take upozornuji na zmeny v API verzi `2026-03-11`.

### OneNote

Pouzitelne jako doplnkovy zdroj poznamek a osobnich zapisniku.

Overeno:

- OneNote je dostupny pres Microsoft Graph API.
- OneNote API uz nepodporuje app-only authentication; podle Microsoft Learn je potreba delegated auth.

Dusledek pro navrh:

- OneNote bude vhodnejsi pro vas osobni prihlaseny ucet nez pro "headless firemni synchronizator bez uzivatele"

### Home Assistant

Vhodny uz od druhe faze.

Overeno:

- Home Assistant ma oficialni REST API i WebSocket API.
- Ma i Conversation API, ktere umi prijmout textovy prikaz.

Dusledek pro navrh:

- muzeme zacit read-only rezimem
- pak pridat doporuceni
- a az potom rizene akce

### Tecomat Foxtrot CP

Vypada jako realne integrovatelny, ale az ve druhe nebo treti fazi.

Overeno:

- oficialni materialy Teco uvadeji Ethernet/IP komunikaci, Modbus RTU/TCP, BACnet, web server a moznost fungovat jako komunikacni hub
- Teco dokumentace a wiki zminuji i MQTT a komunikaci s dalsimi systemy

Dusledek pro navrh:

- nejrozumnejsi je neintegrovat Foxtrot primo do AI logiky
- lepsi je postavit bridge vrstvu pres Modbus, MQTT nebo mezisluzbu

### DaVinci Resolve

Pouzitelne az po overeni hlavni hodnoty asistenta.

Overeno:

- Resolve ma scripting API pro Python a Lua
- dokumentace je soucasti developer baliku a wiki DVResolve ji zrcadli

Dusledek pro navrh:

- nechat jako specializovany automation modul
- vhodne na davkove ukoly, importy, timeline akce, marker workflow a exportni pipeline

### DJI Avatar 2

Nedoporucuji resit jako "prime API-first" integraci v prvni vlne.

Doporuceni:

- brat to nejdriv jako media workflow
- nacitani souboru z disku nebo karty
- analyza metadat
- pripadne automatizovane pretrideni, transkripce, vyber zaberu a predpriprava pro Resolve

## 5. Doporuceny produktovy scope

## Faze 1: Personal Health Knowledge Assistant

Toto doporucuji jako skutecne MVP.

Umi:

- chat nad vasim profilem
- chat nad Notion a OneNote
- web research se zdroji
- osobni doporuceni pro zdravi a longevity
- zapis zaveru a follow-upu

Prinos:

- nejrychleji zjistite, zda je to pro vas denne uzitecne
- vytvorite kvalitni memory model
- nevaznete na tezkych integracich

## Faze 2: Action Assistant

Pridat:

- Home Assistant read/write scenare
- ulozeni akci do Notion
- jednoduche operace nad soubory
- pripominky, rutiny, check-iny

## Faze 3: Automation Assistant

Pridat:

- Foxtrot bridge
- pokrocile workflow nad lokalnimi soubory
- Davinci Resolve automatizace
- DJI video ingest pipeline

## 6. Konkretni navrh MVP

Nazev pracovniho MVP:

`Longevity Copilot`

### MVP use-cases

1. "Co je pro me dnes nejdulezitejsi udelat pro zdravi?"
2. "Shrn mi, co o mne vis ohledne spanku, stresu a energie."
3. "Projdi moje poznamky a najdi opakujici se problemy."
4. "Dohledej aktualni informace k tematu X a porovnej je s mym kontextem."
5. "Vytvor mi tydenni plan mikro-kroku."
6. "Uloz zaver do Notion."
7. "Pripomen mi vecer check-in."

### MVP nevyrabi

- lekarskou diagnostiku
- autonomni zasahy do technologie bez potvrzeni
- automaticke tvrzeni "tohle je pravda", kdyz jde jen o odhad

## 7. Doporuceny technicky smer

### Frontend

- web app v React/Next.js

### Backend

- Python nebo TypeScript backend
- pro AI orchestrace je rozumnejsi Python

### Datova vrstva

- Postgres pro structured data
- vector index pro semanticke vyhledavani nad dokumenty
- object/file storage pro prilohy a media

### Integrace

- Notion API
- Microsoft Graph pro OneNote
- Home Assistant REST/WebSocket
- Foxtrot bridge pres Modbus/MQTT
- Resolve scripting connector

### Bezpecnost

- oddelit osobni zdravotni data od experimentalnich agentnich akci
- audit log odpovedi a akci
- potvrzeni pred aktivnimi zasahy

## 8. Nejvetsi rizika

1. Prilis siroky scope od zacatku
2. Nekvalitni osobni pamet, ktera bude michat fakta a domnenky
3. Komplikovane prihlaseni do vice systemu
4. Chybejici pravidla pro duveryhodnost zdroju
5. Snaha resit chat, automatizaci domu a video produkci soucasne

## 9. Doporuceny plan realizace

## Faze 0: Ujasneni a navrh

Termin:

- start 2026-06-03
- delka 3 az 7 dni

Vystupy:

- potvrzena produktova vize
- seznam prioritnich use-cases
- seznam datovych zdroju
- rozhodnuti co je MVP
- hruby datovy model osobni pameti

## Faze 1: Zakladni chat + osobni pamet

Delka:

- 2 az 3 tydny

Vystupy:

- funkcni chat
- user profile
- manualni zapis cilu a pravidel
- historie konverzaci
- prvni personalizace odpovedi

## Faze 2: Notion + OneNote ingest

Delka:

- 2 az 4 tydny

Vystupy:

- nacitani dokumentu
- indexace
- hledani v osobnich datech
- citace a odkazy na zdroje

## Faze 3: Web research a recommendation engine

Delka:

- 2 az 3 tydny

Vystupy:

- odpovedi se zdroji
- oddeleni osobniho kontextu od obecnych informaci
- sablony doporuceni pro longevity a navyky

## Faze 4: Home Assistant integrace

Delka:

- 1 az 3 tydny

Vystupy:

- read-only telemetrie
- doporuceni z domacich dat
- vybrane akce s potvrzenim

## Faze 5: Foxtrot, Resolve, DJI workflow

Delka:

- podle priority jednotlive

Vystupy:

- bridge na Foxtrot
- media ingestion
- automatizace workflow v Resolve

## 10. Co doporucuji udelat hned ted

Nejlepsi dalsi krok neni zacit kodovat vsechno, ale potvrdit tento uzsi cil:

> "Prvni verze bude chat-first Longevity Copilot, ktery zna muj profil, cte Notion a OneNote, umi dohledat aktualni informace na webu a dava personalizovana doporuceni se zdroji."

Pokud tohle potvrdi smer, dalsi konkretni krok je:

1. sepsat prioritnich 10 use-cases
2. vybrat MVP datasource
3. navrhnout datovy model osobni pameti
4. az potom zalozit technicky backlog

## 11. Moje doporuceni jednou vetou

Nevytvarejte hned "vseumelou AI pro zdravi, dum i video", ale nejdriv postavte velmi silneho osobniho chat asistenta pro longevity a osobni znalosti; teprve po overeni uzitku na nej napojte automatizace a specializovane moduly.

## 12. Odkazy na overene zdroje

- Notion API overview: https://developers.notion.com/guides/get-started
- Notion capabilities: https://developers.notion.com/reference/capabilities
- Notion search limitations: https://developers.notion.com/reference/search-optimizations-and-limitations
- Notion content/page APIs: https://developers.notion.com/guides/data-apis
- Microsoft Graph OneNote overview: https://learn.microsoft.com/graph/integrate-with-onenote
- Microsoft Graph OneNote REST overview: https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview?view=graph-rest-1.0
- Home Assistant REST API: https://developers.home-assistant.io/docs/api/rest
- Home Assistant WebSocket API: https://developers.home-assistant.io/docs/api/websocket
- Home Assistant Conversation API: https://developers.home-assistant.io/docs/intent_conversation_api/
- DaVinci Resolve scripting API mirror of bundled docs: https://wiki.dvresolve.com/developer-docs/scripting-api
- Teco Foxtrot communication overview: https://www.tecomat.cz/index.php/en/products/foxtrot-system-overview/communication-interfaces
- Teco Foxtrot catalog overview: https://www.tecomat.com/uploads/files/DOCS/eng/PRINTS/Foxtrot-ENG.pdf
