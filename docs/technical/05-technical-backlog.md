# Longevity Assistant: technical backlog MVP

Datum: 2026-06-03

Navazuje na:

- [01-plan.md](../planning/01-plan.md)
- [02-use-cases.md](../product/02-use-cases.md)
- [03-mvp-spec.md](../product/03-mvp-spec.md)

## 1. Cilem tohoto dokumentu je

Prevest potvrzenou vizi a MVP do technickeho backlogu, podle ktereho lze:

- navrhnout architekturu
- zalozit projekt
- rozdelit praci do epik a sprintu
- zacit implementovat bez dalsi mlhy

## 2. Doporucena technicka forma prvni verze

### Uzivatelska aplikace

Jedna hlavni aplikace:

- webovy chat-first klient
- pozdeji PWA nebo mobilni wrapper

### Backend

Jeden backend s modularni architekturou:

- API layer
- orchestration layer
- memory layer
- connector layer
- research layer
- action layer

### Doporuceny stack

Frontend:

- Next.js
- React
- TypeScript

Backend:

- Python
- FastAPI

Databaze:

- PostgreSQL

Semanticke vyhledavani:

- vector store nebo pgvector nad Postgres

Asynchronni joby:

- worker queue pro ingest a sync

## 3. MVP moduly

### Modul 1: Auth and User Context

Ucel:

- drzet identitu uzivatele
- navazat profil a osobni pamet

MVP scope:

- single-user rezim
- lokalni nebo jednoduche prihlaseni

Pozdeji:

- vice uzivatelu
- role

### Modul 2: Personal Memory

Ucel:

- drzet strukturovanou pravdu o uzivateli

MVP scope:

- osobni profil
- cile
- preference
- omezeni
- navyky
- trusted source rules

### Modul 3: Conversations

Ucel:

- uchovavat chat a jeho kontext

MVP scope:

- seznam konverzaci
- zpravy
- metadata o pouzitych zdrojich
- odpovedi s citacemi

### Modul 4: Knowledge Ingestion

Ucel:

- nacitat a indexovat Notion, OneNote a nahrane soubory

MVP scope:

- manualni sync
- zakladni periodicky sync
- chunking dokumentu
- metadata o zdroji

### Modul 5: Retrieval and Reasoning

Ucel:

- rozhodnout, co vytahnout z pameti, co z konektoru a co z webu

MVP scope:

- source-aware retrieval
- source labels
- confidence rules
- daily recommendation flow

### Modul 6: Web Research

Ucel:

- dohledavat aktualni informace mimo osobni data

MVP scope:

- explicitni research step
- citace
- oddeleni osobnich dat od webu

### Modul 7: Actions

Ucel:

- zapis vysledku zpet do systemu

MVP scope:

- save summary to Notion
- create follow-up
- create task or note draft

### Modul 8: Integrations Later

Az po MVP:

- Home Assistant
- Foxtrot bridge
- Resolve connector
- DJI ingest workflow

## 4. Klicove entity MVP

## A. Core entities

### `user_profile`

Pole:

- id
- display_name
- age_group
- timezone
- health_goals
- current_focus
- constraints
- contraindications
- daily_rhythm
- coaching_preferences
- trusted_sources
- created_at
- updated_at

### `health_goal`

Pole:

- id
- profile_id
- domain
- title
- description
- priority
- status
- target_metric
- target_date

### `habit`

Pole:

- id
- profile_id
- name
- category
- frequency
- preferred_time
- active

### `health_signal`

Pole:

- id
- profile_id
- date
- domain
- title
- description
- severity
- context
- source_type
- source_ref

### `daily_checkin`

Pole:

- id
- profile_id
- date
- sleep_score
- energy_score
- stress_score
- recovery_score
- note
- created_at

## B. Conversation entities

### `conversation`

Pole:

- id
- profile_id
- title
- created_at
- updated_at

### `message`

Pole:

- id
- conversation_id
- role
- content
- structured_summary
- created_at

### `answer_source`

Pole:

- id
- message_id
- source_type
- source_label
- source_ref
- excerpt
- confidence

## C. Knowledge entities

### `knowledge_source`

Pole:

- id
- type
- provider
- external_id
- title
- url
- last_synced_at
- status

### `knowledge_document`

Pole:

- id
- source_id
- external_id
- title
- body_text
- domain_tags
- created_at
- updated_at

