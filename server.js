const express = require('express');
const path = require('path');
const app = express();

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Proxy endpoint — keeps the API key server-side
app.post('/api/analyze', async (req, res) => {
  const { text, batch } = req.body;

  if (!process.env.ANTHROPIC_API_KEY) {
    return res.status(500).json({ error: 'ANTHROPIC_API_KEY not set in environment variables.' });
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

  try {
    if (batch && Array.isArray(batch)) {
      // Batch mode: sequential calls
      const results = [];
      for (const line of batch) {
        const resp = await fetch('https://api.anthropic.com/v1/messages', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'x-api-key': process.env.ANTHROPIC_API_KEY,
            'anthropic-version': '2023-06-01'
          },
          body: JSON.stringify({
            model: 'claude-sonnet-4-6',
            max_tokens: 300,
            messages: [{ role: 'user', content: batchPrompt(line) }]
          })
        });
        const data = await resp.json();
        if (data.error) { results.push({ line, r: { overall: 'unknown', confidence: 0 } }); continue; }
        const raw = data.content.map(i => i.text || '').join('').replace(/```json|```/g, '').trim();
        results.push({ line, r: JSON.parse(raw) });
      }
      return res.json({ results });
    }

    // Single analysis
    const resp = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': process.env.ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-6',
        max_tokens: 1000,
        messages: [{ role: 'user', content: makePrompt(text) }]
      })
    });

    const data = await resp.json();
    if (data.error) return res.status(500).json({ error: data.error.message });
    const raw = data.content.map(i => i.text || '').join('').replace(/```json|```/g, '').trim();
    res.json(JSON.parse(raw));
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
