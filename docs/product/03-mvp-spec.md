# Longevity Assistant: MVP spec

Datum: 2026-06-03

Navazuje na:

- [01-plan.md](../planning/01-plan.md)
- [02-use-cases.md](./02-use-cases.md)

## 1. Cilem MVP neni vse, ale toto

MVP ma byt prvni skutecne pouzitelna verze osobniho asistenta pro zdravi a longevity, ktery:

- vas zna
- umi cist vase osobni podklady
- umi dohledat aktualni informace
- umi odpovedet personalizovane
- umi ulozit vysledek zpet do vaseho systemu

Pracovni definice MVP:

> Chat-first Longevity Copilot, ktery spojuje vas osobni profil, knowledge workspace a internetovy research do jedne personalizovane odpovedi se zdroji.

## 2. Co musi MVP umet

### Povinny vysledek MVP

Asistent musi umet:

- odpovedet na otazku typu `Co je pro me dnes nejdulezitejsi?`
- vytahnout relevantni kontext z osobni pameti
- najit relevantni obsah ve knowledge workspace a osobnich poznamkach
- kdyz je treba, dohledat aktualni informace na webu
- oznacit, co pochazi:
  - z vaseho profilu
  - z knowledge workspace
  - z osobnich poznamek
  - z internetu
  - z interpretace modelu
- navrhnout 1 az 3 dalsi konkretni kroky
- ulozit shrnuti nebo follow-up do zapisove vrstvy

### Co MVP umet nemusi

- ovladat dum
- ridit Foxtrot
- zpracovavat video
- delat slozitou agentni orchestraci
- fungovat jako lekarsky diagnosticky system

## 3. Doporucene prvni oblasti zdravi

Pro MVP doporucuji nezacit vsemi zdravotnimi oblastmi, ale jen peti.

### MVP health domains

1. `Spanek`
2. `Energie a unava`
3. `Stres a regenerace`
4. `Biomarkery a laboratorni hodnoty`
5. `Navyky a denni rutina`

Duvod:

- jsou navzajem silne propojene
- maji vysokou denni uzitnost
- jdou dobre spojit s osobnimi poznamkami, self-trackingem a longevity doporucenimi
- nevyzaduji hned specializovane medicinske workflow

## 4. Doporucene MVP source of truth

Nize uvadim zdroje, ktere uz byly v predchozi praci overene nebo identifikovane jako velmi pravdepodobne relevantni.

## Vrstva A: Structured personal memory

Tato vrstva ma obsahovat:

- profil uzivatele
- cile
- omezeni
- preference
- navyky
- zdravotni priority
- pravidla, ktera ma asistent respektovat

V MVP doporucuji drzet tuto vrstvu mimo knowledge workspace jako vlastni aplikacni data.

Duvod:

- budete chtit presne ridit, co je pravda o vas
- model potrebuje stabilni schema
- neni dobre, kdyz se osobni profil rozpada v nestrukturovanych poznamkach

### Minimalni profilova schema

- jmeno
- vek nebo vekova skupina
- hlavni cile
- aktualni problemy
- omezeni a kontraindikace
- preference pristupu
- obvykly denni rytmus
- klicove navyky
- seznam duveryhodnych zdroju

## Vrstva B: Knowledge workspace

Z drive overenych podkladu doporucuji pro MVP jako hlavni knowledge zdroje:

### 1. Biomarker knowledge base

Role v MVP:

- hlavni referencni vrstva pro biomarkery
- osobni a semistrukturovana znalostni baza pro laboratorni interpretace

Pouziti:

- odpovedi na dotazy k biomarkerum
- porovnavani s dalsimi materialy
- podklad pro personalizovana doporuceni

### 2. Medical evidence and research hub

Role v MVP:

- research hub nad medicinskymi zdroji
- prehled o tom, jake domeny jsou pokryte a ktere chybi

Pouziti:

- podklad pro research memory
- orientace v tom, co uz bylo zpracovane
- vysvetleni, z jakych typu zdroju asistent cipa

### 3. Project hub and operational context

Role v MVP:

- projektovy a organizacni rozcestnik
- ne primarni health knowledge base, ale ridici stranka

Pouziti:

- roadmapa
- tracking dalsiho rozvoje asistenta
- odkazovani na navazne dokumenty

### 4. UBZ knowledge layer

Doporucuji vzit v uvahu i behavioralni a metodickou knowledge vetev, protoze je relevantni jako obsahova a metodicka vrstva kolem zdravi, regenerace, osobni promeny a navyku.

Klicove drive identifikovane materialy:

- behavioralni a hodnotova knowledge vrstva
- tematicke materialy pro rytmus, dech a regeneraci
- osobni reflektivni a metodicke podklady

Role v MVP:

- obsahova vrstva pro filozofii, principy a behavioralni doporuceni
- doplnkova vrstva k biomarkerum a medicinskemu researchi
- zdroj pro jazyk, hodnoty a pristup, ktery je vam blizky
- konkretni tematicka vetev uvnitr vaseho osobniho knowledge systemu, ne oddeleny samostatny system
- nosna vrstva i pro `dech`, praci s autonomnim nervovym systemem, regulaci stresu a souvislost mezi rytmem, pusty, dechem a regeneraci

