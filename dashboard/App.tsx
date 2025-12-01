import React, { useState, useEffect } from 'react';
import {
  Shield,
  Settings,
  Github,
  FileText,
  RefreshCw,
  AlertTriangle,
  Lock,
  Unlock,
  Key,
  Sparkles,
  Cpu
} from 'lucide-react';
import MetricsPanel from './components/MetricsPanel';
import TaskList from './components/TaskList';
import IssuesPanel from './components/IssuesPanel';
import ArchitecturePanel from './components/ArchitecturePanel';
import LogViewer from './components/LogViewer';
import {
  REPOSITORIES,
  MOCK_TASKS,
  MOCK_BUGS,
  MOCK_PRS,
  INITIAL_METRICS,
  COVERAGE_DATA,
  INITIAL_LOGS,
  ARCHITECTURE_DIAGRAM
} from './constants';
import { Repository, LogEntry, Task, Status } from './types';
import { generateProjectFile } from './services/geminiService';
import { fetchDashboardMetrics, fetchArchitecture, fetchHistory } from './services/apiService';

function App() {
  // State
  const [selectedRepo, setSelectedRepo] = useState<Repository>(REPOSITORIES[0]);
  const [logs, setLogs] = useState<LogEntry[]>(INITIAL_LOGS);
  const [isGenerating, setIsGenerating] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [showKeyModal, setShowKeyModal] = useState(false);

  // Real-time State from API
  const [metrics, setMetrics] = useState(INITIAL_METRICS);
  const [coverage, setCoverage] = useState(COVERAGE_DATA);
  const [isConnected, setIsConnected] = useState(false);
  const [architectureDiagram, setArchitectureDiagram] = useState(ARCHITECTURE_DIAGRAM);
  const [tasks, setTasks] = useState<Task[]>(MOCK_TASKS);

  // Fetch real data from FastAPI backend
  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await fetchDashboardMetrics();
        if (data) {
          setIsConnected(true);
          setCoverage({
            total: data.coverage.total,
            uncoveredLines: data.coverage.uncoveredLines,
            mutationScore: data.coverage.mutationScore,
          });
          setMetrics({
            tokensUsed: data.llm.tokensUsed,
            estimatedCost: data.llm.estimatedCost,
            efficiencyScore: data.llm.efficiencyScore,
            sessionMemoryUsage: data.llm.sessionMemoryUsage,
          });
          if (data.logs.length > 0) {
            setLogs(data.logs.map(l => ({ ...l, level: l.level as 'INFO' | 'WARN' | 'ERROR' })));
          }
          setSelectedRepo(prev => ({ ...prev, isSecure: data.security.isSecure }));
        }

        // Fetch Architecture
        const archData = await fetchArchitecture();
        if (archData && archData.diagram) {
          setArchitectureDiagram(archData.diagram);
        }

        // Fetch History (map to Tasks)
        const historyData = await fetchHistory();
        if (historyData && historyData.length > 0) {
          const historyTasks: Task[] = historyData.map((run: any) => ({
            id: run.id,
            title: `Run ${run.commit_sha.substring(0, 7)} (${run.branch})`,
            status: run.status === 'completed' ? Status.Completed :
              run.status === 'running' ? Status.InProgress :
                run.status === 'failed' ? Status.Failed : Status.Pending
          }));
          setTasks(historyTasks);
        }

      } catch (error) {
        console.error('API fetch failed:', error);
        setIsConnected(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleGenerateFile = async (type: 'README' | 'SPEC') => {
    if (!apiKey) {
      setShowKeyModal(true);
      return;
    }

    setIsGenerating(true);
    const newLog: LogEntry = {
      timestamp: new Date().toLocaleTimeString(),
      level: 'INFO',
      message: `Initiating Gemini 2.5 Agent for ${type} generation...`
    };
    setLogs(prev => [...prev, newLog]);

    try {
      const result = await generateProjectFile(apiKey, type, selectedRepo.name, "An automated GitHub dashboard tool.");

      const successLog: LogEntry = {
        timestamp: new Date().toLocaleTimeString(),
        level: 'INFO',
        message: `Generated ${type} successfully using Gemini 2.5 Flash.`
      };
      setLogs(prev => [...prev, successLog]);
      alert(`Success! Generated ${type}. (See console for content)`);
      console.log(`Generated ${type} Content:\n`, result);

      // Update local state to show file exists
      setSelectedRepo(prev => ({
        ...prev,
        hasReadme: type === 'README' ? true : prev.hasReadme,
        hasSpec: type === 'SPEC' ? true : prev.hasSpec
      }));

    } catch (e) {
      const errorLog: LogEntry = {
        timestamp: new Date().toLocaleTimeString(),
        level: 'ERROR',
        message: `Gemini Generation Failed: ${e instanceof Error ? e.message : 'Unknown error'}`
      };
      setLogs(prev => [...prev, errorLog]);
      alert("Generation failed. Check API Key.");
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#020617] text-slate-200 font-sans selection:bg-cyan-500/30 selection:text-cyan-100 flex flex-col relative overflow-hidden">
      {/* Dynamic Background Gradients */}
      <div className="fixed top-[-10%] left-[-10%] w-[50%] h-[50%] bg-blue-600/10 blur-[120px] rounded-full pointer-events-none mix-blend-screen"></div>
      <div className="fixed bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-violet-600/10 blur-[120px] rounded-full pointer-events-none mix-blend-screen"></div>
      <div className="fixed top-[20%] right-[20%] w-[30%] h-[30%] bg-cyan-600/5 blur-[100px] rounded-full pointer-events-none mix-blend-screen animate-pulse"></div>

      {/* Header */}
      <header className="sticky top-0 z-40 bg-[#0f172a]/70 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-[1920px] mx-auto px-8 h-20 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="absolute inset-0 bg-cyan-500 blur-md opacity-20 rounded-xl"></div>
              <div className="relative bg-gradient-to-br from-cyan-950 to-slate-900 border border-cyan-500/20 p-2.5 rounded-xl text-cyan-400 shadow-xl">
                <Cpu className="w-6 h-6" />
              </div>
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
                StudioAI
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 tracking-wider uppercase backdrop-blur-md">Beta</span>
              </h1>
              <p className="text-xs text-slate-400 font-medium tracking-wide">Automated DevOps Intelligence</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Security Indicator */}
            <div className={`flex items-center gap-2 px-4 py-2 rounded-full text-xs font-bold border backdrop-blur-md transition-all duration-300 ${selectedRepo.isSecure
                ? 'bg-emerald-950/30 text-emerald-400 border-emerald-500/30 shadow-[0_0_15px_-5px_rgba(16,185,129,0.3)]'
                : 'bg-rose-950/30 text-rose-400 border-rose-500/30 shadow-[0_0_15px_-5px_rgba(244,63,94,0.3)]'
              }`}>
              {selectedRepo.isSecure ? <Lock className="w-3.5 h-3.5" /> : <Unlock className="w-3.5 h-3.5" />}
              {selectedRepo.isSecure ? 'SYSTEM SECURE' : 'VULNERABILITIES DETECTED'}
            </div>

            {/* Repo Selector */}
            <div className="relative group">
              <select
                className="appearance-none bg-[#1e293b]/50 backdrop-blur-md border border-white/10 text-slate-200 py-2.5 pl-4 pr-10 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all cursor-pointer hover:bg-white/5 hover:border-white/20 min-w-[240px]"
                value={selectedRepo.id}
                onChange={(e) => {
                  const repo = REPOSITORIES.find(r => r.id === e.target.value);
                  if (repo) setSelectedRepo(repo);
                }}
              >
                {REPOSITORIES.map(r => (
                  <option key={r.id} value={r.id}>{r.name} ({r.branch})</option>
                ))}
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-400 group-hover:text-cyan-400 transition-colors">
                <Github className="w-4 h-4" />
              </div>
            </div>

            {/* Settings / API Key */}
            <button
              onClick={() => setShowKeyModal(true)}
              className="p-2.5 text-slate-400 hover:text-cyan-400 transition-all rounded-full hover:bg-white/5 active:scale-95 border border-transparent hover:border-white/10 relative group"
              title="API Key Settings"
            >
              <Settings className="w-5 h-5 group-hover:rotate-90 transition-transform duration-500" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-[1920px] w-full mx-auto px-8 py-8 relative z-10">

        {/* Top Alert for Missing Files */}
        {(!selectedRepo.hasReadme || !selectedRepo.hasSpec) && (
          <div className="mb-8 bg-gradient-to-r from-violet-950/40 to-slate-900/40 backdrop-blur-xl border border-violet-500/20 rounded-2xl p-6 flex items-center justify-between shadow-lg shadow-violet-900/10">
            <div className="flex items-center gap-5">
              <div className="relative">
                <div className="absolute inset-0 bg-violet-500 blur-lg opacity-20 rounded-full"></div>
                <div className="relative p-3 rounded-xl bg-violet-950/50 border border-violet-500/30 text-violet-400">
                  <Sparkles className="w-6 h-6" />
                </div>
              </div>
              <div>
                <h3 className="text-lg font-bold text-white tracking-tight">Project Documentation Incomplete</h3>
                <p className="text-sm text-slate-400 mt-1">
                  AI Agents detected missing files for <span className="text-cyan-300 font-mono bg-cyan-950/30 px-1.5 py-0.5 rounded border border-cyan-500/20">{selectedRepo.name}</span>. Auto-generation available.
                </p>
              </div>
            </div>
            <div className="flex gap-4">
              {!selectedRepo.hasReadme && (
                <button
                  onClick={() => handleGenerateFile('README')}
                  disabled={isGenerating}
                  className="px-5 py-2.5 bg-slate-800/80 hover:bg-slate-700 hover:text-white text-slate-300 border border-white/10 rounded-xl text-sm font-semibold transition-all flex items-center gap-2 disabled:opacity-50 hover:shadow-lg hover:shadow-black/20 active:scale-95"
                >
                  <FileText className="w-4 h-4" /> Generate README
                </button>
              )}
              {!selectedRepo.hasSpec && (
                <button
                  onClick={() => handleGenerateFile('SPEC')}
                  disabled={isGenerating}
                  className="px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl text-sm font-semibold transition-all flex items-center gap-2 disabled:opacity-50 shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/30 active:scale-95 ring-1 ring-inset ring-white/20"
                >
                  <Shield className="w-4 h-4" /> Generate Spec
                </button>
              )}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 h-auto xl:h-[calc(100vh-14rem)] min-h-[850px]">
          {/* Left Column: Metrics & Logs */}
          <div className="flex flex-col gap-8 xl:col-span-1 h-full overflow-hidden">
            <div className="flex-shrink-0">
              <MetricsPanel coverage={coverage} llm={metrics} />
            </div>
            <div className="flex-1 min-h-[300px] flex flex-col">
              <LogViewer logs={logs} />
            </div>
          </div>

          {/* Middle Column: Architecture & Progress */}
          <div className="flex flex-col gap-8 xl:col-span-1 h-full overflow-hidden">
            <div className="flex-[4] min-h-[450px]">
              <ArchitecturePanel diagramDefinition={architectureDiagram} />
            </div>
            <div className="flex-1 min-h-[250px]">
              <TaskList tasks={tasks} />
            </div>
          </div>

          {/* Right Column: Issues & PRs */}
          <div className="flex flex-col gap-8 xl:col-span-1 h-full overflow-hidden">
            <IssuesPanel bugs={MOCK_BUGS} prs={MOCK_PRS} />
          </div>
        </div>
      </main>

      {/* API Key Modal */}
      {showKeyModal && (
        <div className="fixed inset-0 bg-[#020617]/90 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="bg-[#0f172a] border border-white/10 rounded-3xl shadow-2xl max-w-md w-full p-8 relative overflow-hidden group">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-500 via-violet-500 to-fuchsia-500"></div>
            <div className="absolute -top-20 -right-20 w-40 h-40 bg-cyan-500/20 blur-[60px] rounded-full pointer-events-none group-hover:bg-cyan-500/30 transition-colors"></div>

            <div className="flex justify-between items-center mb-6 relative z-10">
              <h3 className="text-xl font-bold text-white flex items-center gap-3">
                <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
                  <Key className="w-5 h-5 text-cyan-400" />
                </div>
                API Configuration
              </h3>
              <button onClick={() => setShowKeyModal(false)} className="text-slate-500 hover:text-white transition-colors rounded-full p-1 hover:bg-white/5">
                <span className="text-2xl leading-none block h-6 w-6 text-center">&times;</span>
              </button>
            </div>
            <p className="text-sm text-slate-400 mb-8 leading-relaxed">
              Securely configure your Gemini API Key to enable GenAI agents for automated spec generation, README updates, and code analysis.
            </p>
            <div className="mb-8 relative z-10">
              <label className="block text-xs font-bold text-cyan-500 mb-2 uppercase tracking-wider ml-1">Gemini API Key</label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="sk-..."
                className="w-full bg-[#1e293b] border border-slate-700 rounded-xl px-5 py-3.5 text-sm text-white focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 outline-none transition-all placeholder:text-slate-600 shadow-inner"
              />
            </div>
            <div className="flex justify-end gap-3 relative z-10">
              <button
                onClick={() => setShowKeyModal(false)}
                className="px-5 py-2.5 text-slate-400 text-sm font-semibold hover:text-white hover:bg-white/5 rounded-xl transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => setShowKeyModal(false)}
                className="px-6 py-2.5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-sm font-bold rounded-xl shadow-lg shadow-cyan-900/20 transition-all active:scale-95 ring-1 ring-white/10"
              >
                Save Configuration
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;