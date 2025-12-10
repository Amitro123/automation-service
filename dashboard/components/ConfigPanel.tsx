import React from 'react';
import { Settings, Shield, Zap, GitPullRequest, Layers, Clock } from 'lucide-react';

interface Config {
    trigger_mode: string;
    group_automation_updates: boolean;
    post_review_on_pr: boolean;
    repository_owner: string;
    repository_name: string;
}

interface ConfigPanelProps {
    config: Config | null;
}

const ConfigPanel: React.FC<ConfigPanelProps> = ({ config }) => {
    if (!config) return null;

    const isRecommended =
        config.trigger_mode === 'pr' &&
        config.group_automation_updates === true;

    return (
        <div className="bg-[#0f172a]/60 backdrop-blur-md border border-white/5 rounded-2xl p-6 flex flex-col gap-6 relative overflow-hidden group hover:border-white/10 transition-colors">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                <Settings className="w-24 h-24 text-slate-500" />
            </div>

            <div className="flex items-center justify-between relative z-10">
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <Settings className="w-5 h-5 text-violet-400" />
                    Configuration
                </h3>
                {isRecommended && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 tracking-wider uppercase backdrop-blur-md">
                        Recommended ✅
                    </span>
                )}
            </div>

            <div className="space-y-4 relative z-10">

                {/* Trigger Mode */}
                <div className="flex items-center justify-between p-3 rounded-xl bg-[#1e293b]/50 border border-white/5">
                    <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${config.trigger_mode === 'pr' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'}`}>
                            <GitPullRequest className="w-4 h-4" />
                        </div>
                        <div>
                            <div className="text-xs text-slate-400 font-medium uppercase tracking-wider">Trigger Mode</div>
                            <div className="text-sm font-semibold text-slate-200 capitalize">{config.trigger_mode === 'both' ? 'PR & Push' : config.trigger_mode}</div>
                        </div>
                    </div>
                    {config.trigger_mode !== 'pr' && (
                        <div className="text-[10px] text-amber-500 font-mono">Consider 'pr'</div>
                    )}
                </div>

                {/* Group Config */}
                <div className="flex items-center justify-between p-3 rounded-xl bg-[#1e293b]/50 border border-white/5">
                    <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${config.group_automation_updates ? 'bg-cyan-500/10 text-cyan-400' : 'bg-slate-700/50 text-slate-400'}`}>
                            <Layers className="w-4 h-4" />
                        </div>
                        <div>
                            <div className="text-xs text-slate-400 font-medium uppercase tracking-wider">Group Updates</div>
                            <div className="text-sm font-semibold text-slate-200">{config.group_automation_updates ? 'Enabled' : 'Disabled'}</div>
                        </div>
                    </div>
                </div>

                {/* Post Review */}
                <div className="flex items-center justify-between p-3 rounded-xl bg-[#1e293b]/50 border border-white/5">
                    <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${config.post_review_on_pr ? 'bg-violet-500/10 text-violet-400' : 'bg-slate-700/50 text-slate-400'}`}>
                            <Shield className="w-4 h-4" />
                        </div>
                        <div>
                            <div className="text-xs text-slate-400 font-medium uppercase tracking-wider">PR Reviews</div>
                            <div className="text-sm font-semibold text-slate-200">{config.post_review_on_pr ? 'Enabled' : 'Disabled'}</div>
                        </div>
                    </div>
                </div>

            </div>

            <div className="pt-2 text-[10px] text-slate-500 font-mono text-center">
                Read-only. Use <code>studioai configure</code> to edit.
            </div>
        </div>
    );
};

export default ConfigPanel;
