import React, { useState, useEffect } from 'react';
import axios from 'axios';

export default function TestCaseOptimizationForm({ onRun, onSetOutput, process, sessionId, disabled, onTestCaseOptimization, onPromptChange, currentPrompt }) {
  const [processTitles, setProcessTitles] = useState([]);
  const [selectedProcessTitle, setSelectedProcessTitle] = useState('');
  const [testCases, setTestCases] = useState([]);
  const [selectedTestCases, setSelectedTestCases] = useState(new Set());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [existingResults, setExistingResults] = useState(null);
  const [processPrompt, setProcessPrompt] = useState('');
  const [canRun, setCanRun] = useState(false);
  const [isRunning, setIsRunning] = useState(false);

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

  // Component mount edildiğinde process title'ları getir
  useEffect(() => {
    fetchProcessTitles();
    setProcessPrompt(defaultPrompt);
  }, []);

  // Process title değiştiğinde test case'leri getir
  useEffect(() => {
    if (selectedProcessTitle) {
      fetchTestCases(selectedProcessTitle);
      checkExistingResults(selectedProcessTitle);
    } else {
      setTestCases([]);
      setSelectedTestCases(new Set());
      setExistingResults(null);
    }
  }, [selectedProcessTitle]);

  // Can run durumunu güncelle
  useEffect(() => {
    setCanRun(selectedTestCases.size > 0 && selectedProcessTitle && !loading && !isRunning);
  }, [selectedTestCases.size, selectedProcessTitle, loading, isRunning]);

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

  const fetchProcessTitles = async () => {
    try {
      setLoading(true);
      const response = await axios.get('http://localhost:8000/api/test-case-optimization/process-titles');
      if (response.data.success) {
        setProcessTitles(response.data.data);
      }
    } catch (err) {
      setError('Failed to fetch process titles: ' + err.message);
    } finally {
      setLoading(false);
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
        process_title: selectedProcessTitle,
        custom_prompt: processPrompt, // Send custom prompt to backend
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
    if (!selectedProcessTitle) return;
    
    try {
      setLoading(true);
      await axios.delete(`http://localhost:8000/api/test-case-optimization/results/${encodeURIComponent(selectedProcessTitle)}`);
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
      {/* Process Title Selection */}
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Test Case Configuration</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Process Title
            </label>
            <select
              value={selectedProcessTitle}
              onChange={(e) => setSelectedProcessTitle(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              disabled={loading || disabled}
            >
              <option value="">Select a Process Title</option>
              {processTitles.map((title, index) => (
                <option key={index} value={title}>{title}</option>
              ))}
            </select>
          </div>
        </div>

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
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Test Cases</h3>
          
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