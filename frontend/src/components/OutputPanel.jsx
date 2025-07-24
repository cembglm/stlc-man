import React from 'react';
import ReactMarkdown from 'react-markdown';
import { useSelector } from 'react-redux';
import { Gantt, ViewMode } from 'gantt-task-react';
import "gantt-task-react/dist/index.css";

// Helper function to safely render children in ReactMarkdown components
const safeRenderChildren = (children) => {
  if (children === null || children === undefined) {
    return '';
  }
  
  // If it's a string or number, return as is
  if (typeof children === 'string' || typeof children === 'number' || typeof children === 'boolean') {
    return children;
  }
  
  // If it's a React element, return its text content or a placeholder
  if (React.isValidElement(children)) {
    return '[React Element]';
  }
  
  // If it's an array, process each item
  if (Array.isArray(children)) {
    return children.map(child => safeRenderChildren(child)).join('');
  }
  
  // If it's a DOM node, return its text content
  if (children && typeof children === 'object' && children.nodeType) {
    return children.textContent || '[DOM Node]';
  }
  
  // For other objects, try to convert to JSON, but handle circular references
  if (typeof children === 'object') {
    try {
      return JSON.stringify(children);
    } catch (error) {
      // If JSON.stringify fails (circular reference), return a safe representation
      if (error.message.includes('circular')) {
        return '[Circular Object]';
      }
      return '[Complex Object]';
    }
  }
  
  return String(children);
};

// Test Case Optimization Results Component
function TestCaseOptimizationResults({ sessionId, liveResults }) {
  const [optimizationResults, setOptimizationResults] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState(null);

  React.useEffect(() => {
    if (liveResults) {
      setOptimizationResults(liveResults);
      setLoading(false);
      setError(null);
    } else if (sessionId) {
      fetchOptimizationResults();
    }
  }, [sessionId, liveResults]);
  const fetchOptimizationResults = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // First try to get the process title from the session
      let processTitle = null;
      
      if (sessionId) {
        try {
          const sessionResponse = await fetch(`http://localhost:8000/api/processes/test-scenario-generation/session/${sessionId}`);
          if (sessionResponse.ok) {
            const sessionData = await sessionResponse.json();
            processTitle = sessionData?.processes?.test_case_generation?.selected_process_title || 
                          sessionData?.selected_process_title;
          }
        } catch (err) {
          console.warn('Could not fetch session data, trying alternative approach:', err);
        }
      }
      
      // If no process title from session, get available process titles and use the first one
      if (!processTitle) {
        try {
          const titlesResponse = await fetch('http://localhost:8000/api/test-case-optimization/process-titles');
          if (titlesResponse.ok) {
            const titlesData = await titlesResponse.json();
            if (titlesData.success && titlesData.data.length > 0) {
              processTitle = titlesData.data[0]; // Use first available process title
              console.log('Using first available process title:', processTitle);
            }
          }
        } catch (err) {
          console.warn('Could not fetch process titles:', err);
        }
      }
      
      if (!processTitle) {
        setError('No process title available for optimization results');
        return;
      }

      // Fetch optimization results for this process title
      const response = await fetch(`http://localhost:8000/api/test-case-optimization/results/${encodeURIComponent(processTitle)}`);
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setOptimizationResults(data.data);
        } else {
          setError('No optimization results found');
        }
      } else if (response.status === 404) {
        setError('No optimization results available yet. Run Test Case Optimization first.');
      } else {
        throw new Error(`Failed to fetch optimization results: ${response.status}`);
      }
    } catch (err) {
      console.error('Error fetching optimization results:', err);
      setError(`Error loading optimization results: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
        <div className="flex items-center justify-center py-4">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-500"></div>
          <span className="ml-2 text-gray-600">Loading optimization results...</span>
        </div>
      </div>
    );
  }
  if (error) {
    return (
      <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
        <div className="text-yellow-800">
          <p className="font-medium">Test Case Optimization</p>
          <p className="text-sm mt-1">{error}</p>
          <div className="flex space-x-2 mt-2">
            <button
              onClick={fetchOptimizationResults}
              className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded text-sm hover:bg-yellow-200"
            >
              Retry
            </button>
            <button
              onClick={() => window.open('/test-case-optimization', '_blank')}
              className="px-3 py-1 bg-blue-100 text-blue-800 rounded text-sm hover:bg-blue-200"
            >
              Go to Optimization
            </button>
          </div>
        </div>
      </div>
    );
  }
  if (!optimizationResults) {
    return (
      <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
        <div className="text-blue-800">
          <p className="font-medium">Test Case Optimization</p>
          <p className="text-sm mt-1">No optimization results available yet. Run Test Case Optimization to see results here.</p>
          <div className="flex space-x-2 mt-2">
            <button
              onClick={fetchOptimizationResults}
              className="px-3 py-1 bg-blue-100 text-blue-800 rounded text-sm hover:bg-blue-200"
            >
              Check Again
            </button>
            <button
              onClick={() => window.open('/#test-case-optimization', '_blank')}
              className="px-3 py-1 bg-green-100 text-green-800 rounded text-sm hover:bg-green-200"
            >
              Go to Optimization
            </button>
          </div>
        </div>
      </div>
    );
  }
  return (
    <div className="space-y-4">
      {/* Refresh Button */}
      <div className="flex justify-end">
        <button
          onClick={fetchOptimizationResults}
          disabled={loading}
          className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600 disabled:bg-gray-400"
        >
          {loading ? 'Loading...' : 'Refresh Results'}
        </button>
      </div>
      
      {/* Summary Stats */}
      <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
        <h4 className="font-medium text-blue-800 mb-2">Optimization Summary</h4>
        <div className="grid grid-cols-3 gap-4 text-sm text-blue-700">
          <div>
            <p className="font-medium">Original Test Cases</p>
            <p className="text-lg">{(optimizationResults.unique_test_cases?.length || 0) + (optimizationResults.similar_test_cases?.length || 0)}</p>
          </div>
          <div>
            <p className="font-medium">Unique Test Cases</p>
            <p className="text-lg text-green-600">{optimizationResults.unique_test_cases?.length || 0}</p>
          </div>
          <div>
            <p className="font-medium">Duplicates Removed</p>
            <p className="text-lg text-red-600">{optimizationResults.similar_test_cases?.length || 0}</p>
          </div>
        </div>
      </div>

      {/* Unique Test Cases */}
      <div className="bg-green-50 border border-green-200 rounded-md p-4">
        <h4 className="font-medium text-green-800 mb-2">
          ✅ Unique Test Cases ({optimizationResults.unique_test_cases?.length || 0})
        </h4>
        <details className="cursor-pointer">
          <summary className="text-sm text-green-700 hover:text-green-900">Click to view details</summary>
          <div className="mt-2 space-y-2">
            {optimizationResults.unique_test_cases?.map((testCase, index) => (
              <div key={index} className="bg-white p-3 rounded border border-green-200">
                <h5 className="font-medium text-gray-900">{testCase.TestCaseID}: {testCase.Title}</h5>
                <p className="text-sm text-gray-600 mt-1">{testCase.Description}</p>
                <p className="text-xs text-gray-500 mt-1"><strong>Objective:</strong> {testCase.Objective}</p>
              </div>
            )) || <p className="text-sm text-gray-500">No unique test cases found.</p>}
          </div>
        </details>
      </div>      {/* Similar Test Cases */}
      {optimizationResults.similar_test_cases?.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
          <h4 className="font-medium text-yellow-800 mb-2">
            🔄 Similar Test Cases Found ({optimizationResults.similar_test_cases.length})
          </h4>
          <details className="cursor-pointer">
            <summary className="text-sm text-yellow-700 hover:text-yellow-900">Click to view duplicates</summary>
            <div className="mt-2 space-y-3">
              {optimizationResults.similar_test_cases.map((duplicate, index) => (
                <div key={index} className="bg-white p-4 rounded border border-yellow-200">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-red-50 p-3 rounded border border-red-200">
                      <h5 className="font-medium text-red-700 mb-2">🗑️ Duplicate (Removed)</h5>
                      <p className="font-medium text-gray-900">{duplicate.DuplicateCase.TestCaseID}: {duplicate.DuplicateCase.Title}</p>
                      <p className="text-sm text-gray-600 mt-1"><strong>Description:</strong> {duplicate.DuplicateCase.Description}</p>
                      <p className="text-xs text-gray-500 mt-1"><strong>Objective:</strong> {duplicate.DuplicateCase.Objective}</p>
                    </div>
                    <div className="bg-green-50 p-3 rounded border border-green-200">
                      <h5 className="font-medium text-green-700 mb-2">✅ Kept (Original)</h5>
                      <p className="font-medium text-gray-900">{duplicate.MatchedWith.TestCaseID}: {duplicate.MatchedWith.Title}</p>
                      <p className="text-sm text-gray-600 mt-1"><strong>Description:</strong> {duplicate.MatchedWith.Description}</p>
                      <p className="text-xs text-gray-500 mt-1"><strong>Objective:</strong> {duplicate.MatchedWith.Objective}</p>
                    </div>
                  </div>
                  <div className="mt-3 pt-3 border-t border-yellow-200">
                    <p className="text-xs text-gray-600">
                      <strong>Reason:</strong> These test cases were found to be contextually similar based on their titles, descriptions, and objectives.
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </details>
        </div>
      )}{/* Comparison Logs Summary */}
      <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
        <h4 className="font-medium text-gray-800 mb-2">
          📊 Comparison Logs ({optimizationResults.comparison_logs?.length || 0} comparisons)
        </h4>
        {optimizationResults.comparison_logs?.length > 0 ? (
          <details className="cursor-pointer">
            <summary className="text-sm text-gray-700 hover:text-gray-900">Click to view detailed comparison logs</summary>
            <div className="mt-2 max-h-96 overflow-y-auto">
              <div className="space-y-3">
                {optimizationResults.comparison_logs.map((log, index) => (
                  <div key={index} className="bg-white p-3 rounded border border-gray-200">
                    <div className="flex justify-between items-start mb-2">
                      <h6 className="font-medium text-gray-900">Comparison #{index + 1}</h6>
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        log.is_same || log.result?.is_same
                          ? 'bg-red-100 text-red-800' 
                          : 'bg-green-100 text-green-800'
                      }`}>
                        {log.is_same || log.result?.is_same ? 'Similar' : 'Different'}
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                      <div className="bg-blue-50 p-2 rounded">
                        <h6 className="font-medium text-blue-800 mb-1">Test Case 1</h6>
                        {(() => {
                          // Flexible key lookup for test case 1
                          const testCase1 = log.test_case_1 || log.Case1 || log.TestCase1 || log.case1;
                          return testCase1 ? (
                            <div className="space-y-1">
                              {Object.entries(testCase1).map(([key, value]) => 
                                value ? (
                                  <div key={key}>
                                    <strong>{key}:</strong> {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                  </div>
                                ) : null
                              )}
                            </div>
                          ) : (
                            <p className="text-gray-500 text-xs">No test case data available</p>
                          );
                        })()}
                      </div>
                      
                      <div className="bg-purple-50 p-2 rounded">
                        <h6 className="font-medium text-purple-800 mb-1">Test Case 2</h6>
                        {(() => {
                          // Flexible key lookup for test case 2
                          const testCase2 = log.test_case_2 || log.Case2 || log.TestCase2 || log.case2;
                          return testCase2 ? (
                            <div className="space-y-1">
                              {Object.entries(testCase2).map(([key, value]) => 
                                value ? (
                                  <div key={key}>
                                    <strong>{key}:</strong> {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                  </div>
                                ) : null
                              )}
                            </div>
                          ) : (
                            <p className="text-gray-500 text-xs">No test case data available</p>
                          );
                        })()}
                      </div>
                    </div>
                    
                    {log.prompt_sent && (
                      <details className="mt-2">
                        <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                          View prompt sent to LLM
                        </summary>
                        <div className="mt-1 bg-gray-100 p-2 rounded text-xs">
                          <pre className="whitespace-pre-wrap">{log.prompt_sent}</pre>
                        </div>
                      </details>
                    )}
                    
                    {log.llm_response && (
                      <details className="mt-2">
                        <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                          View LLM response
                        </summary>
                        <div className="mt-1 bg-gray-100 p-2 rounded text-xs">
                          <pre className="whitespace-pre-wrap">{log.llm_response}</pre>
                        </div>
                      </details>
                    )}
                    
                    {/* Debug: Show raw log data */}
                    <details className="mt-2">
                      <summary className="text-xs text-gray-400 cursor-pointer hover:text-gray-600">
                        View raw comparison data (debug)
                      </summary>
                      <div className="mt-1 bg-gray-50 p-2 rounded text-xs">
                        <pre className="whitespace-pre-wrap">{JSON.stringify(log, null, 2)}</pre>
                      </div>
                    </details>
                  </div>
                ))}
              </div>
            </div>
          </details>
        ) : (
          <p className="text-sm text-gray-600">
            No detailed comparison logs available.
          </p>
        )}
      </div>
    </div>
  );
}