### `knowledge_chunk`

Pole:

- id
- document_id
- chunk_index
- text
- embedding_ref
- metadata_json

## D. Action entities

### `assistant_action`

Pole:

- id
- conversation_id
- action_type
- payload_json
- requires_confirmation
- status
- executed_at

### `follow_up`

Pole:

- id
- profile_id
- title
- due_at
- linked_conversation_id
- linked_action_id
- status

## 5. Obrazovky MVP

### 1. Chat

Musi umet:

- seznam konverzaci
- hlavni chat okno
- zdroje odpovedi
- tlacitko `ulozit do Notion`
- tlacitko `vytvorit follow-up`

### 2. Profile and Preferences

Musi umet:

- editace osobniho profilu
- editace cilu
- editace omezeni a preferenci
- trusted source rules

### 3. Health Dashboard

Musi umet:

- dnesni priorita
- posledni check-iny
- aktivni cile
- posledni doporuceni

### 4. Knowledge Sources

Musi umet:

- seznam konektoru
- stav syncu
- seznam hlavních zdroju
- moznost rucniho refresh

### 5. Review Queue

Musi umet:

- navrhy na ulozeni
- akce cekajici na potvrzeni
- moznost schvalit nebo zamitnout

## 6. Backend API / use-case vrstva

Nemusi to byt finalni REST navrh, ale tato rozhrani MVP potrebuje.

### Profile

- `GET /profile`
- `PUT /profile`
- `GET /goals`
- `POST /goals`
- `PUT /goals/:id`

### Check-ins and signals

- `GET /checkins`
- `POST /checkins`
- `GET /signals`
- `POST /signals`

### Conversations

- `GET /conversations`
- `POST /conversations`
- `GET /conversations/:id/messages`
- `POST /chat/respond`

### Sources and sync

- `GET /sources`
- `POST /sources/notion/sync`
- `POST /sources/onenote/sync`
- `GET /documents/search`

### Actions

- `POST /actions/save-summary`
- `POST /actions/create-followup`
- `POST /actions/confirm`
- `POST /actions/reject`

## 7. Orchestration flow MVP

Na dotaz typu:

`Co je pro me dnes nejdulezitejsi?`

ma backend udelat:

1. nacist profil
2. nacist posledni check-iny
3. najit relevantni knowledge chunks
4. rozhodnout, zda je potreba web research
5. slozit odpoved
6. oznacit zdroje
7. pripravit navrzene akce

Tohle je jadro cele aplikace.

## 8. Integracni backlog

### Notion connector MVP

Potrebuje:

- auth token/config
- fetch pages/databases
- sync selected sources
- map source metadata
- write summary / create follow-up

### OneNote connector MVP

Potrebuje:

- delegated auth
- list notebooks/sections/pages
- ingest page content
- sync selected sections

### Web research MVP

Potrebuje:

- search step
- source filtering
- citation extraction
- result normalization

## 9. Implementacni poradi

### Sprint 1

- project skeleton
- profile schema
- conversations
- basic chat UI

### Sprint 2

- source attribution format
- Notion connector read-only
- ingestion pipeline
- knowledge search

### Sprint 3

- OneNote connector read-only
- daily priority reasoning
- first recommendation templates

### Sprint 4

- save summary to Notion
- follow-up flow
- review queue
- health dashboard v1

## 10. Definition of done pro MVP

MVP je hotove, pokud funguje tento scenar:

1. mate vyplneny profil
2. mate pripojene Notion a OneNote zdroje
3. v chatu polozite otazku na dnesni prioritu
4. asistent vrati odpoved s oddelenim zdroju
5. odpoved obsahuje konkretni kroky
6. muzete ji ulozit do Notion
7. muzete vytvorit follow-up

Pokud toto funguje spolehlive, MVP je uzitecne.

## 11. Co vedome neresit v prvni implementaci

- multi-user architekturu
- pokrocile dashboardy
- notifikacni engine na vsechny platformy
- Home Assistant write actions
- Foxtrot protocol integration
- Resolve automation
- DJI media workflow

## 12. Doporuceni jednou vetou

Stavte nejdriv velmi dobry personal knowledge + recommendation engine v chatu; vsechno ostatni napojujte az ve chvili, kdy tato vrstva prokazatelne funguje a je pro vas denne prinosna.
