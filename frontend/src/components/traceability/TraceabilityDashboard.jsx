import React, { useEffect, useMemo, useState } from 'react';

const stageStyle = {
  verified_dt: 'bg-green-100 text-green-800', executed_dt: 'bg-blue-100 text-blue-800',
  executable: 'bg-indigo-100 text-indigo-800', generated: 'bg-cyan-100 text-cyan-800',
  mapped: 'bg-amber-100 text-amber-800', unmapped: 'bg-gray-100 text-gray-700',
};
const percent = value => value == null ? 'Not assessable' : `${value.toFixed(1)}%`;

function KpiCard({ title, metric, verified, tone }) {
  const achieved = metric?.assessment === 'achieved';
  return <div className={`rounded-xl border p-5 ${tone}`}>
    <div className="text-sm font-semibold text-gray-800">{title}</div>
    <div className="mt-2 text-3xl font-bold text-gray-950">{percent(metric?.percentage)}</div>
    <div className="mt-2 text-sm text-gray-700">{metric?.total_applicable ? `${metric.covered} of ${metric.total_applicable} applicable requirements` : 'No applicable requirements in this scope'}</div>
    <div className="mt-3 flex flex-wrap gap-2 text-xs">
      <span className={`rounded-full px-2 py-1 font-semibold ${achieved ? 'bg-green-100 text-green-800' : metric?.assessment === 'not_assessable' ? 'bg-gray-100 text-gray-700' : 'bg-amber-100 text-amber-800'}`}>Target {metric?.target_percentage}% · {metric?.assessment?.replace('_', ' ') || 'not assessable'}</span>
      <span className="rounded-full bg-white/80 px-2 py-1 text-gray-700">Verified {percent(verified?.percentage)}</span>
    </div>
  </div>;
}

function downloadJson(data) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
  const link = document.createElement('a'); link.href = url;
  link.download = `kpi-3-4-${data.scope?.requirements_set_version || 'unscoped'}.json`;
  link.click(); URL.revokeObjectURL(url);
}