// JSON'dan XML'e dönüştürme fonksiyonu
function jsonToXml(jsonData) {
  try {
    // JSON string ise parse et
    const data = typeof jsonData === 'string' ? JSON.parse(jsonData) : jsonData;
    
    // Eğer bir dizi ise
    if (Array.isArray(data)) {
      let xml = '<TestPlan>\n';
      
      data.forEach(task => {
        xml += '  <Task>\n';
        for (const key in task) {
          // Key adını XML tag formatına çevir (boşlukları kaldır)
          const tagName = key.replace(/\s+/g, '');
          xml += `    <${tagName}>${task[key]}</${tagName}>\n`;
        }
        xml += '  </Task>\n';
      });
      
      xml += '</TestPlan>';
      return xml;
    } else {
      // Tek bir obje ise
      let xml = '<TestPlan>\n  <Task>\n';
      
      for (const key in data) {
        const tagName = key.replace(/\s+/g, '');
        xml += `    <${tagName}>${data[key]}</${tagName}>\n`;
      }
      
      xml += '  </Task>\n</TestPlan>';
      return xml;
    }
  } catch (error) {
    console.error('JSON to XML conversion error:', error);
    return `<!-- Error converting JSON to XML: ${error.message} -->`;
  }
}

// JSON formatını Gantt Chart için task listesine dönüştürme
function jsonToGanttTasks(jsonData) {
  try {
    // JSON string ise parse et
    const data = typeof jsonData === 'string' ? JSON.parse(jsonData) : jsonData;
    
    if (!Array.isArray(data)) {
      console.error('Gantt data is not an array');
      return [];
    }
    
    // Gantt Chart için task listesi oluştur
    return data.map((task, index) => {
      // Tarihleri parse et
      const startDate = parseDate(task["Start Date"]);
      const endDate = parseDate(task["End Date"]);
      
      return {
        id: `task-${index}`,
        name: task["Task Name"],
        start: startDate,
        end: endDate,
        progress: 0, // Varsayılan ilerleme
        type: 'task',
        isDisabled: false,
        styles: { progressColor: '#0275d8', progressSelectedColor: '#0275d8' }
      };
    });
  } catch (error) {
    console.error('JSON to Gantt conversion error:', error);
    return [];
  }
}

// Tarih formatlarını işleme
function parseDate(dateStr) {
  if (!dateStr) return new Date();
  
  // YYYY-MM-DD formatını kontrol et
  if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
    return new Date(dateStr);
  }
  
  // Bugün+N formatını işle (ör: "today+5")
  if (dateStr.toLowerCase().includes('today+')) {
    const daysToAdd = parseInt(dateStr.split('+')[1], 10) || 0;
    const result = new Date();
    result.setDate(result.getDate() + daysToAdd);
    return result;
  }
  
  // Diğer durumlar için geçerli bir tarih döndür
  return new Date(dateStr);
}

// Görevlerin toplam süresine göre uygun görünümü ve sütun genişliğini seçen fonksiyon
function getGanttViewModeAndColumnWidth(tasks) {
  if (!tasks || tasks.length === 0) {
    return { viewMode: ViewMode.Week, columnWidth: 50 };
  }
  // En erken başlangıç ve en geç bitiş tarihini bul
  const minDate = new Date(Math.min(...tasks.map(t => t.start)));
  const maxDate = new Date(Math.max(...tasks.map(t => t.end)));
  const diffDays = Math.ceil((maxDate - minDate) / (1000 * 60 * 60 * 24));

  if (diffDays > 365) {
    return { viewMode: ViewMode.Year, columnWidth: 60 };
  } else if (diffDays > 90) {
    return { viewMode: ViewMode.Month, columnWidth: 60 };
  } else if (diffDays > 30) {
    return { viewMode: ViewMode.Week, columnWidth: 50 };
  } else {
    return { viewMode: ViewMode.Day, columnWidth: 40 };
  }
}

