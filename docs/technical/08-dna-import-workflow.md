# DNA Import Workflow

Tento workflow slouzi pro prvni bezpecny import DNA rozboru do `Longevity-assistant`.

## Co je cil

Neukladat DNA jen jako volny text, ale dostat ji do prvni strukturovane vrstvy:

- `GeneticProfile`
- `GeneticMarker`
- importni draft k rucnimu potvrzeni

DNA se v systemu bere jako:

- silna personalizacni vrstva
- doporucujici signal
- ne konecny verdikt

## Doporuceny zdroj

Pro prvni iteraci:

- nechte original DNA rozbor v Google dokumentu
- do importu berte jen vybrane relevantni pasaze
- import pouzivejte jako pracovni draft, ne jako automaticky finalni profil

## Kde vlozit text

Pracovni vstupni soubor je:

- [notes/dna-import-source.txt](C:/Users/Petr/Documents/AI_ChatGPT_Projekt_Kartičky/Longevity/longevity-assistant/notes/dna-import-source.txt)

Sem vlozte vybrane pasaze z Google dokumentu.

## Jak pustit draft import

1. Spustte backend:

```powershell
npm run dev:backend
```

2. Naplnte [notes/dna-import-source.txt](C:/Users/Petr/Documents/AI_ChatGPT_Projekt_Kartičky/Longevity/longevity-assistant/notes/dna-import-source.txt)

3. Pustte draft import:

```powershell
npm run dna:import-draft
```

Volitelne lze predat vlastni cestu nebo popis zdroje:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\import-dna-draft.ps1 `
  -InputFile "notes\dna-import-source.txt" `
  -SourceType "google_doc" `
  -SourceLabel "DNA rozbor - Google dokument"
```

## Co import vrati

Draft endpoint:

- `POST /genetics/import-draft`

vrati:

- `summary`
- `markers`
- `unresolvedNotes`

Parser v aktualni verzi umi heuristicky zachytit hlavne:

- `laktosa / laktaza / lactose`
- `kofein / caffeine`
- `folat / MTHFR / methylace`

Pokud nic nenajde, vrati upozorneni do `unresolvedNotes`.

## Jak z draftu udelat potvrzeny profil

Po kontrole draftu lze potvrzeny profil zapsat do:

- `PUT /genetics/profile`

Kanonicky profil se uklada do:

- [data/runtime/genetic-profile.json](C:/Users/Petr/Documents/AI_ChatGPT_Projekt_Kartičky/Longevity/longevity-assistant/data/runtime/genetic-profile.json)

## Prakticka metodika

Prvni iterace:

- vlozit jen hlavni relevantni zavery
- neprepisovat tam cely report
- zacit 3-6 markery max

Dobra struktura vstupu:

- tolerance laktozy
- reakce na kofein
- methylace / folat
- dalsi markery k energii, spanku, stresu nebo vyzive

Co zatim nedelat:

- nedelat z draftu automaticky konecny zdravotni vyklad
- netlacit do systemu nejasne nebo velmi spekulativni casti bez poznamky

## Dalsi navazujici krok

Po prvnim uspesnem draft importu doporucuju:

1. rucne potvrdit jen relevantni markery
2. doplnit dalsi parser pravidla podle vaseho realneho DNA dokumentu
3. navazat DNA na meal konflikty, health signals a evidence vrstvu
