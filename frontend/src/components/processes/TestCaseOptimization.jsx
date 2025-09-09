import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const TestCaseOptimization = ({ onPromptChange, onRunFunction, onLoadingChange, onRunningStateChange, onOptimizationResults }) => {
  const [processTitles, setProcessTitles] = useState([]);
  const [selectedProcessTitles, setSelectedProcessTitles] = useState([]);
  const [testCases, setTestCases] = useState([]);
  const [selectedTestCases, setSelectedTestCases] = useState(new Set());
  const [optimizationResults, setOptimizationResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [existingResults, setExistingResults] = useState(null);
  
  // New states for enhanced optimization
  const [optimizationType, setOptimizationType] = useState('individual');
  const [selectedModel, setSelectedModel] = useState('');
  const [availableModels, setAvailableModels] = useState([]);
  const [apiKey, setApiKey] = useState('');
  const [processName, setProcessName] = useState('');

  // Process tracking states
  const [currentProcessId, setCurrentProcessId] = useState(null);
  const [isRunning, setIsRunning] = useState(false);

  // Available models for test case optimization
  const modelsList = [
    // Original models
    {
      key: "codegeex4:9b",
      name: "CodeGeeX4 9B",
      description: "Multilingual code generation with 9B parameters"
    },
    {
      key: "codellama:7b",
      name: "CodeLlama 7B",
      description: "Meta's code generation model with 7B parameters"
    },
    {
      key: "deepseek-coder:6.7b",
      name: "DeepSeek Coder 6.7B",
      description: "Specialized for code analysis and generation"
    },
    {
      key: "gemma2:2b",
      name: "Gemma2 2B",
      description: "Google's lightweight model for code tasks"
    },
    {
      key: "gemma3:4b",
      name: "Gemma3 4B",
      description: "Enhanced Gemma model with 4B parameters"
    },
    {
      key: "google/gemma-3-12b",
      name: "Google Gemma 3 12B",
      description: "Large Gemma model for complex tasks"
    },
    {
      key: "llama3.2:3b",
      name: "Llama 3.2 3B",
      description: "Fast and efficient 3B parameter model"
    },
    {
      key: "llama-3.2-3b-instruct",
      name: "Llama 3.2 3B Instruct",
      description: "Instruction-tuned version of Llama 3.2 3B"
    },
    {
      key: "meta/llama-3.3-70b",
      name: "Meta Llama 3.3 70B",
      description: "Large language model with 70B parameters"
    },
    {
      key: "mistralai/codestral-22b-v0.1",
      name: "Mistral Codestral 22B",
      description: "Specialized for code generation and analysis"
    },
    {
      key: "openai/gpt-oss-20b",
      name: "GPT OSS 20B",
      description: "Open-source GPT model with 20B parameters"
    },
    {
      key: "qwen/qwq-32b",
      name: "Qwen QwQ 32B",
      description: "Reasoning-focused model for complex problem solving"
    },
    {
      key: "qwen2.5:7b",
      name: "Qwen 2.5 7B",
      description: "Multilingual model for code generation"
    },
    {
      key: "qwen2.5:7b-1m",
      name: "Qwen 2.5 7B (1M context)",
      description: "Extended context version for large content"
    },
    {
      key: "qwen2.5-coder:3b",
      name: "Qwen 2.5 Coder 3B",
      description: "Lightweight model for code completion"
    },
    {
      key: "qwen/qwen3-14b",
      name: "Qwen 3 14B",
      description: "Advanced reasoning and code analysis"
    },
    {
      key: "stable-code:3b",
      name: "Stable Code 3B",
      description: "Stable and reliable code generation"
    },
    {
      key: "starcoder2:7b",
      name: "StarCoder2 7B",
      description: "Advanced code generation and analysis"
    },
    // New models added for Test Case Optimization
    {
      key: "codellama:70b-instruct",
      name: "CodeLlama 70B Instruct",
      description: "Large instruction-following model for complex code analysis"
    },
    {
      key: "kimi-dev:72b",
      name: "Kimi Dev 72B",
      description: "Development-focused model with 72B parameters"
    },
    {
      key: "openai/gpt-oss-120b",
      name: "GPT OSS 120B",
      description: "Massive open-source model for complex reasoning"
    },
    {
      key: "deepseek-r1-distill:32b",
      name: "DeepSeek R1 Distill 32B",
      description: "Distilled reasoning model for analytical tasks"
    },
    {
      key: "google/gemma-3-27b",
      name: "Google Gemma 3 27B",
      description: "Large Gemma model for detailed analysis (may be slow)"
    },
    {
      key: "qwen/qwen3-coder-30b",
      name: "Qwen 3 Coder 30B",
      description: "Advanced coding model with 30B parameters (may be slow)"
    },
    {
      key: "deepseek/deepseek-r1-qwen3-8b",
      name: "DeepSeek R1 Qwen3 8B",
      description: "Reasoning-optimized model based on Qwen 3"
    }
  ];

  // Default prompts for each optimization type
  const defaultPrompts = {
    individual: `You are given two test cases, each with a certain set of fields:
- Title
- Description
- Objective

You will decide whether these two test cases are "contextually the same" based on the following criteria:

1. If both have the same Title (case-insensitive) OR their Titles are substantially similar in meaning,
2. AND they have either the same or very similar Description and/or Objective,
3. AND they serve essentially the same testing purpose for the same or very closely related scenarios,
4. THEN you should conclude that these two test cases are the same.
5. The order of importance Description > Objective > Title.

Otherwise, they are considered different.

Return your response **only** in valid JSON with the following format:

{
  "is_same": <true or false>
}

Where:
- is_same = true if the test cases meet the criteria above
- is_same = false otherwise

Important:
- Do not provide any additional text outside the JSON object.
- Do not explain your reasoning, only provide the final JSON response.`,
    bulk: `You are an expert test case analyst. Your task is to analyze ALL provided test cases in a single operation and identify duplicate/similar test cases efficiently.

ANALYSIS CRITERIA:
1. Test cases are considered DUPLICATES if they have:
   - Same or substantially similar Title (case-insensitive)
   - AND very similar Description and/or Objective
   - AND serve essentially the same testing purpose
2. Priority order for comparison: Description > Objective > Title
3. Consider contextual similarity, not just exact text matches

OPTIMIZATION APPROACH:
- Analyze the complete set of test cases holistically
- Group similar test cases and select the best representative for each group
- Preserve unique test cases that serve distinct testing purposes
- Ensure comprehensive coverage while eliminating redundancy

Return your response **only** in valid JSON with the following format:

{
  "unique_indices": [0, 2, 5, ...],
  "duplicate_groups": [
    {
      "representative_index": 0,
      "duplicate_indices": [3, 7, 12]
    },
    {
      "representative_index": 2,
      "duplicate_indices": [8, 15]
    }
  ]
}

Where:
- unique_indices: Array of indices representing unique test cases (including representatives from duplicate groups)
- duplicate_groups: Array of groups where each group has a representative and its duplicates
- representative_index: The index of the test case chosen as the representative for a duplicate group
- duplicate_indices: Array of indices that are duplicates of the representative

IMPORTANT:
- Do not provide any additional text outside the JSON object
- Each test case should appear in either unique_indices or as part of a duplicate group, but not both
- Representatives should also be included in unique_indices
- Ensure all test case indices are accounted for in the response`
  };

  // Get current prompt based on optimization type
  const getCurrentPrompt = useCallback(() => {
    return defaultPrompts[optimizationType] || defaultPrompts.individual;
  }, [optimizationType]);

  // Component mount edildiğinde process title'ları ve modelleri getir
  useEffect(() => {
    fetchProcessTitles();
    fetchAvailableModels();
    // İlk render'da default prompt'u bildir
    if (onPromptChange) {
      onPromptChange(getCurrentPrompt());
    }
  }, [onPromptChange]);

  // Process titles değiştiğinde test case'leri getir
  useEffect(() => {
    if (selectedProcessTitles.length > 0) {
      fetchTestCasesMultiple(selectedProcessTitles);
      // Multi-select durumunda existing results check etmiyoruz
      setExistingResults(null);
    } else {
      setTestCases([]);
      setExistingResults(null);
    }
  }, [selectedProcessTitles]);

  // Optimization type değiştiğinde prompt'u güncelle
  useEffect(() => {
    if (onPromptChange) {
      onPromptChange(getCurrentPrompt());
    }
  }, [optimizationType, onPromptChange, getCurrentPrompt]);

  // runSmartSelection fonksiyonunu parent'a expose et
  useEffect(() => {
    console.log('TestCaseOptimization - useEffect triggered for validation');
    
    if (onRunFunction) {
      // Validasyon logic'i
      const canRun = selectedTestCases.size > 0 && 
                    selectedProcessTitles.length > 0 && 
                    selectedModel && 
                    processName.trim() !== '' && 
                    !(selectedModel.toLowerCase().includes('gemini') && !apiKey.trim());
      
      console.log('TestCaseOptimization - Form validation:', {
        selectedTestCases: selectedTestCases.size,
        selectedProcessTitles: selectedProcessTitles.length,
        selectedModel: selectedModel,
        processName: processName.trim(),
        apiKey: apiKey.trim(),
        isGeminiModel: selectedModel.toLowerCase().includes('gemini'),
        canRun: canRun,
        isRunning: isRunning
      });
      
      // isRunning durumunda da buton aktif olmalı (stop için)
      // canRun = true olduğunda ya da isRunning = true olduğunda buton aktif
      if (canRun || isRunning) {
        if (isRunning) {
          console.log('TestCaseOptimization - Sending stopProcess function to parent');
          onRunFunction(stopProcess);
        } else {
          console.log('TestCaseOptimization - Sending runSmartSelection function to parent');
          onRunFunction(runSmartSelection);
        }
      } else {
        console.log('TestCaseOptimization - Sending null to parent (validation failed)');
        onRunFunction(null);
      }
    } else {
      console.log('TestCaseOptimization - onRunFunction prop not available');
    }
  }, [onRunFunction, selectedTestCases.size, selectedProcessTitles.length, selectedModel, processName, apiKey, isRunning]);

  // isRunning state değişikliklerini parent'a bildir
  useEffect(() => {
    if (onRunningStateChange) {
      onRunningStateChange(isRunning);
    }
  }, [isRunning]); // onRunningStateChange'i dependency'den çıkardık

  // Loading durumunu parent'a bildir
  useEffect(() => {
    if (onLoadingChange) {
      onLoadingChange(loading || isRunning);
    }
  }, [loading, isRunning]); // onLoadingChange'i dependency'den çıkardık

  const fetchProcessTitles = async () => {
    try {
      setLoading(true);
      const response = await axios.get('http://localhost:8000/api/test-case-optimization/process-titles-with-counts');
      if (response.data.success) {
        setProcessTitles(response.data.data);
      }
    } catch (err) {
      setError('Failed to fetch process titles: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailableModels = async () => {
    try {
      console.log('TestCaseOptimization - Initializing available models from static list');
      setAvailableModels(modelsList);
      
      // Set default model if none selected
      if (!selectedModel && modelsList.length > 0) {
        setSelectedModel(modelsList[0].key);
      }
      
      console.log('TestCaseOptimization - Available models loaded:', modelsList.length);
    } catch (err) {
      console.error('Failed to fetch models:', err.message);
      // Fallback to static list
      setAvailableModels(modelsList);
    }
  };

  const fetchTestCasesMultiple = async (processTitles) => {
    try {
      setLoading(true);
      const response = await axios.post('http://localhost:8000/api/test-case-optimization/test-cases-multi-process', {
        process_titles: processTitles
      });
      if (response.data.success) {
        setTestCases(response.data.data);
        setSelectedTestCases(new Set()); // Reset selection
        
        // Debug bilgisi ekle
        const backendUniqueKeys = new Set(response.data.data.map(tc => tc.unique_key));
        console.log(`Fetched ${response.data.data.length} test cases from ${processTitles.length} processes with ${backendUniqueKeys.size} unique backend keys`);
        
        // Eğer backend unique key sayısı test case sayısından farklıysa duplicate var demektir
        if (backendUniqueKeys.size !== response.data.data.length) {
          console.warn('Warning: Some test cases have duplicate unique_key values from backend!');
        }
        
        // Frontend için unique key'leri oluştur
        const frontendUniqueKeys = new Set(response.data.data.map((tc, index) => getUniqueKey(tc, index)));
        console.log(`Frontend will use ${frontendUniqueKeys.size} unique keys for ${response.data.data.length} test cases`);
      }
    } catch (err) {
      setError('Failed to fetch test cases: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Her test case için gerçekten unique bir key oluşturur
  const getUniqueKey = (testCase, index) => {
    // Her test case için index dahil unique key oluştur
    if (testCase.TestCaseID && testCase.ScenarioID) {
      const key = `${testCase.ScenarioID}_${testCase.TestCaseID}_${index}`;
      return key;
    }
    // Fallback: unique_key varsa onu kullan, ama index'i de ekle
    const key = testCase.unique_key ? `${testCase.unique_key}_${index}` : `tc_${index}`;
    return key;
  };

  const handleTestCaseSelection = (testCase, index, isChecked) => {
    const newSelected = new Set(selectedTestCases);
    const uniqueKey = getUniqueKey(testCase, index);
    
    if (isChecked) {
      newSelected.add(uniqueKey);
    } else {
      newSelected.delete(uniqueKey);
    }
    
    setSelectedTestCases(newSelected);
  };

  const handleSelectAll = () => {
    // Tüm test case'ler için tutarlı key'ler oluştur
    const allKeys = new Set(
      testCases.map((tc, index) => getUniqueKey(tc, index))
    );
    
    console.log('handleSelectAll debug:');
    console.log('- testCases.length:', testCases.length);
    console.log('- allKeys.size:', allKeys.size);
    console.log('- selectedTestCases.size:', selectedTestCases.size);
    console.log('- allKeys:', Array.from(allKeys));
    console.log('- selectedTestCases:', Array.from(selectedTestCases));
    
    if (selectedTestCases.size === allKeys.size && allKeys.size === testCases.length) {
      // Tümü seçiliyse, hepsini kaldır
      setSelectedTestCases(new Set());
      console.log('- Action: Deselecting all');
    } else {
      // Hiçbiri veya bazıları seçiliyse, hepsini seç
      setSelectedTestCases(allKeys);
      console.log('- Action: Selecting all, new size will be:', allKeys.size);
    }
  };

  const handleDeselectAll = () => {
    setSelectedTestCases(new Set());
  };

  const runSmartSelection = async () => {
    if (selectedTestCases.size === 0) {
      setError('Please select at least one test case');
      return;
    }

    if (selectedProcessTitles.length === 0) {
      setError('Please select at least one process title');
      return;
    }

    if (!selectedModel) {
      setError('Please select a model');
      return;
    }

    if (!processName.trim()) {
      setError('Please enter a process name');
      return;
    }

    // Check if Gemini model is selected and API key is required
    const isGeminiModel = selectedModel.toLowerCase().includes('gemini');
    if (isGeminiModel && !apiKey.trim()) {
      setError('API key is required for Gemini models');
      return;
    }

    try {
      setLoading(true);
      setIsRunning(true);
      setError(null);
      
      // Seçilen test case'leri filtrele
      const selectedTestCaseData = testCases.filter((tc, index) => {
        const uniqueKey = getUniqueKey(tc, index);
        return selectedTestCases.has(uniqueKey);
      });
      
      console.log(`Running ${optimizationType} optimization on ${selectedTestCaseData.length} test cases out of ${testCases.length} total test cases`);
      console.log(`Selected test case keys:`, Array.from(selectedTestCases));
      console.log(`Available test case keys:`, testCases.map((tc, index) => getUniqueKey(tc, index)));
      
      const requestData = {
        selected_test_cases: selectedTestCaseData,
        process_titles: selectedProcessTitles,
        process_name: processName,
        selected_model: selectedModel,
        optimization_type: optimizationType,
        api_key: apiKey.trim() || undefined
      };

      const response = await axios.post('http://localhost:8000/api/test-case-optimization/smart-selection', requestData);

      console.log('Smart selection response:', response.data);

      if (response.data.success) {
        setOptimizationResults(response.data.data);
        setExistingResults(response.data.data); // Update existing results
        
        // Pass results to sidebar via callback
        if (onOptimizationResults) {
          onOptimizationResults(response.data.data);
        }
        
        // Store process ID for potential stopping
        if (response.data.process_id) {
          console.log(`Process started with ID: ${response.data.process_id}`);
          setCurrentProcessId(response.data.process_id);
        } else {
          console.warn('No process_id received from backend');
        }
      } else {
        // Enhanced error handling for bulk optimization errors
        const errorMessage = response.data.message || 'Smart selection failed';
        const errorType = response.data.error_type;
        
        let displayMessage = errorMessage;
        
        if (errorType === 'bulk_validation_error') {
          displayMessage = `Bulk Optimization Error: ${errorMessage}. This usually happens when LLM returns invalid JSON format or empty response.`;
        } else if (errorType === 'bulk_runtime_error') {
          displayMessage = `Bulk Optimization Runtime Error: ${errorMessage}. Please check your LLM connection and model configuration.`;
        }
        
        setError(displayMessage);
      }
    } catch (err) {
      if (err.response?.status === 400 && err.response?.data?.message?.includes('stopped')) {
        setError('Process was stopped by user');
      } else {
        setError('Failed to run smart selection: ' + err.message);
      }
    } finally {
      setLoading(false);
      setIsRunning(false);
      setCurrentProcessId(null);
    }
  };

  const stopProcess = async () => {
    if (!currentProcessId) {
      console.log('No active process to stop');
      return;
    }

    // Confirmation dialog
    const confirmed = window.confirm(
      'Are you sure you want to stop the test case optimization process?\n\n' +
      'This will interrupt the current optimization and you may lose progress.'
    );

    if (!confirmed) {
      console.log('Process stop cancelled by user');
      return;
    }

    try {
      console.log(`Attempting to stop process: ${currentProcessId}`);
      const response = await axios.post(`http://localhost:8000/api/test-case-optimization/stop-process/${currentProcessId}`);
      
      if (response.data.success) {
        console.log('Process stopped successfully');
        setError('Process stopped by user');
        // Force reset states
        setLoading(false);
        setIsRunning(false);
        setCurrentProcessId(null);
      } else {
        console.error('Failed to stop process:', response.data.message);
        setError('Failed to stop process: ' + response.data.message);
      }
    } catch (err) {
      console.error('Error stopping process:', err);
      setError('Error stopping process: ' + err.message);
      // Force reset states even on error
      setLoading(false);
      setIsRunning(false);
      setCurrentProcessId(null);
    }
  };

  const downloadResults = (data, filename) => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Test Case Optimization</h2>
        
        {/* Process Title Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Process Titles
          </label>
          <div className="space-y-2 max-h-48 overflow-y-auto border border-gray-300 rounded-md p-3">
            {processTitles.map((processData, index) => (
              <div key={index} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id={`process-${index}`}
                    checked={selectedProcessTitles.includes(processData.process_title)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedProcessTitles(prev => [...prev, processData.process_title]);
                      } else {
                        setSelectedProcessTitles(prev => prev.filter(title => title !== processData.process_title));
                      }
                    }}
                    className="h-4 w-4 text-indigo-600 rounded border-gray-300"
                    disabled={loading}
                  />
                  <label htmlFor={`process-${index}`} className="ml-3 text-sm font-medium text-gray-700">
                    {processData.process_title}
                  </label>
                </div>
                <div className="text-xs text-gray-500">
                  {processData.test_case_count} test cases
                </div>
              </div>
            ))}
          </div>
          {selectedProcessTitles.length > 0 && (
            <p className="mt-2 text-sm text-gray-600">
              Selected: {selectedProcessTitles.length} process(es)
            </p>
          )}
        </div>

        {/* Optimization Process Name */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Optimization Process Name *
          </label>
          <input
            type="text"
            value={processName}
            onChange={(e) => setProcessName(e.target.value)}
            placeholder="Enter a name for this optimization process"
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            disabled={loading}
          />
          <p className="mt-1 text-sm text-gray-500">
            This name will help you identify this optimization in your session history.
          </p>
        </div>

        {/* Optimization Type Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Optimization Method
          </label>
          <div className="space-y-3">
            <div className="flex items-center">
              <input
                id="individual-optimization"
                name="optimization-type"
                type="radio"
                value="individual"
                checked={optimizationType === 'individual'}
                onChange={(e) => setOptimizationType(e.target.value)}
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
                disabled={loading}
              />
              <label htmlFor="individual-optimization" className="ml-3 block text-sm text-gray-700">
                <span className="font-medium">Individual Comparison</span>
                <span className="block text-gray-500 text-xs mt-1">
                  Compare each test case pair individually (1-1 comparisons). More accurate but slower for large datasets. Uses multiple LLM calls.
                </span>
              </label>
            </div>
            <div className="flex items-center">
              <input
                id="bulk-optimization"
                name="optimization-type"
                type="radio"
                value="bulk"
                checked={optimizationType === 'bulk'}
                onChange={(e) => setOptimizationType(e.target.value)}
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
                disabled={loading}
              />
              <label htmlFor="bulk-optimization" className="ml-3 block text-sm text-gray-700">
                <span className="font-medium">Bulk Optimization</span>
                <span className="block text-gray-500 text-xs mt-1">
                  Analyze all test cases in a single operation. Faster and more resource-efficient. Uses only ONE LLM call for all test cases.
                </span>
              </label>
            </div>
          </div>
          <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-md">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-blue-700">
                  <strong>Recommendation:</strong> Use <strong>Bulk Optimization</strong> for faster processing when you have many test cases. 
                  Use <strong>Individual Comparison</strong> for maximum accuracy with smaller datasets.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Model Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Model *
          </label>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            disabled={loading}
          >
            <option value="">Select a Model</option>
            {availableModels.map((model) => (
              <option key={model.key} value={model.key}>
                {model.name} - {model.description}
              </option>
            ))}
          </select>
        </div>

        {/* API Key for external models */}
        {selectedModel && selectedModel.toLowerCase().includes('gemini') && (
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              API Key *
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Enter your API key for external models"
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              disabled={loading}
            />
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Test Cases Section */}
        {testCases.length > 0 && (
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-800">Test Cases</h3>
              <div className="text-sm text-gray-600">
                From {selectedProcessTitles.length} process(es): {selectedProcessTitles.join(', ')}
              </div>
            </div>
            
            {/* Select All/Deselect All Buttons */}
            <div className="flex gap-2 mb-4">
              <button
                onClick={handleSelectAll}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                disabled={loading}
              >
                {selectedTestCases.size === testCases.length && testCases.length > 0 ? 'Deselect All' : 'Select All'}
              </button>
              <button
                onClick={handleDeselectAll}
                className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
                disabled={loading}
              >
                Deselect All
              </button>
            </div>
            
            {/* Test Cases List */}
            <div className="max-h-96 overflow-y-auto border border-gray-200 rounded-md">
              {testCases.map((testCase, index) => {
                // Tutarlı unique key oluştur
                const uniqueKey = getUniqueKey(testCase, index);
                const renderKey = `${uniqueKey}_${index}`;
                
                return (
                  <div key={renderKey} className="p-4 border-b border-gray-200 last:border-b-0">
                    <div className="flex items-start space-x-3">
                      <input
                        type="checkbox"
                        checked={selectedTestCases.has(uniqueKey)}
                        onChange={(e) => handleTestCaseSelection(testCase, index, e.target.checked)}
                        className="mt-1"
                        disabled={loading}
                      />
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">
                          {testCase.TestCaseID}: {testCase.Title}
                        </h4>
                        <div className="mt-2 text-sm text-gray-600 space-y-1">
                          <p><strong>Scenario:</strong> {testCase.ScenarioID}</p>
                          <p><strong>Description:</strong> {testCase.Description}</p>
                          <p><strong>Objective:</strong> {testCase.Objective}</p>
                          <p><strong>Category:</strong> {testCase.Category}</p>
                          <p><strong>Test Type:</strong> {testCase.SelectedTestType}</p>
                          <p><strong>Selected Category:</strong> {testCase.SelectedCategory}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Selected Count */}
            <p className="mt-2 text-sm text-gray-600">
              Selected: {selectedTestCases.size} of {testCases.length} test cases
              {/* Debug info */}
              <span className="ml-2 text-xs text-red-500">
                (Debug: keys={Array.from(selectedTestCases).length})
              </span>
            </p>
          </div>
        )}

        {/* Loading Spinner */}
        {loading && (
          <div className="flex justify-center items-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
            <span className="ml-2 text-gray-600">Loading...</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default TestCaseOptimization;
