import React from 'react';
import { X, FileText } from 'lucide-react';

interface SpecViewerModalProps {
    isOpen: boolean;
    onClose: () => void;
    content: string;
    isLoading: boolean;
}

const SpecViewerModal: React.FC<SpecViewerModalProps> = ({ isOpen, onClose, content, isLoading }) => {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-[#020617]/90 backdrop-blur-md z-50 flex items-center justify-center p-4">
            <div className="bg-[#0f172a] border border-white/10 rounded-3xl shadow-2xl max-w-4xl w-full h-[80vh] flex flex-col relative overflow-hidden animate-in fade-in zoom-in duration-200">
                {/* Header */}
                <div className="flex justify-between items-center p-6 border-b border-white/5 bg-white/5">
                    <h3 className="text-xl font-bold text-white flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
                            <FileText className="w-5 h-5 text-cyan-400" />
                        </div>
                        Project Specification (spec.md)
                    </h3>
                    <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors rounded-full p-1 hover:bg-white/5">
                        <X className="w-6 h-6" />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-8 custom-scrollbar bg-[#020617]/50">
                    {isLoading ? (
                        <div className="flex items-center justify-center h-full text-slate-400 animate-pulse">
                            Loading spec.md...
                        </div>
                    ) : (
                        <pre className="font-mono text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">
                            {content || "No content found."}
                        </pre>
                    )}
                </div>
            </div>
        </div>
    );
};

export default SpecViewerModal;
