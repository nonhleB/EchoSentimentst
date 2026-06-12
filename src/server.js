import express from 'express';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const app = express();

// Render port
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json({ limit: '2mb' }));
app.use(express.static(join(__dirname, '../public')));

// Health check
app.get('/health', (req, res) => {
  res.status(200).send('OK');
});

// API proxy
app.post('/api/analyze', async (req, res) => {
  const { messages, max_tokens = 1000 } = req.body;

  const apiKey = process.env.ANTHROPIC_API_KEY;

  if (!apiKey) {
    return res.status(500).json({
      error: 'ANTHROPIC_API_KEY environment variable is not set.',
    });
    app.get('/debug-env', (req, res) => {
  res.json({
    hasKey: !!process.env.ANTHROPIC_API_KEY,
    keys: Object.keys(process.env)
  });
});
  }

  if (!messages || !Array.isArray(messages)) {
    return res.status(400).json({
      error: 'Invalid messages format',
    });
  }

  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens,
        messages,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      return res.status(response.status).json({
        error: data.error?.message || 'Anthropic API error',
      });
    }

    res.json(data);
  } catch (err) {
    console.error('API proxy error:', err);
    res.status(500).json({
      error: 'Failed to reach Anthropic API',
    });
  }
});

// Start server (Render-safe)
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Echo Sentiment running on port ${PORT}`);
});
