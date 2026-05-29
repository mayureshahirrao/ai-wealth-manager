# Skill Dependency Map

Skills are organized in tiers. A skill in Tier N only imports from Tier N-1 or below.
This prevents circular dependencies and makes the build order unambiguous.

---

## Tier 0 — Pure Utilities (no internal imports)

```
indian_constants.py       No dependencies
currency_formatter.py     No dependencies
pan_validator.py          No dependencies
xirr.py                   External: scipy only
constants.js (FE)         No dependencies
```

---

## Tier 1 — Foundation (imports Tier 0 or external libs only)

```
config.py                 External: pydantic-settings
exceptions.py             No dependencies
logging_config.py         External: structlog
base_response.py          imports: exceptions
sip_calculator.py         imports: indian_constants
tax_calculator.py         imports: indian_constants
goal_engine.py            imports: indian_constants, sip_calculator
endpoints.js (FE)         imports: constants.js
formatters.js (FE)        imports: constants.js
```

---

## Tier 2 — Infrastructure (imports Tier 1)

```
base_model.py             imports: config
jwt_handler.py            imports: config, exceptions
error_handler.py          imports: base_response, exceptions, logging_config
password_utils.py         External: bcrypt
claude_client.py          imports: config, exceptions; External: anthropic, tenacity
chroma_client.py          imports: config; External: chromadb
apiClient.js (FE)         imports: endpoints.js; External: axios
useAuth.js (FE)           imports: apiClient.js
chartHelpers.js (FE)      imports: formatters.js, constants.js
```

---

## Tier 3 — Application Patterns (imports Tier 2)

```
repository.py             imports: base_model, exceptions
role_guard.py             imports: jwt_handler, exceptions
base_tool.py              imports: claude_client, exceptions, logging_config
langsmith_tracer.py       imports: config; External: langsmith
document_loader.py        imports: chroma_client
chunker.py                imports: (no internal deps)
embedder.py               imports: chroma_client, claude_client
fixtures.py               imports: base_model, mock_data
api_client.py (test)      imports: error_handler
useApi.js (FE)            imports: apiClient.js; External: @tanstack/react-query
INRAmount.jsx (FE)        imports: formatters.js
PercentBadge.jsx (FE)     imports: formatters.js, constants.js
LoadingSpinner.jsx (FE)   No dependencies
ErrorBoundary.jsx (FE)    No dependencies
```

---

## Tier 4 — Integration Layer (imports Tier 3)

```
base_agent.py             imports: base_tool, claude_client, langsmith_tracer
tool_registry.py          imports: base_tool
response_validator.py     imports: indian_constants, exceptions
compliance_injector.py    imports: indian_constants, response_validator, logging_config
transaction.py            imports: repository
pagination.py             imports: repository
retriever.py              imports: embedder, chunker, chroma_client
indian_schemas.py         imports: pan_validator, indian_constants, base_response
financial_validators.py   imports: indian_constants, indian_schemas, exceptions
streaming.py              imports: claude_client, base_response, compliance_injector
useSSE.js (FE)            imports: apiClient.js, useAuth.js
useINRFormatter.js (FE)   imports: formatters.js
ConfidenceBadge.jsx (FE)  imports: constants.js
```

---

## Tier 5 — Test Infrastructure (imports everything)

```
mock_data.py              imports: indian_constants, currency_formatter
fixtures.py               imports: mock_data, base_model, repository
agent_tester.py           imports: base_agent, tool_registry, mock_data, langsmith_tracer
testUtils.jsx (FE)        imports: useAuth.js, apiClient.js; External: @testing-library/react
mockData.js (FE)          imports: formatters.js, constants.js
```

---

## Import Chain: Chat Endpoint (Most Complex)

```
POST /api/chat/message
    └── error_handler.py            (Tier 2)
    └── role_guard.py               (Tier 3)
    └── streaming.py                (Tier 4)
         └── claude_client.py       (Tier 2)
         └── compliance_injector.py (Tier 4)
              └── response_validator.py (Tier 4)
              └── indian_constants.py   (Tier 0)
         └── base_response.py       (Tier 1)
    └── base_agent.py              (Tier 4)
         └── base_tool.py          (Tier 3)
         └── tool_registry.py      (Tier 4)
         └── langsmith_tracer.py   (Tier 3)
    └── retriever.py               (Tier 4)  ← for knowledge queries
         └── embedder.py           (Tier 3)
         └── chroma_client.py      (Tier 2)
```

---

## Import Chain: Financial Plan Generator (Multi-step Agent)

```
POST /api/financial-plan/generate
    └── base_agent.py (LangGraph graph definition)
         Node 1: gather_data
              └── repository.py (fetch client data)
              └── sip_calculator.py
              └── xirr.py
         Node 2: analyze_feasibility
              └── goal_engine.py
              └── tax_calculator.py
         Node 3: generate_strategies
              └── retriever.py (RAG on financial docs)
              └── compliance_injector.py
         Node 4: assemble_plan
              └── claude_client.py (synthesis)
              └── response_validator.py
         Node 5: format_output
              └── currency_formatter.py
              └── indian_schemas.py
```

---

## Critical Path (what must exist before anything else works)

```
1. config.py              ← Everything needs settings
2. exceptions.py          ← Error handling needs this first
3. logging_config.py      ← Debugging from day one
4. base_response.py       ← All API responses need this shape
5. error_handler.py       ← FastAPI needs this registered at startup
6. indian_constants.py    ← All financial logic needs this
7. base_model.py          ← All DB models need this base
8. claude_client.py       ← All AI features need this
```

Without these 8 files, nothing else can run. Build these first.
