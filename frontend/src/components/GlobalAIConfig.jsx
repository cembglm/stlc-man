import React, { useState } from 'react';
import { clsx } from 'clsx';
import { 
  SparklesIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

/**
 * Global AI Configuration Component
 * 
 * Pipeline'da tüm process'ler için tek seferlik AI model ve parametre ayarları.
 */
export default function GlobalAIConfig({
  selectedProcesses,
  onApplyToAll
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [globalConfig, setGlobalConfig] = useState({
    aiModel: 'gemini-2.5-pro'
  });

  const availableModels = [
    // API Models (External)
    { id: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash', provider: 'Google', type: 'api' },
    { id: 'gemini-2.5-pro', name: 'Gemini 2.5 Pro', provider: 'Google', type: 'api' },
    { id: 'gemini-1.5-pro', name: 'Gemini 1.5 Pro', provider: 'Google', type: 'api' },
    { id: 'gemini-1.5-flash', name: 'Gemini 1.5 Flash', provider: 'Google', type: 'api' },
    
    // Local Models (LM Studio) - Basic
    { id: 'codegeex4:9b', name: 'CodeGeeX4 (9B)', provider: 'LM Studio', type: 'local' },
    { id: 'codellama:7b', name: 'Code Llama (7B)', provider: 'LM Studio', type: 'local' },
    { id: 'deepseek-coder:6.7b', name: 'DeepSeek Coder (6.7B)', provider: 'LM Studio', type: 'local' },
    { id: 'gemma2:2b', name: 'Gemma 2 (2B)', provider: 'LM Studio', type: 'local' },
    { id: 'gemma3:4b', name: 'Gemma 3 (4B)', provider: 'LM Studio', type: 'local' },
    { id: 'google/gemma-3-12b', name: 'Gemma 3 (12B)', provider: 'LM Studio', type: 'local' },
    { id: 'llama3.2:3b', name: 'Llama 3.2 (3B)', provider: 'LM Studio', type: 'local' },
    { id: 'qwen2.5:7b', name: 'Qwen 2.5 (7B)', provider: 'LM Studio', type: 'local' },
    { id: 'qwen2.5:7b-1m', name: 'Qwen 2.5 (7B-1M)', provider: 'LM Studio', type: 'local' },
    { id: 'qwen2.5-coder:3b', name: 'Qwen 2.5 Coder (3B)', provider: 'LM Studio', type: 'local' },
    { id: 'qwen/qwen3-14b', name: 'Qwen 3 (14B)', provider: 'LM Studio', type: 'local' },
    { id: 'stable-code:3b', name: 'Stable Code (3B)', provider: 'LM Studio', type: 'local' },
    { id: 'starcoder2:7b', name: 'StarCoder 2 (7B)', provider: 'LM Studio', type: 'local' },
    
    // Large Scale Models
    { id: 'meta/llama-3.3-70b', name: 'Llama 3.3 (70B)', provider: 'LM Studio', type: 'local' },
    { id: 'mistralai/codestral-22b-v0.1', name: 'Codestral (22B)', provider: 'LM Studio', type: 'local' },
    { id: 'openai/gpt-oss-20b', name: 'GPT OSS (20B)', provider: 'LM Studio', type: 'local' },
    { id: 'qwen/qwq-32b', name: 'QwQ (32B)', provider: 'LM Studio', type: 'local' },
    
    // Advanced Optimization Models
    { id: 'codellama:70b-instruct', name: 'CodeLlama 70B Instruct', provider: 'LM Studio', type: 'local' },
    { id: 'kimi-dev:72b', name: 'Kimi Dev 72B', provider: 'LM Studio', type: 'local' },
    { id: 'openai/gpt-oss-120b', name: 'GPT OSS 120B', provider: 'LM Studio', type: 'local' },
    { id: 'deepseek-r1-distill:32b', name: 'DeepSeek R1 Distill 32B', provider: 'LM Studio', type: 'local' },
    { id: 'google/gemma-3-27b', name: 'Google Gemma 3 27B', provider: 'LM Studio', type: 'local' },
    { id: 'qwen/qwen3-coder-30b', name: 'Qwen 3 Coder 30B', provider: 'LM Studio', type: 'local' },
    { id: 'deepseek/deepseek-r1-qwen3-8b', name: 'DeepSeek R1 Qwen3 8B', provider: 'LM Studio', type: 'local' },
  ];

  const handleConfigChange = (field, value) => {
    setGlobalConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleApplyToAll = () => {
    if (selectedProcesses.size === 0) {
      toast.error('No processes selected! Select processes first.');
      return;
    }

    toast(
      (t) => (
        <div>
          <p className="font-medium mb-3">
            Apply this AI configuration to all {selectedProcesses.size} selected processes?
          </p>
          <div className="flex space-x-2">
            <button
              onClick={() => {
                onApplyToAll(globalConfig);
                toast.dismiss(t.id);
                toast.success(`AI configuration applied to ${selectedProcesses.size} processes!`);
              }}
              className="px-3 py-1 bg-indigo-600 text-white rounded text-sm hover:bg-indigo-700"
            >
              Yes, Apply to All
            </button>
            <button
              onClick={() => toast.dismiss(t.id)}
              className="px-3 py-1 bg-gray-200 text-gray-700 rounded text-sm hover:bg-gray-300"
            >
              Cancel
            </button>
          </div>
        </div>
      ),
      {
        duration: Infinity,
        style: { maxWidth: '500px' }
      }
    );
  };

  const selectedModel = availableModels.find(m => m.id === globalConfig.aiModel);
  const processCount = selectedProcesses.size;

  return (
    <div className="border rounded-lg bg-white shadow-sm mb-4">
      {/* Header */}
      <div className="p-4 bg-gradient-to-r from-purple-50 to-pink-50 border-b border-purple-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1 hover:bg-purple-100 rounded transition-colors"
            >
              {isExpanded ? (
                <ChevronDownIcon className="h-5 w-5 text-purple-600" />
              ) : (
                <ChevronRightIcon className="h-5 w-5 text-purple-600" />
              )}
            </button>
            
            <div className="flex items-center space-x-2">
              <SparklesIcon className="h-6 w-6 text-purple-600" />
              <div>
                <h3 className="font-semibold text-gray-900">Global AI Configuration</h3>
                <p className="text-sm text-gray-600">
                  Set AI model once, apply to all processes
                </p>
              </div>
            </div>
          </div>

          {/* Quick Info */}
          <div className="flex items-center space-x-2">
            <span className="text-sm text-purple-700 font-medium">
              {selectedModel?.name || 'Select Model'}
            </span>
            {processCount > 0 && (
              <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded-full">
                {processCount} process{processCount !== 1 ? 'es' : ''}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="p-6 space-y-6">
          {/* AI Model Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              AI Model
            </label>
            <select
              value={globalConfig.aiModel}
              onChange={(e) => handleConfigChange('aiModel', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <optgroup label="API Models (External)">
                {availableModels.filter(m => m.type === 'api').map(model => (
                  <option key={model.id} value={model.id}>
                    {model.name} ({model.provider})
                  </option>
                ))}
              </optgroup>
              <optgroup label="Local Models (LM Studio)">
                {availableModels.filter(m => m.type === 'local').map(model => (
                  <option key={model.id} value={model.id}>
                    {model.name}
                  </option>
                ))}
              </optgroup>
            </select>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-between pt-4 border-t border-gray-200">
            <div className="text-sm text-gray-600">
              {processCount === 0 ? (
                <span className="text-yellow-600">⚠️ No processes selected</span>
              ) : (
                <span className="flex items-center space-x-2">
                  <CheckCircleIcon className="h-4 w-4 text-green-600" />
                  <span>Ready to apply to {processCount} process{processCount !== 1 ? 'es' : ''}</span>
                </span>
              )}
            </div>

            <button
              onClick={handleApplyToAll}
              disabled={processCount === 0}
              className={clsx(
                'px-6 py-2 rounded-lg font-medium transition-colors inline-flex items-center space-x-2',
                processCount === 0
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-purple-600 text-white hover:bg-purple-700'
              )}
            >
              <SparklesIcon className="h-5 w-5" />
              <span>Apply to All Processes</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
