const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const fs = require('fs');
const path = require('path');

const app = express();

const findAvailablePort = async (startPort) => {
  const net = require('net');
  return new Promise((resolve) => {
    const server = net.createServer();
    server.listen(startPort, () => {
      const port = server.address().port;
      server.close(() => resolve(port));
    });
    server.on('error', () => {
      resolve(findAvailablePort(startPort + 1));
    });
  });
};

app.use(helmet());
app.use(cors());
app.use(morgan('combined'));
app.use(express.json());

const dbPath = path.join(__dirname, 'db.json');

const readModels = () => {
  try {
    const data = fs.readFileSync(dbPath, 'utf8');
    return JSON.parse(data).models;
  } catch (error) {
    console.error('Error reading models from db.json:', error);
    return [];
  }
};

const writeModels = (models) => {
  try {
    fs.writeFileSync(dbPath, JSON.stringify({ models }, null, 2), 'utf8');
  } catch (error) {
    console.error('Error writing models to db.json:', error);
  }
};

app.get('/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

app.get('/api/models', (req, res) => {
  const models = readModels();
  res.json(models);
});

app.post('/api/models', (req, res) => {
  const models = readModels();
  const { name, provider, pricing } = req.body;

  if (!name || !provider || !pricing || !pricing.input || !pricing.output) {
    return res.status(400).json({ error: 'Invalid model data provided.' });
  }

  const newModel = {
    id: `${name.toLowerCase().replace(/\s+/g, '-')}-${Date.now()}`,
    name,
    provider,
    pricing: {
      input: parseFloat(pricing.input),
      output: parseFloat(pricing.output)
    }
  };

  models.push(newModel);
  writeModels(models);

  res.status(201).json(newModel);
});

app.get('/api/models/:id', (req, res) => {
  const models = readModels();
  const model = models.find(m => m.id === req.params.id);
  if (!model) {
    return res.status(404).json({ error: 'Model not found' });
  }
  res.json(model);
});

app.get('/api/models/provider/:provider', (req, res) => {
  const models = readModels();
  const providerModels = models.filter(m => 
    m.provider.toLowerCase() === req.params.provider.toLowerCase()
  );
  res.json(providerModels);
});

app.post('/api/calculator/calculate', (req, res) => {
  try {
    const { modelId, inputTokens, outputTokens } = req.body;
    
    if (!modelId || inputTokens === undefined || outputTokens === undefined) {
      return res.status(400).json({ 
        error: 'Missing required fields: modelId, inputTokens, outputTokens' 
      });
    }

    const models = readModels();
    const model = models.find(m => m.id === modelId);
    if (!model) {
      return res.status(404).json({ error: 'Model not found' });
    }

    const inputCost = (inputTokens / 1_000_000) * model.pricing.input;
    const outputCost = (outputTokens / 1_000_000) * model.pricing.output;
    const totalCost = inputCost + outputCost;

    res.json({
      model,
      calculation: {
        inputTokens,
        outputTokens,
        totalTokens: inputTokens + outputTokens,
        inputCost,
        outputCost,
        totalCost
      },
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.post('/api/calculator/batch-calculate', (req, res) => {
  try {
    const { calculations } = req.body;
    
    if (!Array.isArray(calculations)) {
      return res.status(400).json({ error: 'calculations must be an array' });
    }

    const models = readModels();
    const results = calculations.map(calc => {
      const { modelId, inputTokens, outputTokens } = calc;
      const model = models.find(m => m.id === modelId);
      
      if (!model) {
        return { error: `Model ${modelId} not found`, calculation: calc };
      }

      const inputCost = (inputTokens / 1_000_000) * model.pricing.input;
      const outputCost = (outputTokens / 1_000_000) * model.pricing.output;
      const totalCost = inputCost + outputCost;

      return {
        model,
        calculation: {
          inputTokens,
          outputTokens,
          totalTokens: inputTokens + outputTokens,
          inputCost,
          outputCost,
          totalCost
        }
      };
    });

    res.json({
      results,
      summary: {
        totalCalculations: results.length,
        totalCost: results.reduce((sum, r) => sum + (r.calculation?.totalCost || 0), 0)
      },
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.post('/api/calculator/estimate-tokens', (req, res) => {
  try {
    const { text } = req.body;
    
    if (!text) {
      return res.status(400).json({ error: 'Text is required' });
    }

    const estimatedTokens = Math.ceil(text.length / 4);
    
    res.json({
      text: text.substring(0, 100) + (text.length > 100 ? '...' : ''),
      characterCount: text.length,
      estimatedTokens,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

(async () => {
  const finalPort = await findAvailablePort(3001);
  app.listen(finalPort, () => {
    console.log(`🚀 Server running on http://localhost:${finalPort}`);
    console.log(`📊 Health check: http://localhost:${finalPort}/health`);
    console.log(`🤖 Models API: http://localhost:${finalPort}/api/models`);
  });
})();