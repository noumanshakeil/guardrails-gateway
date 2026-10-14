# Dev server for guardrails-gateway
$env:LLM_MODE = "mock"
uvicorn backend.main:app --reload --port 8000
