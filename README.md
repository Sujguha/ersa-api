# ERSA API

FastAPI wrapper that exposes ERSA as a REST endpoint for the ServiceNow
integration. See `main.py` — the scoring logic is currently a stub; replace
`run_ersa_assessment()` with your actual ERSA/LangChain pipeline.

## 1. Push this to your own GitHub

Run these from inside this folder (`ersa-api/`), on your own machine —
Claude doesn't have access to your GitHub account and won't run these for
you:

```bash
git init
git add .
git commit -m "Initial ERSA API"
git branch -M main
git remote add origin https://github.com/<your-username>/ersa-api.git
git push -u origin main
```

If the repo doesn't exist yet, create it first at github.com/new (keep it
empty — no README/license, so the push above doesn't conflict), then run
the commands.

## 2. Deploy to Render (free)

1. Go to render.com, sign in with your GitHub account.
2. New > Web Service > pick the `ersa-api` repo you just pushed.
3. Render should auto-detect `render.yaml` and pre-fill the settings
   (Python env, build/start commands, free plan). If it doesn't, set them
   manually:
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Click Create Web Service. First deploy takes a couple of minutes.
5. You'll get a URL like `https://ersa-api.onrender.com`. Test it:
   ```bash
   curl https://ersa-api.onrender.com/
   # {"status":"ok","service":"ERSA Risk API"}
   ```

Note: the free tier spins the service down after ~15 minutes of inactivity
and takes 10-30 seconds to wake on the next request. Fine for a Business
Rule you've set to run asynchronously; not fine if ServiceNow needs an
instant synchronous response.

## 3. Point ServiceNow at it

In the ServiceNow REST Message ("ERSA Risk API"), set the endpoint to:

```
https://ersa-api.onrender.com/api/v1/assess-change
```

No auth is configured on this stub app yet — add an API key check in
`main.py` (and matching header in the ServiceNow REST Message) before
using this beyond testing.

## 4. Replace the stub logic

Everything in `run_ersa_assessment()` in `main.py` is placeholder scoring.
Swap it for your real ERSA pipeline call — the function signature (receives
the full Change Request payload, returns `(risk_score, recommendation)`)
is the only contract the rest of the app depends on.
