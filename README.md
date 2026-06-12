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

### 3. Add your Anthropic API key
In Render → your service → **Environment**:

| Key | Value |
|---|---|
| `ANTHROPIC_API_KEY` | `sk-ant-...` |

Click **Save changes** — Render redeploys automatically.

Your app will be live at `https://your-service-name.onrender.com`.

---

## Run locally

```bash
npm install
ANTHROPIC_API_KEY=sk-ant-... npm start
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
