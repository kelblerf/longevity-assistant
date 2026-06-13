# Longevity Assistant: prioritizovane use-cases a MVP backlog

Datum: 2026-06-03

Navazuje na dokument:

- [01-plan.md](../planning/01-plan.md)

## 1. Princip prioritizace

Use-case ma jit do MVP, pokud splnuje vetsinu z techto podminek:

- prinasi hodnotu i bez dalsich tezkych integraci
- pouzili byste ho aspon nekolikrat tydne
- pomaha dokazat, ze asistent vas opravdu zna
- jde postavit bez velkeho provozniho rizika
- nevytvari falesny dojem lekarske autority

## 2. Top 10 use-cases

### 1. Dnesni zdravotni priorita

Otazka:

`Co je pro me dnes nejdulezitejsi udelat pro zdravi a proc?`

Co ma asistent udelat:

- spojit vas profil, cile, historii a posledni poznamky
- dat 1 az 3 konkretni doporucene kroky
- vysvetlit, z jakych dat a zdroju vysel

Hodnota:

- maximalne prakticke pro kazdodenni pouziti
- okamzite overuje personalizaci

Priorita:

- `MVP`

### 2. Souhrn toho, co o vas vi

Otazka:

`Shrn mi, co o mne vis v oblasti spanku, stresu, energie a longevity.`

Co ma asistent udelat:

- shrnout dlouhodobe informace o vas
- ukazat nejistoty a chybejici data
- oddelit overena fakta od pracovnich odhadu

Hodnota:

- pomaha budovat duveru
- ukazuje kvalitu pameti a ingestu

Priorita:

- `MVP`

### 3. Vyhledani odpovedi v Notion a OneNote

Otazka:

`Najdi vse, co uz mam k tematu vitamin D / spanek / zatez / suplementace.`

Co ma asistent udelat:

- prohledat Notion a OneNote
- vytahnout relevantni pasaze
- udelat souhrn s odkazy na puvodni zdroje

Hodnota:

- overuje, ze asistent je opravdu napojeny na vase znalosti
- snizuje informacni chaos

Priorita:

- `MVP`

### 4. Osobni web research se zdroji

Otazka:

`Dohledej aktualni pohled na tema X a porovnej to s mym kontextem.`

Co ma asistent udelat:

- dohledat aktualni zdroje
- rozlisit obecna fakta a osobni dopady
- priznat nejistotu a ukazat citace

Hodnota:

- velmi silny rozdil oproti beznemu chatbotu
- kombinuje research a personalizaci

Priorita:

- `MVP`

### 5. Tydenni mikro-plan

Otazka:

`Navrhni mi tydenni plan malych kroku pro energii, spanek a regeneraci.`

Co ma asistent udelat:

- navrhnout realisticke kroky
- respektovat vase preference, cas a zvyky
- navazat na predchozi doporuceni

Hodnota:

- prevadi znalosti do akce
- dela z asistenta kouce, ne jen vyhledavac

Priorita:

- `MVP`

### 6. Ukladani zaveru a follow-upu

Otazka:

`Uloz shrnuti do Notion a vytvor mi follow-up na zitra.`

Co ma asistent udelat:

- ulozit zaver z chatu
- vytvorit ukol nebo poznamku
- oznacit kontext a tema

Hodnota:

- uzavira smycku mezi doporucenim a realnou praci
- zamezuje ztrate dulezitych vystupu

Priorita:

- `MVP`

### 7. Vecerni check-in

Otazka:

`Poloz mi vecer 3 kratke otazky a vyhodnot trend.`

Co ma asistent udelat:

- ziskat odpovedi
- ulozit je
- srovnat je s predchozimi dny

Hodnota:

- zaklada pravidelna osobni data
- zlepsuje kvalitu budouci personalizace

Priorita:

- `Phase 2`

### 8. Home Assistant kontext a doporuceni

Otazka:

`Jak moje domaci prostredi ovlivnuje spanek nebo regeneraci?`

