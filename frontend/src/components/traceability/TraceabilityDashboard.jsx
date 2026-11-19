import React, { useEffect, useMemo, useState } from 'react';

const badge = {
  PASS: 'bg-green-100 text-green-800', FAIL: 'bg-red-100 text-red-800',
  INCONCLUSIVE: 'bg-amber-100 text-amber-800', NOT_VERIFIED: 'bg-amber-100 text-amber-800',
  NOT_COVERED: 'bg-gray-100 text-gray-700', STALE: 'bg-purple-100 text-purple-800',
};

function MetricCard({ label, value, hint }) {
  return <div className="rounded-lg border border-gray-200 bg-white p-4">
    <div className="text-xs font-medium uppercase tracking-wide text-gray-500">{label}</div>
    <div className="mt-1 text-2xl font-semibold text-gray-900">{value}</div>
    {hint && <div className="mt-1 text-xs text-gray-500">{hint}</div>}
  </div>;
}

export default function TraceabilityDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [verdict, setVerdict] = useState('');
  const [selected, setSelected] = useState(null);

  const load = async () => {
    setLoading(true); setError('');
    try {
      const params = new URLSearchParams();
      if (search) params.set('search', search);
      if (verdict) params.set('verdict', verdict);
      const response = await fetch(`/api/integrations/ifarlab/v1/traceability?${params}`);
      if (!response.ok) throw new Error(await response.text());
      const payload = await response.json();
      setData(payload);
      setSelected(current => current && payload.rows.find(row => row.submission_id === current.submission_id && row.test_case_id === current.test_case_id));
    } catch (exc) { setError(exc.message || 'Traceability data could not be loaded.'); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps
  const metrics = data?.metrics || {};
  const requirementById = useMemo(() => Object.fromEntries((data?.requirements || []).map(item => [item.id, item])), [data]);

  if (loading && !data) return <div className="p-8 text-center text-gray-500">Loading traceability records…</div>;
  return <div className="space-y-5">
    <div className="flex flex-wrap items-end gap-3">
      <div className="min-w-64 flex-1"><label className="block text-xs font-medium text-gray-600">Search</label><input value={search} onChange={e => setSearch(e.target.value)} onKeyDown={e => e.key === 'Enter' && load()} placeholder="Requirement, test case, model, run or hash" className="mt-1 w-full rounded-md border-gray-300" /></div>
      <div><label className="block text-xs font-medium text-gray-600">Verdict</label><select value={verdict} onChange={e => setVerdict(e.target.value)} className="mt-1 rounded-md border-gray-300"><option value="">All</option>{['PASS','FAIL','INCONCLUSIVE','NOT_VERIFIED','NOT_COVERED','STALE'].map(v => <option key={v}>{v}</option>)}</select></div>
      <button onClick={load} className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">Apply</button>
    </div>
    {error && <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4 lg:grid-cols-6">
      <MetricCard label="Requirements" value={metrics.total_requirements ?? 0} />
      <MetricCard label="Coverage" value={`${(metrics.coverage_percentage || 0).toFixed(1)}%`} hint={`${metrics.covered_requirements || 0} covered`} />
      <MetricCard label="Verification" value={`${(metrics.verification_percentage || 0).toFixed(1)}%`} hint={`${metrics.verified_requirements || 0} passed`} />
      <MetricCard label="Uncovered" value={metrics.uncovered_requirements ?? 0} />
      <MetricCard label="Test cases" value={metrics.total_generated_test_cases ?? 0} />
      <MetricCard label="Stale" value={metrics.requirement_states?.STALE ?? 0} />
      <MetricCard label="Submissions" value={metrics.external_submissions ?? 0} />
      <MetricCard label="Robot metrics" value={metrics.robot_metrics_received ?? 0} />
      <MetricCard label="Trace gaps" value={metrics.traceability_gaps ?? 0} />
    </div>
    <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
      <div className="overflow-x-auto"><table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50"><tr>{['Requirement','Test Case','LLM','Code Hash','Run ID','Quality','Verdict'].map(h => <th key={h} className="px-3 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">{h}</th>)}</tr></thead>
        <tbody className="divide-y divide-gray-100">{(data?.rows || []).map((row, index) => <tr key={`${row.submission_id}-${row.test_case_id}-${index}`} onClick={() => setSelected(row)} className="cursor-pointer hover:bg-indigo-50">
          <td className="px-3 py-3"><div className="font-medium text-gray-900">{row.requirement_ids?.join(', ') || 'Unlinked'}</div><div className="max-w-xs truncate text-xs text-gray-500">{row.requirement_ids?.map(id => requirementById[id]?.text).filter(Boolean).join('; ')}</div></td>
          <td className="px-3 py-3 text-gray-700">{row.test_case_id || 'Not covered'}</td><td className="px-3 py-3"><div>{row.llm}</div><div className="text-xs text-gray-500">{row.provider}</div></td>
          <td className="px-3 py-3 font-mono text-xs" title={row.code_sha256}>{row.code_sha256?.slice(0, 12) || 'Unavailable'}</td><td className="px-3 py-3">{row.run_id || 'Unavailable'}</td><td className="px-3 py-3">{row.code_quality}</td>
          <td className="px-3 py-3"><span className={`rounded-full px-2 py-1 text-xs font-semibold ${badge[row.verdict] || badge.NOT_VERIFIED}`}>{row.verdict}</span>{row.contradiction && <div className="mt-1 text-xs font-medium text-red-700">Contradiction</div>}</td>
        </tr>)}</tbody>
      </table></div>
      {!data?.rows?.length && <div className="p-8 text-center text-gray-500">No traceability records match this scope.</div>}
    </div>
    {selected && <div className="rounded-lg border border-gray-200 bg-white p-5">
      <div className="flex items-center justify-between"><h3 className="text-lg font-semibold text-gray-900">Verification details</h3><button onClick={() => setSelected(null)} className="text-sm text-gray-500">Close</button></div>
      <dl className="mt-4 grid grid-cols-1 gap-3 text-sm md:grid-cols-3">
        <div><dt className="text-gray-500">Requirement</dt><dd className="font-medium">{selected.requirement_ids?.join(', ')}</dd></div><div><dt className="text-gray-500">Test case</dt><dd className="font-medium">{selected.test_case_id || 'Unavailable'}</dd></div><div><dt className="text-gray-500">Run</dt><dd className="font-medium">{selected.run_id || 'Unavailable'}</dd></div>
        <div><dt className="text-gray-500">Submission</dt><dd className="font-mono text-xs">{selected.submission_id || 'Unavailable'}</dd></div><div><dt className="text-gray-500">Code hash</dt><dd className="break-all font-mono text-xs">{selected.code_sha256 || 'Unavailable'}</dd></div><div><dt className="text-gray-500">Evidence</dt><dd>{selected.evidence?.length ? `${selected.evidence.length} reference(s)` : 'Unavailable'}</dd></div>
        <div><dt className="text-gray-500">Engine and rules</dt><dd>{selected.verdict_engine_version || 'Unavailable'} / {selected.rule_set_version || 'Unavailable'}</dd></div><div><dt className="text-gray-500">Assertion and robot</dt><dd>{selected.assertion_result || 'Unavailable'} / {selected.robot_evaluation || 'Unavailable'}</dd></div><div><dt className="text-gray-500">Execution validity</dt><dd>{selected.execution_validity || 'Unavailable'}</dd></div>
        <div><dt className="text-gray-500">Admission</dt><dd>{selected.admission || 'Unavailable'}</dd></div><div><dt className="text-gray-500">IFARLAB verdict</dt><dd>{selected.authoritative_verdict || 'Unavailable'}</dd></div><div><dt className="text-gray-500">STLC re-evaluation</dt><dd>{selected.stlc_verdict || 'Unavailable'}</dd></div>
      </dl>
      <p className="mt-4 text-sm text-gray-700">{selected.explanation || 'No deterministic evaluation has been recorded.'}</p>
      <div className="mt-4 overflow-x-auto"><table className="min-w-full divide-y divide-gray-200 text-sm"><thead className="bg-gray-50"><tr>{['Rule','Metric','Measured','Operator','Threshold','Unit','Result'].map(h => <th key={h} className="px-3 py-2 text-left text-xs font-semibold uppercase text-gray-500">{h}</th>)}</tr></thead><tbody className="divide-y divide-gray-100">{(selected.applied_rules || []).map((rule, index) => <tr key={`${rule.rule_id}-${index}`}><td className="px-3 py-2">{rule.rule_id}</td><td className="px-3 py-2">{rule.metric}</td><td className="px-3 py-2">{rule.actual ?? 'Unavailable'}</td><td className="px-3 py-2">{rule.operator}</td><td className="px-3 py-2">{String(rule.threshold)}</td><td className="px-3 py-2">{rule.unit || '—'}</td><td className="px-3 py-2 font-semibold">{rule.passed === true ? 'PASS' : rule.passed === false ? 'FAIL' : 'INCONCLUSIVE'}</td></tr>)}</tbody></table></div>
    </div>}
  </div>;
}
