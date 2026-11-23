import React, { useState } from 'react';
import TestCodeGeneration from './TestCodeGeneration';
import MutationTestingPanel from './MutationTestingPanel';

export default function TestCodeGenerationWorkspace(props) {
  const [tab, setTab] = useState('generation');
  return <div className="space-y-5">
    <div className="flex border-b border-gray-200" role="tablist" aria-label="Test code generation tools">
      {[['generation','Test Code Generation'], ['mutation','Mutation Testing']].map(([id,label]) => <button key={id} role="tab" aria-selected={tab===id} onClick={() => setTab(id)} className={`border-b-2 px-5 py-3 text-sm font-medium ${tab===id ? 'border-blue-600 text-blue-700' : 'border-transparent text-gray-500'}`}>{label}</button>)}
    </div>
    {tab === 'generation' ? <TestCodeGeneration {...props}/> : <MutationTestingPanel managedFiles={props.managedFiles} sessionId={props.sessionId}/>} 
  </div>;
}
