# Biomarker Intake Workflow from Google Sheets

Tento dokument popisuje prakticky postup, jak dostat historicke krevni rozbory z Google Sheets do `Longevity-assistant`.

## Cil

Prevest 5 let stary archiv laboratornich vysledku do podoby, ktera:

- zachova puvodni data
- bude trendovatelna v case
- pujde napojit na DNA, evidence layer a osobni guidance
- nevyzaduje prekopani zakladu pozdeji

## Doporucena strategie

Nejlepsi cesta je:

1. nechat puvodni Google Sheets jako `working source`
2. sjednotit ji do jedne intake struktury
3. z intake struktury delat `draft import`
4. po kontrole teprve potvrzovat do kanonickych biomarker entit

To znamena:

- Google Sheets neni finalni source of truth
- ale je vyborny prechodny zdroj pro historicka data

## Doporucena organizace Google Sheets

Idealni jsou dve vrstvy listu:

### 1. `raw_import`

Sem zustanou vase puvodni nebo polo-puvodni hodnoty.

Pravidla:

- nemenit puvodni vyznam
- nesjednocovat tu slozite pravidla
- je to auditni a pracovni list

### 2. `normalized_intake`

Sem se pripravi data pro import do aplikace.

Pravidla:

- jeden radek = jedna biomarker observation
- jednotne nazvy markeru
- povinny datum
- povinna jednotka

## Doporucene sloupce v `normalized_intake`

Pouzijte tuto strukturu:

- `report_date`
- `reported_date`
- `lab_name`
- `fasting_state`
- `marker_key`
- `marker_label`
- `category`
- `value`
- `unit`
- `comparator`
- `reference_low`
- `reference_high`
- `reference_text`
- `status`
- `source_sheet`
- `source_row`
- `notes`

## Co znamena kazdy sloupec

### `report_date`

Datum odberu nebo datum reportu, pokud datum odberu neni.

Format:

- `YYYY-MM-DD`

### `reported_date`

Volitelne datum vydani vysledku.

### `lab_name`

Nazev laboratore nebo kliniky.

Priklad:

- `Synlab`
- `AeskuLab`
- `Praktik 2023`

### `fasting_state`

Jedna z hodnot:

- `fasting`
- `non_fasting`
- `unknown`

### `marker_key`

Kanonicky strojovy klic markeru.

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
- `ferritin`
- `tsh`
- `alt`
- `ast`
- `creatinine`

### `marker_label`

Lidsky citelny nazev.

Priklady:

- `Glukoza nalacno`
- `HbA1c`
- `LDL cholesterol`

### `category`

Jedna z hodnot:

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

### `value`

Ciselna hodnota bez jednotky.

### `unit`

Povinna jednotka.

Priklady:

- `mmol/L`
- `pmol/L`
- `ug/L`
- `ng/mL`
- `%`
- `mIU/L`

### `comparator`

Obvykle:

- `exact`

Pouze kdyz laborator uvadi neco jako:

- `<`
- `>`

pak pouzit:

- `lt`
- `gt`

### `reference_low`

Dolni mez reference, pokud je znama.

### `reference_high`

Horni mez reference, pokud je znama.

### `reference_text`

Volny text reference z laboratore, pokud ciselne meze nestaci.

### `status`

Pro intake je bezpecne pouzivat:

- `unknown`

Pozdeji se muze dopocitat nebo potvrdit.

### `source_sheet`

Nazev puvodniho listu v Google Sheets.

### `source_row`

Cislo radku puvodniho zaznamu.

### `notes`

Volitelne poznamky:

- jednotka byla prepocitana
- fasting stav nejasny
- laboratorni reference chybi

## Doporuceny prvni scope

Nezacinat vsemi markery.

Prvni vlna ma byt:

- glukoza
- HbA1c
- inzulin
- total cholesterol
- LDL-C
- HDL-C
- triglyceridy
- CRP nebo hs-CRP
- homocystein
- vitamin D
- vitamin B12
- ferritin
- TSH
- ALT
- AST
- kreatinin

To uz da velmi silnou vrstvu pro longevity.

## Dulezita metodika cisteni

### 1. Jeden marker, jeden radek

Nepouzivat siroke tabulky typu:

- datum v radku
- markery ve sloupcich

To je dobry archiv, ale spatny intake.

Pro import je lepsi:

- jeden radek = jedna hodnota

### 2. Nesjednocovat interpretace do hodnot

Do `value` patri jen cislo.

Ne:

- `vysoke`
- `ok`
- `lehce zvysene`

To patri do poznamky nebo do pozdejsi interpretace.

### 3. Jednotky nechat explicitne

I kdyz jsou vsechny hodnoty v jednom listu, jednotku zapisovat ke kazdemu radku.

### 4. Datum je povinne

Kdyz chybi presny den, lze docasne pouzit odhadnuty format:

- prvni den v mesici

Ale do `notes` zapsat, ze je datum aproximovane.

## Jak budeme pracovat s vasimi podklady

Az mi ukazete Google Sheets podklady, udelame toto:

1. zhodnotim, jak jsou data usporadana
2. reknu, jestli je lepsi:
   - transformace v jednom listu
   - nebo pomocny `normalized_intake` list
3. navrhnu mapovani sloupcu
4. pripravim z nich import-ready strukturu

## Co po vas budu potrebovat

Az budete pripraveny ukazat podklady, bude idealni dodat:

- screenshot struktury listu
- nebo export / ukazku hlavicky sloupcu
- nebo vybrane radky z anonymizovane verze

Nejlepsi je videt:

- jak vypada jeden report
- jak jsou zapsane datumy
- jak jsou zapsane jednotky
- jestli jsou reference v samostatnych sloupcich

## Dalsi navazujici krok

Po zhodnoceni vaseho Google Sheets podkladu doporucuju:

1. pripravit `normalized_intake` mapping
2. doplnit prvni `biomarker import draft endpoint`
3. otestovat ingest na 1-2 reale reporty
