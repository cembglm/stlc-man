import React, { useState, useEffect } from 'react';
import axios from 'axios';

export default function TestCaseOptimizationForm({ onRun, onSetOutput, process, sessionId, disabled, onTestCaseOptimization, onPromptChange, currentPrompt }) {
  const [processOptions, setProcessOptions] = useState([]);
  const [selectedProcesses, setSelectedProcesses] = useState(new Set());
  const [testCases, setTestCases] = useState([]);
  const [selectedTestCases, setSelectedTestCases] = useState(new Set());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [existingResults, setExistingResults] = useState(null);
  const [processPrompt, setProcessPrompt] = useState('');
  const [canRun, setCanRun] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [showMultiSelect, setShowMultiSelect] = useState(false);
  const [availableModels, setAvailableModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('llama3.2:3b');
  const [processName, setProcessName] = useState('');

  // Default prompt for test case optimization
  const defaultPrompt = `You are given two test cases, each with a certain set of fields:
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
- Do not explain your reasoning, only provide the final JSON response.`;

  // Component mount edildiğinde process title'ları ve modelleri getir
  useEffect(() => {
    fetchProcessOptions();
    fetchAvailableModels();
    setProcessPrompt(defaultPrompt);
  }, []);

  // Seçilen process'ler değiştiğinde test case'leri getir
  useEffect(() => {
    if (selectedProcesses.size > 0) {
      fetchTestCasesForSelectedProcesses();
    } else {
      setTestCases([]);
      setSelectedTestCases(new Set());
    }
  }, [selectedProcesses]);

  // Can run durumunu güncelle
  useEffect(() => {
    setCanRun(selectedTestCases.size > 0 && selectedProcesses.size > 0 && selectedModel && processName.trim() !== '' && !loading && !isRunning);
  }, [selectedTestCases.size, selectedProcesses.size, selectedModel, processName, loading, isRunning]);

  // processPrompt değiştiğinde parent'ı bildir
  useEffect(() => {
    if (onPromptChange && typeof onPromptChange === 'function') {
      onPromptChange(processPrompt);
    }
  }, [processPrompt, onPromptChange]);

  // currentPrompt prop'u değiştiğinde processPrompt'u güncelle
  useEffect(() => {
    if (currentPrompt && currentPrompt !== processPrompt) {
      setProcessPrompt(currentPrompt);
    }
  }, [currentPrompt, processPrompt]);

  const fetchAvailableModels = async () => {
    try {
      setLoading(true);
      const response = await axios.get('http://localhost:8000/api/test-case-optimization/models');
      if (response.data.success) {
        setAvailableModels(response.data.data);
      }
    } catch (err) {
      setError('Failed to fetch available models: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchProcessOptions = async () => {
    try {
      setLoading(true);
      const response = await axios.get('http://localhost:8000/api/test-case-optimization/process-titles-with-counts');
      if (response.data.success) {
        setProcessOptions(response.data.data);
      }
    } catch (err) {
      setError('Failed to fetch process options: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchTestCasesForSelectedProcesses = async () => {
    try {
      setLoading(true);
      const selectedProcessTitles = Array.from(selectedProcesses);
      
      const response = await axios.post('http://localhost:8000/api/test-case-optimization/test-cases-multi-process', {
        process_titles: selectedProcessTitles
      });
      
      if (response.data.success) {
        setTestCases(response.data.data);
        setSelectedTestCases(new Set()); // Reset selection
        
        // Debug bilgisi ekle
        const uniqueKeys = new Set(response.data.data.map(tc => tc.unique_key));
        console.log(`TestCaseOptimizationForm - Fetched ${response.data.data.length} test cases from ${selectedProcessTitles.length} processes with ${uniqueKeys.size} unique keys`);
        
        // Eğer unique key sayısı test case sayısından farklıysa duplicate var demektir
        if (uniqueKeys.size !== response.data.data.length) {
          console.warn('TestCaseOptimizationForm - Warning: Some test cases have duplicate unique_key values!');
        }
      }
    } catch (err) {
      setError('Failed to fetch test cases: ' + err.message);
      setTestCases([]);
      setSelectedTestCases(new Set());
    } finally {
      setLoading(false);
    }
  };

  const handleProcessSelection = (processTitle, isChecked) => {
    const newSelected = new Set(selectedProcesses);
    
    if (isChecked) {
      newSelected.add(processTitle);
    } else {
      newSelected.delete(processTitle);
    }
    
    setSelectedProcesses(newSelected);
  };

  const handleSelectAllProcesses = () => {
    const allProcessTitles = new Set(processOptions.map(p => p.process_title));
    
    if (selectedProcesses.size === allProcessTitles.size) {
      // Tümü seçiliyse, hepsini kaldır
      setSelectedProcesses(new Set());
    } else {
      // Hiçbiri veya bazıları seçiliyse, hepsini seç
      setSelectedProcesses(allProcessTitles);
    }
  };

  const fetchTestCases = async (processTitle) => {
    try {
      setLoading(true);
      const response = await axios.get(`http://localhost:8000/api/test-case-optimization/test-cases/${encodeURIComponent(processTitle)}`);
      if (response.data.success) {
        setTestCases(response.data.data);
        setSelectedTestCases(new Set()); // Reset selection
        
        // Debug bilgisi ekle
        const uniqueKeys = new Set(response.data.data.map(tc => tc.unique_key));
        console.log(`TestCaseOptimizationForm - Fetched ${response.data.data.length} test cases with ${uniqueKeys.size} unique keys`);
        
        // Eğer unique key sayısı test case sayısından farklıysa duplicate var demektir
        if (uniqueKeys.size !== response.data.data.length) {
          console.warn('TestCaseOptimizationForm - Warning: Some test cases have duplicate unique_key values!');
        }
      }
    } catch (err) {
      setError('Failed to fetch test cases: ' + err.message);
      setTestCases([]);
      setSelectedTestCases(new Set());
    } finally {
      setLoading(false);
    }
  };

  const checkExistingResults = async (processTitle) => {
    try {
      const response = await axios.get(`http://localhost:8000/api/test-case-optimization/results/${encodeURIComponent(processTitle)}`);
      if (response.data.success) {
        setExistingResults(response.data.data);
      } else {
        setExistingResults(null);
      }
    } catch (err) {
      // 404 hatası normal, sonuç yoksa
      setExistingResults(null);
    }
  };

  const handleTestCaseSelection = (testCase, isChecked, index) => {
    const newSelected = new Set(selectedTestCases);
    // unique_key yerine index kullan çünkü unique_key'ler duplicate
    const testCaseKey = `${index}_${testCase.TestCaseID || index}`;
    
    if (isChecked) {
      newSelected.add(testCaseKey);
    } else {
      newSelected.delete(testCaseKey);
    }
    
    setSelectedTestCases(newSelected);
  };

  const handleSelectAll = () => {
    // Tüm test case'lerin index-based key'lerini oluştur
    const allKeys = new Set(testCases.map((tc, index) => `${index}_${tc.TestCaseID || index}`));
    
    if (selectedTestCases.size === allKeys.size && allKeys.size === testCases.length) {
      // Tümü seçiliyse, hepsini kaldır
      setSelectedTestCases(new Set());
    } else {
      // Hiçbiri veya bazıları seçiliyse, hepsini seç
      setSelectedTestCases(allKeys);
    }
    
    // Debug için log ekle
    console.log(`TestCaseOptimizationForm - Total test cases: ${testCases.length}, All keys: ${allKeys.size}, Selected: ${allKeys.size}`);
  };

  const handleDeselectAll = () => {
    setSelectedTestCases(new Set());
  };

  const runSmartSelection = async () => {
    if (selectedTestCases.size === 0) {
      setError('Please select at least one test case');
      return;
    }

    try {
      setIsRunning(true);
      setLoading(true);
      setError(null);
      
      // Seçilen test case'leri filtrele - index-based key'leri kullan
      const selectedTestCaseData = testCases.filter((tc, index) => {
        const testCaseKey = `${index}_${tc.TestCaseID || index}`;
        return selectedTestCases.has(testCaseKey);
      });
      
      console.log(`TestCaseOptimizationForm - Running optimization on ${selectedTestCaseData.length} test cases out of ${testCases.length} total test cases`);
      console.log(`TestCaseOptimizationForm - Selected test case keys:`, Array.from(selectedTestCases));
      console.log(`TestCaseOptimizationForm - Available test case keys:`, testCases.map((tc, index) => `${index}_${tc.TestCaseID || index}`));
      
      const response = await axios.post('http://localhost:8000/api/test-case-optimization/smart-selection', {
        selected_test_cases: selectedTestCaseData,
        process_titles: Array.from(selectedProcesses), // Send multiple process titles
        process_name: processName, // Send process name to backend
        custom_prompt: processPrompt, // Send custom prompt to backend
        selected_model: selectedModel, // Send selected model to backend
        session_id: sessionId // Send session_id to backend
      });

      if (response.data.success) {
        // Use onSetOutput to display results in the right panel
        if (onSetOutput && typeof onSetOutput === 'function') {
          onSetOutput('test-case-optimization', {
            processId: 'test-case-optimization',
            results: response.data.data,
            timestamp: new Date().toISOString(),
            status: 'completed',
            type: 'test-case-optimization'
          });
        }
        setExistingResults(response.data.data); // Update existing results
      } else {
        setError('Smart selection failed: ' + response.data.message);
      }
    } catch (err) {
      setError('Failed to run smart selection: ' + err.message);
    } finally {
      setIsRunning(false);
      setLoading(false);
    }
  };

  const clearResults = async () => {
    if (selectedProcesses.size === 0) return;
    
    try {
      setLoading(true);
      // Clear results for all selected processes
      const selectedProcessTitles = Array.from(selectedProcesses);
      for (const processTitle of selectedProcessTitles) {
        await axios.delete(`http://localhost:8000/api/test-case-optimization/results/${encodeURIComponent(processTitle)}`);
      }
      setExistingResults(null);
    } catch (err) {
      setError('Failed to clear results: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Store the run function for parent component access
  const [runFunction, setRunFunction] = useState(null);

  // Expose the run function to the parent component
  React.useEffect(() => {
    const runHandler = {
      handleRun: runSmartSelection,
      canRun: canRun,
      isRunning: isRunning
    };
    
    setRunFunction(runHandler);
    
    // Call onTestCaseOptimization to set the form state in TabPanel
    if (onTestCaseOptimization && typeof onTestCaseOptimization === 'function') {
      onTestCaseOptimization(runHandler);
    }
    
    // TestCaseOptimizationForm kendi execution'ını yönetir, onRun'ı çağırmaz
  }, [canRun, isRunning, onTestCaseOptimization]);

  return (
    <div className="space-y-6">
      {/* Model Selection */}
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-medium text-gray-900 mb-4">LLM Model Selection</h3>
        <div className="space-y-2">
          <label htmlFor="model-select" className="block text-sm font-medium text-gray-700">
            Select LLM Model *
          </label>
          <select
            id="model-select"
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            disabled={loading || disabled}
          >
            <option value="">Select a Model</option>
            {availableModels.map((model, index) => (
              <option key={index} value={model.key}>
                {model.name} - {model.description}
              </option>
            ))}
          </select>
          {!selectedModel && (
            <p className="text-sm text-red-600">Model selection is required to start optimization</p>
          )}
        </div>
      </div>

      {/* Process Name Input */}
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Optimization Process Name</h3>
        <div className="space-y-2">
          <label htmlFor="process-name" className="block text-sm font-medium text-gray-700">
            Enter Process Name *
          </label>
          <input
            type="text"
            id="process-name"
            value={processName}
            onChange={(e) => setProcessName(e.target.value)}
            placeholder="e.g., Test Case Process 1"
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            disabled={loading || disabled}
          />
          {processName.trim() === '' && (
            <p className="text-sm text-red-600">Process name is required to start optimization</p>
          )}
          <p className="text-sm text-gray-500">
            This name will be used to save and retrieve your optimization results.
          </p>
        </div>
      </div>

      {/* Process Selection */}
      <div className="bg-white p-4 rounded-lg shadow">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">Generated Test Case Selection</h3>
          <button
            onClick={() => setShowMultiSelect(!showMultiSelect)}
            className="text-sm text-indigo-600 hover:text-indigo-800"
          >
            {showMultiSelect ? 'Simple Select' : 'Multi-Select Mode'}
          </button>
        </div>
        
        {showMultiSelect ? (
          /* Multi-Select Interface */
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                Select Multiple Processes ({selectedProcesses.size} selected)
              </label>
              <button
                onClick={handleSelectAllProcesses}
                className="text-sm text-indigo-600 hover:text-indigo-800"
                disabled={loading || disabled}
              >
                {selectedProcesses.size === processOptions.length ? 'Deselect All' : 'Select All'}
              </button>
            </div>
            
            <div className="max-h-60 overflow-y-auto border border-gray-200 rounded-md">
              {processOptions.map((processOption, index) => (
                <div key={index} className="flex items-start p-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0">
                  <input
                    type="checkbox"
                    checked={selectedProcesses.has(processOption.process_title)}
                    onChange={(e) => handleProcessSelection(processOption.process_title, e.target.checked)}
                    className="mr-3 mt-1"
                    disabled={loading || disabled}
                  />
                  <div className="flex-1">
                    <div className="flex items-center">
                      <span className="font-medium text-gray-900">{processOption.process_title}</span>
                      <span className="ml-2 text-sm text-gray-500">
                        ({processOption.test_case_count} test cases)
                      </span>
                    </div>
                    {processOption.source_files && processOption.source_files.length > 0 && (
                      <div className="mt-1">
                        <span className="text-xs text-gray-400">Source files: </span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {processOption.source_files.map((fileName, fileIndex) => (
                            <span 
                              key={fileIndex} 
                              className="inline-block px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded"
                              title={fileName}
                            >
                              {fileName.length > 15 ? `${fileName.substring(0, 12)}...` : fileName}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
            
            {selectedProcesses.size > 0 && (
              <div className="text-sm text-gray-600 bg-blue-50 p-3 rounded">
                Selected processes: {Array.from(selectedProcesses).join(', ')}
              </div>
            )}
          </div>
        ) : (
          /* Single Select Interface */
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Generated Test Case Process Title
            </label>
            <select
              value={Array.from(selectedProcesses)[0] || ''}
              onChange={(e) => setSelectedProcesses(e.target.value ? new Set([e.target.value]) : new Set())}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              disabled={loading || disabled}
            >
              <option value="">Select a Process Title</option>
              {processOptions.map((processOption, index) => (
                <option key={index} value={processOption.process_title}>
                  {processOption.process_title} ({processOption.test_case_count} test cases)
                </option>
              ))}
            </select>
            
            {/* Show source files for selected process */}
            {selectedProcesses.size === 1 && (() => {
              const selectedTitle = Array.from(selectedProcesses)[0];
              const selectedProcess = processOptions.find(p => p.process_title === selectedTitle);
              return selectedProcess && selectedProcess.source_files && selectedProcess.source_files.length > 0 ? (
                <div className="mt-3 p-3 bg-gray-50 rounded-md">
                  <span className="text-sm font-medium text-gray-700">Source Files:</span>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {selectedProcess.source_files.map((fileName, fileIndex) => (
                      <span 
                        key={fileIndex} 
                        className="inline-block px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded"
                        title={fileName}
                      >
                        {fileName}
                      </span>
                    ))}
                  </div>
                </div>
              ) : null;
            })()}
          </div>
        )}

        {/* Existing Results Warning */}
        {existingResults && (
          <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-md">
            <div className="flex justify-between items-center">
              <p className="text-yellow-800">
                Smart Selection results already exist for this process title!
              </p>
              <button
                onClick={clearResults}
                className="px-3 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600"
                disabled={loading || disabled}
              >
                Clear Results
              </button>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-red-800">{error}</p>
          </div>
        )}
      </div>

      {/* Test Cases Section */}
      {testCases.length > 0 && (
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-800">Test Cases</h3>
            <div className="text-sm text-gray-600">
              {selectedProcesses.size > 1 ? (
                <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded">
                  {testCases.length} cases from {selectedProcesses.size} processes
                </span>
              ) : (
                <span className="bg-gray-100 text-gray-800 px-2 py-1 rounded">
                  {testCases.length} cases
                </span>
              )}
            </div>
          </div>
          
          {/* Select All/Deselect All Buttons */}
          <div className="flex gap-2 mb-4">
            <button
              onClick={handleSelectAll}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              disabled={loading || disabled}
            >
              {selectedTestCases.size === testCases.length && testCases.length > 0 ? 'Deselect All' : 'Select All'}
            </button>
            <button
              onClick={handleDeselectAll}
              className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
              disabled={loading || disabled}
            >
              Deselect All
            </button>
          </div>

          {/* Test Cases List */}
          <div className="max-h-96 overflow-y-auto border border-gray-200 rounded-md">
            {testCases.map((testCase, index) => {
              // Index-based unique key oluştur
              const renderKey = `test_case_${index}`;
              const testCaseKey = `${index}_${testCase.TestCaseID || index}`;
              
              return (
                <div key={renderKey} className="p-4 border-b border-gray-200 last:border-b-0">
                  <div className="flex items-start space-x-3">
                    <input
                      type="checkbox"
                      checked={selectedTestCases.has(testCaseKey)}
                      onChange={(e) => handleTestCaseSelection(testCase, e.target.checked, index)}
                      className="mt-1"
                      disabled={loading || disabled}
                    />
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium text-gray-900">
                          {testCase.TestCaseID}: {testCase.Title}
                        </h4>
                        {selectedProcesses.size > 1 && (
                          <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded">
                            {testCase.ProcessTitle || testCase.SessionID || 'Unknown'}
                          </span>
                        )}
                      </div>
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
          </p>
        </div>
      )}

      {/* Loading Spinner */}
      {loading && (
        <div className="flex justify-center items-center py-4">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-500"></div>
          <span className="ml-2 text-gray-600">Loading...</span>
        </div>
      )}
    </div>
  );
}