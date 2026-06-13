# Backend

Tento backend uz neni jen scaffold. Ve Sprintu 1.1 drzi:

- profile service s JSON persistenci
- rules service s JSON persistenci
- conversation service s JSON persistenci
- guidance service pro source-aware odpovedi
- source-scope policy heuristiku podle typu dotazu
- pripravu pro genetics layer a evidence/research orchestration

Aktualni endpointy:

- `GET /health`
- `GET /profile`
- `GET /assistant/rules`
- `GET /assistant/bootstrap`
- `GET /assistant/today`
- `GET /conversations`
- `POST /conversations`
- `GET /conversations/{conversation_id}/messages`
- `POST /chat/respond`

Runtime data:

- `data/runtime/profile.json`
- `data/runtime/assistant-rules.json`
- `data/runtime/conversations.json`

Blizke dalsi kroky:

- meal and nutrition entity flow
- DNA ingestion
- Notion and OneNote connectors
- action approval flow
