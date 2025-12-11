import React, { useState } from 'react';
import { Task, Status } from '../types';
import { CheckCircle2, Circle, Clock, Loader2, ListTodo, RotateCcw } from 'lucide-react';

interface TaskListProps {
  tasks: Task[];
  progress: number;
  onViewSpec?: () => void;
  onRetry?: () => void;
}

const TaskList: React.FC<TaskListProps> = ({ tasks, progress, onViewSpec, onRetry }) => {
  const [retryingId, setRetryingId] = useState<string | null>(null);
  const [retryResult, setRetryResult] = useState<{ id: string; success: boolean; message: string } | null>(null);

  const handleRetry = async (taskId: string) => {
    setRetryingId(taskId);
    setRetryResult(null);

    try {
      const response = await fetch(`/api/runs/${taskId}/retry`, {
        method: 'POST',
      });

      const data = await response.json();

      if (response.ok) {
        setRetryResult({ id: taskId, success: true, message: 'Retry triggered successfully!' });
        // Notify parent to refresh data
        if (onRetry) {
          setTimeout(onRetry, 1000);
        }
      } else {
        setRetryResult({ id: taskId, success: false, message: data.detail || 'Failed to retry' });
      }
    } catch (error) {
      setRetryResult({
        id: taskId,
        success: false,
        message: error instanceof Error ? error.message : 'Network error'
      });
    } finally {
      setRetryingId(null);
      // Clear result after 3 seconds
      setTimeout(() => setRetryResult(null), 3000);
    }
  };

  const getIcon = (status: Status) => {
    switch (status) {
      case Status.Completed: return <CheckCircle2 className="w-5 h-5 text-emerald-500 drop-shadow-[0_0_8px_rgba(16,185,129,0.5)]" />;
      case Status.InProgress: return <Loader2 className="w-5 h-5 text-cyan-400 animate-spin drop-shadow-[0_0_8px_rgba(34,211,238,0.5)]" />;
      case Status.Pending: return <Circle className="w-5 h-5 text-slate-600" />;
      case Status.Failed: return <Clock className="w-5 h-5 text-rose-500 drop-shadow-[0_0_8px_rgba(244,63,94,0.5)]" />;
    }
  };

  return (
    <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl shadow-2xl flex flex-col h-full hover:border-white/20 transition-all duration-300 group overflow-hidden">
      <div className="p-6 border-b border-white/5 relative z-10">
        <div className="flex justify-between items-end mb-5">
          <h3 className="font-bold text-white flex items-center gap-3 tracking-wide">
            <div className="bg-gradient-to-br from-blue-500/20 to-indigo-500/20 p-2 rounded-xl border border-blue-500/30">
              <ListTodo className="w-5 h-5 text-blue-400" />
            </div>
            Project Progress
          </h3>
          <span
            className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500 cursor-help"
            title="Based on ✅ markers and [x] checkboxes in spec.md"
          >
            {progress}%
          </span>
        </div>

        <div
          className="w-full bg-slate-800/50 rounded-full h-3 shadow-inner border border-white/5 cursor-help"
          title={`Progress: ${progress}% - Calculated from spec.md milestones`}
        >
          <div
            className="bg-gradient-to-r from-cyan-400 via-blue-500 to-indigo-500 h-full rounded-full transition-all duration-1000 shadow-[0_0_15px_rgba(6,182,212,0.5)] relative overflow-hidden"
            style={{ width: `${Math.max(progress, 2)}%` }}
          >
            <div className="absolute inset-0 bg-white/20 w-full h-full animate-[shimmer_2s_infinite]"></div>
          </div>
        </div>
        <p className="text-[10px] text-slate-500 mt-2 text-right">Based on ✅ markers in local spec.md</p>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-2 scrollbar-hide relative z-10">
        <h4 className="px-3 text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Latest Run Tasks</h4>
        {tasks.map(task => (
          <div key={task.id} className="group/item flex items-center gap-3 p-4 hover:bg-white/5 rounded-2xl transition-all border border-transparent hover:border-white/10 cursor-default relative">
            <div className="group-hover/item:scale-110 transition-transform duration-200">
              {getIcon(task.status)}
            </div>
            <span className={`text-sm font-medium transition-colors flex-1 ${task.status === Status.Completed ? 'text-slate-500 line-through' : 'text-slate-300 group-hover/item:text-white'}`}>
              {task.title}
            </span>
            {task.status === Status.Failed && (
              <button
                onClick={() => handleRetry(task.id)}
                disabled={retryingId === task.id}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-400 text-xs font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 active:scale-95"
                title="Retry this run"
              >
                {retryingId === task.id ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <RotateCcw className="w-3.5 h-3.5" />
                )}
                {retryingId === task.id ? 'Retrying...' : 'Retry'}
              </button>
            )}
            {retryResult && retryResult.id === task.id && (
              <div className={`absolute right-4 top-1/2 -translate-y-1/2 px-3 py-1.5 rounded-lg text-xs font-semibold animate-fadeIn ${retryResult.success
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                }`}>
                {retryResult.success ? '✓' : '✗'} {retryResult.message}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="p-4 border-t border-white/5 text-center bg-slate-950/30 rounded-b-3xl">
        <button
          onClick={onViewSpec}
          className="text-[10px] text-cyan-400 hover:text-cyan-300 font-bold tracking-widest uppercase transition-colors flex items-center justify-center gap-2 group/btn"
        >
          View Spec Details
          <span className="group-hover/btn:translate-x-1 transition-transform">→</span>
        </button>
      </div>
    </div>
  );
};

export default TaskList;