export default function TraceabilityDashboard() {
  const [data, setData] = useState(null); const [loading, setLoading] = useState(true);
  const [error, setError] = useState(''); const [type, setType] = useState('');
  const [stage, setStage] = useState(''); const [environment, setEnvironment] = useState('');
  const [sutVersion, setSutVersion] = useState(''); const [level, setLevel] = useState('');
  const [selected, setSelected] = useState(null);
  const load = async () => {
    setLoading(true); setError('');
    try {
      const params = new URLSearchParams();
      if (type) params.set('requirement_type', type); if (stage) params.set('coverage_stage', stage);
      if (environment) params.set('environment_id', environment);
      if (sutVersion) params.set('sut_version', sutVersion); if (level) params.set('verification_level', level);
      const response = await fetch(`/api/integrations/ifarlab/v1/coverage?${params}`);
      if (!response.ok) throw new Error(await response.text());
      setData(await response.json()); setSelected(null);
    } catch (exc) { setError(exc.message || 'Coverage data could not be loaded.'); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps
  const rows = data?.requirements || [];
  const environments = useMemo(() => [...new Set(rows.flatMap(row => row.traceability_chains || []).flatMap(chain => chain.executions || []).map(run => run.environment?.environment_id).filter(Boolean))], [rows]);
  const sutVersions = useMemo(() => [...new Set(rows.flatMap(row => row.traceability_chains || []).map(chain => chain.sut_version).filter(Boolean))], [rows]);
  if (loading && !data) return <div className="p-8 text-center text-gray-500">Loading KPI 3.4 coverage…</div>;
  return <div className="space-y-5">
    <div className="flex flex-wrap items-start justify-between gap-3"><div><h2 className="text-xl font-semibold text-gray-950">MATISSE KPI 3.4 Requirement Coverage</h2><p className="mt-1 max-w-3xl text-sm text-gray-600">Primary coverage counts only valid, evidenced executions in registered Digital Twin environments. Generated tests do not count as tested requirements.</p></div><button disabled={!data} onClick={() => downloadJson(data)} className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50">Export JSON report</button></div>
    {error && <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
    <div className="grid gap-4 lg:grid-cols-2"><KpiCard title="Functional Requirements – DT Tested Coverage" metric={data?.kpi?.functional} verified={data?.verified?.functional} tone="border-blue-200 bg-blue-50" /><KpiCard title="Non-Functional Requirements – DT Tested Coverage" metric={data?.kpi?.non_functional} verified={data?.verified?.non_functional} tone="border-purple-200 bg-purple-50" /></div>
    <div className="grid grid-cols-2 gap-3 md:grid-cols-5">{[['Applicable', data?.summary?.total_applicable], ['Uncovered', data?.summary?.uncovered_requirements], ['Generated, not executed', data?.summary?.generated_not_executed], ['Failed/inconclusive', data?.summary?.failed_or_inconclusive], ['Unclassified', data?.summary?.unclassified_requirements]].map(([label, value]) => <div key={label} className="rounded-lg border border-gray-200 bg-white p-4"><div className="text-xs font-medium uppercase text-gray-500">{label}</div><div className="mt-1 text-2xl font-semibold">{value ?? 0}</div></div>)}</div>
    <div className="rounded-lg border border-gray-200 bg-white p-4 text-sm"><div className="font-semibold">Release readiness</div><div className="mt-2 flex flex-wrap gap-2"><span className="rounded-full bg-gray-100 px-2 py-1">Mandatory without test: {data?.generation_gate?.mandatory_without_test?.length ?? 0}</span><span className="rounded-full bg-gray-100 px-2 py-1">Mandatory not PASS: {data?.release_candidate_gate?.mandatory_not_pass?.length ?? 0}</span><span className="rounded-full bg-amber-100 px-2 py-1 text-amber-900">Fidelity: {data?.release_candidate_gate?.fidelity?.replaceAll('_', ' ') || 'not assessed'}</span></div></div>
    <div className="flex flex-wrap items-end gap-3 rounded-lg border border-gray-200 bg-white p-4">
      <label className="text-xs font-medium text-gray-600">Requirement type<select value={type} onChange={e => setType(e.target.value)} className="mt-1 block rounded-md border-gray-300 text-sm"><option value="">All</option><option value="functional">Functional</option><option value="non_functional">Non-functional</option><option value="unclassified">Unclassified</option></select></label>
      <label className="text-xs font-medium text-gray-600">Coverage stage<select value={stage} onChange={e => setStage(e.target.value)} className="mt-1 block rounded-md border-gray-300 text-sm"><option value="">All</option>{['unmapped','mapped','generated','executable','executed_dt','verified_dt'].map(value => <option key={value} value={value}>{value.replaceAll('_', ' ')}</option>)}</select></label>
      <label className="text-xs font-medium text-gray-600">DT environment<select value={environment} onChange={e => setEnvironment(e.target.value)} className="mt-1 block rounded-md border-gray-300 text-sm"><option value="">All</option>{environments.map(value => <option key={value}>{value}</option>)}</select></label>
      <label className="text-xs font-medium text-gray-600">SUT version<select value={sutVersion} onChange={e => setSutVersion(e.target.value)} className="mt-1 block rounded-md border-gray-300 text-sm"><option value="">All</option>{sutVersions.map(value => <option key={value}>{value}</option>)}</select></label>
      <label className="text-xs font-medium text-gray-600">Verification level<select value={level} onChange={e => setLevel(e.target.value)} className="mt-1 block rounded-md border-gray-300 text-sm"><option value="">All</option><option value="twin">Twin</option><option value="hil">HIL</option><option value="physical">Physical</option></select></label>
      <button onClick={load} className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">Apply scope</button>
      <div className="ml-auto text-xs text-gray-500">Evaluated {data?.evaluation_timestamp ? new Date(data.evaluation_timestamp).toLocaleString() : '—'} · Set {data?.scope?.requirements_set_version || 'not selected'}</div>
    </div>
    <div className="overflow-hidden rounded-lg border border-gray-200 bg-white"><div className="overflow-x-auto"><table className="min-w-full divide-y divide-gray-200 text-sm"><thead className="bg-gray-50"><tr>{['Requirement','Type','Version','Coverage stage','DT executions','Verification','Trace chains'].map(label => <th key={label} className="px-3 py-3 text-left text-xs font-semibold uppercase text-gray-500">{label}</th>)}</tr></thead><tbody className="divide-y divide-gray-100">{rows.map(row => <tr key={`${row.id}:${row.version}`} onClick={() => setSelected(row)} className="cursor-pointer hover:bg-indigo-50"><td className="px-3 py-3"><div className="font-semibold text-gray-900">{row.id}</div><div className="max-w-md text-xs text-gray-500">{row.text}</div></td><td className="px-3 py-3">{row.type?.replace('_', ' ')}</td><td className="px-3 py-3">{row.version}</td><td className="px-3 py-3"><span className={`rounded-full px-2 py-1 text-xs font-semibold ${stageStyle[row.coverage_stage]}`}>{row.coverage_stage?.replaceAll('_', ' ')}</span></td><td className="px-3 py-3">{row.valid_dt_execution_count}</td><td className="px-3 py-3 font-semibold">{row.verification_state}</td><td className="px-3 py-3">{row.traceability_chains?.length || 0}</td></tr>)}</tbody></table></div>{!rows.length && <div className="p-8 text-center text-gray-500">No applicable requirements match this scope. KPI achievement is not assessable.</div>}</div>
    {selected && <div className="rounded-lg border border-gray-200 bg-white p-5"><div className="flex justify-between"><div><h3 className="text-lg font-semibold">{selected.id} traceability</h3><p className="text-sm text-gray-600">Requirement → scenario → case → code → execution → verdict</p></div><button onClick={() => setSelected(null)} className="text-sm text-gray-500">Close</button></div><div className="mt-4 space-y-3">{(selected.traceability_chains || []).map((chain, index) => <div key={`${chain.submission_id}-${index}`} className="rounded-md border border-gray-200 p-3 text-sm"><div className="grid gap-2 md:grid-cols-5"><div><span className="text-gray-500">Scenario</span><br/>{chain.scenario_id || 'Missing'}</div><div><span className="text-gray-500">Test case</span><br/>{chain.test_case_id}</div><div><span className="text-gray-500">Function</span><br/><code className="text-xs">{chain.function}</code></div><div><span className="text-gray-500">Code</span><br/><code className="text-xs">{chain.code_sha256?.slice(0, 12)}</code></div><div><span className="text-gray-500">Executions</span><br/>{chain.executions?.length || 0}</div></div>{(chain.executions || []).map(run => <div key={run.run_id} className="mt-3 rounded bg-gray-50 p-2 text-xs"><b>{run.run_id}</b> · {run.environment?.environment_id || 'unknown environment'} · {run.final_verdict} · {run.dt_eligible ? 'KPI eligible' : `Excluded: ${run.exclusions?.join(', ')}`}</div>)}</div>)}{!selected.traceability_chains?.length && <div className="rounded bg-gray-50 p-4 text-sm text-gray-600">No valid test mapping exists for this requirement.</div>}</div></div>}
    <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">This dashboard reports technical evidence for the selected requirement set and scope. It does not make a universal MATISSE achievement claim, and synthetic demonstration data must remain separately labelled.</div>
  </div>;
}
