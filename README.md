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

## React frontend

From the `frontend` directory:

```powershell
npm install
npm run dev
```

The dashboard runs at `http://127.0.0.1:5173/` and uses
`frontend/.env.example` for the backend URL and non-secret loom list. It never
contains OpenRouter or Tavily credentials.

## Phase 6 advanced AI

The `tools/advanced_analysis_tools.py` orchestration combines current
telemetry, historical telemetry, maintenance records, the existing diagnostic
tool, web-backed root-cause analysis, and explainable prediction modules.

- **Anomalies:** each metric is compared with the prior historical median. The
	score increases with deviation relative to historical spread and is raised
	when a configured prototype threshold is breached.
- **Trends:** first-to-latest relative change is classified as improving,
	stable, or deteriorating using a 3% stability band.
- **Maintenance risk:** LOW, MEDIUM, or HIGH is a rule-based estimate using
	severe anomalies, deteriorating trends, current status, and recurring
	maintenance records.
- **Production forecast:** a one-step estimate from the historical production
	slope with observed variation reported as uncertainty.
- **Failure risk:** named failure modes receive transparent evidence scores
	from current thresholds, anomalies, trends, and relevant maintenance text.

The analysis requires current telemetry and at least three historical readings
for reliable trend and prediction output. With less data it returns
`Insufficient historical data for reliable prediction.` No synthetic training
data is created. Scores and confidence values are evidence-based indicators,
not probabilities, guarantees, or exact failure dates. The small CSV dataset,
prototype thresholds, and simple rules should eventually be replaced by
OEM-specific baselines and production-grade, labeled time-series models.
