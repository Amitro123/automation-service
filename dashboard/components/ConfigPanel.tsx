import React, { useState } from 'react';
import { Settings, Shield, GitPullRequest, Layers, Save, RotateCcw } from 'lucide-react';

interface Config {
    trigger_mode: string;
    group_automation_updates: boolean;
    post_review_on_pr: boolean;
    repository_owner: string;
    repository_name: string;
    llm_provider?: string;
    llm_model?: string;
    review_provider?: string;
}

interface ConfigPanelProps {
    config: Config | null;
    onSave?: (updates: Partial<Config>) => Promise<void>;
}

const ConfigPanel: React.FC<ConfigPanelProps> = ({ config, onSave }) => {
    const [editedConfig, setEditedConfig] = useState<Partial<Config>>({});
    const [saving, setSaving] = useState(false);
    const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle');

    if (!config) return null;

    const currentConfig = { ...config, ...editedConfig };
    const hasChanges = Object.keys(editedConfig).length > 0;

    const isRecommended =
        currentConfig.trigger_mode === 'pr' &&
        currentConfig.group_automation_updates === true;

    const handleChange = (key: keyof Config, value: any) => {
        setEditedConfig(prev => ({ ...prev, [key]: value }));
        setSaveStatus('idle');
    };

    const handleSave = async () => {
        if (!onSave || !hasChanges) return;

        setSaving(true);
        setSaveStatus('idle');

        try {
            await onSave(editedConfig);
            setSaveStatus('success');
            setEditedConfig({});
            setTimeout(() => setSaveStatus('idle'), 3000);
        } catch (error) {
            console.error('Failed to save config:', error);
            setSaveStatus('error');
        } finally {
            setSaving(false);
        }
    };

    const handleReset = () => {
        setEditedConfig({});
        setSaveStatus('idle');
    };

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
                        <div className={`p-2 rounded-lg ${currentConfig.trigger_mode === 'pr' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'}`}>
                            <GitPullRequest className="w-4 h-4" />
                        </div>
                        <div>
                            <div className="text-xs text-slate-400 font-medium uppercase tracking-wider">Trigger Mode</div>
                            <select
                                value={currentConfig.trigger_mode}
                                onChange={(e) => handleChange('trigger_mode', e.target.value)}
                                className="text-sm font-semibold text-slate-200 bg-transparent border-none outline-none cursor-pointer capitalize"
                            >
                                <option value="pr">PR Only</option>
                                <option value="push">Push Only</option>
                                <option value="both">PR & Push</option>
                            </select>
                        </div>
                    </div>
                    {currentConfig.trigger_mode !== 'pr' && (
                        <div className="text-[10px] text-amber-500 font-mono">Consider 'pr'</div>
                    )}
                </div>

                {/* Group Updates */}
                <div className="flex items-center justify-between p-3 rounded-xl bg-[#1e293b]/50 border border-white/5">
                    <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${currentConfig.group_automation_updates ? 'bg-cyan-500/10 text-cyan-400' : 'bg-slate-700/50 text-slate-400'}`}>
                            <Layers className="w-4 h-4" />
                        </div>
                        <div>
                            <div className="text-xs text-slate-400 font-medium uppercase tracking-wider">Group Updates</div>
                            <div className="text-sm font-semibold text-slate-200">{currentConfig.group_automation_updates ? 'Enabled' : 'Disabled'}</div>
                        </div>
                    </div>
                    <button
                        onClick={() => handleChange('group_automation_updates', !currentConfig.group_automation_updates)}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${currentConfig.group_automation_updates ? 'bg-cyan-500' : 'bg-slate-700'
                            }`}
                    >
                        <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${currentConfig.group_automation_updates ? 'translate-x-6' : 'translate-x-1'
                            }`} />
                    </button>
                </div>

                {/* Post Review on PR */}
                <div className="flex items-center justify-between p-3 rounded-xl bg-[#1e293b]/50 border border-white/5">
                    <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${currentConfig.post_review_on_pr ? 'bg-violet-500/10 text-violet-400' : 'bg-slate-700/50 text-slate-400'}`}>
                            <Shield className="w-4 h-4" />
                        </div>
                        <div>
                            <div className="text-xs text-slate-400 font-medium uppercase tracking-wider">PR Reviews</div>
                            <div className="text-sm font-semibold text-slate-200">{currentConfig.post_review_on_pr ? 'Enabled' : 'Disabled'}</div>
                        </div>
                    </div>
                    <button
                        onClick={() => handleChange('post_review_on_pr', !currentConfig.post_review_on_pr)}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${currentConfig.post_review_on_pr ? 'bg-violet-500' : 'bg-slate-700'
                            }`}
                    >
                        <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${currentConfig.post_review_on_pr ? 'translate-x-6' : 'translate-x-1'
                            }`} />
                    </button>
                </div>

            </div>

            {/* Save/Reset Buttons */}
            {hasChanges && (
                <div className="flex gap-2 relative z-10">
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-emerald-500 hover:bg-emerald-600 disabled:bg-emerald-500/50 text-white rounded-lg font-semibold text-sm transition-colors"
                    >
                        <Save className="w-4 h-4" />
                        {saving ? 'Saving...' : 'Save Changes'}
                    </button>
                    <button
                        onClick={handleReset}
                        disabled={saving}
                        className="px-4 py-2 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-700/50 text-white rounded-lg font-semibold text-sm transition-colors"
                    >
                        <RotateCcw className="w-4 h-4" />
                    </button>
                </div>
            )}

            {/* Status Messages */}
            {saveStatus === 'success' && (
                <div className="text-xs text-emerald-400 text-center font-mono">
                    ✓ Configuration saved successfully
                </div>
            )}
            {saveStatus === 'error' && (
                <div className="text-xs text-red-400 text-center font-mono">
                    ✗ Failed to save configuration
                </div>
            )}

            {!hasChanges && (
                <div className="pt-2 text-[10px] text-slate-500 font-mono text-center">
                    Or use <code>studioai configure</code> via CLI
                </div>
            )}
        </div>
    );
};

export default ConfigPanel;
