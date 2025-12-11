import React, { useState } from 'react';

interface ManualTriggerProps {
    onTrigger?: () => void;
}

export function ManualTrigger({ onTrigger }: ManualTriggerProps) {
    const [commitSha, setCommitSha] = useState('');
    const [branch, setBranch] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<{ success: boolean; message?: string; error?: string } | null>(null);

    const handleTrigger = async () => {
        if (!commitSha && !branch) {
            setResult({ success: false, error: 'Please provide either a commit SHA or branch name' });
            return;
        }

        setLoading(true);
        setResult(null);

        try {
            const response = await fetch('/api/manual-run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    commit_sha: commitSha || undefined,
                    branch: branch || undefined
                }),
            });

            const data = await response.json();

            if (response.ok) {
                setResult({ success: true, message: data.message || 'Automation triggered successfully!' });
                // Clear inputs on success
                setCommitSha('');
                setBranch('');
                // Notify parent to refresh data
                if (onTrigger) {
                    setTimeout(onTrigger, 1000);
                }
            } else {
                setResult({ success: false, error: data.detail || 'Failed to trigger automation' });
            }
        } catch (error) {
            setResult({
                success: false,
                error: error instanceof Error ? error.message : 'Network error'
            });
        } finally {
            setLoading(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !loading) {
            handleTrigger();
        }
    };

    return (
        <div className="manual-trigger-panel" style={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            borderRadius: '12px',
            padding: '24px',
            marginBottom: '24px',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
        }}>
            <h3 style={{
                margin: '0 0 16px 0',
                color: 'white',
                fontSize: '20px',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
            }}>
                <span style={{ fontSize: '24px' }}>⚡</span>
                Manual Trigger
            </h3>

            <p style={{
                color: 'rgba(255, 255, 255, 0.9)',
                fontSize: '14px',
                marginBottom: '20px',
            }}>
                Manually trigger automation for any commit or branch
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <input
                    type="text"
                    placeholder="Commit SHA (optional)"
                    value={commitSha}
                    onChange={(e) => setCommitSha(e.target.value)}
                    onKeyPress={handleKeyPress}
                    disabled={loading}
                    style={{
                        padding: '12px 16px',
                        borderRadius: '8px',
                        border: 'none',
                        fontSize: '14px',
                        background: 'rgba(255, 255, 255, 0.95)',
                        color: '#333',
                        outline: 'none',
                        transition: 'all 0.2s',
                    }}
                />

                <input
                    type="text"
                    placeholder="Branch name (required if no SHA)"
                    value={branch}
                    onChange={(e) => setBranch(e.target.value)}
                    onKeyPress={handleKeyPress}
                    disabled={loading}
                    style={{
                        padding: '12px 16px',
                        borderRadius: '8px',
                        border: 'none',
                        fontSize: '14px',
                        background: 'rgba(255, 255, 255, 0.95)',
                        color: '#333',
                        outline: 'none',
                        transition: 'all 0.2s',
                    }}
                />

                <button
                    onClick={handleTrigger}
                    disabled={loading || (!commitSha && !branch)}
                    style={{
                        padding: '12px 24px',
                        borderRadius: '8px',
                        border: 'none',
                        fontSize: '15px',
                        fontWeight: '600',
                        background: loading ? 'rgba(255, 255, 255, 0.3)' : 'rgba(255, 255, 255, 0.95)',
                        color: loading ? 'rgba(255, 255, 255, 0.7)' : '#667eea',
                        cursor: loading || (!commitSha && !branch) ? 'not-allowed' : 'pointer',
                        transition: 'all 0.2s',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '8px',
                        opacity: (!commitSha && !branch) ? 0.5 : 1,
                    }}
                    onMouseEnter={(e) => {
                        if (!loading && (commitSha || branch)) {
                            e.currentTarget.style.transform = 'translateY(-2px)';
                            e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
                        }
                    }}
                    onMouseLeave={(e) => {
                        e.currentTarget.style.transform = 'translateY(0)';
                        e.currentTarget.style.boxShadow = 'none';
                    }}
                >
                    {loading ? (
                        <>
                            <span className="spinner" style={{
                                width: '16px',
                                height: '16px',
                                border: '2px solid rgba(102, 126, 234, 0.3)',
                                borderTopColor: '#667eea',
                                borderRadius: '50%',
                                animation: 'spin 0.8s linear infinite',
                            }} />
                            Triggering...
                        </>
                    ) : (
                        <>
                            <span>🚀</span>
                            Trigger Automation
                        </>
                    )}
                </button>
            </div>

            {result && (
                <div
                    style={{
                        marginTop: '16px',
                        padding: '12px 16px',
                        borderRadius: '8px',
                        background: result.success
                            ? 'rgba(16, 185, 129, 0.15)'
                            : 'rgba(239, 68, 68, 0.15)',
                        border: `1px solid ${result.success ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
                        color: 'white',
                        fontSize: '14px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        animation: 'slideIn 0.3s ease-out',
                    }}
                >
                    <span>{result.success ? '✅' : '❌'}</span>
                    <span>{result.success ? result.message : result.error}</span>
                </div>
            )}

            <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
        </div>
    );
}
