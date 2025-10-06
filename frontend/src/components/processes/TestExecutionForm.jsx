import React, { useState, useEffect, useCallback } from 'react';
import { toast } from 'react-hot-toast';
import { 
  CogIcon, 
  ArrowPathIcon, 
  PlayIcon,
  ExclamationTriangleIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import { clsx } from 'clsx';
import { useSelector } from 'react-redux';
import PropTypes from 'prop-types';
import { useModels } from '../../hooks/useModels';

// Custom hook to manage model information
function useModelInfo(selectedModel) {
  const modelDescriptions = {
    'llama3.2:1b': [
      'Ultra-lightweight 1B parameter model',
      'Optimized for speed and low resource usage',
      'Good for simple tasks and quick responses'
    ],
    'llama3.2:3b': [
      '3B parameter model with balanced performance',
      'Good balance of speed and capability',
      'Suitable for most general tasks'
    ],
    'codegeex4:9b': [
      'Specialized code generation model',
      'Excellent for programming tasks',
      'Supports multiple programming languages'
    ],
    'codellama:7b': [
      'Meta\'s code-focused language model',
      'Optimized for code completion and generation',
      'Strong performance on programming tasks'
    ],
    'gemini-2.5-flash': [
      'Google\'s fast multimodal AI model',
      'Excellent balance of speed and quality',
      'Supports text, image, and code tasks'
    ],
    'gemini-2.5-pro': [
      'Google\'s most capable AI model',
      'Advanced reasoning and analysis',
      'Premium performance for complex tasks'
    ]
  };
  
  return modelDescriptions[selectedModel] || [];
}

export default function TestExecutionForm({ 
  sessionId,
  onSetOutput,
  managedFiles = [],
  disabled = false,
  process
}) {
  // Redux state for API keys
  const apiKeys = useSelector((state) => state.apiKey.apiKeys);
  
  // Merkezi model hook'unu kullan
  const { 
    models: availableModels, 
    loading: modelsLoading, 
    error: modelsError,
    getModelDescriptions
  } = useModels({ 
    autoFetch: true,
    includeDescriptions: true 
  });
  
  // Component state
  const [isLoading, setIsLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState('llama3.2:1b');

  const [isExecuting, setIsExecuting] = useState(false);
  const [mcpStatus, setMcpStatus] = useState(null);
  const [availableProcessNames, setAvailableProcessNames] = useState([]);
  const [selectedProcessName, setSelectedProcessName] = useState('');
  
  // New states for record-based execution
  const [processRecords, setProcessRecords] = useState([]);
  const [selectedRecords, setSelectedRecords] = useState([]);
  const [isLoadingRecords, setIsLoadingRecords] = useState(false);
  const [showCodePreview, setShowCodePreview] = useState(false);
  
  // New states for individual test execution
  const [individualTests, setIndividualTests] = useState([]);
  const [selectedTests, setSelectedTests] = useState([]);
  const [isLoadingTests, setIsLoadingTests] = useState(false);
  const [viewMode, setViewMode] = useState('records'); // 'records' or 'individual'

  // Model info hook kullanımı
  const modelInfo = useModelInfo(selectedModel);

  // Handle model change
  const handleModelChange = (e) => {
    const selectedModel = e.target.value;
    setSelectedModel(selectedModel);
    console.log('Model changed to:', selectedModel);
  };

  // Fetch process records
  const fetchProcessRecords = useCallback(async (processName) => {
    if (!processName) {
      setProcessRecords([]);
      return;
    }

    setIsLoadingRecords(true);
    try {
      const response = await fetch(`http://localhost:8000/api/test-execution/process/${encodeURIComponent(processName)}/records`);
      const data = await response.json();

      if (data.success) {
        setProcessRecords(data.records || []);
        setSelectedRecords([]); // Clear previous selections
        toast.success(`Found ${data.records.length} records for process: ${processName}`);
      } else {
        setProcessRecords([]);
        toast.error('Failed to load process records');
      }
    } catch (error) {
      console.error('Error fetching process records:', error);
      setProcessRecords([]);
      toast.error('Failed to load process records');
    } finally {
      setIsLoadingRecords(false);
    }
  }, []);

  // Fetch individual tests
  const fetchIndividualTests = useCallback(async (processName) => {
    if (!processName) {
      setIndividualTests([]);
      return;
    }

    setIsLoadingTests(true);
    try {
      const response = await fetch(`http://localhost:8000/api/test-execution/process/${encodeURIComponent(processName)}/individual-tests`);
      const data = await response.json();

      if (data.success) {
        setIndividualTests(data.tests || []);
        setSelectedTests([]); // Clear previous selections
        toast.success(`Found ${data.tests.length} individual tests for process: ${processName}`);
      } else {
        setIndividualTests([]);
        toast.error('Failed to load individual tests');
      }
    } catch (error) {
      console.error('Error fetching individual tests:', error);
      setIndividualTests([]);
      toast.error('Failed to load individual tests');
    } finally {
      setIsLoadingTests(false);
    }
  }, []);

  // Handle record selection
  const handleRecordSelection = (recordId, isSelected) => {
    setSelectedRecords(prev => {
      if (isSelected) {
        return [...prev, recordId];
      } else {
        return prev.filter(id => id !== recordId);
      }
    });
  };

  // Handle select all
  const handleSelectAll = (selectAll) => {
    if (selectAll) {
      setSelectedRecords(processRecords.map(record => record.id));
    } else {
      setSelectedRecords([]);
    }
  };

  // Handle individual test selection
  const handleTestSelection = (testId, isSelected) => {
    setSelectedTests(prev => {
      if (isSelected) {
        return [...prev, testId];
      } else {
        return prev.filter(id => id !== testId);
      }
    });
  };

  // Handle select all tests
  const handleSelectAllTests = (selectAll) => {
    if (selectAll) {
      setSelectedTests(individualTests.map(test => test.test_id));
    } else {
      setSelectedTests([]);
    }
  };

  // Check MCP status
  const checkMcpStatus = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/test-execution/mcp/status');
      const data = await response.json();
      setMcpStatus(data);
    } catch (error) {
      console.error('Error checking MCP status:', error);
      setMcpStatus({ status: 'error', message: error.message });
    }
  }, []);

  // Fetch available process names
  const fetchProcessNames = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/test-execution/process-names');
      const data = await response.json();
      setAvailableProcessNames(data.process_names || []);
    } catch (error) {
      console.error('Error fetching process names:', error);
      toast.error('Failed to load process names');
    }
  }, []);



  // Execute tests
  const executeTests = async () => {
    // Check if records/tests are selected based on view mode
    if (viewMode === 'records' && selectedRecords.length === 0) {
      toast.error('Please select at least one record to execute');
      return;
    }
    
    if (viewMode === 'individual' && selectedTests.length === 0) {
      toast.error('Please select at least one individual test to execute');
      return;
    }

    // API key kontrolü - seçilen modelin tipine göre
    const selectedModelInfo = availableModels.find(m => m.key === selectedModel);
    let apiKey = null;
    
    if (selectedModelInfo?.type === 'api') {
      // Gemini modeller için Google API key kullan
      if (selectedModel.includes('gemini')) {
        apiKey = apiKeys.google;
        if (!apiKey) {
          toast.error('Gemini API key is required. Please configure it in API Settings.');
          return;
        }
      }
      // Diğer API modeller için uygun key'i bul
      else if (!selectedModelInfo?.apiKeyStatus?.hasKey) {
        toast.error('API key is required for this model. Please configure it in API Settings.');
        return;
      }
    }

    // Validation - process name is required
    if (!selectedProcessName) {
      toast.error('Please select a test code generation process');
      return;
    }

    setIsExecuting(true);
    
    // Create initial output with loading state
    const selectedCount = viewMode === 'records' ? selectedRecords.length : selectedTests.length;
    const selectedType = viewMode === 'records' ? 'test records' : 'individual tests';
    
    const loadingOutput = {
      status: 'running',
      content: `🔄 Executing ${selectedCount} selected ${selectedType} with ${selectedModelInfo?.name || selectedModel}...\n\nModel: ${selectedModel}\nType: ${selectedModelInfo?.type || 'unknown'}\nProcess: ${selectedProcessName}\nSelection Mode: ${viewMode}\nSelected ${selectedType}: ${selectedCount}\n\nPlease wait...`,
      timestamp: new Date().toISOString(),
      model: selectedModel,
      processType: 'Test Execution'
    };

    if (onSetOutput) {
      onSetOutput(loadingOutput);
    }

    try {
      let requestBody, endpoint;
      
      if (viewMode === 'records') {
        requestBody = {
          record_ids: selectedRecords,
          model: selectedModel,
          ...(apiKey ? { api_key: apiKey } : {})
        };
        endpoint = 'http://localhost:8000/api/test-execution/execute-selected';
      } else {
        requestBody = {
          test_ids: selectedTests,
          model: selectedModel,
          ...(apiKey ? { api_key: apiKey } : {})
        };
        endpoint = 'http://localhost:8000/api/test-execution/execute-selected-tests';
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      const result = await response.json();

      if (result.success) {
        const successOutput = {
          status: 'completed',
          content: `✅ Test Execution Completed Successfully\n\n📊 **Execution Details:**\n- Model: ${result.model_used || selectedModel}\n- Type: ${selectedModelInfo?.type || 'Unknown'}\n- Selection Mode: ${viewMode}\n- ${selectedType.charAt(0).toUpperCase() + selectedType.slice(1)} Executed: ${selectedCount}\n- Timestamp: ${new Date(result.timestamp).toLocaleString()}\n\n📤 **Test Output:**\n\`\`\`\n${result.terminal_output || 'No output received'}\n\`\`\`\n\n🏁 Execution finished successfully.`,
          timestamp: result.timestamp,
          model: result.model_used || selectedModel,
          model_used: result.model_used,
          processType: 'Test Execution'
        };

        if (onSetOutput) {
          onSetOutput(successOutput);
        }
        
        toast.success('Test execution completed!');
      } else {
        const errorOutput = {
          status: 'error',
          content: `❌ Test Execution Failed\n\n🔴 **Error Details:**\n${result.error || 'Unknown error occurred'}\n\nPlease check your configuration and try again.`,
          timestamp: new Date().toISOString(),
          model: selectedModel,
          processType: 'Test Execution'
        };

        if (onSetOutput) {
          onSetOutput(errorOutput);
        }
        
        toast.error('Test execution failed');
      }
    } catch (error) {
      console.error('Execution error:', error);
      
      const errorOutput = {
        status: 'error',
        content: `❌ Connection Error\n\n🔴 **Network Error:**\n${error.message}\n\nPlease ensure the backend services are running:\n- Main Backend: http://localhost:8000\n- MCP Server: http://localhost:8001`,
        timestamp: new Date().toISOString(),
        model: selectedModel,
        processType: 'Test Execution'
      };

      if (onSetOutput) {
        onSetOutput(errorOutput);
      }
      
      toast.error('Execution failed: Connection error');
    } finally {
      setIsExecuting(false);
    }
  };

  // Load data on component mount
  useEffect(() => {
    fetchProcessNames();
    checkMcpStatus();
  }, []); // Remove functions from dependency array since they have empty deps



  return (
    <div className="space-y-6">
      {/* Status Section */}
      <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
        <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
          <CogIcon className="w-5 h-5 mr-2 text-gray-600" />
          Test Execution Configuration
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Process Info */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Selected Process Information
              </label>
              <div className="bg-gray-50 rounded-lg p-3 border">
                <p className="text-sm text-gray-600">
                  <span className="font-medium">Process Name:</span> {selectedProcessName || 'Not selected'}
                </p>
                <p className="text-sm text-gray-600 mt-1">
                  <span className="font-medium">Status:</span> 
                  <span className={clsx(
                    'ml-2 px-2 py-1 rounded-full text-xs',
                    selectedProcessName && selectedRecords.length > 0
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  )}>
                    {selectedProcessName && selectedRecords.length > 0 ? 'Ready' : 'Not Ready'}
                  </span>
                </p>
              </div>
            </div>

            {/* MCP Status */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center justify-between">
                MCP Server Status
                <button
                  onClick={checkMcpStatus}
                  className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                  title="Refresh MCP Status"
                >
                  <ArrowPathIcon className="w-4 h-4" />
                </button>
              </label>
              <div className="bg-gray-50 rounded-lg p-3 border">
                <div className="flex items-center">
                  <div className={clsx(
                    'w-3 h-3 rounded-full mr-3',
                    mcpStatus?.status === 'error' ? 'bg-red-500' : 'bg-green-500'
                  )} />
                  <span className="text-sm text-gray-700">
                    {mcpStatus?.status === 'error' ? 'Offline' : 'Online'}
                  </span>
                </div>
                {mcpStatus?.message && (
                  <p className="text-xs text-gray-500 mt-1">{mcpStatus.message}</p>
                )}
              </div>
            </div>
          </div>

          {/* AI Model Configuration */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                AI Model <span className="text-red-500">*</span>
              </label>
              <select
                value={selectedModel}
                onChange={handleModelChange}
                disabled={disabled || isExecuting || modelsLoading}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {!modelsLoading && availableModels.length === 0 && (
                  <option value="">No models available</option>
                )}
                {availableModels.map(model => (
                  <option key={model.key} value={model.key}>
                    {model.displayName || model.name}
                  </option>
                ))}
              </select>
              {modelsLoading && (
                <p className="text-xs text-gray-500 mt-1">
                  Loading available models...
                </p>
              )}
              {modelsError && (
                <p className="text-xs text-red-600 mt-1">
                  ⚠️ Error loading models: {modelsError}
                </p>
              )}
            </div>

            {/* Model Information */}
            {selectedModel && modelInfo.length > 0 && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <h4 className="text-sm font-medium text-blue-900 mb-2">Model Information</h4>
                <ul className="text-xs text-blue-800 space-y-1">
                  {modelInfo.map((info, index) => (
                    <li key={index} className="flex items-start">
                      <span className="text-blue-600 mr-2">•</span>
                      <span>{info}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Test Code Selection Section */}
      <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
        <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
          <DocumentTextIcon className="w-5 h-5 mr-2 text-gray-600" />
          Test Code Selection
        </h3>
        
        <div className="space-y-4">
          {/* Process Name Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Test Code Generation Process Name <span className="text-red-500">*</span>
            </label>
            <div className="flex space-x-2">
              <select
                value={selectedProcessName}
                onChange={(e) => {
                  setSelectedProcessName(e.target.value);
                  if (e.target.value) {
                    fetchProcessRecords(e.target.value);
                    fetchIndividualTests(e.target.value);
                  }
                }}
                disabled={disabled || isLoading}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:opacity-50"
              >
                <option value="">Select a test code generation process...</option>
                {availableProcessNames.map(process => (
                  <option key={process.name} value={process.name}>
                    {process.name} ({process.count} records)
                  </option>
                ))}
              </select>
              <button
                onClick={fetchProcessNames}
                disabled={isLoading}
                className="px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 disabled:opacity-50"
                title="Refresh process names"
              >
                <ArrowPathIcon className="w-4 h-4" />
              </button>
            </div>
            {availableProcessNames.length === 0 && (
              <p className="text-xs text-gray-500 mt-1">
                No test code generation processes found. Generate some test code first in the Test Code Generation tab.
              </p>
            )}
            {selectedProcessName && (
              <p className="text-xs text-green-600 mt-1">
                ✓ Test code loaded from process: {selectedProcessName}
              </p>
            )}
          </div>

          {/* View Mode Toggle */}
          {selectedProcessName && (
            <div className="mt-4 border-t pt-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Selection Mode
              </label>
              <div className="flex space-x-4">
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="viewMode"
                    value="records"
                    checked={viewMode === 'records'}
                    onChange={(e) => setViewMode(e.target.value)}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">By Records (Bulk)</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="viewMode"
                    value="individual"
                    checked={viewMode === 'individual'}
                    onChange={(e) => setViewMode(e.target.value)}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">Individual Tests (Granular)</span>
                </label>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                {viewMode === 'records' 
                  ? 'Select entire test code generation sessions to execute all tests together'
                  : 'Select individual tests from the generated test arrays for precise control'
                }
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Test Records Selection Section */}
      {viewMode === 'records' && (
      <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900 flex items-center">
            <DocumentTextIcon className="w-5 h-5 mr-2 text-gray-600" />
            Test Records Selection
          </h3>
          <div className="flex space-x-2">
            {selectedProcessName && (
              <button
                onClick={() => fetchProcessRecords(selectedProcessName)}
                disabled={isLoadingRecords}
                className="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:opacity-50 flex items-center"
              >
                <ArrowPathIcon className="w-3 h-3 mr-1" />
                Reload
              </button>
            )}
            {processRecords.length > 0 && (
              <button
                onClick={() => setShowCodePreview(!showCodePreview)}
                className="px-3 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200 flex items-center"
              >
                <DocumentTextIcon className="w-3 h-3 mr-1" />
                {showCodePreview ? 'Hide' : 'Show'} Preview
              </button>
            )}
          </div>
        </div>
        
        {isLoadingRecords ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full mr-3"></div>
            <span className="text-gray-600">Loading records...</span>
          </div>
        ) : processRecords.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            {selectedProcessName 
              ? 'No records found for this process. Generate some test code first.' 
              : 'Please select a process to view records.'}
          </div>
        ) : (
          <div className="space-y-4">
            {/* Select All Controls */}
            <div className="flex items-center justify-between bg-gray-50 p-3 rounded-lg">
              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  id="select-all"
                  checked={selectedRecords.length === processRecords.length && processRecords.length > 0}
                  onChange={(e) => handleSelectAll(e.target.checked)}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <label htmlFor="select-all" className="font-medium text-gray-700">
                  Select All ({processRecords.length} records)
                </label>
              </div>
              <div className="text-sm text-gray-600">
                {selectedRecords.length} of {processRecords.length} selected
              </div>
            </div>

            {/* Records List */}
            <div className="max-h-64 overflow-y-auto border border-gray-200 rounded-lg">
              {processRecords.map((record, index) => (
                <div
                  key={record.id}
                  className={clsx(
                    'p-3 border-b border-gray-100 hover:bg-gray-50',
                    selectedRecords.includes(record.id) && 'bg-blue-50',
                    index === processRecords.length - 1 && 'border-b-0'
                  )}
                >
                  <div className="flex items-start space-x-3">
                    <input
                      type="checkbox"
                      id={`record-${record.id}`}
                      checked={selectedRecords.includes(record.id)}
                      onChange={(e) => handleRecordSelection(record.id, e.target.checked)}
                      className="mt-1 h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-sm font-medium text-gray-900">
                          Record #{index + 1}
                        </h4>
                        <span className="text-xs text-gray-500">
                          {new Date(record.timestamp).toLocaleString()}
                        </span>
                      </div>
                      <div className="bg-gray-900 text-green-400 p-2 rounded text-xs font-mono overflow-x-auto">
                        {record.code_snippet}
                      </div>
                      <div className="mt-2 text-xs text-gray-500">
                        Session: {record.session_id} | Status: {record.status}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Combined Code Preview for Selected Records */}
        {showCodePreview && selectedRecords.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900 flex items-center">
              <DocumentTextIcon className="w-5 h-5 mr-2 text-gray-600" />
              Combined Code Preview ({selectedRecords.length} records)
            </h3>
            <button
              onClick={() => setShowCodePreview(false)}
              className="px-3 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200"
            >
              Close Preview
            </button>
          </div>
          
          <div className="border rounded-lg overflow-hidden">
            <div className="bg-gray-50 px-3 py-2 border-b text-xs text-gray-600 font-mono flex items-center justify-between">
              <span>Combined Test Code</span>
              <span>{selectedRecords.length} records selected</span>
            </div>
            <div className="p-4 bg-gray-900 text-green-400 text-sm overflow-x-auto max-h-96 font-mono">
              {processRecords
                .filter(record => selectedRecords.includes(record.id))
                .map((record, index) => (
                  <div key={record.id} className="mb-6">
                    <div className="text-blue-400 mb-2">
                      {`# ============================================`}
                    </div>
                    <div className="text-blue-400 mb-2">
                      {`# Record ${index + 1}: ${record.session_id}`}
                    </div>
                    <div className="text-blue-400 mb-2">
                      {`# Timestamp: ${new Date(record.timestamp).toLocaleString()}`}
                    </div>
                    <div className="text-blue-400 mb-4">
                      {`# ============================================`}
                    </div>
                    <pre className="whitespace-pre-wrap">{record.full_code}</pre>
                  </div>
                ))}
            </div>
          </div>

          <div className="mt-4 text-sm text-gray-600">
            <p className="mb-2">
              <span className="font-medium">Total Records:</span> {selectedRecords.length}
            </p>
            <p>
              <span className="font-medium">Ready to execute:</span> 
              <span className="ml-2 text-green-600">
                Yes - Combined code will be sent to the selected AI model
              </span>
            </p>
          </div>
        </div>
        )}
      </div>
      )}

      {/* Individual Tests Selection Section */}
      {viewMode === 'individual' && (
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900 flex items-center">
              <DocumentTextIcon className="w-5 h-5 mr-2 text-gray-600" />
              Individual Tests Selection
            </h3>
            <div className="flex space-x-2">
              {selectedProcessName && (
                <button
                  onClick={() => fetchIndividualTests(selectedProcessName)}
                  disabled={isLoadingTests}
                  className="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:opacity-50 flex items-center"
                >
                  <ArrowPathIcon className="w-3 h-3 mr-1" />
                  Reload
                </button>
              )}
              {individualTests.length > 0 && (
                <span className="px-3 py-1 text-xs bg-green-100 text-green-700 rounded">
                  {individualTests.length} tests found
                </span>
              )}
            </div>
          </div>

          {selectedProcessName && (
            <div className="space-y-4">
              {/* Select All Tests */}
              {individualTests.length > 0 && (
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={selectedTests.length === individualTests.length}
                      onChange={(e) => handleSelectAllTests(e.target.checked)}
                      className="mr-2 rounded"
                    />
                    <span className="text-sm font-medium text-gray-700">
                      Select All ({individualTests.length} tests)
                    </span>
                  </label>
                  <span className="text-xs text-gray-500">
                    {selectedTests.length} selected
                  </span>
                </div>
              )}

              {/* Loading State */}
              {isLoadingTests && (
                <div className="flex items-center justify-center p-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                  <span className="ml-2 text-gray-600">Loading individual tests...</span>
                </div>
              )}

              {/* Individual Tests List */}
              {!isLoadingTests && individualTests.length > 0 && (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {individualTests.map((test, index) => (
                    <div
                      key={test.test_id}
                      className={clsx(
                        'p-3 border rounded-lg cursor-pointer transition-colors',
                        selectedTests.includes(test.test_id)
                          ? 'border-indigo-300 bg-indigo-50'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      )}
                      onClick={() => handleTestSelection(test.test_id, !selectedTests.includes(test.test_id))}
                    >
                      <div className="flex items-start space-x-3">
                        <input
                          type="checkbox"
                          checked={selectedTests.includes(test.test_id)}
                          onChange={(e) => handleTestSelection(test.test_id, e.target.checked)}
                          className="mt-1 rounded"
                          onClick={(e) => e.stopPropagation()}
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-1">
                            <h4 className="text-sm font-medium text-gray-900 truncate">
                              {test.test_name || `Test ${test.test_index + 1}`}
                            </h4>
                            <span className="text-xs text-gray-500 ml-2">
                              #{test.test_index + 1}
                            </span>
                          </div>
                          <p className="text-xs text-gray-600 mb-1">
                            Session: {test.session_id}
                          </p>
                          <div className="text-xs text-gray-700 bg-gray-100 rounded p-2 font-mono">
                            {test.code_snippet}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* No Tests Found */}
              {!isLoadingTests && individualTests.length === 0 && selectedProcessName && (
                <div className="text-center p-8 text-gray-500">
                  <DocumentTextIcon className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p className="text-sm">No individual tests found for this process.</p>
                  <p className="text-xs mt-1">Make sure the process contains generated_tests array.</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Execution Controls */}
      <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Execution Controls</h3>
        
        <div className="flex items-center justify-between">
          <div className="flex-1 mr-4">
            <p className="text-sm text-gray-600 mb-2">
              Click the button below to execute the selected {viewMode === 'records' ? 'test records' : 'individual tests'} using the chosen AI model.
              Results will appear in the output panel on the right.
            </p>
            <div className="text-xs text-gray-500">
              <span className="font-medium">Selected Model:</span> {selectedModel} | 
              <span className="font-medium ml-2">Type:</span> {availableModels.find(m => m.key === selectedModel)?.type || 'Unknown'} | 
              <span className="font-medium ml-2">
                {viewMode === 'records' ? 'Records' : 'Tests'}:
              </span> {viewMode === 'records' ? `${selectedRecords.length}/${processRecords.length}` : `${selectedTests.length}/${individualTests.length}`}
            </div>
          </div>

          <button
            onClick={executeTests}
            disabled={disabled || isExecuting || (viewMode === 'records' ? selectedRecords.length === 0 : selectedTests.length === 0)}
            className={clsx(
              'flex items-center space-x-2 px-6 py-3 rounded-lg font-medium transition-all duration-200',
              disabled || isExecuting || (viewMode === 'records' ? selectedRecords.length === 0 : selectedTests.length === 0)
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-indigo-600 text-white hover:bg-indigo-700 hover:shadow-lg transform hover:scale-105'
            )}
          >
            {isExecuting ? (
              <>
                <div className="animate-spin w-5 h-5 border-2 border-current border-t-transparent rounded-full" />
                <span>Executing...</span>
              </>
            ) : (
              <>
                <PlayIcon className="w-5 h-5" />
                <span>Execute Selected ({selectedRecords.length})</span>
              </>
            )}
          </button>
        </div>

        {(disabled || selectedRecords.length === 0) && (
          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-sm text-yellow-800">
              <span className="font-medium">⚠️ Execution not available:</span>
              {selectedRecords.length === 0
                ? ' No records selected. Please select at least one record to execute.' 
                : ' Process is currently disabled.'
              }
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

TestExecutionForm.propTypes = {
  sessionId: PropTypes.string,
  onSetOutput: PropTypes.func,
  managedFiles: PropTypes.array,
  disabled: PropTypes.bool,
  process: PropTypes.object
};