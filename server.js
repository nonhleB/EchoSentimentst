const express = require('express');
const path = require('path');
const app = express();

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// xAI Grok endpoint — OpenAI-compatible chat completions format
const GROK_URL = 'https://api.x.ai/v1/chat/completions';
const GROK_MODEL = 'grok-4.3';

// Proxy endpoint — keeps the API key server-side
app.post('/api/analyze', async (req, res) => {
  const { text, batch } = req.body;

  if (!process.env.XAI_API_KEY) {
    return res.status(500).json({ error: 'XAI_API_KEY not set in environment variables.' });
  }

  const makePrompt = (t) => `Analyze the sentiment of this text. Return ONLY a JSON object with NO markdown, no backticks, no explanation. Format exactly:
{
  "overall": "positive" | "negative" | "neutral",
  "confidence": <integer 0-100>,
  "scores": {"positive": <int 0-100>, "negative": <int 0-100>, "neutral": <int 0-100>},
  "summary": "<one sentence>",
  "keywords": [{"word": "<word or phrase>", "type": "positive"|"negative"|"neutral"}],
  "highlighted": "<original text with XML-style tags: wrap positive phrases in <pos>...</pos>, negative in <neg>...</neg>, neutral key phrases in <neu>...</neu>",
  "breakdown": {"positive_pct": <int>, "negative_pct": <int>, "neutral_pct": <int>},
  "sarcasm_flag": <boolean>
}

Text: "${t.replace(/"/g, '\\"')}"`;

  const batchPrompt = (t) => `Return ONLY JSON, no markdown: {"overall":"positive"|"negative"|"neutral","confidence":<int>}. Text: "${t.replace(/"/g, '\\"')}"`;

  const callGrok = async (prompt, maxTokens) => {
    const resp = await fetch(GROK_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.XAI_API_KEY}`
      },
      body: JSON.stringify({
        model: GROK_MODEL,
        max_tokens: maxTokens,
        messages: [{ role: 'user', content: prompt }]
      })
    });
    const data = await resp.json();
    if (data.error) throw new Error(data.error.message || JSON.stringify(data.error));
    const raw = (data.choices?.[0]?.message?.content || '').replace(/```json|```/g, '').trim();
    return JSON.parse(raw);
  };

  try {
    if (batch && Array.isArray(batch)) {
      const results = [];
      for (const line of batch) {
        try {
          const r = await callGrok(batchPrompt(line), 300);
          results.push({ line, r });
        } catch (e) {
          results.push({ line, r: { overall: 'unknown', confidence: 0 } });
        }
      }
      return res.json({ results });
    }

    const r = await callGrok(makePrompt(text), 1000);
    res.json(r);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Catch-all — serve the SPA
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Echo Sentiment running on port ${PORT}`));
