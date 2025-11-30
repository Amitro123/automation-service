import React, { useState } from 'react';
import { Bug, PullRequest } from '../types';
import { AlertCircle, GitPullRequest, Check, X, Bug as BugIcon } from 'lucide-react';

interface IssuesPanelProps {
  bugs: Bug[];
  prs: PullRequest[];
}

const IssuesPanel: React.FC<IssuesPanelProps> = ({ bugs, prs }) => {
  const [activeTab, setActiveTab] = useState<'bugs' | 'prs'>('bugs');

  return (
    <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl shadow-2xl h-full flex flex-col hover:border-white/20 transition-all duration-300 relative group overflow-hidden">
      <div className="absolute top-[-50px] right-[-50px] w-40 h-40 bg-rose-500/10 blur-[80px] rounded-full pointer-events-none group-hover:bg-rose-500/20 transition-colors"></div>

      <div className="flex border-b border-white/5 relative z-10">
        <button
          onClick={() => setActiveTab('bugs')}
          className={`flex-1 py-5 text-sm font-bold tracking-wide flex items-center justify-center gap-2.5 transition-all relative ${
            activeTab === 'bugs' ? 'text-rose-400 bg-white/5' : 'text-slate-500 hover:text-slate-300 hover:bg-white/5'
          }`}
        >
          <BugIcon className="w-4 h-4" />
          BUGS <span className="text-xs opacity-70">({bugs.length})</span>
          {activeTab === 'bugs' && (
              <div className="absolute bottom-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-rose-500 to-transparent shadow-[0_0_10px_rgba(244,63,94,0.8)]"></div>
          )}
        </button>
        <button
          onClick={() => setActiveTab('prs')}
          className={`flex-1 py-5 text-sm font-bold tracking-wide flex items-center justify-center gap-2.5 transition-all relative ${
            activeTab === 'prs' ? 'text-cyan-400 bg-white/5' : 'text-slate-500 hover:text-slate-300 hover:bg-white/5'
          }`}
        >
          <GitPullRequest className="w-4 h-4" />
          PRS <span className="text-xs opacity-70">({prs.length})</span>
          {activeTab === 'prs' && (
              <div className="absolute bottom-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-cyan-500 to-transparent shadow-[0_0_10px_rgba(6,182,212,0.8)]"></div>
          )}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-5 space-y-4 scrollbar-hide relative z-10">
        {activeTab === 'bugs' ? (
          bugs.map(bug => (
            <div key={bug.id} className="border border-white/5 rounded-2xl p-4 flex justify-between items-start bg-[#0B1221]/40 hover:bg-[#0B1221]/60 hover:border-rose-500/20 transition-all group/card cursor-default">
              <div className="w-full">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${
                        bug.severity === 'Critical' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20 shadow-[0_0_10px_-3px_rgba(244,63,94,0.3)]' :
                        bug.severity === 'Major' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20 shadow-[0_0_10px_-3px_rgba(245,158,11,0.3)]' : 'bg-blue-500/10 text-blue-400 border-blue-500/20 shadow-[0_0_10px_-3px_rgba(59,130,246,0.3)]'
                    }`}>
                        {bug.severity}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono group-hover/card:text-slate-400 transition-colors">{bug.id}</span>
                  </div>
                  <span className="text-[10px] text-slate-600">{bug.createdAt}</span>
                </div>
                <h4 className="text-sm font-medium text-slate-200 group-hover/card:text-white transition-colors leading-relaxed">{bug.title}</h4>
                <div className="text-[10px] text-slate-500 mt-3 flex items-center gap-2 font-medium">
                    <span className={`w-2 h-2 rounded-full ${bug.status === 'Open' ? 'bg-rose-500 shadow-[0_0_5px_rgba(244,63,94,0.6)]' : 'bg-amber-500 shadow-[0_0_5px_rgba(245,158,11,0.6)]'}`}></span>
                    {bug.status.toUpperCase()}
                </div>
              </div>
            </div>
          ))
        ) : (
          prs.map(pr => (
            <div key={pr.id} className="border border-white/5 rounded-2xl p-4 flex justify-between items-center bg-[#0B1221]/40 hover:bg-[#0B1221]/60 hover:border-cyan-500/20 transition-all group/card cursor-default">
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <span className="text-slate-500 font-mono text-[10px] group-hover/card:text-slate-400 transition-colors">#{pr.id}</span>
                  <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase tracking-wider border ${
                    pr.status === 'Merged' ? 'bg-purple-500/10 text-purple-400 border-purple-500/20 shadow-[0_0_10px_-3px_rgba(168,85,247,0.3)]' :
                    pr.status === 'Open' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-[0_0_10px_-3px_rgba(16,185,129,0.3)]' : 'bg-slate-700/50 text-slate-400 border-slate-600/30'
                  }`}>
                    {pr.status}
                  </span>
                </div>
                <h4 className="text-sm font-medium text-slate-200 mt-2 group-hover/card:text-white transition-colors">{pr.title}</h4>
                <p className="text-[10px] text-slate-500 mt-1.5 flex items-center gap-1">
                    Created by <span className="text-slate-400 font-medium bg-white/5 px-1.5 rounded">{pr.author}</span>
                </p>
              </div>
              <div title={pr.checksPassed ? 'All Checks Passed' : 'Checks Failed'} className={`p-2 rounded-full transition-colors border ${pr.checksPassed ? 'bg-emerald-500/10 border-emerald-500/20' : 'bg-rose-500/10 border-rose-500/20'}`}>
                {pr.checksPassed ? (
                  <Check className="w-4 h-4 text-emerald-500" />
                ) : (
                  <X className="w-4 h-4 text-rose-500" />
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default IssuesPanel;