import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';
import { CoverageMetrics, LLMMetrics } from '../types';
import { Zap, ShieldCheck, AlertTriangle } from 'lucide-react';

interface MetricsPanelProps {
  coverage: CoverageMetrics;
  llm: LLMMetrics;
}

const MetricsPanel: React.FC<MetricsPanelProps> = ({ coverage, llm }) => {
  const pieData = [
    { name: 'Covered', value: coverage.total },
    { name: 'Uncovered', value: 100 - coverage.total },
  ];

  // Neon Emerald & Dark Navy
  const PIE_COLORS = ['#10b981', '#1e293b'];

  const barData = [
    { name: 'Efficiency', score: llm.efficiencyScore },
    { name: 'Memory', score: llm.sessionMemoryUsage },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 h-full">
      {/* Test Coverage Card */}
      <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl shadow-2xl p-6 hover:border-white/20 transition-all duration-300 relative group overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 blur-[60px] rounded-full pointer-events-none group-hover:bg-emerald-500/20 transition-colors"></div>

        <h3 className="text-slate-200 font-bold mb-6 flex items-center gap-3 relative z-10">
          <div className="bg-gradient-to-br from-emerald-500/20 to-teal-500/20 p-2 rounded-xl border border-emerald-500/30 shadow-lg shadow-emerald-500/10">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
          </div>
          Code Quality
        </h3>

        <div className="flex items-center justify-between h-40 relative z-10">
          <div className="w-[45%] h-full relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  innerRadius={38}
                  outerRadius={58}
                  paddingAngle={8}
                  dataKey="value"
                  stroke="none"
                  cornerRadius={4}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            {/* Center Text */}
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-2xl font-bold text-white tracking-tight drop-shadow-md">{coverage.total}%</span>
              <span className="text-[10px] uppercase text-slate-500 font-bold tracking-widest">Cov</span>
            </div>
          </div>

          <div className="w-[55%] space-y-5 pl-2">
            <div>
              <div className="flex justify-between items-end mb-1.5">
                <span className="text-xs text-slate-400 font-medium">Uncovered Lines</span>
                <span className="text-rose-400 font-bold text-sm bg-rose-950/40 px-1.5 py-0.5 rounded border border-rose-500/20">{coverage.uncoveredLines}</span>
              </div>
              <div className="w-full bg-slate-800/80 rounded-full h-1.5 overflow-hidden border border-white/5">
                <div className="bg-rose-500 h-full rounded-full shadow-[0_0_8px_rgba(244,63,94,0.6)]" style={{ width: `${Math.min((coverage.uncoveredLines / 200) * 100, 100)}%` }}></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between items-end mb-1.5">
                <span className="text-xs text-slate-400 font-medium">Mutation Score</span>
                {coverage.mutationStatus === 'skipped' ? (
                  <div className="group/tooltip relative">
                    <span className="text-amber-400 font-bold text-[10px] bg-amber-950/40 px-1.5 py-0.5 rounded border border-amber-500/20 flex items-center gap-1 cursor-help">
                      <AlertTriangle className="w-3 h-3" /> Skipped
                    </span>
                    <div className="absolute bottom-full right-0 mb-2 w-48 p-2 bg-slate-900 border border-white/10 rounded-lg text-[10px] text-slate-300 shadow-xl opacity-0 group-hover/tooltip:opacity-100 transition-opacity pointer-events-none z-50">
                      Mutation tests skipped ({coverage.mutationReason || 'Windows/No Python'}). Run in Linux/CI for real scores.
                    </div>
                  </div>
                ) : (
                  <span className="text-cyan-400 font-bold text-sm bg-cyan-950/40 px-1.5 py-0.5 rounded border border-cyan-500/20">{coverage.mutationScore}%</span>
                )}
              </div>
              <div className="w-full bg-slate-800/80 rounded-full h-1.5 overflow-hidden border border-white/5">
                <div
                  className={`h-full rounded-full shadow-[0_0_8px_rgba(6,182,212,0.6)] ${coverage.mutationStatus === 'skipped' ? 'bg-amber-500/50' : 'bg-cyan-500'}`}
                  style={{ width: `${coverage.mutationStatus === 'skipped' ? 100 : coverage.mutationScore}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* LLM Metrics Card */}
      <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl shadow-2xl p-6 hover:border-white/20 transition-all duration-300 relative group overflow-hidden">
        <div className="absolute bottom-0 left-0 w-32 h-32 bg-violet-500/10 blur-[60px] rounded-full pointer-events-none group-hover:bg-violet-500/20 transition-colors"></div>

        <h3 className="text-slate-200 font-bold mb-6 flex items-center gap-3 relative z-10">
          <div className="bg-gradient-to-br from-violet-500/20 to-fuchsia-500/20 p-2 rounded-xl border border-violet-500/30 shadow-lg shadow-violet-500/10">
            <Zap className="w-5 h-5 text-violet-400" />
          </div>
          LLM Intelligence
        </h3>

        <div className="grid grid-cols-2 gap-4 mb-6 relative z-10">
          <div className="bg-white/5 p-3 rounded-2xl border border-white/5 backdrop-blur-sm flex flex-col justify-between h-20 overflow-hidden">
            <p className="text-[10px] text-violet-300 uppercase tracking-wider font-bold truncate">Tokens Used</p>
            <p className="text-xl lg:text-2xl font-bold text-white tracking-tight truncate" title={llm.tokensUsed.toLocaleString()}>
              {llm.tokensUsed.toLocaleString()}
            </p>
          </div>
          <div className="bg-white/5 p-3 rounded-2xl border border-white/5 backdrop-blur-sm flex flex-col justify-between h-20">
            <p className="text-[10px] text-emerald-300 uppercase tracking-wider font-bold">Est. Cost</p>
            <p className="text-xl lg:text-2xl font-bold text-white tracking-tight">${llm.estimatedCost.toFixed(2)}</p>
          </div>
        </div>

        <div className="h-20 w-full relative z-10">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart layout="vertical" data={barData} margin={{ left: 0, right: 10, top: 0, bottom: 0 }} barGap={6}>
              <XAxis type="number" hide domain={[0, 100]} />
              <YAxis dataKey="name" type="category" width={70} tick={{ fontSize: 10, fill: '#94a3b8', fontWeight: 600 }} axisLine={false} tickLine={false} />
              <Tooltip
                cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                contentStyle={{ backgroundColor: '#0f172a', borderColor: 'rgba(255,255,255,0.1)', color: '#f8fafc', borderRadius: '12px', fontSize: '12px', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)' }}
                itemStyle={{ color: '#f8fafc' }}
              />
              <Bar dataKey="score" barSize={10} radius={[0, 4, 4, 0]} animationDuration={1000}>
                {barData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={index === 0 ? '#10b981' : '#f59e0b'}
                    style={{ filter: `drop-shadow(0 0 4px ${index === 0 ? 'rgba(16,185,129,0.5)' : 'rgba(245,158,11,0.5)'})` }}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default MetricsPanel;