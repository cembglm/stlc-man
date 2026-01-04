import React, { useState } from 'react';
import { clsx } from 'clsx';
import { 
  ChevronDownIcon, 
  ChevronRightIcon, 
  CheckCircleIcon,
  ExclamationCircleIcon,
  BookmarkIcon
} from '@heroicons/react/24/outline';

/**
 * Pipeline Configuration Item Component
 * 
 * Her process için expandable/collapsible konfigürasyon kartı.
 * Process'in form component'ini içinde render eder ve ayarları kaydeder.
 */
export default function PipelineConfigItem({
  process,
  isSelected,
  isConfigured,
  isExpanded,
  onToggleExpand,
  onToggleSelect,
  onSaveConfig,
  config,
  pipelineStatus,
  children,
  processOrigin = 'manual'
}) {
  const [localExpanded, setLocalExpanded] = useState(isExpanded);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  const handleToggleExpand = () => {
    const newState = !localExpanded;
    setLocalExpanded(newState);
    if (onToggleExpand) {
      onToggleExpand(newState);
    }
  };

  const handleSaveConfig = () => {
    if (onSaveConfig) {
      onSaveConfig();
      setHasUnsavedChanges(false);
    }
  };

  const getStatusIcon = () => {
    if (pipelineStatus === 'running') {
      return (
        <svg className="animate-spin h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 0 1 4 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      );
    }
    
    if (pipelineStatus === 'completed') {
      return <CheckCircleIcon className="h-5 w-5 text-green-600" />;
    }
    
    if (pipelineStatus === 'error') {
      return <ExclamationCircleIcon className="h-5 w-5 text-red-600" />;
    }

    if (isConfigured) {
      return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
    }
    
    return <ExclamationCircleIcon className="h-5 w-5 text-yellow-500" />;
  };

  const getStatusText = () => {
    if (pipelineStatus === 'running') return 'Running';
    if (pipelineStatus === 'completed') return 'Completed';
    if (pipelineStatus === 'error') return 'Error';
    if (isConfigured) return 'Configured';
    return 'Not Configured';
  };

  return (
    <div className={clsx(
      'border rounded-lg transition-all duration-200',
      isSelected ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 bg-white',
      !isSelected && 'opacity-60'
    )}>
      {/* Header */}
      <div className="p-4">
        <div className="flex items-center justify-between">
          {/* Left side - Checkbox, Expand button, Title */}
          <div className="flex items-center space-x-3 flex-1">
            {/* Checkbox */}
            <input
              type="checkbox"
              checked={isSelected}
              onChange={(e) => onToggleSelect && onToggleSelect(e.target.checked)}
              className={clsx(
                "h-5 w-5 rounded border-gray-300",
                processOrigin === 'auto' ? 'text-yellow-500' : 'text-indigo-600'
              )}
              disabled={pipelineStatus === 'running'}
            />
            
            {/* Expand/Collapse Button */}
            <button
              onClick={handleToggleExpand}
              className="p-1 hover:bg-gray-100 rounded transition-colors"
              disabled={!isSelected}
            >
              {localExpanded ? (
                <ChevronDownIcon className="h-5 w-5 text-gray-600" />
              ) : (
                <ChevronRightIcon className="h-5 w-5 text-gray-600" />
              )}
            </button>
            
            {/* Process Title */}
            <div className="flex items-center space-x-2">
              <h3 className="font-medium text-gray-900">{process.name}</h3>
              
              {/* Auto Badge */}
              {processOrigin === 'auto' && (
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                  Auto
                </span>
              )}
              
              {/* Unsaved Changes Badge */}
              {hasUnsavedChanges && (
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                  Unsaved
                </span>
              )}
            </div>
          </div>
          
          {/* Right side - Status */}
          <div className="flex items-center space-x-2">
            {getStatusIcon()}
            <span className={clsx(
              'text-sm font-medium',
              pipelineStatus === 'running' && 'text-blue-600',
              pipelineStatus === 'completed' && 'text-green-600',
              pipelineStatus === 'error' && 'text-red-600',
              !pipelineStatus && isConfigured && 'text-green-600',
              !pipelineStatus && !isConfigured && 'text-yellow-600'
            )}>
              {getStatusText()}
            </span>
          </div>
        </div>
        
        {/* Process Description - Always visible when selected */}
        {isSelected && (
          <div className="mt-2 ml-11 text-sm text-gray-600">
            {process.details && process.details[0]}
          </div>
        )}
      </div>
      
      {/* Expandable Content */}
      {localExpanded && isSelected && (
        <div className="border-t border-gray-200 bg-white">
          <div className="p-4">
            {/* Configuration Status */}
            {isConfigured && config && (
              <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md">
                <div className="flex items-start space-x-2">
                  <BookmarkIcon className="h-5 w-5 text-green-600 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-green-800">Saved Configuration</p>
                    <p className="text-xs text-green-600 mt-1">
                      Last saved: {new Date(config.configuredAt).toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>
            )}
            
            {/* Form Content - Render edilecek form component burada */}
            <div className="mb-4">
              {children}
            </div>
            
            {/* Save Button */}
            <div className="flex items-center justify-between pt-4 border-t border-gray-200">
              <div className="text-sm text-gray-500">
                {isConfigured ? (
                  'Configuration saved and ready to run'
                ) : (
                  'Configure this process and save to include in pipeline'
                )}
              </div>
              <button
                onClick={handleSaveConfig}
                className={clsx(
                  'px-4 py-2 rounded-md font-medium transition-colors',
                  'bg-indigo-600 text-white hover:bg-indigo-700',
                  'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500'
                )}
              >
                {isConfigured ? 'Update Configuration' : 'Save Configuration'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