export default function OutputPanel({ output, outputs, activeTab, processes, outputFormats, hideFooter, hideHeader, testCaseOptimizationResults }) {
  const { status: codeReviewStatus, reviews, error: codeReviewError } = useSelector(state => state.codeReview || {});
  const { status: reqStatus, result: reqResult, error: reqError } = useSelector(state => state.requirementAnalysis || {});
  const { status: testPlanningStatus, plans, error: testPlanningError } = useSelector(state => state.testPlanning || {});
  const { status: envSetupStatus, setups, error: envSetupError } = useSelector(state => state.environmentSetup || {});

  const processId = activeTab !== 'pipeline' && activeTab !== 'files' ? activeTab : null;
  const selectedProcess = processes?.find(p => p.id === processId);
  const processOutput = processId && output && output.processId === processId ? output : null;
  const processName = selectedProcess?.name || '';
  const headerTitle = processId ? `${processName} Output` : 'Output';
  
  // Seçilen output formatını al
  const selectedOutputFormat = outputFormats?.[processId];

  const getSampleOutput = () => {
    if (!processId) return null;
    const samples = {
      'code-review': {
        content: "## Code Review Results\n\n### main.js\n- Function `calculateTotal()` lacks input validation\n- Consider adding error handling for edge cases\n\n### utils.js\n- Good use of modular design\n- Line 42: Potential memory leak in event listener",
        status: 'sample',
        timestamp: new Date().toISOString()
      },
      'test-planning': {
        content: "## Test Planning Document\n\n### Test Objectives\n1. Validate user authentication flows\n2. Verify data integrity across transactions\n\n### Test Scenarios\n- Login with valid credentials\n- Login with invalid credentials\n- Password reset flow",
        status: 'sample',
        timestamp: new Date().toISOString()
      },
      'requirement-analysis': {
        content: "## Requirements Analysis\n\n### Functional Requirements\n- User registration system\n- Product catalog browsing\n- Shopping cart functionality\n\n### Non-Functional Requirements\n- System should support 1000 concurrent users\n- Page load time < 2 seconds",
        status: 'sample',
        timestamp: new Date().toISOString()
      },
      'environment-setup': {
        content: "## Environment Setup Guide\n\n### Development Environment\n```\nnpm install\nnpm run setup-dev\n```\n\n### Testing Environment\n```\ndocker-compose up -d\nnpm run setup-test\n```",
        status: 'sample',
        timestamp: new Date().toISOString()
      },
      'test-scenario-generation': {
        content: "## Generated Test Scenarios\n\n### User Authentication\n1. **TC001**: Verify login with valid username and password\n2. **TC002**: Verify login with invalid credentials\n3. **TC003**: Verify password reset functionality\n\n### Shopping Cart\n1. **TC004**: Add single item to cart\n2. **TC005**: Add multiple items to cart",
        status: 'sample',
        timestamp: new Date().toISOString()
      }
    };
    return samples[processId] || {
      content: `# ${processName} Output\n\nRun this process to see actual output here.`,
      status: 'sample',
      timestamp: new Date().toISOString()
    };
  };

  const displayOutput = processOutput || (processId && !output ? getSampleOutput() : output);

  const renderCodeReviewOutput = () => {
    if (codeReviewStatus === 'loading') {
      return <div>Loading code review results...</div>;
    }
    
    if (codeReviewError) {
      return <div className="text-red-600">Error: {codeReviewError}</div>;
    }
    
    if (reviews.length === 0) {
      return <div>No code review results available</div>;
    }
    
    return (
      <div className="prose prose-sm max-w-full break-words overflow-x-auto">
        {reviews.map((review, index) => (
          <div key={index} className="mb-4">
            <ReactMarkdown 
              className="whitespace-pre-wrap break-words overflow-wrap-anywhere"
              components={{
                p: ({children}) => <p className="break-words">{safeRenderChildren(children)}</p>,
                li: ({children}) => <li className="break-words">{safeRenderChildren(children)}</li>,
                td: ({children}) => <td className="break-words max-w-xs">{safeRenderChildren(children)}</td>,
                th: ({children}) => <th className="break-words">{safeRenderChildren(children)}</th>
              }}
            >
              {review}
            </ReactMarkdown>
          </div>
        ))}
      </div>
    );
  };

  const renderTestScenarioContent = (content) => {
    // Test scenario content'i JSON'dan parse etmeye çalış
    try {
      // Markdown content'ten JSON kısmını çıkar
      const jsonMatch = content.match(/```json\n([\s\S]*?)\n```/);
      if (jsonMatch) {
        const jsonData = JSON.parse(jsonMatch[1]);
        
        if (jsonData.TestScenarios && Array.isArray(jsonData.TestScenarios)) {
          return (
            <div className="space-y-6">
              {/* Summary Section */}
              {jsonData.Summary && (
                <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                  <h4 className="font-semibold text-blue-900 mb-2">Summary</h4>
                  <div className="text-sm text-blue-800">
                    <p><strong>Total Scenarios:</strong> {jsonData.Summary.TotalScenarios}</p>
                    {jsonData.Summary.Categories && (
                      <div className="mt-2">
                        <strong>Categories:</strong>
                        <ul className="ml-4 mt-1">
                          {Object.entries(jsonData.Summary.Categories).map(([category, count]) => (
                            <li key={category}>{category}: {count} scenarios</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {jsonData.Summary.Coverage && (
                      <p className="mt-2"><strong>Coverage:</strong> {jsonData.Summary.Coverage}</p>
                    )}
                  </div>
                </div>
              )}
              
              {/* Test Scenarios Grid */}
              <div className="space-y-6 test-scenario-content overflow-safe">
                {jsonData.TestScenarios.map((scenario, index) => (
                  <div key={scenario.ScenarioID || index} className="bg-white rounded-lg border border-gray-200 shadow-sm p-4 w-full overflow-safe">
                    <div className="flex items-start justify-between mb-3 gap-2">
                      <h4 className="text-lg font-semibold text-gray-900 test-scenario-text flex-1 min-w-0">
                        {index + 1}. {scenario.Title}
                      </h4>
                      <div className="flex flex-col items-end space-y-1 flex-shrink-0">
                        {scenario.ScenarioID && (
                          <span className="inline-block px-2 py-1 text-xs font-mono bg-gray-100 text-gray-700 rounded">
                            {scenario.ScenarioID}
                          </span>
                        )}
                        {scenario.Category && (
                          <span className="inline-block px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
                            {scenario.Category}
                          </span>
                        )}
                      </div>
                    </div>
                    
                    <div className="space-y-3 w-full overflow-safe">
                      {scenario.Description && (
                        <div className="w-full overflow-safe">
                          <strong className="text-sm text-gray-700">Description:</strong>
                          <p className="text-sm text-gray-600 mt-1 test-scenario-text leading-relaxed">
                            {scenario.Description}
                          </p>
                        </div>
                      )}
                      
                      {scenario.Objective && (
                        <div className="w-full overflow-safe">
                          <strong className="text-sm text-gray-700">Objective:</strong>
                          <p className="text-sm text-gray-600 mt-1 test-scenario-text leading-relaxed">
                            {scenario.Objective}
                          </p>
                        </div>
                      )}
                      
                      {scenario.Comments && (
                        <div className="w-full overflow-safe">
                          <strong className="text-sm text-gray-700">Comments:</strong>
                          <p className="text-sm text-gray-600 mt-1 test-scenario-text leading-relaxed">
                            {scenario.Comments}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              
              {/* Raw JSON Section (Collapsible) */}
              <details className="mt-6 w-full">
                <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900">
                  View Raw JSON Output
                </summary>
                <div className="mt-2 bg-gray-100 rounded p-4 w-full overflow-hidden">
                  <pre className="text-xs font-mono whitespace-pre-wrap break-words w-full max-w-full overflow-wrap-anywhere word-break-break-word">
                    {JSON.stringify(jsonData, null, 2)}
                  </pre>
                </div>
              </details>
            </div>
          );
        }
      }        // Fallback to markdown if JSON parsing fails
      return (
        <div className="prose prose-sm max-w-full text-gray-600 break-words w-full overflow-hidden">
          <ReactMarkdown 
            className="whitespace-pre-wrap break-words overflow-wrap-anywhere w-full max-w-full"            components={{
              p: ({children}) => <p className="break-words w-full max-w-full overflow-wrap-anywhere word-break-break-word">{safeRenderChildren(children)}</p>,
              li: ({children}) => <li className="break-words w-full max-w-full overflow-wrap-anywhere word-break-break-word">{safeRenderChildren(children)}</li>,
              td: ({children}) => <td className="break-words max-w-xs overflow-wrap-anywhere word-break-break-word">{safeRenderChildren(children)}</td>,
              th: ({children}) => <th className="break-words overflow-wrap-anywhere word-break-break-word">{safeRenderChildren(children)}</th>,
              strong: ({children}) => <strong className="break-words overflow-wrap-anywhere word-break-break-word">{safeRenderChildren(children)}</strong>
            }}
          >
            {content}
          </ReactMarkdown>
        </div>
      );        } catch (error) {
      console.error('Error parsing test scenario content:', error);
      // Fallback to markdown
      return (
        <div className="prose prose-sm max-w-full text-gray-600 break-words w-full overflow-hidden">
          <ReactMarkdown            className="whitespace-pre-wrap break-words overflow-wrap-anywhere w-full max-w-full"
            components={{
              p: ({children}) => <p className="break-words w-full max-w-full overflow-wrap-anywhere word-break-break-word">{safeRenderChildren(children)}</p>,
              li: ({children}) => <li className="break-words w-full max-w-full overflow-wrap-anywhere word-break-break-word">{safeRenderChildren(children)}</li>,
              td: ({children}) => <td className="break-words max-w-xs overflow-wrap-anywhere word-break-break-word">{safeRenderChildren(children)}</td>,
              th: ({children}) => <th className="break-words overflow-wrap-anywhere word-break-break-word">{safeRenderChildren(children)}</th>,
              strong: ({children}) => <strong className="break-words overflow-wrap-anywhere word-break-break-word">{safeRenderChildren(children)}</strong>
            }}
          >
            {content}
          </ReactMarkdown>
        </div>
      );
    }
  };
  const renderTestCaseContent = (output) => {
    // Test case generation sonuçlarını handle et - Enhanced JSON parsing
    try {
      console.log('[OutputPanel] Processing test case output:', output);
      
      if (output && output.data && output.data.test_case_results) {
        const results = output.data.test_case_results;
        const summary = output.data.summary;
        
        return (
          <div className="space-y-6">
            {/* Summary Section */}
            {summary && (
              <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                <h4 className="font-semibold text-green-900 mb-2">Test Case Generation Summary</h4>
                <div className="text-sm text-green-800">
                  <p><strong>Total Scenarios Processed:</strong> {summary.scenarios_processed || 0}</p>
                  <p><strong>Successful Scenarios:</strong> {summary.successful_scenarios || 0}</p>
                  <p><strong>Failed Scenarios:</strong> {summary.failed_scenarios || 0}</p>
                  <p><strong>Total Test Cases Generated:</strong> {summary.total_test_cases || 0}</p>
                  <p><strong>Model Used:</strong> {summary.model_used || 'Unknown'}</p>
                </div>
              </div>
            )}
            
            {/* Test Case Results */}
            <div className="space-y-6">
              {results.map((result, index) => {
                console.log('[OutputPanel] Processing result:', result);
                
                // Enhanced test case parsing - handle both old text format and new JSON format
                let testCases = result.test_cases || [];
                
                // If test_cases is a string (old format), try to parse it
                if (typeof testCases === 'string') {
                  try {
                    const parsed = JSON.parse(testCases);
                    if (parsed.TestCases && Array.isArray(parsed.TestCases)) {
                      testCases = parsed.TestCases;
                    } else if (Array.isArray(parsed)) {
                      testCases = parsed;
                    }
                  } catch (e) {
                    console.warn('[OutputPanel] Failed to parse test cases as JSON:', e);
                    testCases = [];
                  }
                }
                
                // If still no valid test cases and we have a raw_response, try to extract
                if ((!testCases || testCases.length === 0) && result.raw_response) {
                  try {
                    // Try to find JSON pattern in raw response
                    const jsonMatch = result.raw_response.match(/\{[\s\S]*?"TestCases"[\s\S]*?\}/);
                    if (jsonMatch) {
                      const parsed = JSON.parse(jsonMatch[0]);
                      if (parsed.TestCases && Array.isArray(parsed.TestCases)) {
                        testCases = parsed.TestCases;
                      }
                    }
                  } catch (e) {
                    console.warn('[OutputPanel] Failed to extract JSON from raw response:', e);
                  }
                }
                
                return (
                  <div key={result.scenario_id || index} className="bg-white rounded-lg border border-gray-200 shadow-sm">
                    {/* Scenario Header */}
                    <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 rounded-t-lg">
                      <div className="flex items-start justify-between">
                        <div>
                          <h4 className="text-lg font-semibold text-gray-900">
                            {result.scenario_title || `Scenario ${index + 1}`}
                          </h4>
                          <p className="text-sm text-gray-600">
                            Scenario ID: {result.scenario_id} • 
                            Status: <span className={`font-medium ${result.status === 'success' ? 'text-green-600' : 'text-red-600'}`}>
                              {result.status}
                            </span> • 
                            Test Cases: {result.test_cases_count || testCases?.length || 0}
                          </p>
                        </div>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                          result.status === 'success' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {result.status === 'success' ? 'Success' : 'Failed'}
                        </span>
                      </div>
                      
                      {result.status === 'error' && result.error && (
                        <div className="mt-3 bg-red-50 border border-red-200 rounded-md p-3">
                          <p className="text-sm text-red-700">
                            <strong>Error:</strong> {result.error}
                          </p>
                        </div>
                      )}
                      
                      {/* Show summary info if available */}
                      {result.summary && (
                        <div className="mt-3 bg-blue-50 border border-blue-200 rounded-md p-3">
                          <p className="text-sm text-blue-700">
                            <strong>Summary:</strong> {result.summary.Coverage || 'Test case coverage information'}
                          </p>
                          {result.summary.Categories && (
                            <p className="text-sm text-blue-700 mt-1">
                              <strong>Categories:</strong> {Object.entries(result.summary.Categories).map(([cat, count]) => `${cat} (${count})`).join(', ')}
                            </p>
                          )}
                        </div>
                      )}
                    </div>                  
                  {/* Test Cases */}
                  {testCases && testCases.length > 0 && (
                    <div className="p-4">
                      <h5 className="font-medium text-gray-900 mb-4">
                        Generated Test Cases ({testCases.length})
                      </h5>
                      <div className="space-y-4">
                        {testCases.map((testCase, tcIndex) => (
                          <details key={tcIndex} className="bg-gray-50 rounded-lg border border-gray-200">
                            <summary className="cursor-pointer p-4 hover:bg-gray-100 rounded-lg">
                              <div className="flex items-center justify-between">
                                <div>
                                  <h6 className="font-medium text-gray-900">
                                    {testCase.TestCaseID || `TC_${tcIndex + 1}`}: {testCase.Title || 'Untitled Test Case'}
                                  </h6>
                                  <p className="text-sm text-gray-600 mt-1">
                                    {testCase.Category || 'General'}
                                  </p>
                                </div>
                                <div className="text-sm text-gray-500">
                                  Click to expand
                                </div>
                              </div>
                            </summary>
                            
                            <div className="px-4 pb-4 pt-2 border-t border-gray-200 bg-white rounded-b-lg">
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {/* Left Column */}
                                <div className="space-y-3">
                                  <div>
                                    <h6 className="font-medium text-gray-900 mb-1">Description</h6>
                                    <p className="text-sm text-gray-700">
                                      {testCase.Description || 'No description provided'}
                                    </p>
                                  </div>
                                  
                                  <div>
                                    <h6 className="font-medium text-gray-900 mb-1">Objective</h6>
                                    <p className="text-sm text-gray-700">
                                      {testCase.Objective || 'No objective specified'}
                                    </p>
                                  </div>
                                  
                                </div>
                                
                                {/* Right Column */}
                                <div className="space-y-3">
                                  {testCase.Comments && (
                                    <div>
                                      <h6 className="font-medium text-gray-900 mb-1">Comments</h6>
                                      <p className="text-sm text-gray-600 italic">
                                        {testCase.Comments}
                                      </p>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          </details>
                        ))}
                      </div>
                    </div>
                  )}
                    {/* Raw Response and JSON Output (for debugging) */}
                  <div className="px-4 pb-4 space-y-3">
                    {/* Raw LLM Response */}
                    {result.raw_response && (
                      <details className="mt-3">
                        <summary className="text-sm text-gray-500 cursor-pointer hover:text-gray-700">
                          View Raw LLM Response
                        </summary>
                        <div className="mt-2 bg-gray-100 rounded-md p-3">
                          <pre className="text-xs text-gray-600 whitespace-pre-wrap overflow-auto max-h-48">
                            {result.raw_response}
                          </pre>
                        </div>
                      </details>
                    )}
                    
                    {/* Raw JSON Output (parsed test cases) */}
                    {testCases && testCases.length > 0 && (
                      <details className="mt-3">
                        <summary className="text-sm text-gray-500 cursor-pointer hover:text-gray-700">
                          View Raw JSON Output
                        </summary>
                        <div className="mt-2 bg-gray-100 rounded-md p-3">
                          <pre className="text-xs text-gray-600 whitespace-pre-wrap overflow-auto max-h-48 w-full max-w-full overflow-wrap-anywhere word-break-break-word">
                            {JSON.stringify({ TestCases: testCases }, null, 2)}
                          </pre>
                        </div>
                      </details>
                    )}
                    
                    {/* Complete Result JSON (including metadata) */}
                    <details className="mt-3">
                      <summary className="text-sm text-gray-500 cursor-pointer hover:text-gray-700">
                        View Complete Result JSON
                      </summary>
                      <div className="mt-2 bg-gray-100 rounded-md p-3">
                        <pre className="text-xs text-gray-600 whitespace-pre-wrap overflow-auto max-h-48 w-full max-w-full overflow-wrap-anywhere word-break-break-word">
                          {JSON.stringify(result, null, 2)}
                        </pre>
                      </div>
                    </details>
                  </div>
                </div>
              ); // Closing the results.map function
              })} 
            </div>
          </div>
        );
      }
    } catch (error) {
      console.error('Error rendering test case content:', error);
    }
    
    return null;
  };

  const renderTestCaseOptimizationContent = (output) => {
    // Test case optimization sonuçlarını handle et
    try {
      console.log('[OutputPanel] Processing test case optimization output:', output);
      
      if (output && output.results) {
        const results = output.results;
        
        return (
          <div className="space-y-4">
            <section>
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-lg font-medium">Test Case Optimization Results</h3>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                  output.status === 'completed' 
                    ? 'bg-green-100 text-green-800' 
                    : output.status === 'error'
                    ? 'bg-red-100 text-red-800'
                    : 'bg-blue-100 text-blue-800'
                }`}>
                  {output.status === 'completed' ? 'Success' : 
                   output.status === 'error' ? 'Error' : 'Processing'}
                </span>
              </div>
              
              {/* Summary Stats */}
              <div className="bg-blue-50 rounded-lg p-4 border border-blue-200 mb-4">
                <h4 className="font-medium text-blue-800 mb-2">Optimization Summary</h4>
                <div className="grid grid-cols-3 gap-4 text-sm text-blue-700">
                  <div>
                    <p className="font-medium">Original Test Cases</p>
                    <p className="text-lg">
                      {(results.unique_test_cases?.length || 0) + 
                       (results.similar_test_cases?.length || 0)}
                    </p>
                  </div>
                  <div>
                    <p className="font-medium">Unique Test Cases</p>
                    <p className="text-lg text-green-600">{results.unique_test_cases?.length || 0}</p>
                  </div>
                  <div>
                    <p className="font-medium">Duplicates Removed</p>
                    <p className="text-lg text-red-600">{results.similar_test_cases?.length || 0}</p>
                  </div>
                </div>
              </div>

              {/* Unique Test Cases */}
              <div className="bg-green-50 border border-green-200 rounded-md p-4 mb-4">
                <h4 className="font-medium text-green-800 mb-2">
                  ✅ Unique Test Cases ({results.unique_test_cases?.length || 0})
                </h4>
                <details className="cursor-pointer">
                  <summary className="text-sm text-green-700 hover:text-green-900">Click to view details</summary>
                  <div className="mt-2 space-y-2">
                    {results.unique_test_cases?.map((testCase, index) => (
                      <div key={index} className="bg-white p-3 rounded border border-green-200">
                        <h5 className="font-medium text-gray-900">{testCase.TestCaseID}: {testCase.Title}</h5>
                        <p className="text-sm text-gray-600 mt-1">{testCase.Description}</p>
                        <p className="text-xs text-gray-500 mt-1"><strong>Objective:</strong> {testCase.Objective}</p>
                      </div>
                    )) || <p className="text-sm text-gray-500">No unique test cases found.</p>}
                  </div>
                </details>
              </div>

              {/* Similar Test Cases */}
              {results.similar_test_cases?.length > 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-4">
                  <h4 className="font-medium text-yellow-800 mb-2">
                    🔄 Similar Test Cases Found ({results.similar_test_cases.length})
                  </h4>
                  <details className="cursor-pointer">
                    <summary className="text-sm text-yellow-700 hover:text-yellow-900">Click to view duplicates</summary>
                    <div className="mt-2 space-y-3">
                      {results.similar_test_cases.map((duplicate, index) => (
                        <div key={index} className="bg-white p-4 rounded border border-yellow-200">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="bg-red-50 p-3 rounded border border-red-200">
                              <h5 className="font-medium text-red-700 mb-2">🗑️ Duplicate (Removed)</h5>
                              <p className="font-medium text-gray-900">{duplicate.DuplicateCase.TestCaseID}: {duplicate.DuplicateCase.Title}</p>
                              <p className="text-sm text-gray-600 mt-1"><strong>Description:</strong> {duplicate.DuplicateCase.Description}</p>
                              <p className="text-xs text-gray-500 mt-1"><strong>Objective:</strong> {duplicate.DuplicateCase.Objective}</p>
                            </div>
                            <div className="bg-green-50 p-3 rounded border border-green-200">
                              <h5 className="font-medium text-green-700 mb-2">✅ Kept (Original)</h5>
                              <p className="font-medium text-gray-900">{duplicate.MatchedWith.TestCaseID}: {duplicate.MatchedWith.Title}</p>
                              <p className="text-sm text-gray-600 mt-1"><strong>Description:</strong> {duplicate.MatchedWith.Description}</p>
                              <p className="text-xs text-gray-500 mt-1"><strong>Objective:</strong> {duplicate.MatchedWith.Objective}</p>
                            </div>
                          </div>
                          <div className="mt-3 pt-3 border-t border-yellow-200">
                            <p className="text-xs text-gray-600">
                              <strong>Reason:</strong> These test cases were found to be contextually similar based on their titles, descriptions, and objectives.
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </details>
                </div>
              )}

              {/* Comparison Logs */}
              <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
                <h4 className="font-medium text-gray-800 mb-2">
                  📊 Comparison Logs ({results.comparison_logs?.length || 0} comparisons)
                </h4>
                {results.comparison_logs?.length > 0 ? (
                  <details className="cursor-pointer">
                    <summary className="text-sm text-gray-700 hover:text-gray-900">Click to view detailed comparison logs</summary>
                    <div className="mt-2 max-h-96 overflow-y-auto">
                      <div className="space-y-3">
                        {results.comparison_logs.map((log, index) => (
                          <div key={index} className="bg-white p-3 rounded border border-gray-200">
                            <div className="flex justify-between items-start mb-2">
                              <h6 className="font-medium text-gray-900">Comparison #{index + 1}</h6>
                              <span className={`px-2 py-1 text-xs rounded-full ${
                                log.is_same || log.result?.is_same
                                  ? 'bg-red-100 text-red-800' 
                                  : 'bg-green-100 text-green-800'
                              }`}>
                                {log.is_same || log.result?.is_same ? 'Similar' : 'Different'}
                              </span>
                            </div>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                              <div className="bg-blue-50 p-2 rounded">
                                <h6 className="font-medium text-blue-800 mb-1">Test Case 1</h6>
                                {(() => {
                                  // Esnek key kontrolü - Case1, test_case_1, TestCase1 vb. tüm varyasyonları destekle
                                  const testCase1 = log.test_case_1 || log.Case1 || log.TestCase1 || log.case1;
                                  return testCase1 ? (
                                    <div className="space-y-1">
                                      {Object.entries(testCase1).map(([key, value]) => 
                                        value ? (
                                          <div key={key}>
                                            <strong>{key}:</strong> {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                          </div>
                                        ) : null
                                      )}
                                    </div>
                                  ) : (
                                    <p className="text-gray-500 text-xs">No test case data available</p>
                                  );
                                })()}
                              </div>
                              
                              <div className="bg-purple-50 p-2 rounded">
                                <h6 className="font-medium text-purple-800 mb-1">Test Case 2</h6>
                                {(() => {
                                  // Esnek key kontrolü - Case2, test_case_2, TestCase2 vb. tüm varyasyonları destekle
                                  const testCase2 = log.test_case_2 || log.Case2 || log.TestCase2 || log.case2;
                                  return testCase2 ? (
                                    <div className="space-y-1">
                                      {Object.entries(testCase2).map(([key, value]) => 
                                        value ? (
                                          <div key={key}>
                                            <strong>{key}:</strong> {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                          </div>
                                        ) : null
                                      )}
                                    </div>
                                  ) : (
                                    <p className="text-gray-500 text-xs">No test case data available</p>
                                  );
                                })()}
                              </div>
                            </div>
                            
                            {log.prompt_sent && (
                              <details className="mt-2">
                                <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                                  View prompt sent to LLM
                                </summary>
                                <div className="mt-1 bg-gray-100 p-2 rounded text-xs">
                                  <pre className="whitespace-pre-wrap">{log.prompt_sent}</pre>
                                </div>
                              </details>
                            )}
                            
                            {log.llm_response && (
                              <details className="mt-2">
                                <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                                  View LLM response
                                </summary>
                                <div className="mt-1 bg-gray-100 p-2 rounded text-xs">
                                  <pre className="whitespace-pre-wrap">{log.llm_response}</pre>
                                </div>
                              </details>
                            )}
                            
                            {/* Debug: Show raw log data */}
                            <details className="mt-2">
                              <summary className="text-xs text-gray-400 cursor-pointer hover:text-gray-600">
                                View raw comparison data (debug)
                              </summary>
                              <div className="mt-1 bg-gray-50 p-2 rounded text-xs">
                                <pre className="whitespace-pre-wrap">{JSON.stringify(log, null, 2)}</pre>
                              </div>
                            </details>
                          </div>
                        ))}
                      </div>
                    </div>
                  </details>
                ) : (
                  <p className="text-sm text-gray-600">
                    No detailed comparison logs available.
                  </p>
                )}
              </div>
            </section>
            
            <section>
              <h3 className="text-lg font-medium mb-3">Execution Details</h3>
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 shadow-sm">
                <div className="text-gray-600">
                  <p><strong>Status:</strong> {output.status || 'completed'}</p>
                  <p><strong>Process:</strong> Test Case Optimization</p>
                  <p><strong>Last Updated:</strong> {new Date(output.timestamp).toLocaleString()}</p>
                </div>
              </div>
            </section>
          </div>
        );
      }
    } catch (error) {
      console.error('Error rendering test case optimization content:', error);
    }
    
    return null;
  };

  const renderContent = () => {
    // Test Case Optimization için özel gösterim
    if (activeTab === 'test-case-optimization') {
      // Use testCaseOptimizationResults if available, otherwise check outputs
      if (testCaseOptimizationResults) {
        return (
          <div className="space-y-4">
            <section>
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-lg font-medium">Test Case Optimization Results</h3>
                <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                  Success
                </span>
              </div>
              
              {/* Optimization Summary */}
              <div className="bg-blue-50 rounded-lg p-4 border border-blue-200 mb-4">
                <h4 className="font-medium text-blue-800 mb-2">Optimization Summary</h4>
                <div className="grid grid-cols-3 gap-4 text-sm text-blue-700">
                  <div>
                    <p className="font-medium">Original Test Cases</p>
                    <p className="text-lg">
                      {(testCaseOptimizationResults.unique_test_cases?.length || 0) + 
                       (testCaseOptimizationResults.similar_test_cases?.length || 0)}
                    </p>
                  </div>
                  <div>
                    <p className="font-medium">Unique Test Cases</p>
                    <p className="text-lg text-green-600">{testCaseOptimizationResults.unique_test_cases?.length || 0}</p>
                  </div>
                  <div>
                    <p className="font-medium">Duplicates Removed</p>
                    <p className="text-lg text-red-600">{testCaseOptimizationResults.similar_test_cases?.length || 0}</p>
                  </div>
                </div>
              </div>

              {/* Unique Test Cases */}
              <div className="bg-green-50 border border-green-200 rounded-md p-4 mb-4">
                <h4 className="font-medium text-green-800 mb-2">
                  ✅ Unique Test Cases ({testCaseOptimizationResults.unique_test_cases?.length || 0})
                </h4>
                <details className="cursor-pointer">
                  <summary className="text-sm text-green-700 hover:text-green-900">Click to view details</summary>
                  <div className="mt-2 space-y-2">
                    {testCaseOptimizationResults.unique_test_cases?.map((testCase, index) => (
                      <div key={index} className="bg-white p-3 rounded border border-green-200">
                        <h5 className="font-medium text-gray-900">{testCase.TestCaseID}: {testCase.Title}</h5>
                        <p className="text-sm text-gray-600 mt-1">{testCase.Description}</p>
                        <p className="text-xs text-gray-500 mt-1"><strong>Objective:</strong> {testCase.Objective}</p>
                      </div>
                    )) || <p className="text-sm text-gray-500">No unique test cases found.</p>}
                  </div>
                </details>
              </div>

              {/* Similar Test Cases */}
              {testCaseOptimizationResults.similar_test_cases?.length > 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-4">
                  <h4 className="font-medium text-yellow-800 mb-2">
                    🔄 Similar Test Cases Found ({testCaseOptimizationResults.similar_test_cases.length})
                  </h4>
                  <details className="cursor-pointer">
                    <summary className="text-sm text-yellow-700 hover:text-yellow-900">Click to view duplicates</summary>
                    <div className="mt-2 space-y-3">
                      {testCaseOptimizationResults.similar_test_cases.map((duplicate, index) => (
                        <div key={index} className="bg-white p-4 rounded border border-yellow-200">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="bg-red-50 p-3 rounded border border-red-200">
                              <h5 className="font-medium text-red-700 mb-2">🗑️ Duplicate (Removed)</h5>
                              <p className="font-medium text-gray-900">{duplicate.DuplicateCase?.TestCaseID}: {duplicate.DuplicateCase?.Title}</p>
                              <p className="text-sm text-gray-600 mt-1"><strong>Description:</strong> {duplicate.DuplicateCase?.Description}</p>
                              <p className="text-xs text-gray-500 mt-1"><strong>Objective:</strong> {duplicate.DuplicateCase?.Objective}</p>
                            </div>
                            <div className="bg-green-50 p-3 rounded border border-green-200">
                              <h5 className="font-medium text-green-700 mb-2">✅ Kept (Original)</h5>
                              <p className="font-medium text-gray-900">{duplicate.MatchedWith?.TestCaseID}: {duplicate.MatchedWith?.Title}</p>
                              <p className="text-sm text-gray-600 mt-1"><strong>Description:</strong> {duplicate.MatchedWith?.Description}</p>
                              <p className="text-xs text-gray-500 mt-1"><strong>Objective:</strong> {duplicate.MatchedWith?.Objective}</p>
                            </div>
                          </div>
                          <div className="mt-3 pt-3 border-t border-yellow-200">
                            <p className="text-xs text-gray-600">
                              <strong>Reason:</strong> These test cases were found to be contextually similar based on their titles, descriptions, and objectives.
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </details>
                </div>
              )}

              {/* Comparison Logs */}
              <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
                <h4 className="font-medium text-gray-800 mb-2">
                  📊 Comparison Logs ({testCaseOptimizationResults.comparison_logs?.length || 0} comparisons)
                </h4>
                {testCaseOptimizationResults.comparison_logs?.length > 0 ? (
                  <details className="cursor-pointer">
                    <summary className="text-sm text-gray-700 hover:text-gray-900">Click to view detailed comparison logs</summary>
                    <div className="mt-2 max-h-96 overflow-y-auto">
                      <div className="space-y-3">
                        {testCaseOptimizationResults.comparison_logs.map((log, index) => (
                          <div key={index} className="bg-white p-3 rounded border border-gray-200">
                            <div className="flex justify-between items-start mb-2">
                              <h6 className="font-medium text-gray-900">Comparison #{index + 1}</h6>
                              <span className={`px-2 py-1 text-xs rounded-full ${
                                log.is_same || log.result?.is_same
                                  ? 'bg-red-100 text-red-800' 
                                  : 'bg-green-100 text-green-800'
                              }`}>
                                {log.is_same || log.result?.is_same ? 'Similar' : 'Different'}
                              </span>
                            </div>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                              <div className="bg-blue-50 p-2 rounded">
                                <h6 className="font-medium text-blue-800 mb-1">Test Case 1</h6>
                                {(() => {
                                  // Flexible key lookup for test case 1
                                  const testCase1 = log.test_case_1 || log.Case1 || log.TestCase1 || log.case1;
                                  return testCase1 ? (
                                    <div className="space-y-1">
                                      {Object.entries(testCase1).map(([key, value]) => 
                                        value ? (
                                          <div key={key}>
                                            <strong>{key}:</strong> {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                          </div>
                                        ) : null
                                      )}
                                    </div>
                                  ) : (
                                    <p className="text-gray-500 text-xs">No test case data available</p>
                                  );
                                })()}
                              </div>
                              
                              <div className="bg-purple-50 p-2 rounded">
                                <h6 className="font-medium text-purple-800 mb-1">Test Case 2</h6>
                                {(() => {
                                  // Flexible key lookup for test case 2
                                  const testCase2 = log.test_case_2 || log.Case2 || log.TestCase2 || log.case2;
                                  return testCase2 ? (
                                    <div className="space-y-1">
                                      {Object.entries(testCase2).map(([key, value]) => 
                                        value ? (
                                          <div key={key}>
                                            <strong>{key}:</strong> {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                          </div>
                                        ) : null
                                      )}
                                    </div>
                                  ) : (
                                    <p className="text-gray-500 text-xs">No test case data available</p>
                                  );
                                })()}
                              </div>
                            </div>
                            
                            {log.prompt_sent && (
                              <details className="mt-2">
                                <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                                  View prompt sent to LLM
                                </summary>
                                <div className="mt-1 bg-gray-100 p-2 rounded text-xs">
                                  <pre className="whitespace-pre-wrap">{log.prompt_sent}</pre>
                                </div>
                              </details>
                            )}
                            
                            {log.llm_response && (
                              <details className="mt-2">
                                <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                                  View LLM response
                                </summary>
                                <div className="mt-1 bg-gray-100 p-2 rounded text-xs">
                                  <pre className="whitespace-pre-wrap">{log.llm_response}</pre>
                                </div>
                              </details>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  </details>
                ) : (
                  <p className="text-sm text-gray-600">
                    No detailed comparison logs available.
                  </p>
                )}
              </div>

              <section>
                <h3 className="text-lg font-medium mb-3">Execution Details</h3>
                <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 shadow-sm">
                  <div className="text-gray-600">
                    <p><strong>Status:</strong> Completed</p>
                    <p><strong>Process:</strong> Test Case Optimization</p>
                    <p><strong>Last Updated:</strong> {new Date().toLocaleString()}</p>
                  </div>
                </div>
              </section>
            </section>
          </div>
        );
      } else if (outputs && outputs[activeTab] && outputs[activeTab].type === 'test-case-optimization') {
        const optimizationOutput = outputs[activeTab];
        return (
          <div className="space-y-4">
            <section>
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-lg font-medium">Test Case Optimization Results</h3>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                  optimizationOutput.status === 'completed' 
                    ? 'bg-green-100 text-green-800' 
                    : optimizationOutput.status === 'error'
                    ? 'bg-red-100 text-red-800'
                    : 'bg-blue-100 text-blue-800'
                }`}>
                  {optimizationOutput.status === 'completed' ? 'Success' : 
                   optimizationOutput.status === 'error' ? 'Error' : 'Processing'}
                </span>
              </div>
              
              {optimizationOutput.results && (
                <>
                  {/* Optimization Summary */}
                  <div className="bg-blue-50 rounded-lg p-4 border border-blue-200 mb-4">
                    <h4 className="font-medium text-blue-800 mb-2">Optimization Summary</h4>
                    <div className="grid grid-cols-3 gap-4 text-sm text-blue-700">
                      <div>
                        <p className="font-medium">Original Test Cases</p>
                        <p className="text-lg">
                          {(optimizationOutput.results.unique_test_cases?.length || 0) + 
                           (optimizationOutput.results.similar_test_cases?.length || 0)}
                        </p>
                      </div>
                      <div>
                        <p className="font-medium">Unique Test Cases</p>
                        <p className="text-lg text-green-600">{optimizationOutput.results.unique_test_cases?.length || 0}</p>
                      </div>
                      <div>
                        <p className="font-medium">Duplicates Removed</p>
                        <p className="text-lg text-red-600">{optimizationOutput.results.similar_test_cases?.length || 0}</p>
                      </div>
                    </div>
                  </div>

                  {/* Unique Test Cases */}
                  <div className="bg-green-50 border border-green-200 rounded-md p-4 mb-4">
                    <h4 className="font-medium text-green-800 mb-2">
                      ✅ Unique Test Cases ({optimizationOutput.results.unique_test_cases?.length || 0})
                    </h4>
                    <details className="cursor-pointer">
                      <summary className="text-sm text-green-700 hover:text-green-900">Click to view details</summary>
                      <div className="mt-2 space-y-2">
                        {optimizationOutput.results.unique_test_cases?.map((testCase, index) => (
                          <div key={index} className="bg-white p-3 rounded border border-green-200">
                            <h5 className="font-medium text-gray-900">{testCase.TestCaseID}: {testCase.Title}</h5>
                            <p className="text-sm text-gray-600 mt-1">{testCase.Description}</p>
                            <p className="text-xs text-gray-500 mt-1"><strong>Objective:</strong> {testCase.Objective}</p>
                          </div>
                        )) || <p className="text-sm text-gray-500">No unique test cases found.</p>}
                      </div>
                    </details>
                  </div>                  {/* Similar Test Cases */}
                  {optimizationOutput.results.similar_test_cases?.length > 0 && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-4">
                      <h4 className="font-medium text-yellow-800 mb-2">
                        🔄 Similar Test Cases Found ({optimizationOutput.results.similar_test_cases.length})
                      </h4>
                      <details className="cursor-pointer">
                        <summary className="text-sm text-yellow-700 hover:text-yellow-900">Click to view duplicates</summary>
                        <div className="mt-2 space-y-3">
                          {optimizationOutput.results.similar_test_cases.map((duplicate, index) => (
                            <div key={index} className="bg-white p-4 rounded border border-yellow-200">
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="bg-red-50 p-3 rounded border border-red-200">
                                  <h5 className="font-medium text-red-700 mb-2">🗑️ Duplicate (Removed)</h5>
                                  <p className="font-medium text-gray-900">{duplicate.DuplicateCase.TestCaseID}: {duplicate.DuplicateCase.Title}</p>
                                  <p className="text-sm text-gray-600 mt-1"><strong>Description:</strong> {duplicate.DuplicateCase.Description}</p>
                                  <p className="text-xs text-gray-500 mt-1"><strong>Objective:</strong> {duplicate.DuplicateCase.Objective}</p>
                                </div>
                                <div className="bg-green-50 p-3 rounded border border-green-200">
                                  <h5 className="font-medium text-green-700 mb-2">✅ Kept (Original)</h5>
                                  <p className="font-medium text-gray-900">{duplicate.MatchedWith.TestCaseID}: {duplicate.MatchedWith.Title}</p>
                                  <p className="text-sm text-gray-600 mt-1"><strong>Description:</strong> {duplicate.MatchedWith.Description}</p>
                                  <p className="text-xs text-gray-500 mt-1"><strong>Objective:</strong> {duplicate.MatchedWith.Objective}</p>
                                </div>
                              </div>
                              <div className="mt-3 pt-3 border-t border-yellow-200">
                                <p className="text-xs text-gray-600">
                                  <strong>Reason:</strong> These test cases were found to be contextually similar based on their titles, descriptions, and objectives.
                                </p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </details>
                    </div>
                  )}{/* Comparison Logs Summary */}
                  <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
                    <h4 className="font-medium text-gray-800 mb-2">
                      📊 Comparison Logs ({optimizationOutput.results.comparison_logs?.length || 0} comparisons)
                    </h4>
                    {optimizationOutput.results.comparison_logs?.length > 0 ? (
                      <details className="cursor-pointer">
                        <summary className="text-sm text-gray-700 hover:text-gray-900">Click to view detailed comparison logs</summary>
                        <div className="mt-2 max-h-96 overflow-y-auto">
                          <div className="space-y-3">
                            {optimizationOutput.results.comparison_logs.map((log, index) => (
                              <div key={index} className="bg-white p-3 rounded border border-gray-200">
                                <div className="flex justify-between items-start mb-2">
                                  <h6 className="font-medium text-gray-900">Comparison #{index + 1}</h6>
                                  <span className={`px-2 py-1 text-xs rounded-full ${
                                    log.is_same || log.result?.is_same
                                      ? 'bg-red-100 text-red-800' 
                                      : 'bg-green-100 text-green-800'
                                  }`}>
                                    {log.is_same || log.result?.is_same ? 'Similar' : 'Different'}
                                  </span>
                                </div>
                                
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                                  <div className="bg-blue-50 p-2 rounded">
                                    <h6 className="font-medium text-blue-800 mb-1">Test Case 1</h6>
                                    {(() => {
                                      // Flexible key lookup for test case 1
                                      const testCase1 = log.test_case_1 || log.Case1 || log.TestCase1 || log.case1;
                                      return testCase1 ? (
                                        <div className="space-y-1">
                                          {Object.entries(testCase1).map(([key, value]) => 
                                            value ? (
                                              <div key={key}>
                                                <strong>{key}:</strong> {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                              </div>
                                            ) : null
                                          )}
                                        </div>
                                      ) : (
                                        <p className="text-gray-500 text-xs">No test case data available</p>
                                      );
                                    })()}
                                  </div>
                                  
                                  <div className="bg-purple-50 p-2 rounded">
                                    <h6 className="font-medium text-purple-800 mb-1">Test Case 2</h6>
                                    {(() => {
                                      // Flexible key lookup for test case 2
                                      const testCase2 = log.test_case_2 || log.Case2 || log.TestCase2 || log.case2;
                                      return testCase2 ? (
                                        <div className="space-y-1">
                                          {Object.entries(testCase2).map(([key, value]) => 
                                            value ? (
                                              <div key={key}>
                                                <strong>{key}:</strong> {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                              </div>
                                            ) : null
                                          )}
                                        </div>
                                      ) : (
                                        <p className="text-gray-500 text-xs">No test case data available</p>
                                      );
                                    })()}
                                  </div>
                                </div>
                                
                                {log.prompt_sent && (
                                  <details className="mt-2">
                                    <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                                      View prompt sent to LLM
                                    </summary>
                                    <div className="mt-1 bg-gray-100 p-2 rounded text-xs">
                                      <pre className="whitespace-pre-wrap">{log.prompt_sent}</pre>
                                    </div>
                                  </details>
                                )}
                                
                                {log.llm_response && (
                                  <details className="mt-2">
                                    <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                                      View LLM response
                                    </summary>
                                    <div className="mt-1 bg-gray-100 p-2 rounded text-xs">
                                      <pre className="whitespace-pre-wrap">{log.llm_response}</pre>
                                    </div>
                                  </details>
                                )}
                                
                                {/* Debug: Show raw log data */}
                                <details className="mt-2">
                                  <summary className="text-xs text-gray-400 cursor-pointer hover:text-gray-600">
                                    View raw comparison data (debug)
                                  </summary>
                                  <div className="mt-1 bg-gray-50 p-2 rounded text-xs">
                                    <pre className="whitespace-pre-wrap">{JSON.stringify(log, null, 2)}</pre>
                                  </div>
                                </details>
                              </div>
                            ))}
                          </div>
                        </div>
                      </details>
                    ) : (
                      <p className="text-sm text-gray-600">
                        No detailed comparison logs available.
                      </p>
                    )}
                  </div>
                </>
              )}
            </section>

            <section>
              <h3 className="text-lg font-medium mb-3">Execution Details</h3>
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 shadow-sm">
                <div className="text-gray-600">
                  <p><strong>Status:</strong> {optimizationOutput.status || 'completed'}</p>
                  <p><strong>Process:</strong> Test Case Optimization</p>
                  <p><strong>Last Updated:</strong> {new Date(optimizationOutput.timestamp).toLocaleString()}</p>
                </div>
              </div>
            </section>
          </div>
        );
      } else {
        // No results yet
        return (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="text-gray-400 mb-4">
                <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012-2m-6 9l2 2 4-4" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Optimization Results</h3>
              <p className="text-gray-500">Run Test Case Optimization to see results here.</p>
            </div>
          </div>
        );
      }
    }

    if (activeTab === 'test-scenario-generation' && outputs && outputs[activeTab]) {
      const testScenarioOutput = outputs[activeTab];
      return (
        <div className="space-y-4">
          <section>
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-lg font-medium">Test Scenario Generation Results</h3>
              <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                testScenarioOutput.status === 'completed' 
                  ? 'bg-green-100 text-green-800' 
                  : testScenarioOutput.status === 'error'
                  ? 'bg-red-100 text-red-800'
                  : 'bg-blue-100 text-blue-800'
              }`}>
                {testScenarioOutput.status === 'completed' ? 'Success' : 
                 testScenarioOutput.status === 'error' ? 'Error' : 'Processing'}
              </span>
            </div>
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 shadow-sm overflow-hidden">
              <div className="max-w-full overflow-x-auto">
                {renderTestScenarioContent(testScenarioOutput.content)}
              </div>
            </div>
          </section>
          <section>
            <h3 className="text-lg font-medium mb-3">Execution Details</h3>
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 shadow-sm">
              <div className="text-gray-600">
                <p><strong>Status:</strong> {testScenarioOutput.status}</p>
                <p><strong>Process:</strong> {testScenarioOutput.processType || 'Test Scenario Generation'}</p>
                <p><strong>Process ID:</strong> {testScenarioOutput.processId}</p>
                <p><strong>Last Updated:</strong> {new Date(testScenarioOutput.timestamp).toLocaleString()}</p>
              </div>
            </div>
          </section>
        </div>
      );
    }

    // Check for test-case-generation specific output
    if (activeTab === 'test-case-generation' && outputs && outputs[activeTab]) {
      const testCaseOutput = outputs[activeTab];
      const testCaseContent = renderTestCaseContent(testCaseOutput);
      
      if (testCaseContent) {
        return (
          <div className="space-y-6">
            <section>
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-lg font-medium">Test Case Generation Results</h3>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                  testCaseOutput.status === 'completed' 
                    ? 'bg-green-100 text-green-800' 
                    : testCaseOutput.status === 'error'
                    ? 'bg-red-100 text-red-800'
                    : 'bg-blue-100 text-blue-800'
                }`}>
                  {testCaseOutput.status === 'completed' ? 'Success' : 
                   testCaseOutput.status === 'error' ? 'Error' : 'Processing'}
                </span>
              </div>
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 shadow-sm overflow-hidden">
                <div className="max-w-full overflow-x-auto">
                  {testCaseContent}
                </div>
              </div>
            </section>
            
            {/* Test Case Optimization Output Section */}
            <section>
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-lg font-medium">Test Case Optimization Output</h3>
                <div className="text-sm text-gray-500">Process Results</div>
              </div>
              <TestCaseOptimizationResults sessionId={testCaseOutput.sessionId} liveResults={testCaseOptimizationResults} />
            </section>
            
            <section>
              <h3 className="text-lg font-medium mb-3">Execution Details</h3>
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 shadow-sm">
                <div className="text-gray-600">
                  <p><strong>Status:</strong> {testCaseOutput.status}</p>
                  <p><strong>Process:</strong> Test Case Generation</p>
                  <p><strong>Process ID:</strong> {testCaseOutput.processId}</p>
                  <p><strong>Last Updated:</strong> {testCaseOutput.timestamp ? new Date(testCaseOutput.timestamp).toLocaleString() : new Date().toLocaleString()}</p>
                </div>
              </div>
            </section>
          </div>
        );
      }
    }
    
    let currentOutput = { ...getSampleOutput() };

    if (activeTab === 'code-review') {
      if (codeReviewStatus === 'loading') {
        return <div>Loading code review results...</div>;
      }
      if (codeReviewError) {
        return <div className="text-red-600">Error: {codeReviewError}</div>;
      }
      if (reviews && reviews.length > 0) {
        const reviewContent = reviews.map(review => review).join('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
        currentOutput = {
          content: reviewContent,
          status: 'completed',
          timestamp: new Date().toISOString(),
          processType: 'Code Review'
        };
      }
    }

    if (activeTab === 'requirement-analysis') {
      if (reqStatus === 'loading') {
        return <div>Loading requirement analysis results...</div>;
      }
      if (reqError) {
        return <div className="text-red-600">Error: {reqError}</div>;
      }
      if (reqResult && Array.isArray(reqResult.analysis) && reqResult.analysis.length > 0) {
        const analysisContent = reqResult.analysis.map(item => `**Files Analyzed:**\n${item.files}\n\n**Analysis:**\n${item.result}`).join('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
        return (
          <div className="space-y-4">
            <section>
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-lg font-medium">Process Results</h3>
              </div>              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 shadow-sm overflow-x-auto">
                <div className="prose prose-sm max-w-full text-gray-600 break-words">
                  <ReactMarkdown 
                    className="whitespace-pre-wrap break-words overflow-wrap-anywhere"
                    components={{
                      p: ({children}) => <p className="break-words">{safeRenderChildren(children)}</p>,
                      li: ({children}) => <li className="break-words">{safeRenderChildren(children)}</li>,
                      td: ({children}) => <td className="break-words max-w-xs">{safeRenderChildren(children)}</td>,
                      th: ({children}) => <th className="break-words">{safeRenderChildren(children)}</th>
                    }}
                  >
                    {analysisContent}
                  </ReactMarkdown>
                </div>
              </div>
            </section>
            <section>
              <h3 className="text-lg font-medium mb-3">Execution Details</h3>
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 shadow-sm">
                <div className="text-gray-600">
                  <p><strong>Status:</strong> completed</p>
                  <p><strong>Process:</strong> Requirement Analysis</p>
                  <p><strong>Last Updated:</strong> {new Date().toLocaleString()}</p>
                </div>
              </div>
            </section>
          </div>
        );
      }
      // Sample göster
      return (
        <div className="space-y-4">
          <section>
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-lg font-medium">Process Results</h3>
              <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                Sample
              </span>
            </div>
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 shadow-sm overflow-x-auto">
              <div className="prose prose-sm max-w-full text-gray-600 break-words">
                <ReactMarkdown 
                  className="whitespace-pre-wrap break-words overflow-wrap-anywhere"
                  components={{
                    p: ({children}) => <p className="break-words">{safeRenderChildren(children)}</p>,
                    li: ({children}) => <li className="break-words">{safeRenderChildren(children)}</li>,
                    td: ({children}) => <td className="break-words max-w-xs">{safeRenderChildren(children)}</td>,
                    th: ({children}) => <th className="break-words">{safeRenderChildren(children)}</th>
                  }}
                >
                  {getSampleOutput().content}
                </ReactMarkdown>
              </div>
            </div>
          </section>
          <section>
            <h3 className="text-lg font-medium mb-3">Execution Details</h3>
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 shadow-sm">
              <div className="text-gray-600">                <p><strong>Status:</strong> Not Run</p>
                <p><strong>Process:</strong> Requirement Analysis</p>
                <p><strong>Last Updated:</strong> {new Date().toLocaleString()}</p>
              </div>
            </div>
          </section>
        </div>
      );
    }

    if (activeTab === 'test-planning') {
      if (testPlanningStatus === 'loading') {
        return <div>Loading test planning results...</div>;
      }
      if (testPlanningError) {
        return <div className="text-red-600">Error: {testPlanningError}</div>;
      }
      if (plans && plans.length > 0) {
        // Text olarak gelen JSON planını çıkar
        let planContent = plans[0];
        const jsonMatch = planContent.match(/```json\n([\s\S]*?)```/);
        let jsonContent = null;
        let filesSection = "";
        let ganttTasks = [];
        let ganttParseError = false;
        
        // JSON kısmını ve files section kısmını ayır
        if (jsonMatch) {
          jsonContent = jsonMatch[1];
          // Files kısmını ayıkla
          const filesSectionMatch = planContent.match(/## Files Analyzed\n([\s\S]*?)\n\n## Test Plan/);
          if (filesSectionMatch) {
            filesSection = filesSectionMatch[1];
          }
          // Gantt Chart için task listesi oluştur
          try {
            ganttTasks = jsonToGanttTasks(jsonContent);
          } catch (e) {
            console.error('Error creating Gantt tasks:', e);
            ganttParseError = true;
          }
        }
        // Eğer JSON ayrıştırılamadıysa veya Gantt parse hatası varsa, sadece model çıktısını göster
        if (!jsonContent || ganttParseError) {
          return (
            <div className="mt-6">
              <div className="bg-yellow-100 text-yellow-800 p-4 rounded">
                <strong>Model çıktısı (JSON ayrıştırılamadı veya hatalı):</strong>
                <pre className="mt-2 whitespace-pre-wrap break-words text-xs bg-gray-50 p-2 rounded">{planContent}</pre>
              </div>
            </div>
          );
        }
        
        return (
          <div className="space-y-6">
            <div className="prose prose-sm max-w-full text-gray-600 break-words overflow-x-auto">
              <h2>Files Analyzed</h2>
              <ReactMarkdown 
                className="whitespace-pre-wrap break-words overflow-wrap-anywhere"
                components={{
                  p: ({children}) => <p className="break-words">{safeRenderChildren(children)}</p>,
                  li: ({children}) => <li className="break-words">{safeRenderChildren(children)}</li>,
                  td: ({children}) => <td className="break-words max-w-xs">{safeRenderChildren(children)}</td>,
                  th: ({children}) => <th className="break-words">{safeRenderChildren(children)}</th>
                }}
              >
                {filesSection}
              </ReactMarkdown>
            </div>
            
            {/* JSON veya XML formatında göster */}
            <div className="bg-gray-100 rounded p-4 font-mono text-xs overflow-auto">
              <h2 className="text-lg font-medium mb-2">Test Plan {selectedOutputFormat === 'XML' ? '(XML Format)' : '(JSON Format)'}</h2>
              <pre className="whitespace-pre-wrap break-words">
                {selectedOutputFormat === 'XML' && jsonContent 
                  ? jsonToXml(jsonContent)
                  : jsonContent}
              </pre>
            </div>
            
            {/* Gantt Chart Görünümü */}
            {ganttTasks.length > 0 ? (
              <div className="mt-6">
                <h2 className="text-lg font-medium mb-2">Test Plan Gantt Chart</h2>
                <div className="border rounded-lg p-4 bg-white overflow-x-auto">
                  <div style={{ width: '100%', minWidth: '800px', height: '400px' }}>
                    {/* Dinamik görünüm ve sütun genişliği, hata olursa model çıktısı göster */}
                    {(() => {
                      try {
                        const { viewMode, columnWidth } = getGanttViewModeAndColumnWidth(ganttTasks);
                        return (
                          <Gantt
                            tasks={ganttTasks}
                            viewMode={viewMode}
                            listCellWidth="150px"
                            columnWidth={columnWidth}
                            headerHeight={50}
                            rowHeight={40}
                            ganttHeight={400}
                          />
                        );
                      } catch (err) {
                        console.error('Gantt Chart render error:', err);
                        return (
                          <div className="bg-red-100 text-red-700 p-4 rounded">
                            <strong>Gantt Chart oluşturulamadı. Model çıktısı:</strong>
                            <pre className="mt-2 whitespace-pre-wrap break-words text-xs bg-gray-50 p-2 rounded">{jsonContent}</pre>
                          </div>
                        );
                      }
                    })()}
                  </div>
                </div>
              </div>
            ) : (
              jsonContent && (
                <div className="mt-6">
                  <div className="bg-yellow-100 text-yellow-800 p-4 rounded">
                    <strong>Gantt Chart oluşturulamadı veya görev bulunamadı. Model çıktısı:</strong>
                    <pre className="mt-2 whitespace-pre-wrap break-words text-xs bg-gray-50 p-2 rounded">{jsonContent}</pre>
                  </div>
                </div>
              )
            )}
          </div>
        );
      }
      // Sample göster
      return (
        <div className="space-y-4">
          <section>
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-lg font-medium">Process Results</h3>
              <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                Sample
              </span>
            </div>
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 shadow-sm overflow-x-auto">
              <div className="prose prose-sm max-w-full text-gray-600 break-words">
                <ReactMarkdown 
                  className="whitespace-pre-wrap break-words overflow-wrap-anywhere"
                  components={{
                    p: ({children}) => <p className="break-words">{safeRenderChildren(children)}</p>,
                    li: ({children}) => <li className="break-words">{safeRenderChildren(children)}</li>,
                    td: ({children}) => <td className="break-words max-w-xs">{safeRenderChildren(children)}</td>,
                    th: ({children}) => <th className="break-words">{safeRenderChildren(children)}</th>
                  }}
                >
                  {getSampleOutput().content}
                </ReactMarkdown>
              </div>
            </div>
          </section>
          <section>
            <h3 className="text-lg font-medium mb-3">Execution Details</h3>
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 shadow-sm">
              <div className="text-gray-600">
                <p><strong>Status:</strong> Not Run</p>
                <p><strong>Process:</strong> Test Planning</p>
                <p><strong>Last Updated:</strong> {new Date().toLocaleString()}</p>
              </div>
            </div>
          </section>
        </div>
      );
    }

    if (activeTab === 'environment-setup') {
      if (envSetupStatus === 'loading') {
        return <div> Loading Environment setup results...</div>;
      }
      if (envSetupError) {
        return <div className="text-red-600">Hata: {envSetupError}</div>;
      }
      if (setups && setups.length > 0) {
        // Text olarak gelen JSON planını çıkar
        let setupContent = setups[0];
        const jsonMatch = setupContent.match(/\{[\s\S]*\}/);
        let jsonContent = null;
        let filesSection = "";
        
        // Files kısmını ayıkla
        const filesSectionMatch = setupContent.match(/## Files Analyzed\n([\s\S]*?)\n\n## Environment Setup/);
        if (filesSectionMatch) {
          filesSection = filesSectionMatch[1];
        }
        
        // JSON içeriğini bul
        if (jsonMatch) {
          jsonContent = jsonMatch[0];
          try {
            // JSON formatını düzgünce formatla
            const jsonObject = JSON.parse(jsonContent);
            jsonContent = JSON.stringify(jsonObject, null, 2);
          } catch (e) {
            console.error('JSON parse error:', e);
          }
        }
        
        return (
          <div className="space-y-4">
            <div className="prose prose-sm max-w-full text-gray-600 break-words overflow-x-auto">
              <h2>Files Analyzed</h2>
              <ReactMarkdown 
                className="whitespace-pre-wrap break-words overflow-wrap-anywhere"
                components={{
                  p: ({children}) => <p className="break-words">{safeRenderChildren(children)}</p>,
                  li: ({children}) => <li className="break-words">{safeRenderChildren(children)}</li>,
                  td: ({children}) => <td className="break-words max-w-xs">{safeRenderChildren(children)}</td>,
                  th: ({children}) => <th className="break-words">{safeRenderChildren(children)}</th>
                }}
              >
                {filesSection}
              </ReactMarkdown>
            </div>
            
            {/* JSON veya XML formatında göster */}
            <div className="bg-gray-100 rounded p-4 font-mono text-xs overflow-auto">
              <h2 className="text-lg font-medium mb-2">Environment Setup {selectedOutputFormat === 'XML' ? '(XML Format)' : '(JSON Format)'}</h2>              <pre className="whitespace-pre-wrap break-words">
                {selectedOutputFormat === 'XML' && jsonContent 
                  ? jsonToXml(jsonContent)
                  : jsonContent}
              </pre>
            </div>
          </div>
        );
      }
    }

    if (activeTab === 'code-review') {
      const content = typeof currentOutput.content === 'string'
        ? currentOutput.content 
        : JSON.stringify(currentOutput.content || 'No content available');

    // Special handling for Test Scenario Generation - show only JSON
    if (currentOutput.processType === 'Test Scenario Generation') {
      // Extract JSON from markdown format
      const jsonMatch = content.match(/```json\n([\s\S]*?)\n```/);
      const jsonContent = jsonMatch ? jsonMatch[1] : content;
      
      return (
        <div className="space-y-4">
          <section>
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-lg font-medium">Test Scenario Generation Results</h3>
              {currentOutput.status === 'sample' && (
                <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                  Sample
                </span>
              )}
            </div>
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 shadow-sm">
              <div className="bg-gray-100 rounded p-4 overflow-x-auto">
                <pre className="whitespace-pre-wrap break-words text-xs font-mono max-w-full overflow-x-auto">
                  {jsonContent}
                </pre>
              </div>
            </div>
          </section>

          <section>
            <h3 className="text-lg font-medium mb-3">Execution Details</h3>
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 shadow-sm">
              <div className="text-gray-600">
                <p><strong>Status:</strong> {currentOutput.status === 'sample' ? 'Not Run' : currentOutput.status}</p>
                <p><strong>Process:</strong> {processName || currentOutput.processType || 'Unknown'}</p>
                <p><strong>Last Updated:</strong> {new Date(currentOutput.timestamp).toLocaleString()}</p>
              </div>
            </div>          </section>
        </div>
      );
    }
    }

    return (
      <div className="space-y-4">
        <section>
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-lg font-medium">Process Results</h3>
            {currentOutput.status === 'sample' && (
              <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                Sample
              </span>
            )}
          </div>
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 shadow-sm overflow-x-auto">
            <div className="prose prose-sm max-w-full text-gray-600 break-words">
              {/* Önce açıklama kısmı, sonra kod bloğu */}
              <ReactMarkdown
                className="whitespace-pre-wrap break-words overflow-wrap-anywhere"
                components={{
                  p: ({children}) => <p className="break-words">{safeRenderChildren(children)}</p>,
                  li: ({children}) => <li className="break-words">{safeRenderChildren(children)}</li>,
                  td: ({children}) => <td className="break-words max-w-xs">{safeRenderChildren(children)}</td>,
                  th: ({children}) => <th className="break-words">{safeRenderChildren(children)}</th>,
                  code: ({ node, inline, className, children, ...props }) => {
                    const match = /language-(\w+)/.exec(className || '');
                    const isJson = match && match[1] === 'json';
                    
                    if (!inline && isJson) {
                      return (
                        <div className="bg-gray-100 rounded p-4 my-4 overflow-x-auto">
                          <pre className="whitespace-pre-wrap break-words text-xs font-mono max-w-full">
                            <code {...props}>
                              {safeRenderChildren(children)}
                            </code>
                          </pre>
                        </div>
                      );
                    }
                    
                    return (
                      <code className={className} {...props}>
                        {safeRenderChildren(children)}
                      </code>
                    );
                  }
                }}              >
                {typeof currentOutput.content === 'string' 
                  ? currentOutput.content.replace(/\{[\s\S]*\}/, '').trim()
                  : JSON.stringify(currentOutput.content || 'No content available')
                }
              </ReactMarkdown>
              {currentOutput.prettyJson && (
                <div className="bg-gray-100 rounded p-4 font-mono text-xs overflow-auto mt-4">
                  <pre className="whitespace-pre-wrap break-words">{currentOutput.prettyJson}</pre>
                </div>
              )}
            </div>
          </div>
        </section>

        <section>
          <h3 className="text-lg font-medium mb-3">Execution Details</h3>
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 shadow-sm">
            <div className="text-gray-600">
              <p><strong>Status:</strong> {currentOutput.status === 'sample' ? 'Not Run' : currentOutput.status}</p>
              <p><strong>Process:</strong> {processName || currentOutput.processType || 'Unknown'}</p>
              <p><strong>Last Updated:</strong> {new Date(currentOutput.timestamp).toLocaleString()}</p>
            </div>
          </div>
        </section>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full">
      {!hideHeader && (
        <div className="flex-none h-16 px-6 flex items-center justify-between border-b border-gray-200 bg-white">
          <h2 className="text-xl font-bold text-gray-900">{headerTitle}</h2>
          {processId && (
            <span className="px-3 py-1 text-xs font-medium rounded-full bg-indigo-100 text-indigo-800">
              {processId}
            </span>
          )}
        </div>
      )}
      <div className={`flex-1 overflow-y-auto ${hideHeader ? 'p-4' : 'p-4'}`}>
        {renderContent()}
      </div>
      {!hideFooter && (
        <div className="flex-none h-16 px-6 flex items-center border-t border-gray-200 bg-white">
          <button
            className={`w-full py-3 px-4 rounded-md text-white font-medium transition-colors shadow-sm ${
              !displayOutput || displayOutput.status === 'sample'
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-green-600 hover:bg-green-700'
            }`}
            disabled={!displayOutput || displayOutput.status === 'sample'}
          >            Install Output
          </button>
        </div>
      )}
    </div>  );
}
