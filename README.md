@"
# AI Prompt Template Directory API

Store, categorize, search, and retrieve AI prompt templates.

## Endpoints
- POST/GET /categories/ - Manage categories
- POST/GET /prompts/ - Manage prompt templates
- POST /prompts/{id}/render - Fill in template variables
- POST /prompts/{id}/rate - Rate a prompt

## Run Locally
```
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```
## Docs
Visit /docs for Swagger UI
"@ | Out-File -Encoding utf8 README.md
```

## Step 4: Start Your Server!

```powershell
uvicorn app.main:app --reload
```

You should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Started reloader process
INFO:     Application startup complete.
```

## Step 5: Open Swagger Docs

```powershell
# Open new PowerShell tab, then:
Start-Process "http://127.0.0.1:8000/docs"
```

## Step 6: Test Your Live API With cURL

Open **another PowerShell tab** (keep server running):

```powershell
# Health check
Invoke-RestMethod http://127.0.0.1:8000/health

# Create a category
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/categories/ `
  -ContentType "application/json" `
  -Body '{"name": "Coding", "description": "Software dev prompts"}'
```

Copy the `id` from the response, then:

```powershell
# Create a prompt (replace YOUR_CATEGORY_ID)
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/prompts/ `
  -ContentType "application/json" `
  -Body '{
    "title": "Code Reviewer",
    "template": "Review this {{language}} code:\n\n{{code}}\n\nList bugs and improvements.",
    "description": "AI code review assistant",
    "author": "nahid",
    "model_hint": "gpt-4",
    "use_case": "coding",
    "category_ids": ["YOUR_CATEGORY_ID"]
  }'
```

Copy the prompt `id`, then:

```powershell
# Render the prompt (replace YOUR_PROMPT_ID)
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/prompts/YOUR_PROMPT_ID/render `
  -ContentType "application/json" `
  -Body '{"values": {"language": "Python", "code": "def add(a,b): return a+b"}}'

# Search prompts
Invoke-RestMethod "http://127.0.0.1:8000/prompts/?search=review"

# Rate it
Invoke-RestMethod -Method Post "http://127.0.0.1:8000/prompts/YOUR_PROMPT_ID/rate?score=4.5"
```

---

## Step 7: Deploy to Render (When Ready)

```powershell
# Initialize git
git init
git add -A
git commit -m "AI Prompt Template Directory API - initial commit"

# Create repo on GitHub (go to github.com/new), then:
git remote add origin https://github.com/YOUR_USERNAME/ai-prompt-directory.git
git branch -M main
git push -u origin main
```

Then:

```
1. Go to https://render.com
2. Sign up / Log in
3. Click "New" → "Blueprint"
4. Connect your GitHub repo
5. Render reads render.yaml automatically
6. Click "Apply" → deploys in ~2 minutes
7. Your API is live at: https://ai-prompt-api.onrender.com/docs
```

> **For Render deployment to work with PostgreSQL**, add psycopg to requirements:
> ```powershell
> # Only add this line BEFORE pushing to GitHub
> Add-Content requirements.txt "psycopg[binary]==3.2.4"
> ```

---

## What You Have Now

```
✅ Tests passing (2/2)
✅ Dockerfile ready
✅ render.yaml ready
✅ README ready
✅ Server runs locally
✅ Swagger docs at /docs
✅ Ready to deploy to Render
```

**Go start the server with `uvicorn app.main:app --reload` and open `/docs` in your browser!**