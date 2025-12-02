import React, { useEffect, useRef, useState } from 'react';
import { LogEntry } from '../types';
import { Terminal, ExternalLink } from 'lucide-react';

interface LogViewerProps {
  logs: LogEntry[];
  onLogClick?: (log: LogEntry) => void;
}

const LogViewer: React.FC<LogViewerProps> = ({ logs, onLogClick }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);

  // Handle scroll events to determine if we should auto-scroll
  const handleScroll = () => {
    if (containerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
      // If we are within 50px of the bottom, enable auto-scroll
      const isNearBottom = scrollHeight - scrollTop - clientHeight < 50;
      setShouldAutoScroll(isNearBottom);
    }
  };

  useEffect(() => {
    if (shouldAutoScroll && containerRef.current) {
      containerRef.current.scrollTo({
        top: containerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [logs, shouldAutoScroll]);

  const formatTime = (timestamp: string) => {
    try {
      // If it's already a time string like "18:31:26", just return it
      if (timestamp.includes(':') && timestamp.length < 10) return timestamp;
      return new Date(timestamp).toLocaleTimeString();
    } catch {
      return timestamp;
    }
  };

  return (
    <div className="bg-[#0f172a]/80 backdrop-blur-xl border border-white/10 rounded-3xl shadow-inner h-full flex flex-col font-mono text-xs overflow-hidden relative group">
      <div className="px-5 py-4 flex justify-between items-center border-b border-white/5 bg-white/5">
        <span className="text-slate-300 font-bold flex items-center gap-2.5 tracking-wide">
          <Terminal className="w-4 h-4 text-slate-400" />
          SYSTEM_LOGS
        </span>
        <div className="flex gap-2 opacity-80">
          <div className="w-3 h-3 rounded-full bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.6)]"></div>
          <div className="w-3 h-3 rounded-full bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.6)]"></div>
          <div className="w-3 h-3 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]"></div>
        </div>
      </div>
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="p-5 flex-1 overflow-y-auto space-y-2 text-slate-300 custom-scrollbar bg-[#020617]/50 shadow-inner"
      >
        {logs.length === 0 && <span className="text-slate-600 italic">Waiting for incoming signals...</span>}
        {logs.map((log, idx) => {
          const isClickable = log.message.includes("Automation completed") || log.message.includes("Run ID");
          return (
            <div
              key={idx}
              onClick={() => isClickable && onLogClick && onLogClick(log)}
              className={`flex gap-4 p-1.5 rounded-lg transition-colors group/line ${isClickable ? 'hover:bg-white/10 cursor-pointer' : 'hover:bg-white/5'
                }`}
            >
              <span className="text-slate-600 min-w-[70px] group-hover/line:text-slate-500 transition-colors font-medium">
                {formatTime(log.timestamp)}
              </span>
              <span className={`font-bold min-w-[50px] tracking-wide ${log.level === 'ERROR' ? 'text-rose-500' :
                log.level === 'WARN' ? 'text-amber-500' : 'text-cyan-500'
                }`}>
                {log.level}
              </span>
              <span className="text-slate-400 group-hover/line:text-slate-200 break-all flex-1">
                {log.message}
              </span>
              {isClickable && <ExternalLink className="w-3 h-3 text-slate-600 opacity-0 group-hover/line:opacity-100" />}
            </div>
          );
        })}
        <div ref={endRef} />
      </div>
    </div>
  );
};

export default LogViewer;