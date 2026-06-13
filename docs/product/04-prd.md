# Longevity Assistant PRD

Datum: 2026-06-03

Navazuje na:

- [longevity-assistant-plan.md](C:/Users/Petr/Documents/Codex/2026-06-02/notion-plugin-notion-openai-curated-p/outputs/longevity-assistant-plan.md)
- [longevity-assistant-use-cases.md](C:/Users/Petr/Documents/Codex/2026-06-02/notion-plugin-notion-openai-curated-p/outputs/longevity-assistant-use-cases.md)
- [longevity-assistant-mvp-spec.md](C:/Users/Petr/Documents/Codex/2026-06-02/notion-plugin-notion-openai-curated-p/outputs/longevity-assistant-mvp-spec.md)
- [longevity-assistant-technical-backlog.md](C:/Users/Petr/Documents/Codex/2026-06-02/notion-plugin-notion-openai-curated-p/outputs/longevity-assistant-technical-backlog.md)

## 1. Executive summary

Longevity Assistant je osobni AI asistent zamereny na zdravy zivotni styl, longevity a personalizovane rozhodovani. Jeho hlavni vstup je chat. Jeho hlavni hodnota neni v obecnem povidani, ale v tom, ze:

- zna vas osobni kontext
- umi cist vase vlastni znalosti
- umi dohledat aktualni informace
- umi navrhnout dalsi konkretni krok
- umi vysledek vratit zpet do vaseho systemu

Prvni verze nema byt "AI na vsechno", ale `chat-first Longevity Copilot`.

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
- Notion
- OneNote
- internetovy research
- pozdeji i Home Assistant, Foxtrot, soubory a media workflow

## 4. Product goal

Hlavni cil prvni verze:

> Umoznit vam dostat personalizovanou, zdrojovane podlozenou odpoved na otazky kolem zdravi a longevity, zalozenou na vasem profilu, Notionu, OneNote a aktualnim web researchi.

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
- cteni z Notion
- cteni z OneNote
- web research se zdroji
- oddeleni faktu, citaci a interpretace
- zapis shrnuti nebo follow-upu do Notion

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

### Notion

Hlavni knowledge base pro:

- biomarkery
- medicinsky research hub
- projektovy a organizacni kontext

Aktualne identifikovane relevantni zdroje:

- [Blood Biomarkers - Source of Truth](https://www.notion.so/32a1b27aac7e80f883c4c392744dae8e?pvs=1)
- [NotebookLM - Medical Fundation](https://www.notion.so/32a1b27aac7e80b08edfd8f952014d22?pvs=1)
- [Longevity APP - Projekt Hub (Master page)](https://www.notion.so/32a1b27aac7e80248820d47d2898108a)
- [Energo evoluce 2025](https://www.notion.so/3f07eaf8b5fa407e836b220568780d64)
- [Vize Klub UBZ](https://www.notion.so/19d1b27aac7e8034abf9c25e1e89f91d)
- [VIZE Umění být zdráv](https://www.notion.so/daef812067644ecc874189de396e1c31)
- [Manifest Tvůrce](https://www.notion.so/19d1b27aac7e80abb00cd95e70bc9710)
- [Člověkologie](https://www.notion.so/19d1b27aac7e8084915fef5ff20288c8)
- `Půsty a dech v souvislostech`

UBZ ma v tomto navrhu specifickou roli. Konkretne jde o tematickou vetev:

`Digitální druhý mozek / Témata / UBZ Energo evoluce 2025`

Tedy:

- ne jako hlavni medicinska autorita
- ale jako dulezita obsahova a metodicka vrstva pro navyky, regeneraci, osobni zmenu, motivaci a jazyk doporuceni
- a nově i jako nosna vrstva pro `dech` a jeho vyznam pro regulaci stresu, vnitrni stabilitu, rytmus a dlouhodobou vitalitu

Prakticke pravidlo:

- pokud jde o laboratorni nebo zdravotni tvrzeni, asistent musi UBZ kombinovat s biomarkerovou a evidence-based vrstvou
- pokud jde o denni rytmus, pristupy k regeneraci, dech, hodnoty a behavioralni doporuceni, UBZ muze byt silna personalizacni vrstva

### OneNote

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

Asistent nesmi pusobit jako "magicka cerna skrinka".

Kazda dulezita odpoved ma umet rozlisit:

- co vi o vas
- co nasel ve vasich datech
- co je aktualni poznatek z webu
- co je jen jeho navrh nebo interpretace

## 12. Key use-cases

Nejdůležitější use-cases MVP:

1. `Co je pro me dnes nejdulezitejsi udelat pro zdravi a proc?`
2. `Shrn mi, co o mne vis v oblasti spanku, stresu, energie a longevity.`
3. `Najdi vse, co uz mam k tematu X v Notion a OneNote.`
4. `Dohledej aktualni pohled na tema X a porovnej to s mym kontextem.`
5. `Navrhni mi tydenni plan malych kroku.`
6. `Uloz shrnuti do Notion a vytvor mi follow-up.`

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

- system umi nacist a indexovat vybrane Notion zdroje
- system umi nacist a indexovat vybrane OneNote sekce
- system umi vyhledavat relevantni pasaze

### Research

- system umi dohledat aktualni informace
- system vraci citace a zdroje
- system neprezentuje webove dohady jako osobni fakta

### Actions

- system umi pripravit shrnuti
- system umi po potvrzeni zapsat shrnuti do Notion
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

- Notion ingest
- OneNote ingest
- retrieval

### Faze 3

- web research
- recommendation engine
- source attribution

### Faze 4

- Notion write-back
- follow-up flow
- review queue

### Faze 5

- Home Assistant
- Foxtrot
- Resolve
- DJI workflow

## 18. Final recommendation

Nepokouset se hned o vseumelou AI vrstvu nad zdravim, domem a videem. Nejdriv postavit silneho osobniho chat asistenta pro longevity a osobni znalosti. Teprve po overeni realneho kazdodenniho prinosu na nej navazat integracemi a automatizacemi.
