# Public Repo Audit

Datum: 2026-06-13

## Co bylo upraveno

- odstraneny absolutni lokalni cesty z verejne dokumentace
- odstraneny prime odkazy na soukrome Notion stranky
- nahrazeny interni odkazy mezi dokumenty relativnimi odkazy v repozitari
- konkretni nazvy osobnich knowledge vetvi byly zobecneny do neutralnich kategorii

## Co jsem nasel jako hlavni rizika

- absolutni lokalni cesty v dokumentaci
- prime URL na soukrome Notion stranky
- konkretni nazvy osobnich knowledge vetvi a workspace struktur

## Uz upravene soubory

- `docs/product/02-use-cases.md`
- `docs/product/03-mvp-spec.md`
- `docs/product/04-prd.md`
- `docs/product/05-stable-foundation-v5.md`
- `docs/technical/05-technical-backlog.md`
- `docs/technical/08-dna-import-workflow.md`
- `docs/technical/09-biomarker-data-model.md`

## Stav po kontrole

- rychly scan `docs/` uz nenasel prime Notion URL
- rychly scan `docs/` uz nenasel lokalni `C:/Users/...` cesty
- zbyva prubezne hlidat nove dokumenty, aby se do repozitare podobne odkazy nevracely

## Doporuceni pro public repo

- nevracet do dokumentace prime URL na soukrome Notion nebo OneNote zdroje
- necommitovat osobni zdravotni data, exporty ani screenshoty s identifikatory workspace
- drzet `.env`, runtime data a pracovni importni soubory mimo git
