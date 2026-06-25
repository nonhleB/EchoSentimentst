# Echo Sentiment

AI-powered sentiment analysis — confidence scores, highlighted phrases, batch mode, export.

## Deploy to Render (5 minutes)

### 1. Push to GitHub
Create a new GitHub repo and push this folder to it.

### 2. Create a Web Service on Render
1. Go to [render.com](https://render.com) → **New** → **Web Service**
2. Connect your GitHub repo
3. Use these settings:

| Setting | Value |
|---|---|
| **Runtime** | Node |
| **Build command** | `npm install` |
| **Start command** | `npm start` |
| **Instance type** | Free |

### 3. Add your xAI (Grok) API key
Get a key at [console.x.ai](https://console.x.ai) → API Keys → Create Key (copy it immediately — it's only shown once).

In Render → your service → **Environment**:

| Key | Value |
|---|---|
| `XAI_API_KEY` | `xai-...` |

Click **Save changes** — Render redeploys automatically.

Your app will be live at `https://your-service-name.onrender.com`.

> **Note:** make sure your xAI console has credits or an active free-credit allowance — an "invalid API key" error from a freshly created, correctly-copied key usually means the account has no billing/credits set up, not that the key is wrong.

---

## Run locally

```bash
npm install
XAI_API_KEY=xai-... npm start
```

Then open http://localhost:3000

---

## Features
- Single text analysis with confidence score
- Color-coded highlighted phrases (positive / negative / neutral)
- Keyword extraction
- Sarcasm detection flag
- Sentiment distribution breakdown
- Analysis history (in-session)
- Batch mode — analyze multiple texts at once
- File upload (.txt / .csv)
- Export results as CSV or JSON
