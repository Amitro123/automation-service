/**
 * API Service for connecting to GitHub Automation Agent FastAPI backend
 * 
 * Backend runs on port 8080 by default (configurable via .env)
 * Dashboard runs on port 5173 (Vite dev server)
 */

import { DashboardMetrics, Repository, LogEntry, Task, Status, PRItem, BugItem, RunHistoryItem } from '../types';

// Use environment variable or default to localhost:8080
// Use relative path to leverage Vite proxy (configured in vite.config.ts)
const API_BASE_URL = '/api';

export interface RepositoryStatus {
  name: string;
  hasReadme: boolean;
  hasSpec: boolean;
  branch: string;
  isSecure: boolean;
  lastPush?: string;
  openIssues: number;
  openPRs: number;
}

export interface HealthStatus {
  status: string;
  service: string;
  version: string;
  uptime: string;
}

export async function fetchDashboardMetrics(): Promise<DashboardMetrics> {
  try {
    const response = await fetch(`${API_BASE_URL}/metrics`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch dashboard metrics:', error);
    // Return mock data as fallback
    return getMockMetrics();
  }
}

export async function fetchLogs(limit: number = 50): Promise<Array<{ timestamp: string; level: string; message: string }>> {
  try {
    const response = await fetch(`${API_BASE_URL}/logs?limit=${limit}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch logs:', error);
    return [];
  }
}

export async function fetchRepositoryStatus(repoName: string): Promise<RepositoryStatus | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/repository/${repoName}/status`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch repository status:', error);
    return null;
  }
}

export async function fetchHealthStatus(): Promise<HealthStatus | null> {
  try {
    const response = await fetch(`${API_BASE_URL.replace('/api', '')}/`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch health status:', error);
    return null;
  }
}

export async function fetchArchitecture(): Promise<{ diagram: string } | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/architecture`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch architecture:', error);
    return null;
  }
}

export type { RunHistoryItem };

export async function fetchHistory(limit: number = 50): Promise<Array<RunHistoryItem>> {
  try {
    const response = await fetch(`${API_BASE_URL}/history?limit=${limit}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch history:', error);
    return [];
  }
}

export async function checkBackendConnection(): Promise<boolean> {
  try {
    const health = await fetchHealthStatus();
    return health?.status === 'healthy';
  } catch {
    return false;
  }
}

// Mock data fallback
function getMockMetrics(): DashboardMetrics {
  return {
    coverage: {
      total: 78,
      uncoveredLines: 124,
      mutationScore: 65,
      mutationStatus: 'success',
      mutationReason: 'All tests passed'
    },
    llm: {
      tokensUsed: 145020,
      estimatedCost: 1.45,
      efficiencyScore: 88,
      sessionMemoryUsage: 42,
      totalRuns: 12,
    },
    tasks: [
      { id: 't1', title: 'Implement JWT Authentication', status: Status.Completed },
      { id: 't2', title: 'Setup Mutation Testing (mutmut)', status: Status.InProgress },
      { id: 't3', title: 'Create Mermaid Diagram Generator', status: Status.InProgress },
      { id: 't4', title: 'Integrate Gemini 2.5 Flash', status: Status.Pending },
      { id: 't5', title: 'Finalize Security Audit', status: Status.Pending },
    ],
    bugs: [],
    prs: [],
    logs: [
      { timestamp: new Date().toLocaleTimeString(), level: 'INFO', message: 'StudioAI Backend Service Started' },
      { timestamp: new Date().toLocaleTimeString(), level: 'INFO', message: 'Connected to GitHub Webhook' },
    ],
    security: {
      isSecure: true,
      vulnerabilities: 0,
      lastScan: new Date().toISOString(),
    },
    projectProgress: 45,
  };
}

export async function fetchSpecContent(): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/spec`);
  if (!response.ok) {
    throw new Error('Failed to fetch spec content');
  }
  const data = await response.json();
  return data.content || 'No spec content available';
}

export async function fetchConfig() {
  const response = await fetch(`${API_BASE_URL}/config`);
  if (!response.ok) throw new Error('Failed to fetch config');
  return response.json();
}

export async function updateConfig(updates: any) {
  const response = await fetch(`${API_BASE_URL}/config`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates)
  });
  if (!response.ok) throw new Error('Failed to update config');
  return response.json();
}
