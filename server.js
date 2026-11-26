
const express = require('express');
const path = require('path');
const app = express();

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Groq API configuration
const GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions';
const GROQ_MODEL = 'llama-3.3-70b-versatile';

// Sentiment analysis endpoint
app.post('/api/analyze', async (req, res) => {
  const { text, batch } = req.body;

  if (!process.env.GROQ_API_KEY) {
    return res.status(500).json({
      error: 'GROQ_API_KEY not set in environment variables.'
    });
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

  const callGroq = async (prompt, maxTokens) => {
    const resp = await fetch(GROQ_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.GROQ_API_KEY}`
      },
      body: JSON.stringify({
        model: GROQ_MODEL,
        max_tokens: maxTokens,
        messages: [
          {
            role: 'user',
            content: prompt
          }
        ]
      })
    });

    const data = await resp.json();

    if (!resp.ok) {
      throw new Error(
        `Groq API Error ${resp.status}: ${JSON.stringify(data)}`
      );
    }

    const raw = (
      data.choices?.[0]?.message?.content || ''
    ).replace(/```json|```/g, '').trim();

    if (!raw) {
      throw new Error('Groq returned an empty response.');
    }

    return JSON.parse(raw);
  };

  try {
    if (batch && Array.isArray(batch)) {
      const results = [];

      for (const line of batch) {
        try {
          const r = await callGroq(batchPrompt(line), 300);
          results.push({ line, r });
        } catch (e) {
          console.error('Batch analysis error:', e.message);
          results.push({
            line,
            r: { overall: 'unknown', confidence: 0 }
          });
        }
      }

      return res.json({ results });
    }

    if (typeof text !== 'string' || !text.trim()) {
      return res.status(400).json({
        error: 'Please provide text to analyze.'
      });
    }

    const r = await callGroq(makePrompt(text), 1000);

    return res.json(r);

  } catch (err) {
    console.error('Sentiment analysis error:', err.message);

    return res.status(500).json({
      error: err.message
    });
  }
});

// Serve the frontend
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  console.log(`Echo Sentiment running on port ${PORT}`);
  console.log(`Groq API configured: ${!!process.env.GROQ_API_KEY}`);
});


const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Echo Sentiment running on port ${PORT}`));
