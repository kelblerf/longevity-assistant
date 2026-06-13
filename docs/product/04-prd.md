# Longevity Assistant PRD

Datum: 2026-06-03

Navazuje na:

- [01-plan.md](../planning/01-plan.md)
- [02-use-cases.md](./02-use-cases.md)
- [03-mvp-spec.md](./03-mvp-spec.md)
- [05-technical-backlog.md](../technical/05-technical-backlog.md)

## 1. Executive summary

Longevity Assistant je osobni AI asistent zamereny na zdravy zivotni styl, longevity a personalizovane rozhodovani. Jeho hlavni vstup je chat. Jeho hlavni hodnota neni v obecnem povidani, ale v tom, ze:

- zna vas osobni kontext
- umi cist vase vlastni znalosti
- umi dohledat aktualni informace
- umi navrhnout dalsi konkretni krok
- umi vysledek vratit zpet do vaseho systemu

Prvni verze nema byt AI na vsechno, ale `chat-first Longevity Copilot`.

## 2. Problem statement

Mate rozptylene informace o zdravi, biomarkerech, navycich, poznamkach a researchi v ruznych systemech. Bez asistenta je tezke:

- rychle spojit osobni kontext s aktualnimi informacemi
- delat konzistentni rozhodnuti
- drzet dlouhodobou pamet o tom, co o sobe vite
- pretavit poznani do kazdodenni akce

Existujici chatboty umi odpovidat obecne, ale neznaji vas do hloubky ani neumi spolehlive pracovat s vasimi zdroji jako se zdrojem pravdy.

## 3. Product vision

Vytvorit osobni AI operacni system pro zdravi, longevity a rozhodovani, ktery casem propoji:

- osobni profil a pamet
- knowledge workspace
- osobni poznamky
- internetovy research
- pozdeji i Home Assistant, Foxtrot, soubory a media workflow

## 4. Product goal

Hlavni cil prvni verze:

> Umoznit vam dostat personalizovanou, zdrojovane podlozenou odpoved na otazky kolem zdravi a longevity, zalozenou na vasem profilu, osobnich zdrojich a aktualnim web researchi.

## 5. Non-goals pro MVP

Do prvni verze vedome nepatri:

- lekarska diagnostika
- autonomni ovladani domacnosti
- prime ovladani Tecomat Foxtrot
- automatizace DaVinci Resolve
- zpracovani videi z DJI Avatar 2
- pokrocila multi-agentni orchestrace

## 6. Primary user

Primarni uzivatel jste vy.

To znamena:

- single-user MVP
- silna personalizace
- preference pred generickym multi-user designem
- rychle iterace podle realneho kazdodenniho pouziti

## 7. Core value proposition

Asistent ma byt uzitecny hlavne v techto situacich:

- kdyz chcete vedet, co je pro vas dnes nejdulezitejsi
- kdyz chcete spojit sve poznamky, biomarkery a aktualni research
- kdyz chcete rychle najit, co uz o danem tematu vite
- kdyz chcete navrh dalsiho kroku misto jen obecneho vysvetleni

## 8. MVP scope

MVP musi umet:

- personalizovany chat
- structured personal memory
- cteni z knowledge workspace
- cteni z osobnich poznamek
- web research se zdroji
- oddeleni faktu, citaci a interpretace
- zapis shrnuti nebo follow-upu do zapisove vrstvy

MVP nemusi umet:

- akce v Home Assistantu
- Foxtrot integraci
- video workflow
- slozite dashboardy

## 9. Prioritni health domains

Pro prvni verzi jsou vybrane tyto domeny:

1. spanek
2. energie a unava
3. stres a regenerace
4. biomarkery a laboratorni hodnoty
5. navyky a denni rutina

## 10. Source of truth strategy

### Structured memory v aplikaci

Toto je nejvyssi autorita pro:

- osobni profil
- cile
- preference
- omezeni
- pravidla

### Knowledge workspace

Hlavni knowledge base pro:

- biomarkery
- medicinsky research hub
- projektovy a organizacni kontext

Aktualne identifikovane relevantni zdroje:

- biomarker knowledge base
- medical evidence and research hub
- project hub and operational context
- behavioralni a rytmicka knowledge vetev
- tematicka vrstva pro pust, dech a regeneraci
- relevantni reflektivni a poznamkove zdroje

UBZ ma v tomto navrhu specifickou roli. Konkretne jde o behavioralni a rytmickou knowledge vetev v osobnim knowledge systemu.

