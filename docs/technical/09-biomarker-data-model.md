# Biomarker Data Model

Tento dokument zamyka stabilni zaklad pro krevni rozbory a biomarkery v projektu `Longevity-assistant`.

## Cile modelu

Model musi umet:

- drzet laboratorni historii za vice let
- zachovat puvodni zdroj a auditovatelnost
- oddelit od sebe `panel`, `jednotlivy marker` a `interpretaci`
- podporit pozdejsi import z PDF, fotek, tabulek i rucniho zapisu
- umoznit trendovani v case
- propojit biomarkery s DNA, daily check-ins, health signals a evidence vrstvou

## Zakladni principy

Biomarkery se maji cist ve trech vrstvach:

- `Observation layer`
  - co bylo skutecne namereno
- `Reference layer`
  - v jakych jednotkach a referencich se to ma cist
- `Interpretation layer`
  - co to muze znamenat v osobnim kontextu

Asistent nesmi michat syrovou laboratorni hodnotu s interpretaci.

## Doporucena hierarchie

### 1. BiomarkerReport

Predstavuje jeden realny dokument nebo jednu laboratorni navstevu.

Pouziti:

- PDF z laboratore
- fotka nebo scan
- tabulka z Excelu
- rucne prepsany report

Pole:

- `id`
- `profileId`
- `sourceType`
  - `pdf`
  - `image`
  - `manual_entry`
  - `csv`
  - `notion`
  - `google_doc`
- `sourceLabel`
- `sourceRef`
- `labName`
- `collectedAt`
- `reportedAt`
- `fastingState`
  - `fasting`
  - `non_fasting`
  - `unknown`
- `notes`
- `rawText`
- `createdAt`
- `updatedAt`

### 2. BiomarkerObservation

Predstavuje jednu konkretni laboratorni hodnotu.

Priklady:

- glukoza
- HbA1c
- LDL-C
- HDL-C
- triglyceridy
- hs-CRP
- homocystein
- vitamin D
- B12
- ferritin
- TSH

Pole:

- `id`
- `reportId`
- `markerKey`
- `markerLabel`
- `category`
  - `glucose_metabolism`
  - `lipids`
  - `inflammation`
  - `methylation`
  - `vitamins`
  - `minerals`
  - `thyroid`
  - `liver`
  - `kidney`
  - `blood_count`
  - `hormones`
  - `other`
- `value`
- `unit`
- `comparator`
  - `exact`
  - `lt`
  - `lte`
  - `gt`
  - `gte`
- `referenceLow`
- `referenceHigh`
- `referenceText`
- `status`
  - `low`
  - `optimal`
  - `high`
  - `out_of_range`
  - `unknown`
- `measurementContext`
  - `fasting`
  - `non_fasting`
  - `supplementing`
  - `unknown`
- `observedAt`
- `sourceLine`
- `confidence`
  - `manual_confirmed`
  - `parsed_high`
  - `parsed_medium`
  - `parsed_low`

### 3. BiomarkerMarkerDefinition

Slovnik markeru, aby se stejne markery neukladaly pokaždé jinak.

Priklady:

- `glucose_fasting`
- `hba1c`
- `insulin_fasting`
- `ldl_c`
- `hdl_c`
- `triglycerides`
- `hs_crp`
- `homocysteine`
- `vitamin_d_25oh`
- `vitamin_b12`

Pole:

- `key`
- `label`
- `category`
- `defaultUnit`
- `aliases`
- `canonicalSource`
- `description`

### 4. BiomarkerTrendSnapshot

Nepovinny odvozeny objekt pro rychle cteni trendu.

Pouziti:

- chat odpoved
- daily briefing
- health dashboard

Pole:

- `markerKey`
- `latestValue`
- `latestUnit`
- `latestObservedAt`
- `previousValue`
- `deltaAbsolute`
- `deltaPercent`
- `trendDirection`
  - `up`
  - `down`
  - `stable`
  - `unknown`
- `sampleCount`

## Minimalni MVP model

Pro prvni ingest zpet do historie neni nutne delat vsechno naraz.

MVP minimum:

- `BiomarkerReport`
- `BiomarkerObservation`
- `BiomarkerMarkerDefinition`

To staci pro:

- archiv 5 let vysledku
- vyhledavani podle markeru
- jednoduchy trend v case
- navazani na evidence vrstvu

## Doporucene technicke entity

### Backend / Python

- `BiomarkerReport`
- `BiomarkerObservation`
- `BiomarkerMarkerDefinition`
- `BiomarkerImportDraft`
- `BiomarkerImportDraftInput`

### Shared contracts / TypeScript

- `BiomarkerReport`
- `BiomarkerObservation`
- `BiomarkerMarkerDefinition`
- `BiomarkerTrendSnapshot`

## Doporucena logika importu

Import ma byt dvoustupnovy:

### 1. Draft import

Systém vytahne:

- datum odberu
- jmeno laboratore
- marker
- hodnotu
- jednotku
- reference

Ale jeste z toho nedela kanonickou pravdu.

### 2. Confirmed import

Po kontrole se teprve ulozi potvrzeny report a jeho observations.

To je dulezite, protoze stare laboratorni podklady mohou mit:

- ruzne jednotky
- ruzne nazvy stejnych markeru
- chyby OCR
- nekompletni reference

## Dulezita pravidla

### 1. Nikdy neukladat jen text bez struktury

Originalni dokument muze zustat jako soubor nebo raw text,
ale vedle nej musi vzniknout strukturovane observations.

### 2. Jednotky jsou povinne

Bez jednotky je biomarker skoro nepouzitelny.

### 3. Datum odberu je povinne

Bez datumu nelze delat trendy.

### 4. Reference ukladat, ale nepreceňovat

Laboratorni reference se mohou lisit mezi laboratoremi.
Maji zustat ulozene, ale interpretace nesmi stat jen na nich.

### 5. DNA nikdy neprepisuje biomarkery

DNA je predispozice.
Biomarker je skutecne merena realita.

## Vazby na ostatni vrstvy

Biomarker vrstva se ma napojit na:

- `GeneticProfile`
  - napr. folat, B12, homocystein, lipidy, glukoza
- `HealthSignal`
  - napr. unava, nadymani, zhorsena regenerace
- `DailyCheckIn`
  - napr. energie, stres, spanek
- `Evidence layer`
  - evidence/research vrstva a biomarker knowledge base

## Doporucene marker groups pro prvni ingest

Prvni vlna by mela obsahovat jen vysoko uzitecne markery:

- glukoza
- HbA1c
- inzulin
- HOMA-IR pokud pujde odvodit
- total cholesterol
- LDL-C
- HDL-C
- triglyceridy
- hs-CRP nebo CRP
- homocystein
- vitamin D
- vitamin B12
- ferritin
- TSH
- ALT
- AST
- kreatinin

Tohle uz da silnou longevity vrstvu bez zbytecne slozitosti.

## Doporuceny dalsi krok

Po tomto modelu navazuje:

1. `biomarker contracts + backend models`
2. `biomarker import draft endpoint`
3. `intake workflow pro 5 let starych vysledku`
