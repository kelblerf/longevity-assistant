# Longevity Assistant: Handoff pro další vlákno

Datum: 12. 6. 2026
Repo: `C:\Users\Petr\Documents\AI_ChatGPT_Projekt_Kartičky\Longevity\longevity-assistant`
Lokální web: `http://127.0.0.1:3000/chat`

## Kde jsme skončili

Projekt je posunutý směrem k reálně použitelné lokální webové aplikaci.

Hotové a ověřené:
- frontend i backend běží lokálně
- runtime data se drží lokálně v `data/runtime`
- Notion funguje jako integrační a znalostní vrstva, ne jako primární runtime
- sync vrstva pro `health_signals` a `follow_ups` byla opravena a má nenulové synced count
- existuje sync pro `daily_check_ins`, `care_recommendations`, `biomarker_reports`, `biomarker_trends`, `genetic_profile`, `genetic_markers`
- chat odpovědi už umí pracovat s jídlem, biomarkerovou vrstvou, UBZ a evidence kontextem
- ve frontendových kartách šlo opravit problematické spojování textu v reminder / pravém sloupci
- z UI jde mazat chybně zadané `meal` a `health signal` záznamy

## Dnešní konkrétní posun

Byly doplněny guided production test flows přímo do UI:

1. Jídlo
- předvyplnění scénářů `Losos a avokado` a `Jogurt a ovoce`
- tlačítko `Zeptat se na poslední jídlo`

2. Health signál
- předvyplnění scénářů `Nadymani po jidle` a `Napeti v tele`
- tlačítko `Zeptat se na poslední signál`

3. Denní check-in
- předvyplnění scénářů `Rano nizsi energie` a `Vecer po narocnem dni`
- tlačítko `Zeptat se na poslední check-in`

Ověření:
- `next build` prošel
- frontend běží na `http://127.0.0.1:3000/chat`
- v browseru bylo ověřeno, že nové guided test panely jsou vidět

## Důležité soubory

- `src/frontend/app/chat/page.tsx`
- `src/frontend/app/globals.css`
- `src/frontend/lib/api.ts`
- `src/backend/app/api.py`
- `src/backend/app/services/meal_service.py`
- `src/backend/app/services/health_signal_service.py`
- `src/backend/tests/test_api.py`

## Co je teď prakticky použitelné

Pro rychlé demo nebo test:
- otevřít `http://127.0.0.1:3000/chat`
- zkusit guided flow pro check-in, signál nebo jídlo
- uložit záznam
- kliknout na navazující tlačítko pro dotaz do chatu
- případně smazat chybný meal nebo signal v pravém přehledu

## Doporučený další krok zítra

Nejlepší navázání:

1. Udělat lehký `test dashboard`
- ukázat, zda byl dnes už vyzkoušen check-in flow, signal flow a meal flow
- cílem je mít rychlý produkční sanity check bez ručního procházení celé stránky

2. Pak navázat workflow clarity
- ještě jasněji ukázat, co je:
- pouze lokální runtime
- sync do Notion
- knowledge-only vrstva

3. Potom případně pokračovat dashboard / vizualizační vrstvou

## Doporučený prompt do nového vlákna

Navazujeme na Longevity Assistant v repu `C:\Users\Petr\Documents\AI_ChatGPT_Projekt_Kartičky\Longevity\longevity-assistant`.

Prosím přečti nejdřív handoff:
`notes/handoff-2026-06-12-production-context.md`

Aktuální stav:
- guided production test flow je hotový pro check-in, health signál a jídlo
- frontend běží na `http://127.0.0.1:3000/chat`
- dalším doporučeným krokem je lehký test dashboard, který ukáže, které produkční flow už byly dnes skutečně vyzkoušené

Prosím navaž přímo realizací bez zbytečné rekapitulace.
