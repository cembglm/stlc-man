import React, { useEffect, useMemo, useState } from 'react';
import { ArrowPathIcon, SparklesIcon } from '@heroicons/react/24/outline';

const FALLBACK_PROVIDERS = [
  { id: 'lm_studio', label: 'LM Studio', connected: false, models: [] },
  { id: 'colibri', label: 'Colibri', connected: false, models: [] },
];

function ModelSelect({ provider, providersById, value, onChange }) {
  const models = providersById[provider]?.models || [];
  const valueIsDiscovered = models.some(model => model.id === value);
  return (
    <select value={value || ''} onChange={event => onChange(event.target.value)} className="min-w-0 flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-purple-500">
      {value && !valueIsDiscovered && <option value={value}>{value} (configured)</option>}
      {!models.length && <option value="">Server default model</option>}
      {models.map(model => (
        <option key={model.id} value={model.id}>
          {model.id}{model.context_length ? ` (${Math.round(model.context_length / 1024)}K)` : ''}
        </option>
      ))}
    </select>
  );
}

export default function GlobalAIConfig({
  selectedProvider = 'lm_studio', onProviderChange, selectedModel = '', onModelChange,
  processes = [], selectedProcesses = new Set(), stepConfigs = {}, onStepConfigChange,
}) {
  const [providers, setProviders] = useState(FALLBACK_PROVIDERS);
  const [loading, setLoading] = useState(false);
  const [discoveryError, setDiscoveryError] = useState('');

  const refresh = async () => {
    setLoading(true);
    setDiscoveryError('');
    try {
      const response = await fetch('/api/models/providers');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = await response.json();
      setProviders(payload.providers || FALLBACK_PROVIDERS);
    } catch (error) {
      setDiscoveryError(`Provider discovery failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { refresh(); }, []);

  const providersById = useMemo(
    () => Object.fromEntries(providers.map(provider => [provider.id, provider])),
    [providers],
  );

  useEffect(() => {
    const info = providersById[selectedProvider];
    const discovered = info?.models || [];
    if (discovered.length && !discovered.some(item => item.id === selectedModel)) {
      onModelChange?.(info.default_model || discovered[0].id);
    }
  }, [providersById, selectedProvider, selectedModel, onModelChange]);

  const selectedSteps = processes.filter(process => selectedProcesses.has(process.id));

  const changeStepProvider = (stepId, provider) => {
    if (!provider) {
      onStepConfigChange?.(stepId, { provider: '', model: '' });
      return;
    }
    const info = providersById[provider];
    onStepConfigChange?.(stepId, {
      provider,
      model: info?.default_model || info?.models?.[0]?.id || '',
    });
  };

  const changeGlobalProvider = provider => {
    const info = providersById[provider];
    onProviderChange?.(provider);
    onModelChange?.(info?.default_model || info?.models?.[0]?.id || '');
  };

  return (
    <div className="border rounded-lg bg-white shadow-sm overflow-hidden">
      <div className="px-4 py-3 bg-gradient-to-r from-purple-50 to-pink-50 border-b border-purple-100 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <SparklesIcon className="h-5 w-5 text-purple-600" />
          <div><h3 className="font-semibold text-gray-900 text-sm">AI Provider & Model</h3><p className="text-xs text-gray-500">Global default with optional per-step overrides</p></div>
        </div>
        <button type="button" onClick={refresh} disabled={loading} className="p-2 text-purple-700 hover:bg-purple-100 rounded-lg disabled:opacity-50" title="Refresh providers">
          <ArrowPathIcon className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="p-4 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-[180px_1fr] gap-3">
          <select value={selectedProvider} onChange={event => changeGlobalProvider(event.target.value)} className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-purple-500">
            {providers.map(provider => <option key={provider.id} value={provider.id}>{provider.label} {provider.connected ? '●' : '○'}</option>)}
          </select>
          <ModelSelect provider={selectedProvider} providersById={providersById} value={selectedModel} onChange={onModelChange} />
        </div>

        {discoveryError && <p className="text-xs text-amber-700">{discoveryError}</p>}

        <div className="border-t pt-3 overflow-x-auto">
          <div className="min-w-[620px]">
            <div className="grid grid-cols-[minmax(150px,1fr)_150px_minmax(180px,1fr)] gap-2 px-2 pb-2 text-[11px] font-semibold uppercase tracking-wide text-gray-400">
              <span>Pipeline step</span><span>Provider</span><span>Model</span>
            </div>
            <div className="divide-y divide-gray-100">
              {selectedSteps.map(process => {
                const config = stepConfigs[process.id] || {};
                const effectiveProvider = config.provider || selectedProvider;
                return (
                  <div key={process.id} className="grid grid-cols-[minmax(150px,1fr)_150px_minmax(180px,1fr)] gap-2 items-center py-2 px-2">
                    <span className="text-sm text-gray-700 truncate" title={process.name}>{process.name}</span>
                    <select value={config.provider || ''} onChange={event => changeStepProvider(process.id, event.target.value)} className="px-2 py-2 border border-gray-300 rounded-lg text-xs">
                      <option value="">Use global</option>
                      {providers.map(provider => <option key={provider.id} value={provider.id}>{provider.label}</option>)}
                    </select>
                    <ModelSelect provider={effectiveProvider} providersById={providersById} value={config.provider ? config.model : selectedModel} onChange={model => onStepConfigChange?.(process.id, { ...config, provider: config.provider || effectiveProvider, model })} />
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 text-xs">
          {providers.map(provider => (
            <span key={provider.id} className={`px-2 py-1 rounded-full ${provider.connected ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
              {provider.label}: {provider.connected ? `${provider.models.length} model` : 'offline'}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
