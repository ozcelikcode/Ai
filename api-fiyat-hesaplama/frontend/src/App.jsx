import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDownIcon, SunIcon, MoonIcon, CalculatorIcon, ClockIcon, CurrencyDollarIcon, PlusCircleIcon } from '@heroicons/react/24/outline'
import { debounce } from 'lodash';

// Try multiple ports for backend
const findBackendURL = async () => {
  const ports = [3001, 3002, 3003, 3004]
  for (const port of ports) {
    try {
      const response = await fetch(`http://localhost:${port}/health`)
      if (response.ok) {
        return `http://localhost:${port}`
      }
    } catch (error) {
      continue
    }
  }
  return 'http://localhost:3001' // fallback
}

let API_BASE_URL = 'http://localhost:3001'

const fadeIn = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 }
}

const staggerChildren = {
  animate: {
    transition: {
      staggerChildren: 0.1
    }
  }
}

function App() {
  const [models, setModels] = useState([])
  const [selectedModel, setSelectedModel] = useState('')
  const [inputTokens, setInputTokens] = useState(1000)
  const [outputTokens, setOutputTokens] = useState(1000)
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [textInput, setTextInput] = useState('')
  const [isDark, setIsDark] = useState(() => {
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  })

  // Custom model form state
  const [showCustomForm, setShowCustomForm] = useState(false)
  const [customModelName, setCustomModelName] = useState('')
  const [customModelProvider, setCustomModelProvider] = useState('')
  const [customInputPrice, setCustomInputPrice] = useState('')
  const [customOutputPrice, setCustomOutputPrice] = useState('')
  const [isSaving, setIsSaving] = useState(false)

  const calculateCost = async () => {
    if (!selectedModel || inputTokens < 0 || outputTokens < 0) return

    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/calculator/calculate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          modelId: selectedModel,
          inputTokens: parseInt(inputTokens),
          outputTokens: parseInt(outputTokens)
        })
      })

      const data = await response.json()
      setResult(data)
      if(data.calculation.totalCost > 0) {
        setHistory(prev => {
          const newHistory = [data, ...prev.filter(item => item.calculation.totalCost !== data.calculation.totalCost)];
          return newHistory.slice(0, 10);
        });
      }
    } catch (error) {
      console.error('Error calculating cost:', error)
    }
    setLoading(false)
  }

  const debouncedCalculateCost = useCallback(debounce(calculateCost, 300), [selectedModel, inputTokens, outputTokens]);

  useEffect(() => {
    debouncedCalculateCost();
    // Cleanup function to cancel any pending debounced calls
    return () => {
      debouncedCalculateCost.cancel();
    };
  }, [selectedModel, inputTokens, outputTokens, debouncedCalculateCost]);


  useEffect(() => {
    initializeAPI()
  }, [])

  const initializeAPI = async () => {
    API_BASE_URL = await findBackendURL()
    fetchModels()
  }

  useEffect(() => {
    document.documentElement.className = isDark ? 'dark' : 'light'
  }, [isDark])

  const fetchModels = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/models`)
      const data = await response.json()
      setModels(data)
      if (data.length > 0 && !selectedModel) {
        setSelectedModel(data[0].id)
      }
    } catch (error) {
      console.error('Error fetching models:', error)
    }
  }

  const handleModelChange = (e) => {
    const value = e.target.value
    if (value === 'add-new') {
      setShowCustomForm(true)
    } else {
      setSelectedModel(value)
      setShowCustomForm(false)
    }
  }

  const handleSaveCustomModel = async () => {
    if (!customModelName || !customModelProvider || customInputPrice === '' || customOutputPrice === '') {
      alert('Please fill all custom model fields.')
      return
    }
    setIsSaving(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/models`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: customModelName,
          provider: customModelProvider,
          pricing: {
            input: parseFloat(customInputPrice),
            output: parseFloat(customOutputPrice)
          }
        })
      })
      const newModel = await response.json()
      await fetchModels() // Refetch all models
      setSelectedModel(newModel.id) // Select the new model
      
      // Reset form
      setShowCustomForm(false)
      setCustomModelName('')
      setCustomModelProvider('')
      setCustomInputPrice('')
      setCustomOutputPrice('')

    } catch (error) {
      console.error('Error saving custom model:', error)
    }
    setIsSaving(false)
  }

  const estimateTokens = async () => {
    if (!textInput.trim()) return

    try {
      const response = await fetch(`${API_BASE_URL}/api/calculator/estimate-tokens`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: textInput })
      })

      const data = await response.json()
      setInputTokens(data.estimatedTokens)
    } catch (error) {
      console.error('Error estimating tokens:', error)
    }
  }

  const loadFromHistory = (item) => {
    setSelectedModel(item.model.id)
    setInputTokens(item.calculation.inputTokens)
    setOutputTokens(item.calculation.outputTokens)
    setResult(item)
    setShowCustomForm(false)
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 6
    }).format(amount)
  }

  const quickTokenSelect = (tokens) => {
    setInputTokens(tokens)
    setOutputTokens(tokens)
  }

  return (
    <div className={isDark ? 'dark' : ''}>
      <div className="min-h-screen gradient-bg transition-all duration-500">
        <motion.header 
          className="glass-effect border-b border-gray-200/20 dark:border-gray-700/20 sticky top-0 z-50"
          initial={{ opacity: 0, y: -50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-4">
              <div className="flex items-center space-x-3">
                <div className="bg-gradient-to-r from-primary-500 to-primary-600 p-2 rounded-lg">
                  <CalculatorIcon className="h-6 w-6 text-white" />
                </div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-primary-600 to-primary-800 bg-clip-text text-transparent">
                  AI API Price Calculator
                </h1>
              </div>
              <motion.button
                className="p-2 rounded-lg glass-effect hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors duration-200"
                onClick={() => setIsDark(!isDark)}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                aria-label="Toggle theme"
              >
                {isDark ? (
                  <SunIcon className="h-5 w-5 text-yellow-500" />
                ) : (
                  <MoonIcon className="h-5 w-5 text-gray-600" />
                )}
              </motion.button>
            </div>
          </div>
        </motion.header>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <motion.div 
            className="grid grid-cols-1 lg:grid-cols-2 gap-8"
            variants={staggerChildren}
            initial="initial"
            animate="animate"
          >
            <motion.div 
              className="glass-effect rounded-2xl p-8 card-hover"
              variants={fadeIn}
            >
              <div className="flex items-center space-x-3 mb-6">
                <CurrencyDollarIcon className="h-6 w-6 text-primary-600" />
                <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">Calculate Costs</h2>
              </div>
              
              <div className="mb-6">
                <label htmlFor="model-select" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  AI Model
                </label>
                <div className="relative">
                  <select
                    id="model-select"
                    value={selectedModel}
                    onChange={handleModelChange}
                    className="input-field appearance-none pr-10 cursor-pointer"
                  >
                    {models.map(model => (
                      <option key={model.id} value={model.id}>
                        {model.name} ({model.provider}) - Input: ${model.pricing.input}/1M, Output: ${model.pricing.output}/1M
                      </option>
                    ))}
                    <option value="add-new" className="font-bold text-primary-600">+ Add New Custom Model...</option>
                  </select>
                  <ChevronDownIcon className="absolute right-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400 pointer-events-none" />
                </div>
              </div>

              <AnimatePresence>
                {showCustomForm && (
                  <motion.div
                    className="bg-gradient-to-br from-gray-50/50 to-white/50 dark:from-gray-800/30 dark:to-gray-900/30 rounded-xl p-6 mb-6 border border-primary-300/50 dark:border-primary-700/50"
                    initial={{ opacity: 0, height: 0, y: -20 }}
                    animate={{ opacity: 1, height: 'auto', y: 0 }}
                    exit={{ opacity: 0, height: 0, y: -20 }}
                    transition={{ duration: 0.3 }}
                  >
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center"><PlusCircleIcon className="h-6 w-6 mr-2 text-primary-600"/>Add a New Model</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                      <div>
                        <label htmlFor="custom-model-name" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Model Name</label>
                        <input id="custom-model-name" type="text" value={customModelName} onChange={(e) => setCustomModelName(e.target.value)} className="input-field" placeholder="e.g., My-GPT-1"/>
                      </div>
                      <div>
                        <label htmlFor="custom-model-provider" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Provider</label>
                        <input id="custom-model-provider" type="text" value={customModelProvider} onChange={(e) => setCustomModelProvider(e.target.value)} className="input-field" placeholder="e.g., MyCompany"/>
                      </div>
                      <div>
                        <label htmlFor="custom-input-price" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Input Price / 1M ($)</label>
                        <input id="custom-input-price" type="number" min="0" step="0.01" value={customInputPrice} onChange={(e) => setCustomInputPrice(e.target.value)} className="input-field" placeholder="e.g., 0.50"/>
                      </div>
                      <div>
                        <label htmlFor="custom-output-price" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Output Price / 1M ($)</label>
                        <input id="custom-output-price" type="number" min="0" step="0.01" value={customOutputPrice} onChange={(e) => setCustomOutputPrice(e.target.value)} className="input-field" placeholder="e.g., 1.50"/>
                      </div>
                    </div>
                    <div className="flex justify-end gap-3">
                       <motion.button onClick={() => setShowCustomForm(false)} className="button-secondary px-4 py-2" whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>Cancel</motion.button>
                       <motion.button onClick={handleSaveCustomModel} disabled={isSaving} className="button-primary px-4 py-2 disabled:opacity-50" whileHover={{ scale: isSaving ? 1 : 1.05 }} whileTap={{ scale: isSaving ? 1 : 0.95 }}>
                         {isSaving ? 'Saving...' : 'Save Model'}
                       </motion.button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              <div className="bg-gradient-to-br from-gray-50/50 to-white/50 dark:from-gray-800/30 dark:to-gray-900/30 rounded-xl p-6 mb-6 border border-gray-200/50 dark:border-gray-700/50">
                <div className="mb-6">
                  <label htmlFor="input-tokens" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                    Input Tokens: <span className="text-primary-600 font-semibold">{inputTokens.toLocaleString()}</span>
                  </label>
                  <input
                    id="input-tokens"
                    type="range"
                    min="0"
                    max="100000"
                    value={inputTokens}
                    onChange={(e) => setInputTokens(parseInt(e.target.value))}
                    className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer mb-3"
                    style={{
                      background: `linear-gradient(to right, #3B82F6 0%, #3B82F6 ${(inputTokens/100000)*100}%, #e5e7eb ${(inputTokens/100000)*100}%, #e5e7eb 100%)`
                    }}
                  />
                  <input
                    type="number"
                    min="0"
                    value={inputTokens}
                    onChange={(e) => setInputTokens(parseInt(e.target.value) || 0)}
                    className="input-field mt-2"
                    placeholder="Enter token count"
                  />
                </div>

                <div className="mb-6">
                  <label htmlFor="output-tokens" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                    Output Tokens: <span className="text-primary-600 font-semibold">{outputTokens.toLocaleString()}</span>
                  </label>
                  <input
                    id="output-tokens"
                    type="range"
                    min="0"
                    max="100000"
                    value={outputTokens}
                    onChange={(e) => setOutputTokens(parseInt(e.target.value))}
                    className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer mb-3"
                    style={{
                      background: `linear-gradient(to right, #10B981 0%, #10B981 ${(outputTokens/100000)*100}%, #e5e7eb ${(outputTokens/100000)*100}%, #e5e7eb 100%)`
                    }}
                  />
                  <input
                    type="number"
                    min="0"
                    value={outputTokens}
                    onChange={(e) => setOutputTokens(parseInt(e.target.value) || 0)}
                    className="input-field mt-2"
                    placeholder="Enter token count"
                  />
                </div>

                <div className="">
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Quick Select:</p>
                  <div className="flex flex-wrap gap-2">
                    {[1000, 5000, 10000, 50000].map(tokens => (
                      <motion.button
                        key={tokens}
                        onClick={() => quickTokenSelect(tokens)}
                        className="button-secondary text-xs px-3 py-2 rounded-md"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                      >
                        {tokens.toLocaleString()}
                      </motion.button>
                    ))}
                  </div>
                </div>
              </div>

              <div className="mb-6">
                <label htmlFor="text-estimate" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Text Estimation (Optional)
                </label>
                <textarea
                  id="text-estimate"
                  placeholder="Enter your text here to estimate input tokens automatically..."
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  className="input-field resize-none"
                  rows="4"
                />
                <motion.button
                  onClick={estimateTokens}
                  disabled={!textInput.trim()}
                  className="button-secondary mt-3 w-full disabled:opacity-50 disabled:cursor-not-allowed"
                  whileHover={{ scale: !textInput.trim() ? 1 : 1.02 }}
                  whileTap={{ scale: !textInput.trim() ? 1 : 0.98 }}
                >
                  Estimate Tokens
                </motion.button>
              </div>
            </motion.div>

            <AnimatePresence>
              {result && (
                <motion.div 
                  className="glass-effect rounded-2xl p-8 card-hover"
                  variants={fadeIn}
                  initial="initial"
                  animate="animate"
                  exit="exit"
                >
                  <div className="flex items-center space-x-3 mb-6">
                    <CurrencyDollarIcon className="h-6 w-6 text-green-600" />
                    <h3 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">Cost Breakdown</h3>
                  </div>
                  
                  <div className="bg-gradient-to-r from-primary-500 to-primary-600 rounded-xl p-6 mb-6 text-white">
                    <div className="flex justify-between items-center">
                      <div>
                        <h4 className="text-xl font-bold">{result.model.name}</h4>
                        <span className="text-primary-100 text-sm">{result.model.provider}</span>
                      </div>
                      <div className="text-right">
                        <div className="flex items-center justify-end">
                          {loading && <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent mr-2"></div>}
                          <div className="text-3xl font-bold">{formatCurrency(result.calculation.totalCost)}</div>
                        </div>
                        <div className="text-primary-100 text-sm">Total Cost</div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4">
                      <div className="flex justify-between items-center py-2">
                        <span className="text-gray-600 dark:text-gray-300 font-medium">Input Tokens:</span>
                        <span className="text-gray-900 dark:text-gray-100 font-semibold">{result.calculation.inputTokens.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between items-center py-2 border-t border-gray-200 dark:border-gray-700">
                        <span className="text-gray-600 dark:text-gray-300 font-medium">Output Tokens:</span>
                        <span className="text-gray-900 dark:text-gray-100 font-semibold">{result.calculation.outputTokens.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between items-center py-2 border-t border-gray-200 dark:border-gray-700">
                        <span className="text-gray-600 dark:text-gray-300 font-medium">Total Tokens:</span>
                        <span className="text-gray-900 dark:text-gray-100 font-semibold">{result.calculation.totalTokens.toLocaleString()}</span>
                      </div>
                    </div>
                    
                    <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4">
                      <div className="flex justify-between items-center py-2">
                        <span className="text-gray-600 dark:text-gray-300 font-medium">Input Cost:</span>
                        <span className="text-blue-600 dark:text-blue-400 font-semibold">{formatCurrency(result.calculation.inputCost)}</span>
                      </div>
                      <div className="flex justify-between items-center py-2 border-t border-gray-200 dark:border-gray-700">
                        <span className="text-gray-600 dark:text-gray-300 font-medium">Output Cost:</span>
                        <span className="text-green-600 dark:text-green-400 font-semibold">{formatCurrency(result.calculation.outputCost)}</span>
                      </div>
                      <div className="flex justify-between items-center py-3 border-t-2 border-gray-300 dark:border-gray-600 mt-2">
                        <span className="text-lg font-bold text-gray-900 dark:text-gray-100">Total Cost:</span>
                        <span className="text-2xl font-bold text-primary-600">{formatCurrency(result.calculation.totalCost)}</span>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            <AnimatePresence>
              {history.length > 0 && (
                <motion.div 
                  className="glass-effect rounded-2xl p-8 card-hover lg:col-span-2"
                  variants={fadeIn}
                  initial="initial"
                  animate="animate"
                  exit="exit"
                >
                  <div className="flex items-center space-x-3 mb-6">
                    <ClockIcon className="h-6 w-6 text-gray-600 dark:text-gray-400" />
                    <h3 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">Recent Calculations</h3>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {history.slice(0, 6).map((item, index) => (
                      <motion.div
                        key={index}
                        className="bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl p-4 cursor-pointer transition-all duration-200 hover:shadow-lg hover:scale-105 hover:border-primary-300 dark:hover:border-primary-600"
                        onClick={() => loadFromHistory(item)}
                        whileHover={{ y: -2 }}
                        whileTap={{ scale: 0.98 }}
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: index * 0.1 }}
                      >
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <h4 className="font-semibold text-gray-900 dark:text-gray-100 text-sm">{item.model.name}</h4>
                            <p className="text-xs text-gray-500 dark:text-gray-400">{item.model.provider}</p>
                          </div>
                          <div className="text-right">
                            <div className="font-bold text-primary-600 text-lg">{formatCurrency(item.calculation.totalCost)}</div>
                          </div>
                        </div>
                        <div className="text-xs text-gray-600 dark:text-gray-300 space-y-1">
                          <div className="flex justify-between">
                            <span>Input:</span>
                            <span className="font-medium">{item.calculation.inputTokens.toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Output:</span>
                            <span className="font-medium">{item.calculation.outputTokens.toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between pt-1 border-t border-gray-200 dark:border-gray-600">
                            <span>Total:</span>
                            <span className="font-semibold">{item.calculation.totalTokens.toLocaleString()}</span>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </main>

        <motion.footer 
          className="glass-effect border-t border-gray-200/20 dark:border-gray-700/20 mt-16"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <p className="text-center text-gray-600 dark:text-gray-400 text-sm">
              Built with ❤️ using React + Vite + Express + Tailwind CSS
            </p>
          </div>
        </motion.footer>
      </div>
    </div>
  )
}

export default App
