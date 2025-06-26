import React, { useState, useEffect } from 'react';
import axios from 'axios';

const TestCaseOptimization = () => {
  const [processTitles, setProcessTitles] = useState([]);
  const [selectedProcessTitle, setSelectedProcessTitle] = useState('');
  const [testCases, setTestCases] = useState([]);
  const [selectedTestCases, setSelectedTestCases] = useState(new Set());
  const [optimizationResults, setOptimizationResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [existingResults, setExistingResults] = useState(null);

  // Component mount edildiğinde process title'ları getir
  useEffect(() => {
    fetchProcessTitles();
  }, []);

  // Process title değiştiğinde test case'leri getir
  useEffect(() => {
    if (selectedProcessTitle) {
      fetchTestCases(selectedProcessTitle);
      checkExistingResults(selectedProcessTitle);
    }
  }, [selectedProcessTitle]);

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
        console.log(`Fetched ${response.data.data.length} test cases with ${uniqueKeys.size} unique keys`);
        
        // Eğer unique key sayısı test case sayısından farklıysa duplicate var demektir
        if (uniqueKeys.size !== response.data.data.length) {
          console.warn('Warning: Some test cases have duplicate unique_key values!');
        }
      }
    } catch (err) {
      setError('Failed to fetch test cases: ' + err.message);
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

  const handleTestCaseSelection = (testCase, isChecked) => {
    const newSelected = new Set(selectedTestCases);
    const uniqueKey = testCase.unique_key;
    
    if (isChecked) {
      newSelected.add(uniqueKey);
    } else {
      newSelected.delete(uniqueKey);
    }
    
    setSelectedTestCases(newSelected);
  };  const handleSelectAll = () => {
    // Tüm test case'lerin unique_key'lerini al
    const allKeys = new Set(testCases.map(tc => tc.unique_key));
    
    if (selectedTestCases.size === allKeys.size && allKeys.size === testCases.length) {
      // Tümü seçiliyse, hepsini kaldır
      setSelectedTestCases(new Set());
    } else {
      // Hiçbiri veya bazıları seçiliyse, hepsini seç
      setSelectedTestCases(allKeys);
    }
    
    // Debug için log ekle
    console.log(`Total test cases: ${testCases.length}, Unique keys: ${allKeys.size}, Selected: ${allKeys.size}`);
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
      setLoading(true);
      setError(null);
        // Seçilen test case'leri filtrele
      const selectedTestCaseData = testCases.filter(tc => selectedTestCases.has(tc.unique_key));
      
      console.log(`Running optimization on ${selectedTestCaseData.length} test cases out of ${testCases.length} total test cases`);
      console.log(`Selected test case keys:`, Array.from(selectedTestCases));
      console.log(`Available test case keys:`, testCases.map(tc => tc.unique_key));
      
      const response = await axios.post('http://localhost:8000/api/test-case-optimization/smart-selection', {
        selected_test_cases: selectedTestCaseData,
        process_title: selectedProcessTitle
      });

      if (response.data.success) {
        setOptimizationResults(response.data.data);
        setExistingResults(response.data.data); // Update existing results
      } else {
        setError('Smart selection failed: ' + response.data.message);
      }
    } catch (err) {
      setError('Failed to run smart selection: ' + err.message);
    } finally {
      setLoading(false);
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

  const clearResults = async () => {
    if (!selectedProcessTitle) return;
    
    try {
      setLoading(true);
      await axios.delete(`http://localhost:8000/api/test-case-optimization/results/${encodeURIComponent(selectedProcessTitle)}`);
      setOptimizationResults(null);
      setExistingResults(null);
    } catch (err) {
      setError('Failed to clear results: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Test Case Optimization</h2>
        
        {/* Process Title Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Process Title
          </label>
          <select
            value={selectedProcessTitle}
            onChange={(e) => setSelectedProcessTitle(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            disabled={loading}
          >
            <option value="">Select a Process Title</option>
            {processTitles.map((title, index) => (
              <option key={index} value={title}>{title}</option>
            ))}
          </select>
        </div>

        {/* Existing Results Warning */}
        {existingResults && (
          <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-md">
            <div className="flex justify-between items-center">
              <p className="text-yellow-800">
                Smart Selection results already exist for this process title!
              </p>
              <button
                onClick={clearResults}
                className="px-3 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600"
                disabled={loading}
              >
                Clear Results
              </button>
            </div>
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
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Test Cases</h3>
              {/* Select All/Deselect All Buttons */}
            <div className="flex gap-2 mb-4">              <button
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
            </div>            {/* Test Cases List */}
            <div className="max-h-96 overflow-y-auto border border-gray-200 rounded-md">
              {testCases.map((testCase, index) => {
                // Gerçek unique key oluştur - eğer unique_key duplicate ise index ekle
                const renderKey = testCase.unique_key ? `${testCase.unique_key}_${index}` : `test_case_${index}`;
                
                return (
                  <div key={renderKey} className="p-4 border-b border-gray-200 last:border-b-0">
                    <div className="flex items-start space-x-3">
                      <input
                        type="checkbox"
                        checked={selectedTestCases.has(testCase.unique_key)}
                        onChange={(e) => handleTestCaseSelection(testCase, e.target.checked)}
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
            </p>
          </div>
        )}

        {/* Smart Selection Button */}
        {testCases.length > 0 && (
          <div className="mb-6">
            <button
              onClick={runSmartSelection}
              disabled={loading || selectedTestCases.size === 0}
              className="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {loading ? 'Running Smart Selection...' : 'Run Smart Selection'}
            </button>
          </div>
        )}

        {/* Results Section */}
        {(optimizationResults || existingResults) && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-800">Results</h3>
            
            {/* Results to display */}
            {(() => {
              const results = optimizationResults || existingResults;
              return (
                <>
                  {/* Unique Test Cases */}
                  <div className="bg-green-50 border border-green-200 rounded-md p-4">
                    <h4 className="font-medium text-green-800 mb-2">
                      Unique Test Cases ({results.unique_test_cases?.length || 0})
                    </h4>
                    <details className="cursor-pointer">
                      <summary className="text-sm text-green-700">Click to view details</summary>
                      <pre className="mt-2 text-xs bg-white p-2 rounded border overflow-auto max-h-60">
                        {JSON.stringify(results.unique_test_cases, null, 2)}
                      </pre>
                    </details>
                  </div>

                  {/* Similar Test Cases */}
                  {results.similar_test_cases?.length > 0 && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
                      <h4 className="font-medium text-yellow-800 mb-2">
                        Similar Test Cases Found ({results.similar_test_cases.length})
                      </h4>
                      <details className="cursor-pointer">
                        <summary className="text-sm text-yellow-700">Click to view details</summary>
                        <pre className="mt-2 text-xs bg-white p-2 rounded border overflow-auto max-h-60">
                          {JSON.stringify(results.similar_test_cases, null, 2)}
                        </pre>
                      </details>
                    </div>
                  )}

                  {/* Comparison Logs */}
                  <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                    <h4 className="font-medium text-blue-800 mb-2">
                      Comparison Logs ({results.comparison_logs?.length || 0})
                    </h4>
                    <details className="cursor-pointer">
                      <summary className="text-sm text-blue-700">Click to view details</summary>
                      <pre className="mt-2 text-xs bg-white p-2 rounded border overflow-auto max-h-60">
                        {JSON.stringify(results.comparison_logs, null, 2)}
                      </pre>
                    </details>
                  </div>

                  {/* Download Buttons */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => downloadResults(results.unique_test_cases, 'unique_test_cases.json')}
                      className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                    >
                      Download Unique Test Cases
                    </button>
                    <button
                      onClick={() => downloadResults(results, 'all_optimization_results.json')}
                      className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600"
                    >
                      Download All Results
                    </button>
                  </div>
                </>
              );
            })()}
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