Co ma asistent udelat:

- cist vybrane senzory a stavy
- davat doporuceni
- pripadne navrhnout akce

Hodnota:

- vysoky potencial, ale az po zakladnim asistentovi

Priorita:

- `Phase 2`

### 9. Foxtrot a technologicke workflow

Otazka:

`Zjisti stav technologie a navrhni dalsi krok.`

Co ma asistent udelat:

- cist bridge vrstvu nad Foxtrotem
- dat interpretaci a navrh
- aktivni zasahy delat jen s potvrzenim

Hodnota:

- silne, ale mimo hlavni MVP

Priorita:

- `Later`

### 10. Video workflow z DJI a DaVinci Resolve

Otazka:

`Vezmi nove zabery, roztrid je a priprav draft workflow pro Resolve.`

Co ma asistent udelat:

- ingest souboru
- analyza metadat
- predtrideni a priprava dalsiho kroku

Hodnota:

- zajimava specializace
- neni to prvni dokaz hodnoty health asistenta

Priorita:

- `Later`

## 3. Jasna hranice MVP

Do MVP patri:

- personalizovany chat
- osobni profil a pamet
- Notion ingest
- OneNote ingest
- web research se zdroji
- souhrny a doporuceni
- zapis zaveru do systemu

Do MVP nepatri:

- autonomni akce v domacnosti
- prime rizeni Foxtrotu
- pokrocila automatizace nad soubory
- zpracovani videa
- agentni orchestrator pro vse naraz

## 4. MVP backlog podle poradi stavby

### Blok A: Zaklad duvery

1. Chat session a historie
2. User profile schema
3. Memory rules
4. Zdrojove stitky v odpovedich

Smysl:

- bez teto vrstvy nebude asistent pusobit osobne ani duveryhodne

### Blok B: Osobni znalosti

5. Notion connector
6. OneNote connector
7. Indexace dokumentu
8. Vyhledani a citace

Smysl:

- z chatbota se stane opravdu "vas" asistent

### Blok C: Doporuceni

9. Daily recommendation prompt chain
10. Weekly plan generator
11. Reflection and gap detection

Smysl:

- z pouheho hledani vznikne pomocnik pro rozhodovani

### Blok D: Akce

12. Save-to-Notion action
13. Create follow-up action
14. Basic reminder/check-in flow

Smysl:

- uzavira cyklus poznani -> rozhodnuti -> akce

## 5. Doporucene MVP demo

Pokud budete chtit rychle overit smer, idealni demo prvni verze by melo umet tento tok:

1. Otevru chat
2. Zeptam se: `Co je pro me dnes nejdulezitejsi?`
3. Asistent odpovi na zaklade profilu, Notion a OneNote
4. Uvede zdroje a nejistoty
5. Navrhne 3 kroky
6. Ja reknu: `Uloz mi to do Notion a vytvor zitrejsi follow-up`

Kdyz toto funguje dobre, projekt je na spravne koleji.

## 6. Doporuceni pro dalsi rozhodnuti

Pred samotnym kodovanim bych doporucil potvrdit jeste tyto 4 body:

1. Jakych 5 temat zdravi ma asistent resit jako prvni
2. Ktere Notion databaze a OneNote sekce budou MVP zdroj pravdy
3. Jake typy doporuceni chcete dostavat denne a jake tydne
4. Ktere akce muze asistent delat sam a ktere jen po potvrzeni

## 7. Moje doporuceni

Pokud chcete nejvetsi sanci na uspech, stavel bych MVP presne v tomto poradi:

1. `Dnesni zdravotni priorita`
2. `Souhrn toho, co o vas vi`
3. `Vyhledani odpovedi v Notion a OneNote`
4. `Osobni web research se zdroji`
5. `Tydenni mikro-plan`
6. `Ukladani zaveru a follow-upu`

Tohle poradi dava nejrychlejsi cestu k realne uzitecnemu asistentovi.