Pouziti:

- personalizovana doporuceni v oblasti navyku, regenerace a vnitrni zmeny
- personalizovana doporuceni v oblasti dechu, zklidneni, stresove regulace a vedome prace s rytmem tela
- kontext pro vysvetleni proc za doporucenim
- doplnkova znalostni vrstva vedle ciste laboratorni a evidence-based vrstvy

Pravidlo:

- UBZ zdroje pouzivat jako `metodicko-reflexivni vrstvu`, ne jako jedinou autoritu pro medicinska tvrzeni
- pokud asistent pracuje s biomarkery nebo zdravotnimi tvrzenimi, musi UBZ kombinovat s biomarkerovou znalostni vrstvou, evidence/research vrstvou a aktualnim web researchi

### 5. Doporucena nova zapisova databaze pro MVP

Protoze aktualni zdroje samy o sobe nestaci pro osobni pamet, doporucuji vytvorit jeste tyto dve MVP databaze:

#### `Daily Check-ins`

Minimalni pole:

- datum
- energie 1-10
- spanek 1-10
- stres 1-10
- regenerace 1-10
- poznamka
- doporuceni dne

#### `Health Notes / Signals`

Minimalni pole:

- datum
- tema
- symptom nebo pozorovani
- kontext
- zdroj
- priorita
- follow-up

## Vrstva C: Personal notes source of truth

Osobni poznamky v MVP doporucuji pouzit jako:

- osobni zapisnik
- dlouhodobe poznamky
- reflexe
- nezarazene napady a postrehy

Ne jako primarni zdroj strukturovane pravdy.

### Doporucene sekce pro MVP

1. `Zdravi / Longevity`
2. `Denni nebo tydenni reflexe`
3. `Poznamky k symptomum, energii a spanku`
4. `Research / clanky / postrehy`

Pokud tyto sekce zatim nemate, doporucuji je vytvorit presne v teto strukture.

## 5. Jak ma MVP rozhodovat o zdrojich

Kazda odpoved by mela vznikat timto poradi:

1. nejdriv profil a structured memory
2. pak knowledge workspace
3. pak osobni poznamky
4. pak internet, jen kdyz je potreba aktualni nebo chybejici informace
5. nakonec interpretace a doporuceni

### Pravidla odpovedi

Odpoved musi umet rict:

- `Tohle vim o vas`
- `Tohle jsem nasel ve vasich datech`
- `Tohle je aktualni poznatek z webu`
- `Tohle je muj navrh`

To je klicove pro duveru.

## 6. Co smi asistent delat automaticky

### Bez potvrzeni

- cist data
- hledat ve knowledge workspace a osobnich poznamkach
- delat web research
- navrhovat doporuceni
- pripravit draft poznamky nebo shrnuti

### Jen po potvrzeni

- zapis do zapisove vrstvy
- vytvoreni follow-upu
- vytvoreni ukolu
- zmena osobnich pravidel nebo profilu

### Do MVP nepatri

- ovladani Home Assistantu
- ovladani Foxtrotu
- spousteni skriptu v Resolve
- manipulace s lokalnimi video soubory bez potvrzeni

## 7. Doporuceny MVP user flow

Idealni prvni flow:

1. Uzivatel se zepta:
   `Co je pro me dnes nejdulezitejsi z pohledu energie, spanku a regenerace?`
2. Asistent vytahne:
   - profil
   - posledni check-iny
   - relevantni knowledge a osobni poznamky
3. Pokud je potreba, doda aktualni research
4. Vrati:
   - shrnuti situace
   - 1 az 3 konkretni doporucene kroky
   - zdroje
   - upozorneni na nejistoty
5. Uzivatel rekne:
   `Uloz mi to do systemu a vytvor zitrejsi follow-up.`

Pokud tento flow funguje dobre, MVP dava smysl.

## 8. Doporuceny MVP backlog

### Epic 1: Personal Memory

- profil uzivatele
- health goals
- preference a omezeni
- memory rules

### Epic 2: Knowledge Connectors

- knowledge workspace ingest
- personal notes ingest
- document chunking
- metadata a citace

### Epic 3: Reasoning and Response Quality

- source attribution
- confidence / uncertainty rules
- recommendation templates
- daily priority output

### Epic 4: Write-back

- save summary
- create follow-up
- create action item

## 9. Co je potreba overit pred implementaci write-backu

Aktualne je potreba potvrdit:

1. ktere konkretni databaze nebo zapisove cile budou MVP source of truth
2. zda uz existuje databaze vhodna pro `Daily Check-ins`
3. zda uz existuje databaze vhodna pro `Health Notes / Signals`
4. ktere dalsi longevity dokumenty jsou opravdu aktivne pouzivane

Tohle neni blocker pro navrh, ale je to dalsi krok pred implementaci.

## 10. Doporuceni jednou vetou

MVP ma byt osobni longevity chat asistent nad profilem + knowledge workspace + osobnimi poznamkami + web research, ktery umi navrhnout dalsi kroky a ulozit vysledek zpet do vaseho systemu; vsechno ostatni je az dalsi faze.
