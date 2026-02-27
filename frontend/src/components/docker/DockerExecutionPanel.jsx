import React, { useState, useEffect } from 'react';
import axios from 'axios';

const DockerExecutionPanel = () => {
  // State
  const [testCode, setTestCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [robotType, setRobotType] = useState('generic');
  const [executionMode, setExecutionMode] = useState('standard'); // standard, robot
  const [additionalPackages, setAdditionalPackages] = useState('');
  const [timeout, setTimeout] = useState(300);
  const [showConfig, setShowConfig] = useState(true);
  
  // Docker status
  const [dockerAvailable, setDockerAvailable] = useState(false);
  const [dockerImages, setDockerImages] = useState([]);
  const [containerStatus, setContainerStatus] = useState({});
  
  // Execution state
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState(null);
  const [error, setError] = useState(null);
  
  // Available options
  const [availableRobots, setAvailableRobots] = useState([]);
  const [supportedLanguages, setSupportedLanguages] = useState([]);

  // Load Docker status on mount
  useEffect(() => {
    checkDockerStatus();
    loadAvailableOptions();
  }, []);

  const checkDockerStatus = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/docker-execution/status');
      setDockerAvailable(response.data.docker_available);
      setDockerImages(response.data.images || []);
      setContainerStatus(response.data.container_status || {});
    } catch (error) {
      console.error('Failed to check Docker status:', error);
      setDockerAvailable(false);
    }
  };

  const loadAvailableOptions = async () => {
    try {
      const robotsRes = await axios.get('http://localhost:8000/api/docker-execution/available-robots');
      setAvailableRobots(robotsRes.data.robot_types || [
        { id: 'generic', name: 'Generic 3-DOF', dof: 3 },
        { id: 'industrial', name: 'Industrial 6-DOF', dof: 6 },
        { id: 'collaborative', name: 'Collaborative 4-DOF', dof: 4 }
      ]);
      
      setSupportedLanguages([
        { id: 'python', name: 'Python' }
      ]);
    } catch (error) {
      console.error('Failed to load options:', error);
      // Set defaults on error
      setAvailableRobots([
        { id: 'generic', name: 'Generic 3-DOF', dof: 3 },
        { id: 'industrial', name: 'Industrial 6-DOF', dof: 6 },
        { id: 'collaborative', name: 'Collaborative 4-DOF', dof: 4 }
      ]);
      setSupportedLanguages([{ id: 'python', name: 'Python' }]);
    }
  };

  const handleExecute = async () => {
    if (!testCode.trim()) {
      setError('Please enter test code');
      return;
    }

    setIsExecuting(true);
    setError(null);
    setExecutionResult(null);

    try {
      let endpoint = '';
      let payload = {};

      if (executionMode === 'robot') {
        endpoint = '/api/docker-execution/execute-robot-simulation';
        payload = {
          test_code: testCode,
          robot_type: robotType,
          simulation_config: {
            precision: 'high',
            simulation_speed: 1.0
          }
        };
      } else {
        endpoint = '/api/docker-execution/execute';
        payload = {
          test_code: testCode,
          language: language,
          timeout: timeout
        };
        
        if (additionalPackages.trim()) {
          payload.additional_packages = additionalPackages
            .split(',')
            .map(pkg => pkg.trim())
            .filter(pkg => pkg);
        }
      }

      const response = await axios.post(`http://localhost:8000${endpoint}`, payload, {
        timeout: (timeout + 30) * 1000 // Add buffer to timeout
      });

      setExecutionResult(response.data);
    } catch (error) {
      console.error('Execution error:', error);
      setError(error.response?.data?.detail || error.message || 'Execution failed');
    } finally {
      setIsExecuting(false);
    }
  };

  const loadExampleCode = (mode) => {
    const examples = {
      python: `# Simple Python Test
print("Running tests...")

def test_addition():
    assert 2 + 2 == 4
    print("✅ Addition test passed")

def test_multiplication():
    assert 3 * 4 == 12
    print("✅ Multiplication test passed")

test_addition()
test_multiplication()
print("\\n✅ All tests completed!")`,
      
      robot: `# Robot Arm Movement Test
print("🤖 Starting robot arm test...")

# Move to home position
success, pos = robot.move_to_position([0, 0, 0])
print(f"Home position: {pos}")

# Test workspace positions
positions = [
    [0.5, 0.3, 0.2],
    [0.8, 0.4, 0.3],
    [0.6, -0.2, 0.25]
]

for i, pos in enumerate(positions, 1):
    success, position = robot.move_to_position(pos)
    print(f"Position {i}: {'✅' if success else '❌'} - {position}")

print("\\n✅ Robot test completed!")`,
      
      packages: `# Test with NumPy and Pandas
import numpy as np
import pandas as pd

print("Testing NumPy...")
arr = np.array([1, 2, 3, 4, 5])
print(f"Array: {arr}")
print(f"Mean: {np.mean(arr)}")

print("\\nTesting Pandas...")
df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
print(df)
print("\\n✅ Package test completed!")`
    };

    setTestCode(examples[mode] || examples.python);
    
    if (mode === 'robot') {
      setExecutionMode('robot');
    } else if (mode === 'packages') {
      setAdditionalPackages('numpy,pandas');
      setExecutionMode('standard');
    } else {
      setExecutionMode('standard');
      setAdditionalPackages('');
    }
  };

  return (
    <div className="p-6">
      {/* Main Card */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center mb-4">
            <div className="flex items-center flex-1">
              <svg className="w-8 h-8 text-blue-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" />
              </svg>
              <h2 className="text-2xl font-bold text-gray-800">Docker Sandbox</h2>
            </div>
            <button
              onClick={checkDockerStatus}
              className="p-2 text-gray-600 hover:text-blue-600 hover:bg-gray-100 rounded transition"
              title="Refresh Docker status"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>

          {/* Docker Status Alert */}
          <div className={`p-4 mb-4 rounded-lg flex items-center ${
            dockerAvailable 
              ? 'bg-green-50 text-green-800 border border-green-200' 
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}>
            <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
              {dockerAvailable ? (
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              ) : (
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              )}
            </svg>
            <span className="font-medium">
              Docker is {dockerAvailable ? 'available' : 'not available'}
              {dockerAvailable && ` - ${dockerImages.length} images available`}
            </span>
          </div>

          {/* Execution Mode Selection */}
          <div className="mb-4">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Execution Mode
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => setExecutionMode('standard')}
                className={`px-4 py-2 rounded-lg font-medium transition ${
                  executionMode === 'standard'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Standard Test
              </button>
              <button
                onClick={() => setExecutionMode('robot')}
                className={`px-4 py-2 rounded-lg font-medium transition ${
                  executionMode === 'robot'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                🤖 Robot Simulation
              </button>
            </div>
          </div>

          {/* Configuration Section */}
          <div className="border border-gray-200 rounded-lg mb-4">
            <button
              onClick={() => setShowConfig(!showConfig)}
              className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition"
            >
              <div className="flex items-center">
                <svg className="w-5 h-5 text-gray-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                </svg>
                <span className="font-semibold text-gray-700">Configuration</span>
              </div>
              <svg
                className={`w-5 h-5 text-gray-600 transition-transform ${showConfig ? 'transform rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            
            {showConfig && (
              <div className="p-4 border-t border-gray-200 space-y-4">
                {executionMode === 'robot' ? (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Robot Type
                    </label>
                    <select
                      value={robotType}
                      onChange={(e) => setRobotType(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      {availableRobots.map((robot) => (
                        <option key={robot.id} value={robot.id}>
                          {robot.name} ({robot.dof} DOF)
                        </option>
                      ))}
                    </select>
                  </div>
                ) : (
                  <>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Language
                        </label>
                        <select
                          value={language}
                          onChange={(e) => setLanguage(e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        >
                          {supportedLanguages.map((lang) => (
                            <option key={lang.id} value={lang.id}>
                              {lang.name}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Additional Packages
                        </label>
                        <input
                          type="text"
                          value={additionalPackages}
                          onChange={(e) => setAdditionalPackages(e.target.value)}
                          placeholder="numpy,pandas,requests"
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                        <p className="text-xs text-gray-500 mt-1">Comma-separated package names</p>
                      </div>
                    </div>
                  </>
                )}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Timeout (seconds)
                  </label>
                  <input
                    type="number"
                    value={timeout}
                    onChange={(e) => setTimeout(parseInt(e.target.value))}
                    min="30"
                    max="600"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Example Code Buttons */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Load Example:
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => loadExampleCode('python')}
                className="px-3 py-1.5 text-sm border border-blue-500 text-blue-600 rounded hover:bg-blue-50 transition"
              >
                Simple Python
              </button>
              <button
                onClick={() => loadExampleCode('robot')}
                className="px-3 py-1.5 text-sm border border-blue-500 text-blue-600 rounded hover:bg-blue-50 transition"
              >
                Robot Simulation
              </button>
              <button
                onClick={() => loadExampleCode('packages')}
                className="px-3 py-1.5 text-sm border border-blue-500 text-blue-600 rounded hover:bg-blue-50 transition"
              >
                With Packages
              </button>
            </div>
          </div>

          {/* Test Code Editor */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Test Code
            </label>
            <textarea
              value={testCode}
              onChange={(e) => setTestCode(e.target.value)}
              placeholder="Enter your test code here..."
              rows={15}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              style={{ fontFamily: 'Courier New, monospace' }}
            />
          </div>

          {/* Execute Button */}
          <button
            onClick={handleExecute}
            disabled={!dockerAvailable || isExecuting || !testCode.trim()}
            className={`w-full py-3 rounded-lg font-semibold flex items-center justify-center transition ${
              !dockerAvailable || isExecuting || !testCode.trim()
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {isExecuting ? (
              <>
                <svg className="animate-spin h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Executing in Docker...
              </>
            ) : (
              <>
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                </svg>
                Execute in Docker Container
              </>
            )}
          </button>

          {/* Error Display */}
          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
              <div className="flex items-start">
                <svg className="w-5 h-5 mr-2 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <span>{error}</span>
              </div>
            </div>
          )}

          {/* Execution Results */}
          {executionResult && (
            <div className="mt-6">
              <div className="border-t border-gray-200 my-4"></div>
              <h3 className="text-xl font-bold text-gray-800 mb-3">Execution Results</h3>
              
              <div className={`p-4 mb-4 rounded-lg flex items-center ${
                executionResult.success 
                  ? 'bg-green-50 text-green-800 border border-green-200' 
                  : 'bg-red-50 text-red-800 border border-red-200'
              }`}>
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  {executionResult.success ? (
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  ) : (
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  )}
                </svg>
                <div>
                  <div className="font-semibold">
                    {executionResult.success ? 'Execution Completed Successfully' : 'Execution Failed'}
                  </div>
                  {executionResult.exit_code !== undefined && (
                    <div className="text-sm">Exit Code: {executionResult.exit_code}</div>
                  )}
                </div>
              </div>

              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <div className="bg-gray-50 px-4 py-2 border-b border-gray-200">
                  <span className="text-sm font-semibold text-gray-700">Output:</span>
                </div>
                <pre className="p-4 bg-gray-900 text-gray-100 overflow-auto max-h-96 text-sm font-mono whitespace-pre-wrap break-words">
                  {executionResult.output || 'No output'}
                </pre>
                
                {executionResult.error && (
                  <>
                    <div className="bg-red-50 px-4 py-2 border-t border-red-200">
                      <span className="text-sm font-semibold text-red-700">Error:</span>
                    </div>
                    <div className="p-4 bg-red-900 text-red-100 font-mono text-sm">
                      {executionResult.error}
                    </div>
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Docker Info Card */}
      {dockerAvailable && (
        <div className="bg-white rounded-lg shadow-md mt-4 overflow-hidden">
          <div className="p-6">
            <h3 className="text-lg font-bold text-gray-800 mb-4">Docker Environment Info</h3>
            <div className="grid grid-cols-2 gap-6">
              <div>
                <p className="text-sm font-semibold text-gray-700 mb-2">Available Images:</p>
                <div className="flex flex-wrap gap-2">
                  {dockerImages.slice(0, 5).map((image, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full"
                    >
                      {image}
                    </span>
                  ))}
                  {dockerImages.length > 5 && (
                    <span className="px-2 py-1 bg-gray-200 text-gray-600 text-xs rounded-full border border-gray-300">
                      +{dockerImages.length - 5} more
                    </span>
                  )}
                </div>
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-700 mb-2">Container Status:</p>
                <p className="text-sm text-gray-600">
                  Total Containers: {containerStatus.total_containers || 0}
                </p>
                <p className="text-sm text-gray-600">
                  STLC Containers: {containerStatus.stlc_containers?.length || 0}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DockerExecutionPanel;
