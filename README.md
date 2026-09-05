# textile-agentic-ai
Ai Agent for Textile Production Monitoring and Fault Recovery

## FastAPI backend

Install dependencies from `requirements.txt`, then start the backend from the
repository root:

```powershell
uvicorn app.api.main:app --reload
```

Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

The backend reuses the existing machine tools, root-cause analysis, and
OpenRouter agent. Local frontend origins are allowed by default through
`CORS_ORIGINS` in `.env`; production deployments should set that variable to
their explicit frontend origins rather than using `*`.
