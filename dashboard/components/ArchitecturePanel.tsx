import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';
import { Network, RefreshCw } from 'lucide-react';

interface ArchitecturePanelProps {
  diagramDefinition: string;
}

const ArchitecturePanel: React.FC<ArchitecturePanelProps> = ({ diagramDefinition }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svgContent, setSvgContent] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'dark', // Native dark theme from mermaid
      securityLevel: 'loose',
      fontFamily: 'Inter, sans-serif',
      themeVariables: {
        darkMode: true,
        background: 'transparent',
        primaryColor: '#0ea5e9',
        secondaryColor: '#8b5cf6',
        tertiaryColor: '#10b981',
        primaryBorderColor: '#0284c7',
        lineColor: '#64748b',
        textColor: '#f8fafc',
        mainBkg: 'transparent',
      }
    });
  }, []);

  useEffect(() => {
    const renderDiagram = async () => {
      if (!containerRef.current) return;

      try {
        const { svg } = await mermaid.render(`mermaid-${Date.now()}`, diagramDefinition);
        setSvgContent(svg);
        setError(null);
      } catch (err) {
        console.error("Mermaid render error:", err);
        setError("Failed to render architecture diagram.");
      }
    };

    renderDiagram();
  }, [diagramDefinition]);

  return (
    <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl shadow-2xl flex flex-col h-full overflow-hidden hover:border-white/20 transition-all duration-300 group relative">
      {/* Decorative glow */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-violet-500/10 blur-[80px] rounded-full pointer-events-none group-hover:bg-violet-500/20 transition-colors"></div>

      <div className="p-6 border-b border-white/5 flex justify-between items-center relative z-10">
        <h2 className="text-lg font-bold text-white flex items-center gap-3 tracking-wide">
          <div className="bg-gradient-to-br from-violet-500/20 to-purple-500/20 p-2 rounded-xl border border-violet-500/30">
            <Network className="w-5 h-5 text-violet-400" />
          </div>
          Live Architecture
        </h2>
        <span className="flex items-center gap-3 px-3 py-1.5 bg-slate-900/40 rounded-full border border-white/5">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
          </span>
          <span className="text-xs text-slate-300 font-mono font-medium tracking-wider uppercase">Synced</span>
        </span>
      </div>

      {/* Description Section */}
      <div className="px-6 py-4 bg-slate-950/40 border-b border-white/5 relative z-10">
        <p className="text-sm text-slate-300 leading-relaxed">
          This diagram is rendered from <span className="font-mono text-violet-400 bg-violet-500/10 px-1.5 py-0.5 rounded">ARCHITECTURE.md</span> and shows the system architecture:
        </p>
        <ul className="mt-3 space-y-1.5 text-xs text-slate-400">
          <li className="flex items-start gap-2">
            <span className="text-emerald-400 mt-0.5">•</span>
            <span><strong className="text-slate-300">External Systems:</strong> GitHub API, Jules Review Provider</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-emerald-400 mt-0.5">•</span>
            <span><strong className="text-slate-300">Backend Core:</strong> Orchestrator, Agents (Code Reviewer, README/Spec Updaters)</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-emerald-400 mt-0.5">•</span>
            <span><strong className="text-slate-300">Review Providers:</strong> Jules API with LLM fallback (Gemini/OpenAI)</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-emerald-400 mt-0.5">•</span>
            <span><strong className="text-slate-300">Session Memory:</strong> Persistent state and metrics storage</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-emerald-400 mt-0.5">•</span>
            <span><strong className="text-slate-300">Repo Artifacts:</strong> README.md, spec.md, CODE_REVIEW.md</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-emerald-400 mt-0.5">•</span>
            <span><strong className="text-slate-300">This Dashboard:</strong> React UI consuming the FastAPI backend</span>
          </li>
        </ul>
      </div>

      <div
        ref={containerRef}
        className="flex-1 overflow-auto flex justify-center items-center bg-[#0B1221]/50 p-6 min-h-[300px] relative z-10"
      >
        {error ? (
          <div className="text-rose-400 text-sm bg-rose-950/30 px-6 py-4 rounded-xl border border-rose-500/20 flex items-center gap-3">
            <RefreshCw className="w-4 h-4" />
            {error}
          </div>
        ) : (
          <div
            dangerouslySetInnerHTML={{ __html: svgContent }}
            className="w-full h-full flex items-center justify-center opacity-90 hover:opacity-100 transition-opacity scale-95"
          />
        )}
      </div>

      <div className="p-4 border-t border-white/5 flex gap-8 text-xs text-slate-400 justify-center font-medium bg-slate-950/30">
        <div className="flex items-center gap-2.5">
          <span className="w-2.5 h-2.5 bg-[#28a745] rounded-full shadow-[0_0_8px_rgba(40,167,69,0.8)]"></span>
          <span className="tracking-wide uppercase text-[10px] font-bold">Implemented</span>
        </div>
        <div className="flex items-center gap-2.5">
          <span className="w-2.5 h-2.5 bg-[#ffc107] rounded-full shadow-[0_0_8px_rgba(255,193,7,0.8)]"></span>
          <span className="tracking-wide uppercase text-[10px] font-bold">In Progress</span>
        </div>
        <div className="flex items-center gap-2.5">
          <span className="w-2.5 h-2.5 bg-slate-600 border border-slate-500 rounded-full border-dashed"></span>
          <span className="tracking-wide uppercase text-[10px] font-bold">Pending</span>
        </div>
      </div>
    </div>
  );
};

export default ArchitecturePanel;