Tedy:

- ne jako hlavni medicinska autorita
- ale jako dulezita obsahova a metodicka vrstva pro navyky, regeneraci, osobni zmenu, motivaci a jazyk doporuceni
- a take jako nosna vrstva pro `dech` a jeho vyznam pro regulaci stresu, vnitrni stabilitu, rytmus a dlouhodobou vitalitu

Prakticke pravidlo:

- pokud jde o laboratorni nebo zdravotni tvrzeni, asistent musi UBZ kombinovat s biomarkerovou a evidence-based vrstvou
- pokud jde o denni rytmus, pristupy k regeneraci, dech, hodnoty a behavioralni doporuceni, UBZ muze byt silna personalizacni vrstva

### Personal notes

Doplnkova knowledge base pro:

- osobni zapisky
- reflexe
- symptomy
- pozorovani
- research poznamky

### Web

Pouzit jen kdyz:

- je potreba aktualni informace
- chybi data v osobnich zdrojich
- potrebujete srovnani s aktualnim stavem poznani

## 11. UX principle

Asistent nesmi pusobit jako magicka cerna skrinka.

Kazda dulezita odpoved ma umet rozlisit:

- co vi o vas
- co nasel ve vasich datech
- co je aktualni poznatek z webu
- co je jen jeho navrh nebo interpretace

## 12. Key use-cases

Nejdůlezitejsi use-cases MVP:

1. `Co je pro me dnes nejdulezitejsi udelat pro zdravi a proc?`
2. `Shrn mi, co o mne vis v oblasti spanku, stresu, energie a longevity.`
3. `Najdi vse, co uz mam k tematu X v mych zdrojich.`
4. `Dohledej aktualni pohled na tema X a porovnej to s mym kontextem.`
5. `Navrhni mi tydenni plan malych kroku.`
6. `Uloz shrnuti do systemu a vytvor mi follow-up.`

## 13. Functional requirements

### Chat

- uzivatel muze zalozit konverzaci
- asistent vraci odpoved s jasnou strukturou
- odpoved muze obsahovat zdroje a nejistoty

### Profile and memory

- uzivatel ma editovatelny osobni profil
- system uklada cile, omezeni a preference
- system umi pouzit tento profil v odpovedi

### Knowledge retrieval

- system umi nacist a indexovat vybrane knowledge zdroje
- system umi nacist a indexovat vybrane osobni poznamky
- system umi vyhledavat relevantni pasaze

### Research

- system umi dohledat aktualni informace
- system vraci citace a zdroje
- system neprezentuje webove dohady jako osobni fakta

### Actions

- system umi pripravit shrnuti
- system umi po potvrzeni zapsat shrnuti do systemu
- system umi po potvrzeni vytvorit follow-up

## 14. Safety and trust requirements

- zadne zdravotni zavery nesmi byt prezentovany jako diagnoza
- aktivni zmeny a akce musi byt potvrzene
- zdroje musi byt dohledatelne
- nejistota musi byt priznana
- osobni data musi byt oddelena od experimentalnich akci

## 15. Success criteria pro MVP

MVP je uspesne, pokud:

- asistent vrati uzitecnou personalizovanou odpoved
- odpoved je podlozena zdroji
- uzivatel ma duveru v to, odkud odpoved vzesla
- vysledek lze ulozit zpet do systemu
- asistent je dost uzitecny na opakovane pouziti nekolikrat tydne

## 16. Risks

Hlavni rizika:

- prilis siroky scope
- zamenovani faktu a interpretace
- slaba kvalita osobni pameti
- slozita auth integraci
- snaha integrovat automatizaci prilis brzo

## 17. Roadmap

### Faze 0

- ujasneni vize
- use-cases
- MVP spec
- technicky backlog

### Faze 1

- chat
- profil
- personal memory

### Faze 2

- knowledge ingest
- personal notes ingest
- retrieval

### Faze 3

- web research
- recommendation engine
- source attribution

### Faze 4

- write-back
- follow-up flow
- review queue

### Faze 5

- Home Assistant
- Foxtrot
- Resolve
- DJI workflow

## 18. Final recommendation

Nepokouset se hned o vseumelou AI vrstvu nad zdravim, domem a videem. Nejdriv postavit silneho osobniho chat asistenta pro longevity a osobni znalosti. Teprve po overeni realneho kazdodenniho prinosu na nej navazat integracemi a automatizacemi.
