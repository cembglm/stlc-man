import React, { useEffect, useMemo, useState } from 'react';
import api from '../../utils/api';
import { toast } from '../../utils/notifications';

const families = ['AOR', 'ROR', 'LOR', 'CON'];

export default function MutationTestingPanel({ managedFiles = [], sessionId }) {
  const pythonFiles = useMemo(() => managedFiles.filter(file => file.name?.endsWith('.py')), [managedFiles]);
  const [config, setConfig] = useState({ name: 'Mutation campaign', language: 'python', source_path: 'module.py',
    source: '', operator_families: families, max_mutants: 100, seed: '', function_scope: '' });
  const [adapter, setAdapter] = useState(null);
  const [campaign, setCampaign] = useState(null);
  const [mutants, setMutants] = useState([]);
  const [selected, setSelected] = useState(null);
  const [results, setResults] = useState([]);
  const [score, setScore] = useState(null);
  const [resultFilter, setResultFilter] = useState('all');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get('/api/mutations/v1/adapters').then(({ data }) => setAdapter(data)).catch(() => setAdapter(null));
  }, []);

  const toggleFamily = (family) => setConfig(current => ({ ...current,
    operator_families: current.operator_families.includes(family)
      ? current.operator_families.filter(item => item !== family) : [...current.operator_families, family] }));

  const loadFile = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const source = await file.text();
    setConfig(current => ({ ...current, source, source_path: file.name }));
  };

  const generate = async () => {
    if (!config.source.trim() || !config.operator_families.length) return toast.error('Source and at least one operator are required.');
    setBusy(true);
    try {
      const payload = { ...config, max_mutants: Number(config.max_mutants) || null,
        seed: config.seed === '' ? null : Number(config.seed), function_scope: config.function_scope || null };
      const created = await api.post('/api/mutations/v1/campaigns', payload, { headers: sessionId ? { 'X-Session-ID': sessionId } : {} });
      const generated = await api.post(`/api/mutations/v1/campaigns/${created.data.campaign_id}/generate`);
      setCampaign(created.data); setMutants(generated.data.mutants || []); setSelected(generated.data.mutants?.[0] || null);
      toast.success(`Generated ${generated.data.mutant_count} deterministic mutants.`);
    } catch (error) { toast.error(error.response?.data?.detail || error.message); }
    finally { setBusy(false); }
  };

  const requestExecution = async () => {
    if (!campaign) return;
    const { data } = await api.post(`/api/mutations/v1/campaigns/${campaign.campaign_id}/execute`);
    setResults(data.results || []);
    toast.error('Execution unavailable: preview and evidence persistence remain available.');
  };

  const recordBaselineState = async () => {
    if (!campaign) return;
    const { data } = await api.post(`/api/mutations/v1/campaigns/${campaign.campaign_id}/baseline`);
    setCampaign(current => ({ ...current, status: data.status === 'completed' ? 'ready' : 'baseline_unavailable' }));
    toast.error('Baseline execution unavailable under the current isolation policy.');
  };

  const cancel = async () => {
    if (!campaign) return;
    const { data } = await api.post(`/api/mutations/v1/campaigns/${campaign.campaign_id}/cancel`);
    setCampaign(current => ({ ...current, status: data.status }));
  };

  const refreshReport = async () => {
    if (!campaign) return;
    const [{ data: resultData }, { data: scoreData }] = await Promise.all([
      api.get(`/api/mutations/v1/campaigns/${campaign.campaign_id}/results`),
      api.get(`/api/mutations/v1/campaigns/${campaign.campaign_id}/score`),
    ]);
    setResults(resultData.results || []); setScore(scoreData);
  };

  const downloadReport = async () => {
    const { data } = await api.get(`/api/mutations/v1/campaigns/${campaign.campaign_id}/report`);
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
    const link = document.createElement('a'); link.href = url; link.download = `${campaign.campaign_id}.mutation-report.json`; link.click();
    URL.revokeObjectURL(url);
  };

  const executionAvailable = adapter?.execution_adapter?.available === true;
  return <div className="space-y-6">
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
      <strong>Safe execution boundary:</strong> {adapter?.execution_adapter?.reason || 'Checking executor capabilities…'}
      Mutation scores are test-strength evidence and never change requirement verification or KPI 3.4.
    </div>
    <div className="grid gap-6 lg:grid-cols-2">
      <section className="rounded-lg border bg-white p-5 shadow-sm space-y-4">
        <h3 className="font-semibold text-gray-900">Campaign configuration</h3>
        <div className="grid grid-cols-2 gap-3">
          <label className="text-sm">Name<input className="mt-1 w-full rounded border p-2" value={config.name} onChange={e => setConfig({...config, name:e.target.value})}/></label>
          <label className="text-sm">Language<select className="mt-1 w-full rounded border p-2" value={config.language} onChange={e => setConfig({...config, language:e.target.value})}><option value="python">Python AST</option><option value="cpp_ros2">C++ / ROS2 (future)</option></select></label>
          <label className="text-sm">Maximum mutants<input type="number" min="1" max="5000" className="mt-1 w-full rounded border p-2" value={config.max_mutants} onChange={e => setConfig({...config,max_mutants:e.target.value})}/></label>
          <label className="text-sm">Seed (optional)<input type="number" className="mt-1 w-full rounded border p-2" value={config.seed} onChange={e => setConfig({...config,seed:e.target.value})}/></label>
          <label className="col-span-2 text-sm">Function scope (optional)<input className="mt-1 w-full rounded border p-2" value={config.function_scope} onChange={e => setConfig({...config,function_scope:e.target.value})}/></label>
          <label className="text-sm">Timeout (seconds)<input type="number" min="1" className="mt-1 w-full rounded border p-2" value={config.execution_configuration?.timeout_seconds || 60} onChange={e => setConfig({...config,execution_configuration:{...config.execution_configuration,timeout_seconds:Number(e.target.value)}})}/></label>
          <label className="text-sm">Memory limit (MB)<input type="number" min="64" className="mt-1 w-full rounded border p-2" value={config.execution_configuration?.memory_mb || 512} onChange={e => setConfig({...config,execution_configuration:{...config.execution_configuration,memory_mb:Number(e.target.value)}})}/></label>
        </div>
        <div className="flex flex-wrap gap-3">{families.map(family => <label key={family} className="text-sm"><input type="checkbox" checked={config.operator_families.includes(family)} onChange={() => toggleFamily(family)} className="mr-1"/>{family}</label>)}</div>
        <label className="block text-sm">Upload Python source<input className="mt-1 block" type="file" accept=".py,text/x-python" onChange={loadFile}/></label>
        {pythonFiles.length > 0 && <p className="text-xs text-gray-500">{pythonFiles.length} managed Python file(s) available; upload content explicitly to avoid reading hidden paths.</p>}
        <textarea className="h-52 w-full rounded border p-3 font-mono text-xs" value={config.source} onChange={e => setConfig({...config,source:e.target.value})} placeholder="def calculate(a, b):\n    return a + b"/>
        <button disabled={busy || config.language !== 'python'} onClick={generate} className="rounded bg-blue-600 px-4 py-2 text-white disabled:bg-gray-300">{busy ? 'Generating…' : 'Generate & preview'}</button>
      </section>
      <section className="rounded-lg border bg-white p-5 shadow-sm">
        <div className="mb-3 flex items-center justify-between"><h3 className="font-semibold">Mutant preview ({mutants.length})</h3>{campaign && <span className="text-xs text-gray-500">{campaign.campaign_id}</span>}</div>
        <div className="max-h-80 overflow-auto rounded border"><table className="min-w-full text-left text-xs"><thead className="sticky top-0 bg-gray-50"><tr><th className="p-2">Mutant ID</th><th>Source</th><th>Function</th><th>Operator</th><th>Change</th><th>Status</th></tr></thead><tbody>{mutants.map(mutant => <tr key={mutant.mutant_id} onClick={() => setSelected(mutant)} className="cursor-pointer border-t hover:bg-blue-50"><td className="p-2 font-mono">{mutant.mutant_id.slice(0,12)}…</td><td>{mutant.source_path}:{mutant.line}</td><td>{mutant.function || '&lt;module&gt;'}</td><td>{mutant.family}</td><td>{mutant.operator} → {mutant.replacement}</td><td>previewed</td></tr>)}</tbody></table></div>
        <pre className="mt-4 max-h-72 overflow-auto rounded bg-slate-950 p-3 text-xs text-slate-100">{selected?.diff || 'Select a mutant to inspect its unified diff.'}</pre>
      </section>
    </div>
    {campaign && <section className="rounded-lg border bg-white p-5 shadow-sm space-y-4">
      <div className="flex flex-wrap items-center gap-3"><button disabled={!executionAvailable} onClick={recordBaselineState} className="rounded bg-slate-700 px-4 py-2 text-white disabled:bg-gray-300">Run baseline</button><button disabled={!executionAvailable} onClick={requestExecution} className="rounded bg-indigo-600 px-4 py-2 text-white disabled:bg-gray-300">Start mutation campaign</button><button onClick={recordBaselineState} className="rounded border px-4 py-2">Record execution unavailable</button><button onClick={cancel} className="rounded border px-4 py-2">Cancel</button><button onClick={refreshReport} className="rounded border px-4 py-2">Refresh status/results</button><button onClick={downloadReport} className="rounded border px-4 py-2">Download JSON report</button><span className="text-sm text-gray-500">Status: {campaign.status || 'generated'}</span></div>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4 lg:grid-cols-8">{[['Score', score?.overall?.score == null ? 'Not assessable' : `${(score.overall.score*100).toFixed(1)}%`],['Total', mutants.length],['Killed',score?.counts?.killed||0],['Survived',score?.counts?.survived||0],['Invalid',score?.counts?.invalid||0],['Timeout',score?.counts?.timeout||0],['Exec. error',score?.counts?.execution_error||0],['Not executed',score?.counts?.not_executed||0]].map(([label,value]) => <div key={label} className="rounded bg-gray-50 p-3"><div className="text-xs text-gray-500">{label}</div><div className="text-lg font-semibold">{value}</div></div>)}</div>
      <div><label className="text-sm">Result status filter <select className="ml-2 rounded border p-1" value={resultFilter} onChange={e => setResultFilter(e.target.value)}><option value="all">All</option>{['killed','survived','invalid','timeout','execution_error','equivalent','undetermined','not_executed'].map(value => <option key={value}>{value}</option>)}</select></label><div className="mt-2 max-h-48 overflow-auto">{results.filter(item => resultFilter === 'all' || item.outcome === resultFilter).map(item => <details key={item.mutant_id} className="border-t py-2 text-sm"><summary className="cursor-pointer">{item.mutant_id} — {item.outcome}</summary><div className="pl-4 text-xs text-gray-600">{item.reason || item.reason_detail}{item.tests?.map(test => <div key={test.test_id}>{test.test_id}: {test.outcome}</div>)}</div></details>)}</div></div>
    </section>}
  </div>;
}
