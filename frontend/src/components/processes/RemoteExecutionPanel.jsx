import React, { useState, useCallback } from 'react';
import { toast } from 'react-hot-toast';
import {
  FolderOpenIcon,
  CloudArrowUpIcon,
  CloudArrowDownIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
  ServerIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import { clsx } from 'clsx';

/**
 * RemoteExecutionPanel
 * 
 * Manages remote/local test execution folders for robot scenarios.
 * Enables:
 * - Creating execution folders (local/network paths)
 * - Deploying source files for robot consumption
 * - Monitoring execution status
 * - Collecting results from robot execution
 */
export default function RemoteExecutionPanel({ 
  sessionId,
  selectedProcessName,
  testCodes = [],
  onResultsCollected 
}) {
  // Folder configuration states
  const [basePath, setBasePath] = useState('C:\\test_execution');
  const [folderName, setFolderName] = useState('');
  const [executionFolder, setExecutionFolder] = useState('');
  const [folderCreated, setFolderCreated] = useState(false);
  
  // Deployment states
  const [isDeploying, setIsDeploying] = useState(false);
  const [deploymentStatus, setDeploymentStatus] = useState(null);
  const [deployedFiles, setDeployedFiles] = useState([]);
  
  // Status monitoring states
  const [executionStatus, setExecutionStatus] = useState(null);
  const [isCheckingStatus, setIsCheckingStatus] = useState(false);
  const [robotAccessed, setRobotAccessed] = useState(false);
  
  // Results collection states
  const [collectedResults, setCollectedResults] = useState(null);
  const [isCollectingResults, setIsCollectingResults] = useState(false);
  const [resultFilePattern, setResultFilePattern] = useState('*.json');
  
  /**
   * Create execution folder structure
   */
  const handleCreateFolder = useCallback(async () => {
    if (!basePath) {
      toast.error('Please enter a base path');
      return;
    }
    
    try {
      const response = await fetch('http://localhost:8000/api/remote-execution/create-folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          base_path: basePath,
          session_id: sessionId || `session-${Date.now()}`,
          folder_name: folderName || undefined
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setExecutionFolder(data.folder_path);
        setFolderCreated(true);
        toast.success(`✅ Folder created: ${data.folder_name}`);
        
        // Show folder structure
        console.log('📁 Folder structure created:', data.subfolders);
      } else {
        toast.error(`Failed to create folder: ${data.error}`);
      }
    } catch (error) {
      console.error('Error creating folder:', error);
      toast.error('Failed to create execution folder');
    }
  }, [basePath, folderName, sessionId]);
  
  /**
   * Deploy source files to execution folder
   */
  const handleDeployFiles = useCallback(async () => {
    if (!executionFolder) {
      toast.error('Please create a folder first');
      return;
    }
    
    if (testCodes.length === 0) {
      toast.error('No test codes available to deploy');
      return;
    }
    
    setIsDeploying(true);
    
    try {
      // Prepare source files from test codes
      const sourceFiles = testCodes.map((testCode, index) => ({
        filename: testCode.filename || `test_${index + 1}.py`,
        content: testCode.code || testCode.test_code || ''
      }));
      
      const response = await fetch('http://localhost:8000/api/remote-execution/deploy-files', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          execution_folder: executionFolder,
          source_files: sourceFiles,
          metadata: {
            process_name: selectedProcessName,
            deployment_source: 'STLC Manager',
            deployment_time: new Date().toISOString(),
            test_count: sourceFiles.length
          }
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setDeploymentStatus('completed');
        setDeployedFiles(data.files || []);
        toast.success(`✅ Deployed ${data.file_count} files`);
      } else {
        setDeploymentStatus('failed');
        toast.error(`Deployment failed: ${data.error}`);
      }
    } catch (error) {
      console.error('Error deploying files:', error);
      setDeploymentStatus('failed');
      toast.error('Failed to deploy files');
    } finally {
      setIsDeploying(false);
    }
  }, [executionFolder, testCodes, selectedProcessName]);
  
  /**
   * Check execution status
   */
  const handleCheckStatus = useCallback(async () => {
    if (!executionFolder) {
      toast.error('No execution folder selected');
      return;
    }
    
    setIsCheckingStatus(true);
    
    try {
      const response = await fetch(
        `http://localhost:8000/api/remote-execution/status/${encodeURIComponent(executionFolder)}`
      );
      
      const data = await response.json();
      
      if (data.success) {
        setExecutionStatus(data);
        setRobotAccessed(data.robot_accessed || false);
        
        // Show status notification
        if (data.has_results) {
          toast.success('✅ Results are available!', {
            icon: '📊',
            duration: 4000
          });
        } else if (data.robot_accessed) {
          toast('Robot has accessed files', {
            icon: '🤖',
            duration: 3000
          });
        } else {
          toast('Waiting for robot execution...', {
            icon: '⏳',
            duration: 2000
          });
        }
      } else {
        toast.error(`Status check failed: ${data.error}`);
      }
    } catch (error) {
      console.error('Error checking status:', error);
      toast.error('Failed to check status');
    } finally {
      setIsCheckingStatus(false);
    }
  }, [executionFolder]);
  
  /**
   * Collect execution results
   */
  const handleCollectResults = useCallback(async () => {
    if (!executionFolder) {
      toast.error('No execution folder selected');
      return;
    }
    
    setIsCollectingResults(true);
    
    try {
      const response = await fetch('http://localhost:8000/api/remote-execution/collect-results', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          execution_folder: executionFolder,
          result_file_pattern: resultFilePattern
        })
      });
      
      const data = await response.json();
      
      if (data.success && data.results_available) {
        setCollectedResults(data);
        toast.success(`✅ Collected ${data.result_count} result files`);
        
        // Notify parent component
        if (onResultsCollected) {
          onResultsCollected(data);
        }
      } else if (data.success && !data.results_available) {
        toast('No results available yet', {
          icon: '⏳',
          duration: 3000
        });
      } else {
        toast.error(`Failed to collect results: ${data.error}`);
      }
    } catch (error) {
      console.error('Error collecting results:', error);
      toast.error('Failed to collect results');
    } finally {
      setIsCollectingResults(false);
    }
  }, [executionFolder, resultFilePattern, onResultsCollected]);
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-50 to-indigo-50 p-6 rounded-lg border border-purple-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <ServerIcon className="w-8 h-8 text-purple-600" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                🤖 Remote Robot Execution
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Deploy test files to remote/local folder for robot consumption
              </p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Step 1: Create Folder */}
      <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
        <div className="flex items-center gap-2 mb-4">
          <div className={clsx(
            "w-8 h-8 rounded-full flex items-center justify-center text-white font-bold",
            folderCreated ? "bg-green-500" : "bg-blue-500"
          )}>
            1
          </div>
          <h4 className="text-md font-semibold text-gray-900">Create Execution Folder</h4>
        </div>
        
        <div className="space-y-4 ml-10">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Base Path (Local or Network)
            </label>
            <input
              type="text"
              value={basePath}
              onChange={(e) => setBasePath(e.target.value)}
              placeholder="C:\test_execution or \\server\share\tests"
              disabled={folderCreated}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50"
            />
            <p className="text-xs text-gray-500 mt-1">
              💡 Use UNC paths (\\server\share) for network locations
            </p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Folder Name (Optional)
            </label>
            <input
              type="text"
              value={folderName}
              onChange={(e) => setFolderName(e.target.value)}
              placeholder="Auto-generated if empty"
              disabled={folderCreated}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50"
            />
          </div>
          
          {executionFolder && (
            <div className="bg-green-50 border border-green-200 rounded-md p-3">
              <p className="text-sm text-green-800">
                <strong>📁 Folder:</strong> {executionFolder}
              </p>
            </div>
          )}
          
          <button
            onClick={handleCreateFolder}
            disabled={folderCreated || !basePath}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <FolderOpenIcon className="w-5 h-5" />
            {folderCreated ? 'Folder Created ✓' : 'Create Folder'}
          </button>
        </div>
      </div>
      
      {/* Step 2: Deploy Files */}
      <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
        <div className="flex items-center gap-2 mb-4">
          <div className={clsx(
            "w-8 h-8 rounded-full flex items-center justify-center text-white font-bold",
            deploymentStatus === 'completed' ? "bg-green-500" : "bg-blue-500"
          )}>
            2
          </div>
          <h4 className="text-md font-semibold text-gray-900">Deploy Test Files</h4>
        </div>
        
        <div className="space-y-4 ml-10">
          <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
            <p className="text-sm text-blue-800">
              <strong>📊 Available Test Codes:</strong> {testCodes.length}
            </p>
            {selectedProcessName && (
              <p className="text-xs text-blue-700 mt-1">
                From process: {selectedProcessName}
              </p>
            )}
          </div>
          
          {deployedFiles.length > 0 && (
            <div className="bg-green-50 border border-green-200 rounded-md p-3">
              <p className="text-sm font-semibold text-green-800 mb-2">
                ✅ Deployed Files:
              </p>
              <ul className="text-xs text-green-700 space-y-1">
                {deployedFiles.slice(0, 5).map((file, idx) => (
                  <li key={idx}>• {file.filename} ({file.size} bytes)</li>
                ))}
                {deployedFiles.length > 5 && (
                  <li className="text-green-600">...and {deployedFiles.length - 5} more files</li>
                )}
              </ul>
            </div>
          )}
          
          <button
            onClick={handleDeployFiles}
            disabled={!folderCreated || isDeploying || testCodes.length === 0}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <CloudArrowUpIcon className="w-5 h-5" />
            {isDeploying ? 'Deploying...' : deploymentStatus === 'completed' ? 'Files Deployed ✓' : 'Deploy Files'}
          </button>
        </div>
      </div>
      
      {/* Step 3: Monitor Status */}
      <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-8 h-8 rounded-full flex items-center justify-center bg-blue-500 text-white font-bold">
            3
          </div>
          <h4 className="text-md font-semibold text-gray-900">Monitor Execution Status</h4>
        </div>
        
        <div className="space-y-4 ml-10">
          {executionStatus && (
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 border border-gray-200 rounded-md p-3">
                <p className="text-xs text-gray-600 mb-1">Deployment Status</p>
                <p className={clsx(
                  "text-sm font-semibold",
                  executionStatus.deployment_status === 'completed' ? "text-green-600" : "text-yellow-600"
                )}>
                  {executionStatus.deployment_status || 'N/A'}
                </p>
              </div>
              
              <div className="bg-gray-50 border border-gray-200 rounded-md p-3">
                <p className="text-xs text-gray-600 mb-1">Execution Status</p>
                <p className={clsx(
                  "text-sm font-semibold",
                  executionStatus.execution_status === 'completed' ? "text-green-600" : "text-yellow-600"
                )}>
                  {executionStatus.execution_status || 'pending'}
                </p>
              </div>
              
              <div className="bg-gray-50 border border-gray-200 rounded-md p-3">
                <p className="text-xs text-gray-600 mb-1">Robot Access</p>
                <div className="flex items-center gap-2">
                  {robotAccessed ? (
                    <CheckCircleIcon className="w-5 h-5 text-green-600" />
                  ) : (
                    <XCircleIcon className="w-5 h-5 text-gray-400" />
                  )}
                  <p className="text-sm font-semibold">
                    {robotAccessed ? 'Accessed' : 'Not Yet'}
                  </p>
                </div>
              </div>
              
              <div className="bg-gray-50 border border-gray-200 rounded-md p-3">
                <p className="text-xs text-gray-600 mb-1">Results Available</p>
                <div className="flex items-center gap-2">
                  {executionStatus.has_results ? (
                    <CheckCircleIcon className="w-5 h-5 text-green-600" />
                  ) : (
                    <XCircleIcon className="w-5 h-5 text-gray-400" />
                  )}
                  <p className="text-sm font-semibold">
                    {executionStatus.has_results ? `${executionStatus.result_files_count} files` : 'None'}
                  </p>
                </div>
              </div>
            </div>
          )}
          
          <button
            onClick={handleCheckStatus}
            disabled={!folderCreated || isCheckingStatus}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <ArrowPathIcon className={clsx("w-5 h-5", isCheckingStatus && "animate-spin")} />
            {isCheckingStatus ? 'Checking...' : 'Check Status'}
          </button>
        </div>
      </div>
      
      {/* Step 4: Collect Results */}
      <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
        <div className="flex items-center gap-2 mb-4">
          <div className={clsx(
            "w-8 h-8 rounded-full flex items-center justify-center text-white font-bold",
            collectedResults ? "bg-green-500" : "bg-blue-500"
          )}>
            4
          </div>
          <h4 className="text-md font-semibold text-gray-900">Collect Results</h4>
        </div>
        
        <div className="space-y-4 ml-10">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Result File Pattern
            </label>
            <input
              type="text"
              value={resultFilePattern}
              onChange={(e) => setResultFilePattern(e.target.value)}
              placeholder="*.json"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              💡 Use glob patterns like *.json, *.xml, or test_results_*.log
            </p>
          </div>
          
          {collectedResults && collectedResults.aggregated && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h5 className="text-sm font-semibold text-green-900 mb-3 flex items-center gap-2">
                <DocumentTextIcon className="w-5 h-5" />
                Aggregated Results
              </h5>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <p className="text-xs text-green-700">Total Tests</p>
                  <p className="text-lg font-bold text-green-900">
                    {collectedResults.aggregated.total_tests}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-green-700">Pass Rate</p>
                  <p className="text-lg font-bold text-green-900">
                    {collectedResults.aggregated.pass_rate}%
                  </p>
                </div>
                <div>
                  <p className="text-xs text-green-700">Passed</p>
                  <p className="text-lg font-bold text-green-600">
                    {collectedResults.aggregated.passed}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-green-700">Failed</p>
                  <p className="text-lg font-bold text-red-600">
                    {collectedResults.aggregated.failed}
                  </p>
                </div>
              </div>
              <p className="text-xs text-green-700 mt-3 pt-3 border-t border-green-200">
                {collectedResults.aggregated.summary}
              </p>
            </div>
          )}
          
          <button
            onClick={handleCollectResults}
            disabled={!folderCreated || isCollectingResults}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <CloudArrowDownIcon className="w-5 h-5" />
            {isCollectingResults ? 'Collecting...' : collectedResults ? 'Results Collected ✓' : 'Collect Results'}
          </button>
        </div>
      </div>
      
      {/* Robot Instructions */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <h5 className="text-sm font-semibold text-yellow-900 mb-2">
          🤖 Robot Instructions
        </h5>
        <ol className="text-xs text-yellow-800 space-y-1 ml-4 list-decimal">
          <li>Robot reads test files from <code>source_files/</code> folder</li>
          <li>Robot executes tests in its own environment</li>
          <li>Robot writes results to <code>results/</code> folder in JSON format</li>
          <li>Robot writes execution logs to <code>logs/</code> folder</li>
          <li>Robot updates <code>execution_status.json</code> with execution_status='completed'</li>
        </ol>
        <p className="text-xs text-yellow-700 mt-3 pt-2 border-t border-yellow-200">
          💡 <strong>Tip:</strong> Check <code>deployment_info.json</code> in the execution folder for detailed robot instructions
        </p>
      </div>
    </div>
  );
}
