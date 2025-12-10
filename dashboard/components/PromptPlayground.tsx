import React, { useState, useEffect } from 'react';
import { Code, FileText, Save, RotateCcw, Sparkles } from 'lucide-react';

interface PromptPlaygroundProps {
    initialCodeReviewPrompt?: string;
    initialDocsPrompt?: string;
    onSave?: (prompts: { code_review_system_prompt?: string; docs_update_system_prompt?: string }) => Promise<void>;
}

const PromptPlayground: React.FC<PromptPlaygroundProps> = ({
    initialCodeReviewPrompt = '',
    initialDocsPrompt = '',
    onSave
}) => {
    const [codeReviewPrompt, setCodeReviewPrompt] = useState(initialCodeReviewPrompt);
    const [docsPrompt, setDocsPrompt] = useState(initialDocsPrompt);
    const [activeTab, setActiveTab] = useState<'code_review' | 'docs'>('code_review');
    const [saving, setSaving] = useState(false);
    const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle');

    useEffect(() => {
        setCodeReviewPrompt(initialCodeReviewPrompt);
        setDocsPrompt(initialDocsPrompt);
    }, [initialCodeReviewPrompt, initialDocsPrompt]);

    const hasChanges =
        codeReviewPrompt !== initialCodeReviewPrompt ||
        docsPrompt !== initialDocsPrompt;

    const handleSave = async () => {
        if (!onSave || !hasChanges) return;

        setSaving(true);
        setSaveStatus('idle');

        try {
            const updates: any = {};
            if (codeReviewPrompt !== initialCodeReviewPrompt) {
                updates.code_review_system_prompt = codeReviewPrompt;
            }
            if (docsPrompt !== initialDocsPrompt) {
                updates.docs_update_system_prompt = docsPrompt;
            }

            await onSave(updates);
            setSaveStatus('success');
            setTimeout(() => setSaveStatus('idle'), 3000);
        } catch (error) {
            console.error('Failed to save prompts:', error);
            setSaveStatus('error');
        } finally {
            setSaving(false);
        }
    };

    const handleReset = () => {
        setCodeReviewPrompt(initialCodeReviewPrompt);
        setDocsPrompt(initialDocsPrompt);
        setSaveStatus('idle');
    };

    const currentPrompt = activeTab === 'code_review' ? codeReviewPrompt : docsPrompt;
    const setCurrentPrompt = activeTab === 'code_review' ? setCodeReviewPrompt : setDocsPrompt;

    return (
        <div className="bg-[#0f172a]/60 backdrop-blur-md border border-white/5 rounded-2xl p-6 flex flex-col gap-4 relative overflow-hidden group hover:border-white/10 transition-colors">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                <Sparkles className="w-24 h-24 text-slate-500" />
            </div>

            {/* Header */}
            <div className="flex items-center justify-between relative z-10">
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-violet-400" />
                    Prompt Playground
                </h3>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-violet-500/10 text-violet-400 border border-violet-500/20 tracking-wider uppercase">
                    Live Edit
                </span>
            </div>

            {/* Tabs */}
            <div className="flex gap-2 relative z-10">
                <button
                    onClick={() => setActiveTab('code_review')}
                    className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-semibold text-sm transition-colors ${activeTab === 'code_review'
                            ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                            : 'bg-slate-800/50 text-slate-400 border border-white/5 hover:bg-slate-700/50'
                        }`}
                >
                    <Code className="w-4 h-4" />
                    Code Review
                </button>
                <button
                    onClick={() => setActiveTab('docs')}
                    className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-semibold text-sm transition-colors ${activeTab === 'docs'
                            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                            : 'bg-slate-800/50 text-slate-400 border border-white/5 hover:bg-slate-700/50'
                        }`}
                >
                    <FileText className="w-4 h-4" />
                    Docs Update
                </button>
            </div>

            {/* Prompt Editor */}
            <div className="relative z-10">
                <textarea
                    value={currentPrompt}
                    onChange={(e) => setCurrentPrompt(e.target.value)}
                    className="w-full h-64 px-4 py-3 bg-[#1e293b]/80 border border-white/10 rounded-xl text-slate-200 text-sm font-mono resize-none focus:outline-none focus:border-violet-500/50 transition-colors"
                    placeholder={`Enter ${activeTab === 'code_review' ? 'code review' : 'documentation'} prompt...`}
                />
                <div className="mt-2 text-xs text-slate-500 font-mono">
                    {currentPrompt.length} characters
                </div>
            </div>

            {/* Action Buttons */}
            {hasChanges && (
                <div className="flex gap-2 relative z-10">
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-violet-500 hover:bg-violet-600 disabled:bg-violet-500/50 text-white rounded-lg font-semibold text-sm transition-colors"
                    >
                        <Save className="w-4 h-4" />
                        {saving ? 'Saving...' : 'Save Prompts'}
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
                <div className="text-xs text-emerald-400 text-center font-mono relative z-10">
                    ✓ Prompts saved successfully - changes will apply to next run
                </div>
            )}
            {saveStatus === 'error' && (
                <div className="text-xs text-red-400 text-center font-mono relative z-10">
                    ✗ Failed to save prompts
                </div>
            )}

            {!hasChanges && (
                <div className="text-[10px] text-slate-500 font-mono text-center relative z-10">
                    Edit prompts to customize LLM behavior
                </div>
            )}
        </div>
    );
};

export default PromptPlayground;
