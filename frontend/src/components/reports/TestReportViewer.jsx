import React from 'react';
import ReactMarkdown from 'react-markdown';
import { 
  ChevronDownIcon, 
  ChevronRightIcon, 
  ArrowDownTrayIcon, 
  DocumentTextIcon 
} from '@heroicons/react/24/outline';

/**
 * TestReportViewer - Interactive, collapsible markdown renderer for ISTQB/IEEE test reports
 */
const TestReportViewer = ({ output, isLoading }) => {
  const [error, setError] = React.useState(null);
  const [expandedSections, setExpandedSections] = React.useState({});
  const [viewMode, setViewMode] = React.useState('sections'); // 'sections' or 'full'
  
  // Clean output: remove code block wrappers
  const cleanOutput = React.useMemo(() => {
    if (!output) return '';
    
    let cleaned = output.trim();
    // Remove ```markdown or ```json wrappers
    if (cleaned.startsWith('```')) {
      cleaned = cleaned.replace(/^```(?:markdown|json)?\n?/, '').replace(/\n?```$/, '');
    }
    
    return cleaned;
  }, [output]);

  // Parse report into sections based on ## headings
  const reportSections = React.useMemo(() => {
    if (!cleanOutput) return [];
    
    const lines = cleanOutput.split('\n');
    const sections = [];
    let currentSection = null;
    
    lines.forEach((line, index) => {
      // Detect main sections (## headings with optional emoji/numbering)
      const mainHeadingMatch = line.match(/^##\s+(?:\d+\.\s*)?(?:[📋📊🐛🎯⚠️💡📈📉✅❌🔍🚀📝]+\s*)?(.+)/);
      
      if (mainHeadingMatch) {
        // Save previous section
        if (currentSection) {
          sections.push(currentSection);
        }
        
        // Start new section
        currentSection = {
          title: mainHeadingMatch[1].trim(),
          content: [line],
          startLine: index,
          icon: line.match(/[📋📊🐛🎯⚠️💡📈📉✅❌🔍🚀📝]/)?.[0] || '📄'
        };
      } else if (currentSection) {
        currentSection.content.push(line);
      } else {
        // Content before first section (header, title, etc.)
        if (!sections.length || sections[0].title !== '__header__') {
          sections.unshift({
            title: '__header__',
            content: [line],
            startLine: 0,
            icon: '📄'
          });
        } else {
          sections[0].content.push(line);
        }
      }
    });
    
    // Add last section
    if (currentSection) {
      sections.push(currentSection);
    }
    
    // Convert content arrays to strings
    return sections.map(section => ({
      ...section,
      content: section.content.join('\n')
    }));
  }, [cleanOutput]);

  // Toggle section expansion
  const toggleSection = (index) => {
    setExpandedSections(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  // Expand all sections
  const expandAll = () => {
    const allExpanded = {};
    reportSections.forEach((_, index) => {
      allExpanded[index] = true;
    });
    setExpandedSections(allExpanded);
  };

  // Collapse all sections
  const collapseAll = () => {
    setExpandedSections({});
  };

  // Download report as markdown file
  const downloadReport = () => {
    const blob = new Blob([cleanOutput], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `test-report-${new Date().toISOString().split('T')[0]}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 m-4">
        <h3 className="text-lg font-semibold text-red-800 mb-2">⚠️ Rendering Error</h3>
        <p className="text-red-700 mb-4">{error.message}</p>
        <details className="mt-4">
          <summary className="cursor-pointer text-sm text-red-600 hover:text-red-800">Show raw content</summary>
          <pre className="mt-2 p-4 bg-white rounded border border-red-200 text-xs overflow-x-auto max-h-96">
            {cleanOutput.substring(0, 2000)}...
          </pre>
        </details>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Generating test report...</p>
        </div>
      </div>
    );
  }

  if (!output) {
    return (
      <div className="text-center p-12 text-gray-500">
        No report generated yet. Select sessions and generate a report.
      </div>
    );
  }

  // Render sectioned view
  const renderSectionedView = () => {
    return (
      <div className="space-y-3">
        {reportSections.map((section, index) => {
          // Skip rendering internal header section separately
          if (section.title === '__header__') {
            return (
              <div key={index} className="mb-6">
                <div className="prose prose-blue prose-lg max-w-none">
                  <ReactMarkdown components={markdownComponents}>
                    {section.content}
                  </ReactMarkdown>
                </div>
              </div>
            );
          }

          const isExpanded = expandedSections[index];

          return (
            <div 
              key={index} 
              className="border border-gray-300 rounded-lg overflow-hidden bg-white shadow-sm hover:shadow-md transition-shadow"
            >
              {/* Section Header - Clickable */}
              <button
                onClick={() => toggleSection(index)}
                className="w-full flex items-center justify-between p-4 bg-gradient-to-r from-gray-50 to-gray-100 hover:from-gray-100 hover:to-gray-200 transition-colors text-left"
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{section.icon}</span>
                  <h3 className="text-lg font-semibold text-gray-800">{section.title}</h3>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500 mr-2">
                    {isExpanded ? 'Collapse' : 'Expand'}
                  </span>
                  {isExpanded ? (
                    <ChevronDownIcon className="w-5 h-5 text-gray-600" />
                  ) : (
                    <ChevronRightIcon className="w-5 h-5 text-gray-600" />
                  )}
                </div>
              </button>

              {/* Section Content - Collapsible */}
              {isExpanded && (
                <div className="p-6 border-t border-gray-200 bg-white">
                  <div className="prose prose-blue prose-lg max-w-none">
                    <ReactMarkdown components={markdownComponents}>
                      {section.content}
                    </ReactMarkdown>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  // Render full view
  const renderFullView = () => {
    return (
      <div className="prose prose-blue prose-lg max-w-none">
        <ErrorBoundary onError={setError}>
          <ReactMarkdown components={markdownComponents}>
            {cleanOutput}
          </ReactMarkdown>
        </ErrorBoundary>
      </div>
    );
  };

  // Markdown component configuration
  const markdownComponents = {
    // Custom table styling
    table: ({ node, ...props }) => (
      <div className="overflow-x-auto my-6">
        <table className="min-w-full divide-y divide-gray-300 border border-gray-300 shadow-sm" {...props} />
      </div>
    ),
    thead: ({ node, ...props }) => (
      <thead className="bg-gray-50" {...props} />
    ),
    th: ({ node, ...props }) => (
      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 border-b-2 border-gray-300" {...props} />
    ),
    td: ({ node, ...props }) => (
      <td className="px-4 py-3 text-sm text-gray-700 border-b border-gray-200" {...props} />
    ),
    // Custom code block styling
    code: ({ node, inline, ...props }) => (
      inline 
        ? <code className="bg-gray-100 text-red-600 px-1.5 py-0.5 rounded text-sm font-mono" {...props} />
        : <code className="block bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm font-mono" {...props} />
    ),
    // Custom heading styling with better spacing
    h1: ({ node, ...props }) => (
      <h1 className="text-3xl font-bold text-gray-900 mt-8 mb-4 pb-2 border-b-2 border-blue-600" {...props} />
    ),
    h2: ({ node, ...props }) => (
      <h2 className="text-2xl font-bold text-gray-800 mt-8 mb-3 pb-2 border-b border-gray-300" {...props} />
    ),
    h3: ({ node, ...props }) => (
      <h3 className="text-xl font-semibold text-gray-800 mt-6 mb-2" {...props} />
    ),
    h4: ({ node, ...props }) => (
      <h4 className="text-lg font-semibold text-gray-700 mt-4 mb-2" {...props} />
    ),
    // Custom list styling
    ul: ({ node, ...props }) => (
      <ul className="list-disc list-inside space-y-1 my-4" {...props} />
    ),
    ol: ({ node, ...props }) => (
      <ol className="list-decimal list-inside space-y-1 my-4" {...props} />
    ),
    // Custom blockquote
    blockquote: ({ node, ...props }) => (
      <blockquote className="border-l-4 border-blue-500 pl-4 py-2 my-4 bg-blue-50 italic text-gray-700" {...props} />
    ),
    // Horizontal rule
    hr: ({ node, ...props }) => (
      <hr className="my-8 border-t-2 border-gray-300" {...props} />
    ),
  };

  return (
    <div className="test-report-viewer bg-white">
      {/* Standards Badge Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-4 mb-6 rounded-t-lg">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-white/20 text-white">
              📘 ISTQB Foundation
            </span>
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-white/20 text-white">
              📘 ISTQB Test Manager
            </span>
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-white/20 text-white">
              📘 IEEE 829-2008
            </span>
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-white/20 text-white">
              📘 ISO/IEC/IEEE 29119-3
            </span>
          </div>
          
          {/* View Controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={downloadReport}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium bg-white/20 text-white hover:bg-white/30 transition-colors"
              title="Download report as Markdown"
            >
              <ArrowDownTrayIcon className="w-4 h-4" />
              Download
            </button>
          </div>
        </div>
      </div>

      {/* View Mode Toggle & Section Controls */}
      <div className="px-6 mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setViewMode('sections')}
            className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              viewMode === 'sections'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            <DocumentTextIcon className="w-4 h-4" />
            Sections View
          </button>
          <button
            onClick={() => setViewMode('full')}
            className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              viewMode === 'full'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            <DocumentTextIcon className="w-4 h-4" />
            Full View
          </button>
        </div>

        {viewMode === 'sections' && (
          <div className="flex items-center gap-2">
            <button
              onClick={expandAll}
              className="px-3 py-1.5 rounded-lg text-sm font-medium bg-green-100 text-green-700 hover:bg-green-200 transition-colors"
            >
              Expand All
            </button>
            <button
              onClick={collapseAll}
              className="px-3 py-1.5 rounded-lg text-sm font-medium bg-orange-100 text-orange-700 hover:bg-orange-200 transition-colors"
            >
              Collapse All
            </button>
          </div>
        )}
      </div>

      {/* Report Content */}
      <div className="px-6 pb-6">
        {viewMode === 'sections' ? renderSectionedView() : renderFullView()}
      </div>
    </div>
  );
};

// Simple error boundary component
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Markdown rendering error:', error, errorInfo);
    if (this.props.onError) {
      this.props.onError(error);
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-yellow-800">⚠️ Error rendering markdown. Please check the report format.</p>
        </div>
      );
    }

    return this.props.children;
  }
}

export default TestReportViewer;
